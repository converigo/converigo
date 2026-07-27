# Learning Center Content Audit

Date: 2026-07-21
Scope: Reviewed 20 article JSON files under [app/data/articles](app/data/articles).

Note: This audit is review-only. No files were modified.

## Executive Summary

The Learning Center content has a solid foundation and good breadth, but it still needs tightening around search intent, duplicate coverage, internal linking quality, and metadata completeness.

Overall assessment:
- Strong: article coverage is broad and the dataset is structurally consistent.
- Moderate: titles and descriptions are mostly readable, but several are too generic for SEO.
- Needs work: duplicate topics, weak keyword targeting, broken or non-canonical cross-references, missing CTA data, and absent breadcrumb metadata.

## 1. Title Quality

### What is working
- Most titles are descriptive and understandable for a reader.
- The step-by-step guide articles have strong intent-driven titles such as:
  - [app/data/articles/guides/how-to-convert-jpg-to-png.json](app/data/articles/guides/how-to-convert-jpg-to-png.json)
  - [app/data/articles/guides/how-to-convert-pdf-to-jpg.json](app/data/articles/guides/how-to-convert-pdf-to-jpg.json)
  - [app/data/articles/guides/how-to-convert-mp4-to-mp3.json](app/data/articles/guides/how-to-convert-mp4-to-mp3.json)

### Weak or generic titles
These titles are too broad, too generic, or not strongly aligned with a clear search intent:
- [app/data/articles/fundamentals/getting-started.json](app/data/articles/fundamentals/getting-started.json) — "Getting Started with File Conversion"
  - Too broad and not specific enough for search demand.
- [app/data/articles/fundamentals/understanding-file-formats.json](app/data/articles/fundamentals/understanding-file-formats.json) — "Understanding File Formats for Better Conversion Results"
  - Useful, but still generic and not keyword-rich.
- [app/data/articles/guides/audio-quality-prep.json](app/data/articles/guides/audio-quality-prep.json) — "Audio Quality Prep for Cleaner Conversion Results"
  - The title is understandable, but it feels less search-intent-driven than the stronger how-to articles.

### Recommendation
Prefer titles that mirror a real query:
- "File Conversion Basics: A Beginner's Guide"
- "What Is a File Format? A Simple Guide"
- "How to Prepare Audio for Better Conversion Results"

## 2. Description Quality

### What is working
- Descriptions are generally clear and human-friendly.
- They provide a useful summary of what the user will learn.

### Gaps
Several descriptions are too broad and do not strongly differentiate the article from adjacent fundamentals content.
Examples:
- [app/data/articles/fundamentals/getting-started.json](app/data/articles/fundamentals/getting-started.json)
- [app/data/articles/fundamentals/understanding-file-formats.json](app/data/articles/fundamentals/understanding-file-formats.json)
- [app/data/articles/guides/audio-quality-prep.json](app/data/articles/guides/audio-quality-prep.json)

### Recommendation
Descriptions should include one primary intent phrase and one outcome phrase, for example:
- "Learn file conversion basics, including common formats, why conversion matters, and how to choose the right output."
- "Compare PNG and JPG to decide which format is better for quality, transparency, and file size."

## 3. Keyword Targeting

### Strengths
The stronger articles already target clear phrases:
- [app/data/articles/guides/how-to-convert-jpg-to-png.json](app/data/articles/guides/how-to-convert-jpg-to-png.json)
- [app/data/articles/guides/how-to-convert-pdf-to-jpg.json](app/data/articles/guides/how-to-convert-pdf-to-jpg.json)
- [app/data/articles/comparisons/webp-vs-png.json](app/data/articles/comparisons/webp-vs-png.json)

### Weak keyword targeting
The fundamentals articles are under-optimized:
- [app/data/articles/fundamentals/getting-started.json](app/data/articles/fundamentals/getting-started.json)
- [app/data/articles/fundamentals/understanding-file-formats.json](app/data/articles/fundamentals/understanding-file-formats.json)
- [app/data/articles/fundamentals/understanding-image-quality.json](app/data/articles/fundamentals/understanding-image-quality.json)

