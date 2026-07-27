# Format Knowledge Generator Quality Report

## Purpose

Review of `app/services/format_knowledge_generator.py` to identify quality deficiencies in generated output and propose improvements. No code was modified.

---

## Issues found

### 1. Grammar error in `quick_answer` and `definition`

**Location:** `_generate_quick_answer()` and `_generate_definition()`

**Problem:** Both methods produce "a {category}" which yields incorrect grammar for vowel-initial categories.

```
"GIF is a image file format."
"AVIF is a image file format."
"MP3 is a audio file format."
```

The article should be "an" before vowel sounds ("image", "audio", "archive").

**Suggested fix:** Add a helper that selects "a" or "an" based on the first character of the category noun.

```python
def _article(self, word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"
```

Then replace `f"{name} is a {category} file format."` with `f"{name} is {self._article(category)} {category} file format."`.

---

### 2. `quick_answer` and `definition` are structurally identical

**Location:** `_generate_quick_answer()` and `_generate_definition()`

**Problem:** Both methods use the same `description` field as their primary content, separated only by a slightly different closing sentence. Readers receive the same sentence twice, making the definition section redundant.

```
quick_answer: "GIF is a image file format. GIF is a lossless bitmap... It is widely used..."
definition:   "GIF is a image file format. GIF is a lossless bitmap... It is commonly used..."
```

**Suggested fix:** `quick_answer` should produce a terse single sentence. `definition` should expand to a paragraph by paraphrasing the description with added context about the format's strengths. The opening sentence ("X is a Y file format.") should only appear in `definition`.

---

### 3. `use_cases` are fully identical across all image formats

**Location:** `_USE_CASES_BY_CATEGORY["image"]`

**Problem:** All image formats share exactly the same five use-case entries. A GIF, a TIFF, an ICO, and a HEIC file get identical text after `{NAME}` substitution. This makes the pages uninformative and damages SEO differentiation.

Examples of conflated uses:
- "GIF is used for E-commerce product images" — misleading; GIF is rarely used for product photos.
- "ICO is used for Photography and creative work" — wrong; ICO is exclusively for icons/favicons.
- "TIFF is used for Web graphics and page assets" — inaccurate; TIFF is a print/archival format.
- "SVG is used for E-commerce product images" — partially true but the phrasing doesn't mention scalability.

**Suggested fix:** Break the `"image"` category into format-specific sub-tables, or add a `slug`-keyed override table `_USE_CASES_BY_SLUG` that the generator checks before falling back to the category table.

```python
_USE_CASES_BY_SLUG: dict[str, list[...]] = {
    "gif": [...],   # animation, memes, email, social clips
    "svg": [...],   # icons, logos, scalable diagrams
    "ico": [...],   # favicons, app icons, desktop shortcuts
    "tiff": [...],  # professional photography, print, archiving
    "heic": [...],  # mobile photography, Apple device sharing
    "avif": [...],  # web delivery, HDR, next-gen compression
    "bmp": [...],   # Windows legacy, uncompressed editing
}
```

---

### 4. `advantages` are fully identical across all image formats

**Location:** `_ADVANTAGES_BY_CATEGORY["image"]`

**Problem:** Every image format gets the same four advantages regardless of what actually distinguishes it.

```
"TIFF offers practical file size options." — false; TIFF is known for large, uncompressed files.
"GIF is supported by virtually all image editors." — true but says nothing about animation.
"AVIF offers practical file size options." — misses AVIF's primary value: outstanding compression.
```

**Suggested fix:** Same slug-keyed override approach as use_cases. Slug-specific advantage text should highlight the format's actual selling points (animation for GIF, lossless quality for TIFF, compression for AVIF/WEBP, scalability for SVG, icon container for ICO).

---

### 5. `limitations` are fully identical across all image formats

**Location:** `_LIMITATIONS_BY_CATEGORY["image"]`

**Problem:** All image formats produce the same three limitations including "Limited editing metadata" — applicable to PNG/WEBP but wrong for TIFF which has extensive metadata support.

```
"GIF may not retain all editing metadata." — misleading; GIF's real limitation is 256-color palette.
"AVIF may not retain all editing metadata." — misses AVIF's real limitation: encoder speed and limited legacy support.
"TIFF is optimized for certain image types." — TIFF is explicitly a general-purpose archival format.
```

**Suggested fix:** Slug-specific limitation tables are needed for image formats. The generic fallback is too broad.

---

### 6. `comparisons` text is generic for all formats

**Location:** `_generate_comparisons()`

**Problem:** Every comparison entry uses the same boilerplate sentence regardless of which two formats are being compared.

```
"GIF and PNG are both widely used file formats. Choosing between them depends on your compatibility needs, quality requirements, and the tools available in your workflow."

"AVIF and WEBP are both widely used file formats. Choosing between them depends on your compatibility needs, quality requirements, and the tools available in your workflow."
```

