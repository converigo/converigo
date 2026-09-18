"""XLS to XLSX converter plugin.

Converts legacy Excel files (BIFF5/BIFF8) to modern XLSX format using LibreOffice headless.
Includes pure-Python OLE2 preflight, process-tree containment, and concurrency guard.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from app.core.settings import settings
from app.plugins.base import ConverterPlugin
from app.utils.ole2_preflight import BiffClassification, classify_xls, is_acceptable
from app.utils.soffice_runner import (
    SofficeError,
    SofficeNotFoundError,
    SofficeTimeoutError,
    SofficeValidationError,
    convert_xls_to_xlsx,
)

logger = logging.getLogger(__name__)

# Module-scoped concurrency guard: max 1 active LibreOffice conversion
_CONVERSION_SEMAPHORE: Optional[asyncio.Semaphore] = None
_SEMAPHORE_LOCK = asyncio.Lock()


class XlsToXlsxPlugin(ConverterPlugin):
    """Convert XLS (Excel 97-2003) to XLSX format.
    
    Features:
    - Pure-Python OLE2 preflight (no olefile dependency)
    - Accepts BIFF5 (Excel 5.0/95) and BIFF8 (Excel 97-2003)
    - Rejects BIFF2/3/4, OOXML masquerades, corrupt files
    - LibreOffice headless with per-request temp profiles
    - Process-tree containment + SIGTERM→SIGKILL timeout ladder
    - Output validation via openpyxl
    - Retry-on-SIGABRT (1 attempt)
    - Concurrency guard: max 1 active conversion (503 on overflow)
    """

    slug = "xls-to-xlsx"
    name = "XLS to XLSX"
    description = "Convert legacy Excel files (97-2003 format) to modern XLSX."
    category = "document"
    engine = "document"
    source_formats = ["xls"]
    target_formats = ["xlsx"]
    icon = "📄"
    color = "blue"
    goal = "document"
    use_case = "Best for converting legacy Excel files to modern format."
    priority = 80
    quality = 90
    compatibility = 95

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """Convert XLS to XLSX.
        
        Args:
            source_path: Path to source XLS file
            target_format: Target format (should be "xlsx")
            output_dir: Output directory (required)
            temp_dir: Temporary directory (not used)
        
        Returns:
            Path to generated XLSX file
        
        Raises:
            RuntimeError: On preflight rejection, timeout, validation failure, or
                         concurrency limit exceeded
        """
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError(
                f"XlsToXlsxPlugin only supports XLS -> XLSX conversion, "
                f"not {source_path.suffix} -> {target_format}."
            )
        
        output_dir = output_dir or settings.OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: OLE2 preflight
        classification = classify_xls(source_path)
        logger.info(f"Preflight: {source_path.name} classified as {classification.value}")
        
        if not is_acceptable(classification):
            # Honest error messages per classification
            if classification == BiffClassification.NOT_OLE2:
                raise RuntimeError(
                    "File is not a valid XLS file (not OLE2 format). "
                    "Please upload a genuine Excel 97-2003 (.xls) file."
                )
            elif classification == BiffClassification.NO_WORKBOOK_STREAM:
                raise RuntimeError(
                    "File appears corrupt or is not a valid Excel file "
                    "(missing Workbook stream)."
                )
            elif classification == BiffClassification.UNSUPPORTED_BIFF:
                raise RuntimeError(
                    "This Excel file uses an unsupported legacy format. "
                    "Please save it in Excel 97-2003 format first."
                )
            elif classification == BiffClassification.CORRUPT:
                raise RuntimeError(
                    "File appears truncated or corrupt. Please check the file and try again."
                )
            else:
                raise RuntimeError(f"Unsupported XLS format: {classification.value}")
        
        # Step 2: Acquire concurrency guard
        global _CONVERSION_SEMAPHORE
        async with _SEMAPHORE_LOCK:
            if _CONVERSION_SEMAPHORE is None:
                _CONVERSION_SEMAPHORE = asyncio.Semaphore(
                    settings.XLS_CONVERTER_MAX_CONCURRENT
                )
        
        if not _CONVERSION_SEMAPHORE.locked() and _CONVERSION_SEMAPHORE._value == 0:
            # Queue is full
            raise RuntimeError(
                "Server is currently processing the maximum number of XLS conversions. "
                "Please try again in a moment."
            )
        
        try:
            acquired = await asyncio.wait_for(
                _CONVERSION_SEMAPHORE.acquire(),
                timeout=settings.XLS_CONVERTER_QUEUE_TIMEOUT,
            )
            if not acquired:
                raise RuntimeError(
                    "Conversion queue is full. Please try again later."
                )
        except asyncio.TimeoutError:
            raise RuntimeError(
                "Conversion queue timeout. Please try again later."
            )
        
        try:
            # Step 3: LibreOffice conversion
            output_path = await convert_xls_to_xlsx(
                input_path=source_path,
                output_dir=output_dir,
                soffice_path=settings.XLS_CONVERTER_SOFFICE_PATH,
                timeout_seconds=settings.XLS_CONVERTER_TIMEOUT,
                sigterm_grace_seconds=settings.XLS_CONVERTER_SIGTERM_GRACE,
                max_retries=1,
            )
            
            logger.info(f"Successfully converted {source_path.name} to {output_path.name}")
            return output_path
        
        except SofficeNotFoundError as e:
            logger.error(f"LibreOffice not found: {e}")
            raise RuntimeError(
                "Conversion service is not available. Please contact support."
            )
        except SofficeTimeoutError as e:
            logger.warning(f"Conversion timeout: {e}")
            raise RuntimeError(
                "Conversion took too long. The file may be too large or complex. "
                "Please try a smaller file."
            )
        except SofficeValidationError as e:
            logger.error(f"Output validation failed: {e}")
            raise RuntimeError(
                "Conversion completed but output validation failed. "
                "The source file may be corrupt or use unsupported features."
            )
        except SofficeError as e:
            logger.error(f"LibreOffice conversion failed: {e}")
            raise RuntimeError(
                "Conversion failed. The file may be corrupt or use unsupported features."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during XLS conversion: {e}")
            raise RuntimeError("An unexpected error occurred during conversion.")
        
        finally:
            _CONVERSION_SEMAPHORE.release()