These use overly generic keywords such as "conversion", "basics", and "image conversion" rather than intent-led long-tail phrases.

### Recommendation
Add more search-intent phrases such as:
- "file conversion basics"
- "what is a file format"
- "image quality for conversion"
- "best format for web images"
- "convert PDF to JPG online"

## 4. Duplicate Topics and Overlapping Articles

### High-overlap pairs
These articles are too similar and should either be merged, consolidated, or narrowed:
- [app/data/articles/comparisons/png-vs-jpg.json](app/data/articles/comparisons/png-vs-jpg.json) and [app/data/articles/comparisons/png-vs-jpg-explained.json](app/data/articles/comparisons/png-vs-jpg-explained.json)
  - These cover nearly the same topic with only a slight framing difference.
- [app/data/articles/troubleshooting/conversion-fails.json](app/data/articles/troubleshooting/conversion-fails.json) and [app/data/articles/troubleshooting/why-file-conversion-fails.json](app/data/articles/troubleshooting/why-file-conversion-fails.json)
  - Both address conversion failure, but one is more procedural while the other is more explanatory.
- [app/data/articles/fundamentals/what-is-file-conversion.json](app/data/articles/fundamentals/what-is-file-conversion.json) and [app/data/articles/fundamentals/understanding-file-formats.json](app/data/articles/fundamentals/understanding-file-formats.json)
  - These overlap in introductory scope and could be better separated by intent.

### Recommendation
Keep one primary article per core intent:
- Use one canonical article for general conversion basics.
- Use one canonical article for format comparison.
- Use one canonical troubleshooting article for failure causes.

## 5. Slug Quality

### Strengths
Most slugs are simple and readable.

### Issues
Some slugs are too generic or not clearly distinct:
- [app/data/articles/fundamentals/getting-started.json](app/data/articles/fundamentals/getting-started.json)
  - "getting-started" is broad and weak for SEO.
- [app/data/articles/comparisons/png-vs-jpg.json](app/data/articles/comparisons/png-vs-jpg.json) and [app/data/articles/comparisons/png-vs-jpg-explained.json](app/data/articles/comparisons/png-vs-jpg-explained.json)
  - These are near-duplicates and should not both remain as distinct entry points.

### Recommendation
Prefer intent-led slugs such as:
- "file-conversion-basics"
- "what-is-a-file-format"
- "png-vs-jpg-guide"
- "why-file-conversion-fails"

## 6. Internal Link Quality

### What is working
The articles already contain related article suggestions, which is a good start.

### Gaps
The current related-article links are not always the best next-step links. Some links are broad or weakly sequenced rather than guiding the user toward a clear next action.
Examples:
- [app/data/articles/guides/how-to-convert-pdf-to-jpg.json](app/data/articles/guides/how-to-convert-pdf-to-jpg.json) links to the image guide, but the stronger next-step content may be a document workflow or troubleshooting article.
- [app/data/articles/guides/audio-quality-prep.json](app/data/articles/guides/audio-quality-prep.json) is useful, but it could better link to the audio comparison article or conversion troubleshooting content.

### Recommendation
Build internal links by intent:
- Beginner to overview
- Overview to comparison
- Comparison to how-to guide
- How-to guide to troubleshooting

## 7. Related Formats Validity

### Issues found
Some article references point to format slugs that do not appear to be canonical or currently available in the format dataset:
- "mp4"
- "zip"

These should either be replaced with existing supported formats or removed if they are not part of the site’s canonical format model.

## 8. Related Converters Validity

### Issues found
The following related converter references appear invalid or non-canonical:
- "mp3-to-wav"
- "svg-to-png"

These should be validated against the actual converter inventory before being left in the content.

## 9. Related Articles Validity

### Issue found
One related article reference points to a target that does not appear to exist:
- [app/data/articles/guides/pdf-workflow-checklist.json](app/data/articles/guides/pdf-workflow-checklist.json) references "understanding-pdf"

This should be replaced with an existing article slug or removed.

## 10. FAQ Quality

### What is working
The presence of FAQ sections is good and gives the articles a richer structure.

