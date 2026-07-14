# Converter Contract

## Purpose

Every Converigo converter definition must declare a minimum contract so that landing pages, SEO metadata, upload flows, and regression coverage can rely on the same structure.

## Required Fields

Each converter record must define the following fields:

- id: unique internal identifier for the converter
- slug: URL-safe slug used by routes and landing pages
- name: human-readable converter name
- category: converter category such as audio, image, document, or video
- description: short summary of the conversion workflow
- input formats: list of supported source formats
- output formats: list of supported target formats
- accepted MIME types: MIME types accepted by the upload form
- max upload size: maximum upload size in bytes
- conversion engine: engine identifier used for processing
- landing path: public landing-page path for the converter
- canonical URL: canonical public URL for SEO
- SEO status: whether SEO metadata has been prepared for the converter
- schema status: whether structured data has been prepared for the converter
- FAQ status: whether FAQ content has been prepared for the converter
- regression sample: path to a sample file used for regression testing
- supported platforms: list of supported client platforms such as web, mobile, api
- lifecycle status: one of active, deprecated, or beta

## Required Shape

```json
{
  "id": "mp4-to-mp3",
  "slug": "mp4-to-mp3",
  "name": "MP4 to MP3",
  "category": "audio",
  "description": "Convert MP4 video files into MP3 audio.",
  "input_formats": ["mp4"],
  "output_formats": ["mp3"],
  "accepted_mime_types": ["video/mp4"],
  "max_upload_size": 104857600,
  "conversion_engine": "ffmpeg",
  "landing_path": "/mp4-to-mp3",
  "canonical_url": "https://converigo.com/mp4-to-mp3",
  "seo_status": "ready",
  "schema_status": "ready",
  "faq_status": "ready",
  "regression_sample": "tests/sample.mp4",
  "supported_platforms": ["web"],
  "lifecycle_status": "active"
}
```

## Compliance Rules

Every future converter must:

1. Include every required field above.
2. Use a non-empty string for id, slug, name, category, description, landing_path, canonical_url, conversion_engine, and lifecycle_status.
3. Ensure input_formats and output_formats contain at least one supported format.
4. Ensure accepted_mime_types contains at least one MIME type.
5. Ensure supported_platforms contains at least one platform.
6. Ensure regression_sample points to a file that exists in the repository when the converter is active.
7. Keep lifecycle_status set to one of active, deprecated, or beta.

## Example: MP4 → MP3

See the example contract in app/data/converters/mp4-to-mp3.contract.json.
