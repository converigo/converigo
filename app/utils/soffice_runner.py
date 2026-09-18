"""LibreOffice headless runner for XLS→XLSX conversion.

Process-tree containment, timeout ladder (SIGTERM→SIGKILL), per-request temp profiles,
output validation via openpyxl, and retry-on-SIGABRT logic.
"""

import asyncio
import logging
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SofficeError(Exception):
    """Base exception for LibreOffice conversion failures."""
    pass


class SofficeTimeoutError(SofficeError):
    """Conversion exceeded timeout limits."""
    pass


class SofficeValidationError(SofficeError):
    """Output file failed validation."""
    pass


class SofficeNotFoundError(SofficeError):
    """soffice executable not found."""
    pass


async def convert_xls_to_xlsx(
    input_path: Path,
    output_dir: Path,
    soffice_path: str = "soffice",
    timeout_seconds: int = 300,
    sigterm_grace_seconds: int = 5,
    max_retries: int = 1,
) -> Path:
    """Convert XLS to XLSX using LibreOffice headless.
    
    Args:
        input_path: Path to source XLS file
        output_dir: Directory for output XLSX file
        soffice_path: Path/command for soffice executable
        timeout_seconds: Total conversion timeout
        sigterm_grace_seconds: Grace period between SIGTERM and SIGKILL
        max_retries: Retry attempts on SIGABRT (0=no retry, 1=one retry)
    
    Returns:
        Path to generated XLSX file
    
    Raises:
        SofficeNotFoundError: soffice executable not found
        SofficeTimeoutError: Conversion exceeded timeout
        SofficeValidationError: Output validation failed
        SofficeError: Other conversion failures
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check soffice availability
    try:
        result = await asyncio.create_subprocess_exec(
            soffice_path, "--version",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        await asyncio.wait_for(result.wait(), timeout=5.0)
    except (FileNotFoundError, asyncio.TimeoutError):
        raise SofficeNotFoundError(f"soffice not found or not responding: {soffice_path}")
    
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        try:
            return await _convert_attempt(
                input_path=input_path,
                output_dir=output_dir,
                soffice_path=soffice_path,
                timeout_seconds=timeout_seconds,
                sigterm_grace_seconds=sigterm_grace_seconds,
            )
        except SofficeError as e:
            last_error = e
            # Retry only on SIGABRT-like errors
            if "aborted" in str(e).lower() or "signal" in str(e).lower():
                attempt += 1
                if attempt <= max_retries:
                    logger.warning(f"Retry {attempt}/{max_retries} after error: {e}")
                    await asyncio.sleep(0.5)  # Brief delay before retry
                    continue
            raise
    
    raise last_error or SofficeError("Conversion failed after retries")



async def _convert_attempt(
    input_path: Path,
    output_dir: Path,
    soffice_path: str,
    timeout_seconds: int,
    sigterm_grace_seconds: int,
) -> Path:
    """Single conversion attempt with process-tree containment."""
    # Create isolated temp profile for this request
    temp_profile = tempfile.mkdtemp(prefix="soffice_profile_")
    
    try:
        # Expected output filename (LibreOffice replaces .xls → .xlsx)
        expected_output = output_dir / (input_path.stem + ".xlsx")
        if expected_output.exists():
            expected_output.unlink()
        
        # Launch soffice in headless mode with isolated profile
        cmd = [
            soffice_path,
            "--headless",
            "--invisible",
            "--nocrashreport",
            "--nodefault",
            "--nofirststartwizard",
            "--nolockcheck",
            "--nologo",
            "--norestore",
            f"-env:UserInstallation=file:///{temp_profile.replace(os.sep, '/')}",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(output_dir),
            str(input_path),
        ]
        
        logger.debug(f"Launching: {' '.join(cmd)}")
        
        # Windows: CREATE_NEW_PROCESS_GROUP for process-tree containment
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        
        # Wait with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )
            returncode = proc.returncode
        except asyncio.TimeoutError:
            # Timeout: escalate SIGTERM → SIGKILL
            logger.warning(f"Conversion timeout after {timeout_seconds}s, sending SIGTERM")
            try:
                if os.name == "nt":
                    # Windows: CTRL_BREAK_EVENT to process group
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    proc.terminate()
                
                await asyncio.wait_for(proc.wait(), timeout=sigterm_grace_seconds)
            except asyncio.TimeoutError:
                logger.warning(f"SIGTERM grace period expired, sending SIGKILL")
                proc.kill()
                await proc.wait()
            
            raise SofficeTimeoutError(
                f"Conversion exceeded {timeout_seconds}s timeout"
            )
        
        # Check exit code
        if returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""
            raise SofficeError(
                f"soffice exited with code {returncode}: {stderr_text[:500]}"
            )
        
        # Validate output exists
        if not expected_output.exists():
            raise SofficeError(
                f"Conversion succeeded but output not found: {expected_output}"
            )
        
        # Validate output is valid XLSX via openpyxl
        try:
            import openpyxl
            wb = openpyxl.load_workbook(expected_output, read_only=True, data_only=True)
            wb.close()
        except Exception as e:
            raise SofficeValidationError(
                f"Output XLSX validation failed: {e}"
            )
        
        logger.info(f"Converted {input_path.name} → {expected_output.name}")
        return expected_output
    
    finally:
        # Clean up temp profile
        try:
            shutil.rmtree(temp_profile, ignore_errors=True)
        except:
            pass
