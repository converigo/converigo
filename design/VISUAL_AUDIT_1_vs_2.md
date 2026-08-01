# Visual Audit — 1.png vs 2.png

**Scope:** Visual comparison only. No DOM/HTML/JS/CSS inspected.
**Method:** Computational pixel analysis (Pillow + numpy). 40.18% of pixels differ between the two images.

| Property | 1.png | 2.png |
|---|---|---|
| Dimensions | 1917 × 982 | 1917 × 990 |
| Overall background feel | Light blue gradient + colorful cards | Predominantly white, clean/light |
| Header | ~55 px dark bar (y 0–54) | ~111 px dark bar (y 0–110), ~2× taller |
| Main content | Colored/gradient panels + colorful card grid | White background, sparse blue accents |
| Footer | Dark footer (y 930–982) | Light/white footer with dark text row |

---

## DIFFERENCE LIST

### 1. Header height & background
- **What:** The dark header bar is much taller in 2.png.
- **Where:** Top edge, full width. 1.png header ends at y≈55; 2.png header ends at y≈110.
- **How it should look:** In 1.png the header is a thin dark strip (~55 px). In 2.png the dark strip extends to ~110 px, so the logo row plus a taller nav zone occupy more vertical space. The header background is also slightly darker in 2.png (≈RGB 36,37,38) vs 1.png (≈RGB 64,65,65).

### 2. Header nav content density
- **What:** 2.png has significantly more bright (text/icon) pixels in the header region.
- **Where:** Header strip, full width.
- **How it should look:** 1.png ≈ 4,301 bright pixels; 2.png ≈ 14,036 bright pixels. 2.png contains more visible nav/logo items (or larger/bolder text) across the header, particularly in the left half (x 200–600 shows ~1,000+ bright px in 2.png vs ~500 in 1.png).

### 3. Hero section vertical position
- **What:** The hero content (title/CTAs) sits higher in 1.png and lower in 2.png.
- **Where:** y≈55–200 in 1.png; y≈110–240 in 2.png.
- **How it should look:** 1.png hero begins right below the short header. 2.png hero begins lower, directly below the taller header, with the same visual spacing preserved below the header.

### 4. Accent color strip position
- **What:** A thin saturated accent band appears at different heights.
- **Where:** 1.png: colored band at y≈131–154 (24 px tall). 2.png: colored band at y≈202–217 (16 px tall).
- **How it should look:** Both images have a small horizontal accent strip, but it is positioned ~70 px lower and is slightly shorter/thinner in 2.png.

### 5. Hero title text placement
- **What:** Title text glyphs occupy different coordinates.
- **Where:** 1.png title text at y≈140–150; 2.png title text at y≈155–175. Small deltas also detected at (456–504, 144–167) and (552–648, 144–167) where 1.png is pure white (no glyph) and 2.png has dark glyph pixels.
- **How it should look:** The heading is centered at a slightly lower vertical position in 2.png. In 1.png the region (552–648,144–167) is blank white; in 2.png it contains dark text (~519 dark px).

### 6. Hero CTA (blue accent) extent
- **What:** The blue accent/button area is wider in 1.png than in 2.png.
- **Where:** 1.png blue accent spans x≈153–1747, y≈109–174. 2.png blue accent spans x≈246–1660, y≈130–181.
- **How it should look:** 1.png has a broader horizontal blue accent band; 2.png's is narrower (shifted inward on both sides) and lower. The blue tone is slightly more saturated/royal in 2.png (≈RGB 32,64,224) vs 1.png (≈RGB 32,96,224 / 160,192,224 blends).

### 7. Main content background — colored gradient vs white
- **What:** The entire main content area changes from a light blue gradient/colored background to a plain white background.
- **Where:** y≈240–930 in 1.png vs y≈380–900 in 2.png.
- **How it should look:** 1.png has a light blue (≈RGB 200–235, 220–240, 245–255) gradient with visible saturation. 2.png is almost pure white (68.9% of content area is white vs 15.6% in 1.png), with colored content only at y≈280–340 (text/image rows) and y≈760–840.

### 8. Colorful card grid → sparse white layout
- **What:** 1.png shows a dense grid of colorful cards/tiles; 2.png shows a clean, mostly white layout with fewer color accents.
- **Where:** Central content region, y≈240–930.
- **How it should look:** 1.png has ~91,023 colored pixels dominated by light blue (160,192,224), blue (32,96,224), purple (96,32,224), teal (0,160,128), orange (224,96,0), red (224,64,64), and yellow (224,160,32) — a multi-color card palette. 2.png has only ~24,541 colored pixels, dominated almost entirely by blue tones (32,64,224 / 32,96,224 / 0,64,192) — i.e., blue links/buttons/headers on white rather than colorful cards.

### 9. Left column treatment
- **What:** The left edge (x 0–160) has a persistent colored tint in 1.png but is white in 2.png.
- **Where:** Left edge column, y≈240–900.
- **How it should look:** In 1.png the left column carries saturation 15–38 (light blue/purple gradient panel). In 2.png the left column saturation drops to near 0 by y≈780 — it is plain white.

### 10. Content rows with dark text
- **What:** The distribution of dark text rows differs.
- **Where:** 1.png has text/colored rows at y≈250–310, 330–390, 470–530, 550–610, 650–710, 730–910. 2.png has text rows at y≈280–340 and y≈760–840.
- **How it should look:** 1.png has a continuous stream of densely packed sections (text + colored cards) down the whole page. 2.png is mostly whitespace with text concentrated in two narrower bands (one around y 280–340, one around y 760–840), separated by large white gaps.

### 11. Footer style
- **What:** Dark footer vs light footer.
- **Where:** Bottom of page. 1.png footer y≈930–982; 2.png footer y≈930–990.
- **How it should look:** 1.png ends in a dark footer (lum ≈ 34–44) with minimal text (~2,083 bright px). 2.png has a light/white footer (lum ≈ 253) with a dense dark text row spanning the full width at y≈975–990 (~2,000 dark px per 200 px column), suggesting a fuller footer content block. In 2.png the very bottom edge (y≈980) shows a thin darker strip (lum ≈ 67).

### 12. Overall page height
- **What:** 2.png is 8 px taller (982 vs 990).
- **Where:** Whole page.
- **How it should look:** 2.png extends 8 px taller, consistent with the taller header + extra footer content.

---

## Reference artifacts generated
- `design/visual_diff_mask.png` — pixel-difference mask
- `design/visual_diff_boxes.png` — 1.png with top-40 changed regions boxed in red
- `design/visual_regions.png` — 1.png with clustered changed-region boundaries highlighted
- `design/visual_side_by_side.png` — side-by-side montage with header/footer guide lines

## Summary
2.png is a taller, cleaner, predominantly white page with a taller dark header, a light footer containing more content, fewer and bluer accent colors, and text/CTA elements positioned lower and more inward. 1.png is a colorful gradient page with a short dark header, a dense multi-color card grid filling the main content area, and a dark minimal footer.