### Gaps
Most FAQs are shallow and generic. They do not yet capture the common real-world questions that users are likely to ask.
Examples:
- [app/data/articles/fundamentals/getting-started.json](app/data/articles/fundamentals/getting-started.json)
- [app/data/articles/guides/audio-quality-prep.json](app/data/articles/guides/audio-quality-prep.json)
- [app/data/articles/troubleshooting/conversion-fails.json](app/data/articles/troubleshooting/conversion-fails.json)

### Recommendation
Use FAQ questions that match common search intent, for example:
- "Why does my file look blurry after conversion?"
- "Which format should I choose for web images?"
- "How do I convert PDF pages to JPG without losing quality?"
- "Why does a conversion fail on my browser?"

## 11. CTA Quality

### Issue
No CTA block is present in any article JSON file.

This is a gap because the articles currently lack a clear conversion prompt or next-step action.

### Recommendation
Add a CTA object to each article with:
- a short persuasive title
- a clear action sentence
- a direct link to the most relevant converter

## 12. Breadcrumb Consistency

### Issue
No breadcrumb fields are populated in the current article JSON files.

This creates a minor consistency gap because breadcrumb navigation cannot be generated reliably from the content layer.

### Recommendation
Define breadcrumb data consistently for each article, for example:
- Home > Learning Center > Fundamentals > File Conversion Basics
- Home > Learning Center > Comparisons > PNG vs JPG

## Topic Cluster Opportunities

The strongest topic clusters are already visible and should be formalized more clearly.

### A. Image Conversion Cluster
Good core articles:
- [app/data/articles/comparisons/png-vs-jpg.json](app/data/articles/comparisons/png-vs-jpg.json)
- [app/data/articles/comparisons/webp-vs-png.json](app/data/articles/comparisons/webp-vs-png.json)
- [app/data/articles/fundamentals/understanding-image-quality.json](app/data/articles/fundamentals/understanding-image-quality.json)
- [app/data/articles/fundamentals/raster-vs-vector-images.json](app/data/articles/fundamentals/raster-vs-vector-images.json)
- [app/data/articles/format-specific/what-is-svg.json](app/data/articles/format-specific/what-is-svg.json)

### B. Document Conversion Cluster
Good core articles:
- [app/data/articles/fundamentals/what-is-file-conversion.json](app/data/articles/fundamentals/what-is-file-conversion.json)
- [app/data/articles/fundamentals/understanding-file-formats.json](app/data/articles/fundamentals/understanding-file-formats.json)
- [app/data/articles/guides/how-to-convert-pdf-to-jpg.json](app/data/articles/guides/how-to-convert-pdf-to-jpg.json)
- [app/data/articles/guides/pdf-workflow-checklist.json](app/data/articles/guides/pdf-workflow-checklist.json)

### C. Audio Conversion Cluster
Good core articles:
- [app/data/articles/comparisons/mp3-vs-wav-explained.json](app/data/articles/comparisons/mp3-vs-wav-explained.json)
- [app/data/articles/guides/how-to-convert-mp4-to-mp3.json](app/data/articles/guides/how-to-convert-mp4-to-mp3.json)
- [app/data/articles/guides/audio-quality-prep.json](app/data/articles/guides/audio-quality-prep.json)
- [app/data/articles/fundamentals/lossy-vs-lossless-compression.json](app/data/articles/fundamentals/lossy-vs-lossless-compression.json)

### D. Troubleshooting Cluster
Good core articles:
- [app/data/articles/troubleshooting/conversion-fails.json](app/data/articles/troubleshooting/conversion-fails.json)
- [app/data/articles/troubleshooting/quality-issues.json](app/data/articles/troubleshooting/quality-issues.json)
- [app/data/articles/troubleshooting/why-file-conversion-fails.json](app/data/articles/troubleshooting/why-file-conversion-fails.json)

## Priority Recommendations

1. Consolidate or reduce duplicate articles.
2. Improve titles and descriptions to better match real search intent.
3. Replace invalid or weak related-format, related-converter, and related-article references.
4. Expand FAQ content so it answers real user questions.
5. Add CTA metadata and breadcrumb data for better page experience and SEO consistency.