The sentence is identical for every pair. It gives no actionable information about the actual differences.

**Suggested fix:** Add a `_COMPARISON_OVERRIDES` dict keyed by `"{slug_a}-vs-{slug_b}"` or a symmetric key. Where an override exists, use the specific contrast text. Fall back to the generic template only when no override is found.

```python
_COMPARISON_OVERRIDES: dict[str, str] = {
    "gif-vs-png": "GIF supports animation and has a 256-color limit, while PNG is lossless with full color depth and transparency but no animation.",
    "gif-vs-webp": "WEBP offers better compression and full color at smaller sizes, while GIF remains the more universally supported animated format.",
    "svg-vs-png": "SVG scales to any resolution without quality loss as a vector format, while PNG is a raster format suited to detailed photographs and screenshots.",
    "avif-vs-webp": "AVIF delivers stronger compression than WEBP especially for photographic images, but WEBP has wider browser support at this time.",
    "tiff-vs-png": "TIFF is the professional archival and print standard with rich metadata, while PNG is better for everyday web graphics and lossless editing.",
    "heic-vs-jpg": "HEIC stores the same image quality as JPG in roughly half the file size, but requires conversion for use outside Apple devices.",
    "ico-vs-png": "ICO stores multiple icon resolutions in a single container optimized for desktop and OS contexts, while PNG is preferred for web favicons and single-resolution use.",
}
```

---

### 7. `faq` questions are uniform across every format in the same category

**Location:** `_FAQ_BY_CATEGORY["image"]`

**Problem:** Every image format gets the same five generic questions after `{NAME}` substitution. No format-specific questions are generated.

Missing obvious high-value FAQ questions by format:
- **GIF:** "Does GIF support animation?" — the most-asked GIF question is missing entirely.
- **SVG:** "Is SVG a vector format?" and "Can SVG be used on websites?" — both omitted.
- **ICO:** "What size should a favicon be?" and "Can ICO files contain multiple sizes?" — both missing.
- **HEIC:** "How do I open HEIC on Windows?" and "Can I convert HEIC to JPG?" — central user pain points omitted.
- **AVIF:** "Is AVIF supported by all browsers?" — most critical AVIF question missing.
- **TIFF:** "Is TIFF good for printing?" and "Does TIFF support layers?" — both omitted.
- **BMP:** "Why is BMP so large?" — the most-searched BMP question is absent.

**Suggested fix:** Add `_FAQ_BY_SLUG` with format-specific questions appended to or replacing the generic set.

---

### 8. `related_tools` descriptions are generated from slug patterns only

**Location:** `_generate_related_tools()`

**Problem:** Tool descriptions are derived solely by splitting the slug on `-to-` to produce sentences like "Convert GIF files to MP4 quickly and easily." This is accurate but does not surface any differentiating value.

**Suggested fix:** Accept an optional `tool_descriptions` dict in the master record or a `_TOOL_DESCRIPTION_OVERRIDES` table keyed by converter slug that provides richer, converter-specific descriptions.

---

### 9. No slug-level override mechanism exists

**Root cause of issues 3–7:** The entire template system works at the category level. There is no path for a specific format to receive tailored content short of editing the category tables, which would affect all formats in that category.

**Suggested fix:** Add a uniform slug-keyed override lookup in each `_generate_*` method. The pattern is:

```python
templates = _USE_CASES_BY_SLUG.get(slug) or _USE_CASES_BY_CATEGORY.get(category) or fallback
```

This is a non-breaking additive change. All existing behavior is preserved for any slug without an override.

---

## Priority summary

| Priority | Issue | Sections affected |
|----------|-------|-------------------|
| High | Grammar "a image / a audio" | quick_answer, definition |
| High | quick_answer = definition (same content) | quick_answer, definition |
| High | No slug-level overrides | all sections |
| High | Identical use_cases across all image formats | use_cases |
| High | Identical advantages across all image formats | advantages |
| High | Identical limitations across all image formats | limitations |
| Medium | Generic comparison text with zero factual content | comparisons |
| Medium | FAQ misses format-specific high-value questions | faq |
| Low | related_tools descriptions lack differentiating value | related_tools |

---

## Recommended implementation order

1. Add `_article()` helper — smallest fix, highest visible impact.
2. Separate `quick_answer` and `definition` logic so they produce distinct content.
3. Add `_USE_CASES_BY_SLUG`, `_ADVANTAGES_BY_SLUG`, `_LIMITATIONS_BY_SLUG` override tables.
4. Add `_COMPARISON_OVERRIDES` keyed by format pair.
5. Add `_FAQ_BY_SLUG` for format-specific questions.
6. Optionally add `_TOOL_DESCRIPTION_OVERRIDES` for richer converter descriptions.

None of these changes alter the public interface of `FormatKnowledgeGenerator` or break schema validation. They are purely additive.
