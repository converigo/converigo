# JSON Schema V1 Proposal

## 1. Tujuan

Dokumen ini mengusulkan schema JSON V1 untuk seluruh converter di Converigo. Schema ini dirancang untuk menjadi satu sumber kebenaran untuk landing page, SEO, FAQ, hub, rekomendasi, sitemap, dan structured data.

## 2. Draft Schema V1

Contoh JSON yang konsisten:

```json
{
  "slug": "png-to-webp",
  "title": "PNG to WEBP Converter",
  "description": "Convert PNG images to WEBP online for free.",
  "category": "image",
  "source": "png",
  "target": "webp",
  "active": true,
  "popular": true,
  "featured": false,
  "tags": ["image", "compression", "webp"],
  "upload_form": {
    "action": "/upload",
    "method": "post",
    "accept": ".png",
    "button_text": "Upload PNG"
  },
  "hero": {
    "eyebrow": "Converter tool",
    "title": "Convert PNG to WEBP Online Free",
    "description": "Convert PNG images to WEBP online for free.",
    "panel_label": "Ready to convert",
    "panel_title": "Upload a PNG file and receive a WEBP result in seconds."
  },
  "features": [
    {
      "title": "High-quality output",
      "text": "Preserve image quality while reducing file size."
    }
  ],
  "supported_formats": {
    "input": ["PNG"],
    "output": ["WEBP"],
    "description": "PNG input, WEBP output"
  },
  "how_to_use": [
    {
      "title": "Upload your file",
      "description": "Select a PNG file to begin the conversion."
    }
  ],
  "about_formats": [
    {
      "title": "What is PNG?",
      "text": "PNG is a raster image format that preserves image quality."
    }
  ],
  "cta": {
    "eyebrow": "Ready to convert",
    "title": "Convert PNG files to WEBP in seconds",
    "text": "Upload your file and receive a ready-to-use result instantly.",
    "primary_text": "Convert now",
    "secondary_text": "Read FAQs",
    "primary_href": "#converter",
    "secondary_href": "#faq"
  },
  "faq": [
    {
      "question": "Why convert PNG to WEBP?",
      "answer": "WEBP offers smaller files and good quality."
    }
  ],
  "benefits": [
    {
      "title": "Smaller file sizes",
      "text": "Reduce bandwidth and improve page speed."
    }
  ],
  "use_cases": [
    "Website optimization",
    "Faster page loads"
  ],
  "related_tools": [
    { "slug": "png-to-jpg", "title": "PNG to JPG" }
  ],
  "seo": {
    "title": "PNG to WEBP | Converigo",
    "description": "Free online PNG to WEBP converter.",
    "keywords": "png to webp, image converter",
    "canonical": "/png-to-webp",
    "image": "/static/images/og-default.png",
    "type": "website",
    "twitter_card": "summary_large_image"
  },
  "created_at": "2026-01-01",
  "updated_at": "2026-07-12"
}
```

## 3. Schema Formal (Draft 2020-12 Style)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://converigo.com/schemas/converter-v1.schema.json",
  "title": "Converter Definition",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "slug",
    "title",
    "description",
    "category",
    "source",
    "target",
    "active",
    "upload_form",
    "hero",
    "features",
    "supported_formats",
    "how_to_use",
    "about_formats",
    "cta",
    "faq",
    "seo"
  ],
  "properties": {
    "slug": {
      "type": "string",
      "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"
    },
    "title": {
      "type": "string",
      "minLength": 1
    },
    "description": {
      "type": "string",
      "minLength": 1
    },
    "category": {
      "type": "string",
      "enum": ["image", "audio", "video", "document", "general"]
    },
    "source": {
      "type": "string",
      "minLength": 1
    },
    "target": {
      "type": "string",
      "minLength": 1
    },
    "active": {
      "type": "boolean",
      "default": true
    },
    "popular": {
      "type": "boolean",
      "default": false
    },
    "featured": {
      "type": "boolean",
      "default": false
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "upload_form": {
      "type": "object",
      "required": ["action", "method", "accept", "button_text"],
      "properties": {
        "action": { "type": "string" },
        "method": { "type": "string" },
        "accept": { "type": "string" },
        "button_text": { "type": "string" }
      },
      "additionalProperties": false
    },
    "hero": {
      "type": "object",
      "required": ["eyebrow", "title", "description", "panel_label", "panel_title"],
      "properties": {
        "eyebrow": { "type": "string" },
        "title": { "type": "string" },
        "description": { "type": "string" },
        "panel_label": { "type": "string" },
        "panel_title": { "type": "string" }
      },
      "additionalProperties": false
    },
    "features": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "text"],
        "properties": {
          "title": { "type": "string" },
          "text": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "supported_formats": {
      "type": "object",
      "required": ["input", "output", "description"],
      "properties": {
        "input": { "type": "array", "items": { "type": "string" } },
        "output": { "type": "array", "items": { "type": "string" } },
        "description": { "type": "string" }
      },
      "additionalProperties": false
    },
    "how_to_use": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "description"],
        "properties": {
          "title": { "type": "string" },
          "description": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "about_formats": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "text"],
        "properties": {
          "title": { "type": "string" },
          "text": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "cta": {
      "type": "object",
      "required": ["eyebrow", "title", "text", "primary_text", "secondary_text", "primary_href", "secondary_href"],
      "properties": {
        "eyebrow": { "type": "string" },
        "title": { "type": "string" },
        "text": { "type": "string" },
        "primary_text": { "type": "string" },
        "secondary_text": { "type": "string" },
        "primary_href": { "type": "string" },
        "secondary_href": { "type": "string" }
      },
      "additionalProperties": false
    },
    "faq": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["question", "answer"],
        "properties": {
          "question": { "type": "string" },
          "answer": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "benefits": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "text"],
        "properties": {
          "title": { "type": "string" },
          "text": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "use_cases": {
      "type": "array",
      "items": { "type": "string" }
    },
    "related_tools": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slug", "title"],
        "properties": {
          "slug": { "type": "string" },
          "title": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "seo": {
      "type": "object",
      "required": ["title", "description", "keywords"],
      "properties": {
        "title": { "type": "string" },
        "description": { "type": "string" },
        "keywords": { "type": "string" },
        "canonical": { "type": "string" },
        "image": { "type": "string" },
        "type": { "type": "string" },
        "twitter_card": { "type": "string" }
      },
      "additionalProperties": false
    },
    "created_at": {
      "type": "string",
      "format": "date"
    },
    "updated_at": {
      "type": "string",
      "format": "date"
    }
  }
}
```

## 4. Catatan Implementasi

- `source` dan `target` boleh tetap diturunkan otomatis dari slug untuk backward compatibility, tetapi schema V1 menyarankan nilainya selalu eksplisit.
- `engine`, `icon`, dan `keywords` level atas tidak lagi menjadi bagian dari schema inti.
- Jika field lama masih ada, sebaiknya dipetakan ke field baru selama masa migrasi.
