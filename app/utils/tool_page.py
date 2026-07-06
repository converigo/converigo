from pathlib import Path
from typing import Dict, List

BASE_URL = "/tools"


def normalize_slug(slug: str) -> str:
    return slug.strip().lower().replace(" ", "-")


def tool_page_entry(
    title: str,
    description: str,
    faq: List[Dict[str, str]],
    upload_form: Dict[str, str],
    related_tools: List[Dict[str, str]],
    seo: Dict[str, str],
) -> Dict[str, object]:
    return {
        "title": title,
        "description": description,
        "faq": faq,
        "upload_form": upload_form,
        "related_tools": related_tools,
        "seo": seo,
    }


TOOL_PAGES = {
    "mp4-to-mp3": tool_page_entry(
        title="MP4 to MP3 Converter",
        description="Convert MP4 video files into MP3 audio quickly and reliably.",
        faq=[
            {"question": "What file types can I upload?", "answer": "Upload MP4 video files only."},
            {"question": "What output do I get?", "answer": "A high-quality MP3 audio file."},
        ],
        upload_form={
            "action": "/convert",
            "method": "post",
            "accept": ".mp4",
            "button_text": "Convert MP4 to MP3",
        },
        related_tools=[
            {"slug": "png-to-jpg", "title": "PNG to JPG"},
            {"slug": "pdf-to-word", "title": "PDF to Word"},
        ],
        seo={"title": "MP4 to MP3 | Convertin", "description": "Convert MP4 video to MP3 audio with Convertin.", "keywords": "mp4 to mp3, video to audio, file converter"},
    ),
    "png-to-jpg": tool_page_entry(
        title="PNG to JPG Converter",
        description="Convert PNG images into JPG format with browser-friendly optimization.",
        faq=[
            {"question": "Can I convert transparent PNGs?", "answer": "Yes, transparent PNGs are supported, but transparency becomes a white background in JPG format."},
            {"question": "How do I get the converted image?", "answer": "You will receive a downloadable JPG file after conversion."},
        ],
        upload_form={
            "action": "/upload",
            "method": "post",
            "accept": ".png",
            "button_text": "Upload PNG",
        },
        related_tools=[
            {"slug": "mp4-to-mp3", "title": "MP4 to MP3"},
            {"slug": "pdf-to-word", "title": "PDF to Word"},
        ],
        seo={"title": "PNG to JPG | Convertin", "description": "Convert PNG images to JPG format.", "keywords": "png to jpg, image converter, photo converter"},
    ),
    "pdf-to-word": tool_page_entry(
        title="PDF to Word Converter",
        description="Transform PDF documents into editable Word files in seconds.",
        faq=[
            {"question": "Does this preserve layout?", "answer": "The converter preserves basic layout and text formatting."},
            {"question": "What file formats are allowed?", "answer": "Upload PDF files to receive DOCX output."},
        ],
        upload_form={
            "action": "/upload",
            "method": "post",
            "accept": ".pdf",
            "button_text": "Upload PDF",
        },
        related_tools=[
            {"slug": "mp4-to-mp3", "title": "MP4 to MP3"},
            {"slug": "png-to-jpg", "title": "PNG to JPG"},
        ],
        seo={"title": "PDF to Word | Convertin", "description": "Convert PDF to Word documents with ease.", "keywords": "pdf to word, document converter, docx converter"},
    ),
}
