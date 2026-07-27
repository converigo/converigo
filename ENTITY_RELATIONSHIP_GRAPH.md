# Entity Relationship Graph

This graph is derived from active converter relationships and the current format knowledge dataset. It highlights format clusters and the direction of conversions.

## Relationship chains by primary cluster

### PDF / Office / Document cluster
PDF
↓
DOCX → PPT → PPTX → XLSX → OODT / ODS / ODP
↓
JPG / PNG / WEBP
↓
Image formats for export, display, and rasterization.

### Image cluster
JPG / JPEG → PNG → WEBP → SVG → TIFF → BMP → HEIC

### Audio / Video cluster
MP4 → MP3 / AAC / M4A / OGG / WAV / FLAC

### Archive cluster
ZIP / RAR / TAR / 7Z / GZ / GZIP

## Direct converter edges from active inventory

- 7Z → 7Z
- AAC → MP4
- AVIF → JPEG, JPG
- BMP → JPG
- DOCX → JPG, PDF, PPT, XLSX
- FLAC → MP4
- GZ → GZ, GZIP
- GZIP → GZ, GZIP
- HEIC → JPG
- JPEG → AVIF, PNG
- JPG → AVIF, BMP, DOCX, HEIC, PNG, PPT, TIFF
- M4A → MP4
- MP3 → MP4
- MP4 → AAC, FLAC, M4A, MP3, OGG, WAV
- ODS → XLSX
- ODT → PDF
- OGG → MP4
- PDF → DOCX, ODT, PDF, PPT, PPTX, XLSX
- PNG → JPEG, JPG, SVG, WEBP
- PPT → DOCX, JPG, PDF, XLSX
- PPTX → PDF
- RAR → RAR
- SVG → PNG
- TAR → TAR
- TIFF → JPG
- WAV → MP4
- WEBP → PNG
- XLSX → DOCX, ODS, PDF, PPT
- ZIP → ZIP
