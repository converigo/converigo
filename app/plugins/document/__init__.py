from __future__ import annotations

from app.plugins.document.docx_to_ppt import DOCXToPPTPlugin
from app.plugins.document.docx_to_xlsx import DOCXToXLSXPlugin
from app.plugins.document.excel_to_pdf import ExcelToPDFPlugin
from app.plugins.document.jpg_to_pdf import JPGToPDFPlugin
from app.plugins.document.office_conversion_plugins import (
    DOCXToJPGPlugin,
    PDFToWordPlugin,
    PPTToJPGPlugin,
    WordToPDFPlugin,
)
from app.plugins.document.pdf_to_excel import PDFToExcelPlugin
from app.plugins.document.pdf_to_ppt import PDFToPPTPlugin
from app.plugins.document.pdf_to_word import PDFToWordPlugin
from app.plugins.document.ppt_to_docx import PPTToDOCXPlugin
from app.plugins.document.ppt_to_pdf import PPTToPDFPlugin
from app.plugins.document.ppt_to_xlsx import PPTToXLSXPlugin
from app.plugins.document.word_to_pdf import WordToPDFPlugin
from app.plugins.document.xlsx_to_docx import XLSXToDOCXPlugin
from app.plugins.document.xlsx_to_ppt import XLSXToPPTPlugin

__all__ = [
    "ExcelToPDFPlugin",
    "JPGToPDFPlugin",
    "PDFToExcelPlugin",
    "PDFToPPTPlugin",
    "PDFToWordPlugin",
    "PPTToPDFPlugin",
    "WordToPDFPlugin",
    "DOCXToJPGPlugin",
    "DOCXToPPTPlugin",
    "DOCXToXLSXPlugin",
    "PPTToDOCXPlugin",
    "PPTToJPGPlugin",
    "PPTToXLSXPlugin",
    "XLSXToDOCXPlugin",
    "XLSXToPPTPlugin",
]
