from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.services.knowledge_schema import validate_format_knowledge

# ---------------------------------------------------------------------------
# Template data — category-driven content tables
# ---------------------------------------------------------------------------

_USE_CASES_BY_CATEGORY: dict[str, list[dict[str, str]]] = {
    "image": [
        {
            "title": "Web graphics and page assets",
            "text": "{NAME} is used to deliver visual assets on websites, including banners, illustrations, and content images.",
        },
        {
            "title": "Photography and creative work",
            "text": "{NAME} is widely used by photographers and designers for storing, sharing, and publishing images.",
        },
        {
            "title": "Screenshots and documentation",
            "text": "{NAME} is a practical choice for capturing screenshots and creating visual documentation for tutorials and guides.",
        },
        {
            "title": "Social media and marketing",
            "text": "{NAME} is commonly used for sharing images on social platforms, email campaigns, and marketing content.",
        },
        {
            "title": "E-commerce product images",
            "text": "{NAME} files are used for product visuals on online stores where image quality and loading speed matter.",
        },
    ],
    "document": [
        {
            "title": "Official document sharing",
            "text": "{NAME} is used to share documents that need to look the same on every device and operating system.",
        },
        {
            "title": "Business reports and proposals",
            "text": "{NAME} is a reliable format for distributing professional reports, contracts, and formal documents.",
        },
        {
            "title": "Form and template publishing",
            "text": "{NAME} is commonly used for fillable forms, legal documents, and templates with fixed structure.",
        },
        {
            "title": "Archive and long-term storage",
            "text": "{NAME} is a trusted choice for archiving documents that need to remain readable over many years.",
        },
        {
            "title": "Printing and publishing",
            "text": "{NAME} is used in print workflows because it preserves layout, fonts, and formatting across different printers.",
        },
    ],
    "audio": [
        {
            "title": "Music streaming and distribution",
            "text": "{NAME} is widely used to distribute music online and on streaming platforms because it balances quality and file size.",
        },
        {
            "title": "Podcast and spoken content",
            "text": "{NAME} is commonly used for podcasts and audio content where efficient storage and broad playback support are needed.",
        },
        {
            "title": "Ringtones and alert sounds",
            "text": "{NAME} files are used for mobile ringtones and notification sounds because of their compact size and wide compatibility.",
        },
        {
            "title": "Video game and app audio",
            "text": "{NAME} is used in games and applications for background music, sound effects, and audio cues.",
        },
        {
            "title": "Audio editing and production",
            "text": "{NAME} is used in production workflows for audio mixing, processing, and final export.",
        },
    ],
    "video": [
        {
            "title": "Online video sharing",
            "text": "{NAME} is a popular format for uploading and sharing videos on websites and streaming platforms.",
        },
        {
            "title": "Video editing and post-production",
            "text": "{NAME} is used in editing workflows as a deliverable or intermediate format for video projects.",
        },
        {
            "title": "Mobile video playback",
            "text": "{NAME} is compatible with mobile devices and used for recording, playing, and sharing video on smartphones.",
        },
        {
            "title": "Tutorials and screen recordings",
            "text": "{NAME} is used for tutorial videos, walkthroughs, and screen captures shared across devices.",
        },
        {
            "title": "Video archiving",
            "text": "{NAME} is used to store high-quality video for long-term archiving and later reproduction.",
        },
    ],
    "archive": [
        {
            "title": "Software distribution",
            "text": "{NAME} is used to package and distribute software installers and application bundles.",
        },
        {
            "title": "Bulk file sharing",
            "text": "{NAME} lets users compress many files into one archive for easy transfer and download.",
        },
        {
            "title": "Backup and storage",
            "text": "{NAME} is used to back up files and reduce disk usage by compressing data in storage.",
        },
        {
            "title": "Project delivery",
            "text": "{NAME} is used to deliver project files, assets, and source code in a single compressed package.",
        },
        {
            "title": "File transfer over email",
            "text": "{NAME} allows oversized file sets to be compressed and shared within email attachment size limits.",
        },
    ],
}

_ADVANTAGES_BY_CATEGORY: dict[str, list[dict[str, str]]] = {
    "image": [
        {
            "title": "Broad compatibility",
            "text": "{NAME} is supported by virtually all image editors, browsers, and operating systems.",
        },
        {
            "title": "Reliable rendering",
            "text": "{NAME} files render consistently across different platforms and viewing conditions.",
        },
        {
            "title": "Good compression options",
            "text": "{NAME} offers practical file size options depending on the use case.",
        },
        {
            "title": "Easy to share and embed",
            "text": "{NAME} is one of the most widely accepted formats for embedding in websites, documents, and presentations.",
        },
    ],
    "document": [
        {
            "title": "Layout preservation",
            "text": "{NAME} preserves fonts, formatting, and page layout across different operating systems and devices.",
        },
        {
            "title": "Universal compatibility",
            "text": "{NAME} can be opened on virtually any device without requiring the authoring software.",
        },
        {
            "title": "Security features",
            "text": "{NAME} can include password protection, permissions, and digital signatures for sensitive documents.",
        },
        {
            "title": "Print-ready output",
            "text": "{NAME} is reliable for printing because it accurately represents the intended page design.",
        },
    ],
    "audio": [
        {
            "title": "Efficient compression",
            "text": "{NAME} reduces file size while maintaining audio quality acceptable for most playback scenarios.",
        },
        {
            "title": "Wide playback support",
            "text": "{NAME} is compatible with most media players, streaming services, and mobile devices.",
        },
        {
            "title": "Standardized format",
            "text": "{NAME} follows an established audio standard that ensures consistent playback behavior.",
        },
        {
            "title": "Flexible bitrate options",
            "text": "{NAME} supports a range of quality settings, allowing tradeoffs between file size and fidelity.",
        },
    ],
    "video": [
        {
            "title": "High compatibility",
            "text": "{NAME} is supported across browsers, streaming platforms, and media players without additional software.",
        },
        {
            "title": "Efficient video compression",
            "text": "{NAME} uses modern codecs to deliver good video quality at manageable file sizes.",
        },
        {
            "title": "Supports audio and video tracks",
            "text": "{NAME} bundles video, audio, and metadata in a single container file.",
        },
        {
            "title": "Flexible for different outputs",
            "text": "{NAME} supports a variety of resolution, codec, and quality settings for diverse use cases.",
        },
    ],
    "archive": [
        {
            "title": "Reduces file size",
            "text": "{NAME} compresses files to save storage space and speed up transfers.",
        },
        {
            "title": "Bundles multiple files",
            "text": "{NAME} packages many files or directories into one convenient file.",
        },
        {
            "title": "Widely supported tools",
            "text": "{NAME} is supported by common archive utilities on Windows, macOS, and Linux.",
        },
        {
            "title": "Preserves file structure",
            "text": "{NAME} keeps folder hierarchies and file metadata intact inside the archive.",
        },
    ],
}

_LIMITATIONS_BY_CATEGORY: dict[str, list[dict[str, str]]] = {
    "image": [
        {
            "title": "Quality tradeoffs with compression",
            "text": "Compressing {NAME} images too aggressively may produce visible artifacts or quality loss.",
        },
        {
            "title": "Not suitable for all use cases",
            "text": "{NAME} is optimized for certain image types and may not be the best choice for every workflow.",
        },
        {
            "title": "Limited editing metadata",
            "text": "{NAME} may not retain all editing metadata or layers needed for complex image workflows.",
        },
    ],
    "document": [
        {
            "title": "Limited editability",
            "text": "{NAME} is not always easy to edit directly, especially for users without compatible software.",
        },
        {
            "title": "Complex formatting may not transfer",
            "text": "Converting from or to {NAME} can sometimes lose custom styles, fonts, or layout elements.",
        },
        {
            "title": "Large file sizes",
            "text": "{NAME} files with many embedded images or assets can be large and slow to load or send.",
        },
    ],
    "audio": [
        {
            "title": "Lossy compression reduces quality",
            "text": "Compressing audio into {NAME} can remove fine detail that audiophiles or professional workflows may require.",
        },
        {
            "title": "Not ideal for editing",
            "text": "{NAME} is not optimal for audio editing because compression artifacts accumulate with repeated saves.",
        },
        {
            "title": "Limited metadata support",
            "text": "Some {NAME} variants have limited support for embedding detailed track and artist metadata.",
        },
    ],
    "video": [
        {
            "title": "Large file sizes",
            "text": "High-quality {NAME} files can be large, which may be a challenge for storage or distribution.",
        },
        {
            "title": "Codec dependency",
            "text": "Playback of {NAME} files may depend on specific codec support in the viewer's system.",
        },
        {
            "title": "Conversion may reduce quality",
            "text": "Converting {NAME} to other formats with aggressive compression may introduce visual artifacts.",
        },
    ],
    "archive": [
        {
            "title": "Requires extraction to use files",
            "text": "{NAME} archives must be decompressed before files inside can be opened or modified.",
        },
        {
            "title": "Compatibility with older tools",
            "text": "Some older or lightweight utilities may not fully support all {NAME} features.",
        },
        {
            "title": "No inline editing",
            "text": "Files inside a {NAME} archive cannot typically be edited without extracting them first.",
        },
    ],
}

_FAQ_BY_CATEGORY: dict[str, list[dict[str, str]]] = {
    "image": [
        {
            "question": "What is a {NAME} file?",
            "answer": "A {NAME} file is a {CATEGORY} format used for storing images with broad support across devices and software.",
        },
        {
            "question": "When should I use {NAME}?",
            "answer": "{NAME} is a good choice when you need a widely compatible image format for web, design, or photography workflows.",
        },
        {
            "question": "Can I convert {NAME} to other formats?",
            "answer": "Yes, {NAME} can be converted to many other image formats using an online converter or image editing software.",
        },
        {
            "question": "Is {NAME} supported by all browsers?",
            "answer": "Most modern browsers support {NAME} natively for displaying images on web pages.",
        },
        {
            "question": "How do I reduce the size of a {NAME} file?",
            "answer": "You can reduce the size of a {NAME} file by compressing it, resizing the image, or converting to a more compact format.",
        },
    ],
    "document": [
        {
            "question": "What is a {NAME} file?",
            "answer": "A {NAME} file is a {CATEGORY} format used to store and share formatted content in a consistent, device-independent layout.",
        },
        {
            "question": "How do I open a {NAME} file?",
            "answer": "You can open a {NAME} file using a compatible viewer or editor such as Adobe Acrobat, LibreOffice, or a browser-based tool.",
        },
        {
            "question": "Can I convert {NAME} to other formats?",
            "answer": "Yes, {NAME} can be converted to other document and image formats using conversion tools online or in desktop applications.",
        },
        {
            "question": "Is {NAME} good for printing?",
            "answer": "{NAME} is often a reliable format for printing because it preserves document layout and fonts.",
        },
        {
            "question": "Can {NAME} files be password protected?",
            "answer": "Many {NAME} formats support password protection or permission controls for sensitive documents.",
        },
    ],
    "audio": [
        {
            "question": "What is a {NAME} file?",
            "answer": "A {NAME} file is an {CATEGORY} format used to store audio content such as music, podcasts, and sound recordings.",
        },
        {
            "question": "How do I play a {NAME} file?",
            "answer": "You can play a {NAME} file using most modern media players, music apps, or browser-based audio tools.",
        },
        {
            "question": "Is {NAME} a good format for music?",
            "answer": "{NAME} is suitable for music when a balance between quality and file size is acceptable for your use case.",
        },
        {
            "question": "Can I convert {NAME} to other audio formats?",
            "answer": "Yes, {NAME} can be converted to other audio formats using online converters or audio editing applications.",
        },
        {
            "question": "What is the audio quality of {NAME}?",
            "answer": "The quality of {NAME} depends on the bitrate and codec settings used during encoding.",
        },
    ],
    "video": [
        {
            "question": "What is a {NAME} file?",
            "answer": "A {NAME} file is a {CATEGORY} container format used for storing video and audio tracks together.",
        },
        {
            "question": "How do I play a {NAME} file?",
            "answer": "You can play a {NAME} file using most modern media players or video apps that support the format.",
        },
        {
            "question": "Can I convert {NAME} to other video formats?",
            "answer": "Yes, {NAME} can be converted to other video formats using online converters or video editing tools.",
        },
        {
            "question": "Is {NAME} compatible with mobile devices?",
            "answer": "{NAME} is supported on most modern mobile devices and operating systems for video playback.",
        },
        {
            "question": "What resolution is supported by {NAME}?",
            "answer": "{NAME} supports a wide range of resolutions depending on the codec and encoding settings used.",
        },
    ],
    "archive": [
        {
            "question": "What is a {NAME} file?",
            "answer": "A {NAME} file is a compressed archive that bundles multiple files or folders into a single package.",
        },
        {
            "question": "How do I open a {NAME} file?",
            "answer": "You can open a {NAME} file using common archive utilities such as 7-Zip, WinRAR, or the built-in archive tools on macOS and Windows.",
        },
        {
            "question": "Does {NAME} support encryption?",
            "answer": "Many {NAME} archives support optional encryption for protecting sensitive files.",
        },
        {
            "question": "Can I convert {NAME} to other archive formats?",
            "answer": "Yes, {NAME} can be extracted and re-archived into other formats using archive management tools.",
        },
        {
            "question": "Is {NAME} the best archive format?",
            "answer": "The best archive format depends on your compatibility needs, compression requirements, and the tools available to your recipients.",
        },
    ],
}

_DEFAULT_FAQ: list[dict[str, str]] = [
    {
        "question": "What is a {NAME} file?",
        "answer": "A {NAME} file is a {CATEGORY} format used for storing and sharing content.",
    },
    {
        "question": "How do I open a {NAME} file?",
        "answer": "You can open a {NAME} file using compatible software for the {CATEGORY} category.",
    },
    {
        "question": "Can I convert {NAME} to other formats?",
        "answer": "Yes, {NAME} can be converted to other formats using online tools or dedicated software.",
    },
    {
        "question": "Is {NAME} widely supported?",
        "answer": "{NAME} is supported by many modern applications and platforms.",
    },
]

# ---------------------------------------------------------------------------
# Slug-level overrides — checked before category fallback
# ---------------------------------------------------------------------------

_USE_CASES_BY_SLUG: dict[str, list[dict[str, str]]] = {
    "gif": [
        {
            "title": "Animated web content",
            "text": "GIF is widely used for short animated clips, looping animations, and reaction images on websites and social platforms.",
        },
        {
            "title": "Memes and social media posts",
            "text": "GIF has become the standard format for shareable memes, humorous clips, and short visual reactions across messaging apps and social feeds.",
        },
        {
            "title": "Email and newsletter animations",
            "text": "GIF adds lightweight animation to email campaigns and newsletters where video is not supported by most email clients.",
        },
        {
            "title": "UI micro-interactions and loading indicators",
            "text": "GIF is used in app interfaces for small animations such as loading spinners, progress indicators, and onboarding illustrations.",
        },
        {
            "title": "Simple graphics with limited colors",
            "text": "GIF works well for flat graphics, logos, and icons with a limited number of distinct colors where its 256-color palette is sufficient.",
        },
    ],
    "svg": [
        {
            "title": "Logos and brand identity assets",
            "text": "SVG is the preferred format for logos and brand assets because it scales perfectly from a small favicon to a billboard without any quality loss.",
        },
        {
            "title": "Icons and interface graphics",
            "text": "SVG is widely used for UI icons in web applications and design systems because the files are tiny and render sharply at every screen density.",
        },
        {
            "title": "Data visualizations and charts",
            "text": "SVG is used for interactive charts, graphs, and infographics on the web because it can be manipulated with CSS and JavaScript.",
        },
        {
            "title": "Responsive web illustrations",
            "text": "SVG illustrations adapt to any container size, making them ideal for responsive web pages and high-DPI displays.",
        },
        {
            "title": "Animated and interactive graphics",
            "text": "SVG supports CSS and SMIL animation as well as JavaScript-driven interactions, enabling rich visual experiences without video.",
        },
    ],
    "bmp": [
        {
            "title": "Legacy Windows application graphics",
            "text": "BMP is the native raster format on Windows and is used in legacy applications and system interfaces that require uncompressed images.",
        },
        {
            "title": "Uncompressed image editing",
            "text": "BMP stores pixel data without compression, making it suitable for workflows that need to avoid any quality change during editing or saving.",
        },
        {
            "title": "Intermediate format in image pipelines",
            "text": "BMP is sometimes used as an intermediate format between processing steps where lossless fidelity matters and file size is not a concern.",
        },
        {
            "title": "Printing and scanning workflows",
            "text": "BMP can be used in scanning and basic print workflows on Windows where compatibility with legacy drivers is required.",
        },
        {
            "title": "Simple system and desktop graphics",
            "text": "BMP is used for basic desktop wallpapers, system splash screens, and simple graphics in Windows environments.",
        },
    ],
    "tiff": [
        {
            "title": "Professional photography and retouching",
            "text": "TIFF is the industry standard for professional photographers who need lossless quality and full color depth when editing and archiving master images.",
        },
        {
            "title": "Print production and pre-press",
            "text": "TIFF is widely used in print workflows because it supports CMYK color, high resolution, and lossless compression required by commercial printers.",
        },
        {
            "title": "Document and artwork archiving",
            "text": "TIFF is a trusted long-term archival format for digitized documents, artworks, and scanned records that must be preserved without any quality loss.",
        },
        {
            "title": "Medical and scientific imaging",
            "text": "TIFF is used in medical imaging, microscopy, and scientific research where pixel-accurate lossless images are required for analysis.",
        },
        {
            "title": "High-resolution scanning",
            "text": "Flatbed and document scanners commonly output TIFF files to preserve the full detail of scanned photographs, negatives, and printed materials.",
        },
    ],
    "heic": [
        {
            "title": "iPhone and Apple device photography",
            "text": "HEIC is the default camera format on iPhones and iPads, used to store photos at half the file size of JPG with equivalent or better visual quality.",
        },
        {
            "title": "iCloud and Apple ecosystem sharing",
            "text": "HEIC files sync efficiently through iCloud and share natively between Apple devices in Messages, AirDrop, and Photos.",
        },
        {
            "title": "Live Photos and burst sequences",
            "text": "HEIC containers support Apple Live Photos and burst image sequences in a single file, preserving motion and context alongside the still image.",
        },
        {
            "title": "Space-efficient photo storage",
            "text": "HEIC allows iPhone users to store roughly twice as many photos compared to JPG at the same perceived quality, reducing storage pressure.",
        },
        {
            "title": "High dynamic range and wide color",
            "text": "HEIC preserves the full HDR and wide color gamut captured by modern iPhone cameras, retaining detail in highlights and shadows.",
        },
    ],
    "avif": [
        {
            "title": "Modern web image delivery",
            "text": "AVIF is used by websites and CDNs to deliver images at significantly smaller file sizes than JPG or PNG, improving page speed and Core Web Vitals.",
        },
        {
            "title": "E-commerce and product photography",
            "text": "AVIF delivers high-quality product images at smaller file sizes, helping online stores load faster without sacrificing visual detail.",
        },
        {
            "title": "HDR and wide color gamut images",
            "text": "AVIF natively supports 10-bit and 12-bit color depth along with HDR, making it suitable for premium photography and display-optimized content.",
        },
        {
            "title": "Responsive and adaptive image pipelines",
            "text": "AVIF is used alongside WebP and JPG in responsive image pipelines, served via the HTML picture element to browsers that support it.",
        },
        {
            "title": "Next-generation image optimization",
            "text": "AVIF is adopted by image optimization services and static site generators as the default output format for maximum compression with quality preservation.",
        },
    ],
    "ico": [
        {
            "title": "Website favicons",
            "text": "ICO is the standard format for the favicon displayed in browser tabs, bookmarks, and address bars for websites.",
        },
        {
            "title": "Windows application icons",
            "text": "ICO is the native icon format on Windows, used for executable files, desktop shortcuts, folders, and taskbar icons.",
        },
        {
            "title": "Multi-resolution icon containers",
            "text": "ICO files store multiple icon sizes (16x16 to 256x256) in a single file so the OS automatically uses the most appropriate resolution.",
        },
        {
            "title": "Browser tab and bookmark icons",
            "text": "Browsers request favicon.ico automatically from the website root and display it in tabs, bookmarks, and history entries.",
        },
        {
            "title": "Desktop shortcut and system graphics",
            "text": "ICO is used for custom desktop shortcut icons on Windows, giving applications and files a recognizable visual identity on the desktop.",
        },
    ],
}

_ADVANTAGES_BY_SLUG: dict[str, list[dict[str, str]]] = {
    "gif": [
        {
            "title": "Native animation support",
            "text": "GIF is one of the oldest and most universally supported animation formats, playable in every browser and email client without plugins.",
        },
        {
            "title": "Universal compatibility",
            "text": "GIF is recognized by virtually every platform, device, messaging app, and browser, making it the safest choice for animated images.",
        },
        {
            "title": "Lossless for flat graphics",
            "text": "GIF uses lossless compression for images with up to 256 colors, preserving the exact appearance of logos, icons, and simple diagrams.",
        },
        {
            "title": "Transparency support",
            "text": "GIF supports binary transparency, allowing one color to be designated as transparent for use over different backgrounds.",
        },
    ],
    "svg": [
        {
            "title": "Infinite scalability",
            "text": "SVG images scale to any size without pixelation or quality loss because they are defined by mathematical paths, not pixels.",
        },
        {
            "title": "Very small file sizes for line art",
            "text": "SVG files for icons and logos are typically a few kilobytes, far smaller than equivalent raster images at the same visual quality.",
        },
        {
            "title": "Editable and accessible text",
            "text": "SVG markup is human-readable XML, making it easy to edit in a text editor, inspect in browser devtools, and index by search engines.",
        },
        {
            "title": "CSS and JavaScript integration",
            "text": "SVG elements can be styled with CSS and animated or manipulated with JavaScript directly in the browser DOM.",
        },
        {
            "title": "Resolution-independent on all displays",
            "text": "SVG renders sharply on standard, Retina, and high-DPI screens without requiring separate image assets for different pixel densities.",
        },
    ],
    "bmp": [
        {
            "title": "Lossless pixel-perfect quality",
            "text": "BMP stores every pixel without compression, guaranteeing that image data is never altered when saving or loading the file.",
        },
        {
            "title": "Native Windows support",
            "text": "BMP is built into Windows at the OS level and can be opened by any Windows application without additional software.",
        },
        {
            "title": "Simple and well-documented format",
            "text": "BMP has a straightforward file structure that is easy to parse and widely understood across development environments.",
        },
        {
            "title": "No compression artifacts",
            "text": "Because BMP is uncompressed, there are never any encoding artifacts or quality degradation regardless of how many times the file is saved.",
        },
    ],
    "tiff": [
        {
            "title": "Lossless image quality",
            "text": "TIFF preserves every pixel without lossy compression, making it the preferred archival format for professional photography and print.",
        },
        {
            "title": "Rich metadata support",
            "text": "TIFF supports extensive metadata including EXIF, IPTC, XMP, GPS data, and custom tags used in professional and scientific workflows.",
        },
        {
            "title": "CMYK and multi-channel color",
            "text": "TIFF supports CMYK color profiles and multi-channel images required by commercial printing, prepress, and color-managed workflows.",
        },
        {
            "title": "Multi-page and multi-image support",
            "text": "A single TIFF file can contain multiple pages or images, making it suitable for scanned documents and image stacks.",
        },
        {
            "title": "Industry standard for archiving",
            "text": "TIFF is widely mandated by libraries, museums, and government agencies as the long-term archival format for digitized cultural assets.",
        },
    ],
    "heic": [
        {
            "title": "Half the size of JPG at the same quality",
            "text": "HEIC uses the HEVC codec to compress photos to roughly half the file size of an equivalent JPG without visible quality loss.",
        },
        {
            "title": "HDR and wide color gamut support",
            "text": "HEIC preserves the 10-bit HDR and P3 wide color gamut captured by modern iPhone cameras, which JPG cannot fully represent.",
        },
        {
            "title": "Multi-image and Live Photo containers",
            "text": "HEIC can bundle multiple images, depth maps, and Apple Live Photo sequences in a single file that JPG cannot match.",
        },
        {
            "title": "Excellent detail preservation",
            "text": "HEIC retains fine detail in textures, foliage, and complex scenes better than JPG at the same file size.",
        },
    ],
    "avif": [
        {
            "title": "Best-in-class compression efficiency",
            "text": "AVIF typically produces files 50% smaller than JPG and 20-30% smaller than WebP at comparable perceptual quality.",
        },
        {
            "title": "HDR and wide color gamut support",
            "text": "AVIF supports 10-bit and 12-bit color depth with HDR metadata, enabling premium image quality on compatible displays.",
        },
        {
            "title": "Both lossy and lossless encoding",
            "text": "AVIF can be used for photographic lossy compression or lossless graphics, covering a wide range of image use cases in a single format.",
        },
        {
            "title": "Alpha transparency support",
            "text": "AVIF supports full alpha channel transparency at smaller file sizes than PNG, making it useful for overlays and web graphics.",
        },
        {
            "title": "Based on the open AV1 standard",
            "text": "AVIF is built on the royalty-free AV1 codec, ensuring long-term availability without licensing costs.",
        },
    ],
    "ico": [
        {
            "title": "Multi-resolution container",
            "text": "ICO stores multiple icon sizes (typically 16x16 up to 256x256) in one file so the OS and browser always use the most appropriate size.",
        },
        {
            "title": "Native OS integration on Windows",
            "text": "ICO is recognized natively by Windows Explorer, the taskbar, and the Start menu without any additional software.",
        },
        {
            "title": "Transparency support",
            "text": "ICO supports full alpha transparency in 32-bit variants, allowing icons to appear cleanly over any background color or wallpaper.",
        },
        {
            "title": "Universal browser favicon support",
            "text": "Every browser automatically requests favicon.ico from the website root, making ICO the most broadly compatible favicon format.",
        },
    ],
}

_LIMITATIONS_BY_SLUG: dict[str, list[dict[str, str]]] = {
    "gif": [
        {
            "title": "256-color palette limit",
            "text": "GIF supports only 256 colors per frame, making it unsuitable for photographs and images with gradients or rich color detail.",
        },
        {
            "title": "Large file size for long animations",
            "text": "Animated GIFs can become very large compared to equivalent video formats like MP4 or WebP, especially for longer or higher-resolution clips.",
        },
        {
            "title": "No audio support",
            "text": "GIF cannot carry an audio track, so any content requiring synchronized sound must use a video format instead.",
        },
        {
            "title": "Not suitable for photographs",
            "text": "The 256-color restriction causes visible banding and dithering artifacts in photographic content with continuous tones.",
        },
    ],
    "svg": [
        {
            "title": "Not suitable for photographs",
            "text": "SVG is a vector format and is not designed for photographic images with complex color gradients or camera-captured detail.",
        },
        {
            "title": "Complex SVGs can be slow to render",
            "text": "SVG files with many paths, filters, or animations can cause rendering performance issues in browsers when used at scale.",
        },
        {
            "title": "Security risk with embedded scripts",
            "text": "SVG files can contain JavaScript and external references, making user-submitted SVGs a potential security risk if not sanitized.",
        },
        {
            "title": "Limited support in some email clients",
            "text": "Most email clients do not render inline SVG, requiring fallback raster images for HTML email campaigns.",
        },
    ],
    "bmp": [
        {
            "title": "Very large file sizes",
            "text": "BMP stores uncompressed pixel data, resulting in files far larger than PNG, JPG, or WebP for the same image dimensions.",
        },
        {
            "title": "Not suitable for the web",
            "text": "BMP files are rarely used on websites because their large size makes page loading slow and bandwidth usage high.",
        },
        {
            "title": "Limited metadata support",
            "text": "BMP has minimal support for embedded metadata compared to TIFF or JPG, making it unsuitable for professional image management workflows.",
        },
        {
            "title": "Limited cross-platform compatibility",
            "text": "BMP was designed for Windows and is not as universally supported on macOS, Linux, or mobile platforms as PNG or JPG.",
        },
    ],
    "tiff": [
        {
            "title": "Very large file sizes",
            "text": "TIFF files with lossless compression can be extremely large, making them impractical for web delivery, email, or everyday sharing.",
        },
        {
            "title": "Not supported in web browsers",
            "text": "Browsers do not natively display TIFF files, so TIFF images must be converted to JPG, PNG, or WebP for use on websites.",
        },
        {
            "title": "Slow to open and process",
            "text": "High-resolution TIFF files can take significant time to open, save, and export, especially on lower-powered hardware.",
        },
        {
            "title": "Not suitable for everyday sharing",
            "text": "TIFF is a professional format and is rarely the right choice for casual sharing via email, messaging apps, or social media.",
        },
    ],
    "heic": [
        {
            "title": "Limited compatibility outside Apple ecosystem",
            "text": "HEIC is not natively supported on Windows without codec installation or on older Android devices, requiring conversion for broad sharing.",
        },
        {
            "title": "Requires conversion for web use",
            "text": "Web browsers do not universally support HEIC, so images must be converted to JPG or WebP before publishing online.",
        },
        {
            "title": "Not widely supported by editing tools",
            "text": "Many image editors and photo management applications outside the Apple ecosystem have limited or no native HEIC support.",
        },
        {
            "title": "Patent-encumbered format",
            "text": "HEIC relies on HEVC which involves patent licensing, which has contributed to slower adoption compared to open formats like AVIF.",
        },
    ],
    "avif": [
        {
            "title": "Slower encoding than JPG and WebP",
            "text": "AVIF encoding is computationally intensive, which can make it slow to generate in bulk compared to JPG or WebP.",
        },
        {
            "title": "Incomplete legacy browser support",
            "text": "Older browsers and some environments do not support AVIF, requiring fallback images for full compatibility.",
        },
        {
            "title": "Limited support in editing tools",
            "text": "Not all image editors natively support AVIF, which can complicate production and retouching workflows.",
        },
        {
            "title": "Newer format with evolving tooling",
            "text": "As a relatively new format, AVIF tooling, CDN support, and best practices are still maturing compared to JPG or PNG.",
        },
    ],
    "ico": [
        {
            "title": "Not suitable for general images",
            "text": "ICO is designed exclusively for icons and favicons and is not appropriate for photographs, illustrations, or everyday image sharing.",
        },
        {
            "title": "Complex to create without dedicated tools",
            "text": "Generating a valid multi-resolution ICO file manually is non-trivial; dedicated tools or converters are typically required.",
        },
        {
            "title": "Limited color depth in small sizes",
            "text": "Older ICO sizes (16x16, 32x32) have historically supported limited color depths, which can reduce visual quality for complex icons.",
        },
        {
            "title": "Primarily a Windows-centric format",
            "text": "Outside of favicons and Windows applications, ICO has limited use on macOS, Linux, or cross-platform systems.",
        },
    ],
}

_FAQ_BY_SLUG: dict[str, list[dict[str, str]]] = {
    "gif": [
        {
            "question": "What is a GIF file?",
            "answer": "A GIF (Graphics Interchange Format) file is a raster image format that supports animation, transparency, and lossless compression for up to 256 colors.",
        },
        {
            "question": "Does GIF support animation?",
            "answer": "Yes, GIF is one of the most widely supported animation formats. Multiple frames can be stored in a single file and played back in a loop.",
        },
        {
            "question": "Why does GIF only use 256 colors?",
            "answer": "GIF was designed in 1987 when 256 colors were standard. Its palette-based color model is fixed at 8 bits per pixel, which limits photographic quality.",
        },
        {
            "question": "Is GIF better than MP4 for animations?",
            "answer": "MP4 is far more efficient for longer or higher-quality animations. GIF is preferred when broad compatibility without video player controls is required.",
        },
        {
            "question": "Can I convert GIF to WebP for smaller file size?",
            "answer": "Yes, converting GIF to animated WebP typically reduces file size significantly while retaining animation and supporting full color depth.",
        },
        {
            "question": "Is GIF lossless?",
            "answer": "GIF uses lossless LZW compression, but because it is limited to 256 colors, photographic images are visually degraded by dithering.",
        },
    ],
    "svg": [
        {
            "question": "What is an SVG file?",
            "answer": "An SVG (Scalable Vector Graphics) file is an XML-based vector image format that describes shapes, paths, and text mathematically rather than as pixels.",
        },
        {
            "question": "Is SVG a vector or raster format?",
            "answer": "SVG is a vector format. It stores image data as mathematical descriptions of shapes, so it scales to any size without loss of quality.",
        },
        {
            "question": "Can SVG be used directly on websites?",
            "answer": "Yes, SVG can be embedded directly in HTML or referenced as a src attribute, and all modern browsers render it natively.",
        },
        {
            "question": "Can I edit SVG files in a text editor?",
            "answer": "Yes, SVG is plain XML text. You can open and edit it with any text editor, though vector design tools like Inkscape or Figma are more practical.",
        },
        {
            "question": "When should I use SVG instead of PNG?",
            "answer": "Use SVG for logos, icons, and line art that need to scale at multiple sizes. Use PNG for photographs and complex raster images.",
        },
        {
            "question": "Can SVG files contain animation?",
            "answer": "Yes, SVG supports animation using CSS transitions, SMIL animation attributes, or JavaScript, making it useful for interactive web graphics.",
        },
    ],
    "bmp": [
        {
            "question": "What is a BMP file?",
            "answer": "A BMP (Bitmap) file is an uncompressed raster image format developed by Microsoft that stores pixel data directly without any quality loss.",
        },
        {
            "question": "Why are BMP files so large?",
            "answer": "BMP files store every pixel without compression. A 1920x1080 24-bit BMP is over 6 MB, compared to under 1 MB for an equivalent JPG.",
        },
        {
            "question": "Should I use BMP or PNG?",
            "answer": "PNG is almost always preferable to BMP. PNG is also lossless but uses efficient compression that dramatically reduces file size with no quality loss.",
        },
        {
            "question": "Is BMP supported on Mac?",
            "answer": "macOS can open BMP files with Preview, but BMP is a Windows-native format and is less common in Mac or Linux workflows.",
        },
        {
            "question": "When would I use BMP instead of other formats?",
            "answer": "BMP is relevant when working with legacy Windows software, system-level graphics, or pipelines that specifically require uncompressed bitmap data.",
        },
    ],
    "tiff": [
        {
            "question": "What is a TIFF file?",
            "answer": "A TIFF (Tagged Image File Format) file is a flexible raster image format designed for professional photography, print production, and archiving.",
        },
        {
            "question": "Is TIFF lossless?",
            "answer": "Yes, TIFF supports lossless compression options including LZW and ZIP, preserving image data exactly. It can also store uncompressed data.",
        },
        {
            "question": "Can TIFF files support layers?",
            "answer": "Some applications such as Adobe Photoshop save TIFF files with layer data embedded as proprietary metadata, but not all TIFF readers support layers.",
        },
        {
            "question": "Is TIFF good for printing?",
            "answer": "Yes, TIFF is the standard format for high-resolution print production, supporting CMYK color profiles and the precision required by commercial printers.",
        },
        {
            "question": "Can I use TIFF on a website?",
            "answer": "Web browsers do not support TIFF natively. TIFF images must be converted to JPG, PNG, or WebP before being used on a website.",
        },
        {
            "question": "How does TIFF compare to JPG for photography?",
            "answer": "TIFF is lossless and preserves full image quality, making it ideal for editing and archiving. JPG uses lossy compression and is better for sharing and web use.",
        },
    ],
    "heic": [
        {
            "question": "What is a HEIC file?",
            "answer": "A HEIC (High Efficiency Image Container) file is the photo format used by iPhones and other Apple devices to store images at roughly half the size of JPG.",
        },
        {
            "question": "How do I open a HEIC file on Windows?",
            "answer": "On Windows 10 and 11 you can install the Microsoft HEVC Video Extensions from the Microsoft Store, or convert the file to JPG using an online tool.",
        },
        {
            "question": "Is HEIC better quality than JPG?",
            "answer": "HEIC provides equal or better quality than JPG at around half the file size, and it supports HDR and wide color gamut that JPG cannot fully represent.",
        },
        {
            "question": "Can I convert HEIC to JPG?",
            "answer": "Yes, HEIC can be converted to JPG using online converters, Apple Photos, or image editing software for maximum compatibility.",
        },
        {
            "question": "Why does my iPhone save photos as HEIC?",
            "answer": "Apple uses HEIC by default because it stores the same quality as JPG in about half the storage space, helping manage limited device storage.",
        },
        {
            "question": "Is HEIC supported on Android?",
            "answer": "Android support for HEIC varies by device and OS version. For sharing with Android users, converting to JPG ensures compatibility.",
        },
    ],
    "avif": [
        {
            "question": "What is an AVIF file?",
            "answer": "An AVIF (AV1 Image File Format) file is a next-generation image format based on the AV1 video codec that offers outstanding compression efficiency.",
        },
        {
            "question": "Is AVIF supported by all browsers?",
            "answer": "AVIF is supported by Chrome, Firefox, Opera, and Safari 16+. Older browsers such as Internet Explorer and some legacy versions do not support it.",
        },
        {
            "question": "How does AVIF compare to WebP?",
            "answer": "AVIF typically compresses images 20-30% more efficiently than WebP at comparable quality, and it supports HDR. WebP has wider legacy browser support.",
        },
        {
            "question": "How does AVIF compare to JPG?",
            "answer": "AVIF produces files roughly 50% smaller than JPG at the same perceptual quality, with support for transparency and HDR that JPG lacks.",
        },
        {
            "question": "Can I use AVIF on my website today?",
            "answer": "Yes, using the HTML picture element with AVIF as the first source and JPG or WebP as a fallback lets you serve AVIF to supported browsers.",
        },
        {
            "question": "Is AVIF royalty-free?",
            "answer": "Yes, AVIF is based on the AV1 codec which is royalty-free and maintained by the Alliance for Open Media.",
        },
    ],
    "ico": [
        {
            "question": "What is an ICO file?",
            "answer": "An ICO file is an icon container format used for website favicons, Windows application icons, and desktop shortcuts, storing multiple resolutions in one file.",
        },
        {
            "question": "What size should a favicon ICO be?",
            "answer": "A favicon.ico typically contains 16x16 and 32x32 pixel images at minimum. Including 48x48 and 256x256 improves appearance on high-DPI displays and taskbars.",
        },
        {
            "question": "Can ICO files contain multiple sizes?",
            "answer": "Yes, ICO is specifically designed to bundle multiple resolutions in a single file so the operating system or browser picks the most suitable size automatically.",
        },
        {
            "question": "Should I use ICO or PNG for my favicon?",
            "answer": "ICO provides the best compatibility across all browsers including older IE versions. PNG favicons are supported by modern browsers and are simpler to produce.",
        },
        {
            "question": "How do I create an ICO file from PNG?",
            "answer": "You can convert a PNG to ICO using online converters or image editors that support ICO export. Many favicon generators accept PNG input and produce multi-size ICO files.",
        },
        {
            "question": "Is ICO supported on macOS?",
            "answer": "macOS uses ICNS as its native icon format. ICO files can be opened with some tools on macOS but the format is primarily used in Windows and web contexts.",
        },
    ],
}

_COMPARISON_OVERRIDES: dict[str, str] = {
    "gif-vs-png": "GIF supports animation but is limited to 256 colors per frame, while PNG is lossless with full color depth and transparency but has no animation support.",
    "png-vs-gif": "PNG is lossless with full color depth and transparency but has no animation support, while GIF supports animation and is limited to 256 colors per frame.",
    "gif-vs-webp": "WebP offers far better compression and full color depth at smaller sizes, while GIF remains more universally supported for animation in legacy environments.",
    "webp-vs-gif": "WebP offers far better compression and full color depth at smaller sizes, while GIF remains more universally supported for animation in legacy environments.",
    "gif-vs-jpg": "JPG is optimized for photographic images with millions of colors, while GIF is limited to 256 colors but uniquely supports looping animation.",
    "jpg-vs-gif": "JPG is optimized for photographic images with millions of colors, while GIF is limited to 256 colors but uniquely supports looping animation.",
    "svg-vs-png": "SVG is a resolution-independent vector format ideal for logos and icons at any size, while PNG is a raster format best suited to detailed photographs and screenshots.",
    "png-vs-svg": "PNG is a raster format best suited to detailed photographs and screenshots, while SVG is a resolution-independent vector format ideal for logos and icons at any size.",
    "svg-vs-pdf": "SVG is optimized for interactive and scalable web graphics and is rendered by browsers natively, while PDF is a document format designed for fixed-layout print and sharing.",
    "svg-vs-webp": "SVG is a vector format that scales infinitely and is ideal for line art and icons, while WebP is a raster format optimized for photographic compression on the web.",
    "bmp-vs-png": "PNG is lossless like BMP but uses efficient compression to produce files many times smaller, making PNG almost always the better choice for uncompressed-quality images.",
    "png-vs-bmp": "PNG is lossless like BMP but uses efficient compression to produce files many times smaller, making PNG almost always the better choice for uncompressed-quality images.",
    "bmp-vs-jpg": "BMP stores uncompressed data with no quality loss, while JPG uses lossy compression to produce much smaller files suitable for sharing and web use.",
    "jpg-vs-bmp": "JPG uses lossy compression to produce much smaller files suitable for sharing and web use, while BMP stores uncompressed data with no quality loss.",
    "bmp-vs-tiff": "Both BMP and TIFF can store lossless images, but TIFF supports richer metadata, CMYK color, multi-page documents, and compression options that BMP lacks.",
    "tiff-vs-bmp": "Both TIFF and BMP can store lossless images, but TIFF supports richer metadata, CMYK color, multi-page documents, and compression options that BMP lacks.",
    "tiff-vs-png": "TIFF is the professional archival standard with CMYK support and extensive metadata, while PNG is more efficient for web use and everyday lossless graphics.",
    "png-vs-tiff": "PNG is more efficient for web use and everyday lossless graphics, while TIFF is the professional archival standard with CMYK support and extensive metadata.",
    "tiff-vs-jpg": "TIFF is lossless and ideal for professional editing and archiving, while JPG uses lossy compression to produce small files suited for sharing and the web.",
    "jpg-vs-tiff": "JPG uses lossy compression to produce small files suited for sharing and the web, while TIFF is lossless and ideal for professional editing and archiving.",
    "heic-vs-jpg": "HEIC stores the same perceived quality as JPG at roughly half the file size and supports HDR, but JPG has far wider compatibility outside the Apple ecosystem.",
    "jpg-vs-heic": "JPG has far wider compatibility outside the Apple ecosystem, while HEIC stores the same perceived quality at roughly half the file size and supports HDR.",
    "heic-vs-png": "HEIC is more efficient than PNG for photographic images, but PNG is lossless and universally supported, making it preferable when exact quality preservation is required.",
    "heic-vs-webp": "Both HEIC and WebP offer better compression than JPG, but WebP has broader browser and platform support while HEIC is better integrated in the Apple ecosystem.",
    "avif-vs-webp": "AVIF compresses images 20-30% more efficiently than WebP at comparable quality and supports HDR, but WebP has wider legacy browser and tool support.",
    "webp-vs-avif": "WebP has wider legacy browser and tool support, while AVIF compresses images 20-30% more efficiently at comparable quality and supports HDR.",
    "avif-vs-jpg": "AVIF produces files roughly 50% smaller than JPG at the same perceptual quality and supports transparency and HDR, but JPG has near-universal compatibility.",
    "jpg-vs-avif": "JPG has near-universal compatibility across all devices and tools, while AVIF produces files roughly 50% smaller at the same perceptual quality.",
    "avif-vs-png": "AVIF offers dramatically smaller files than PNG for photographic images while supporting transparency and HDR, but PNG remains the universal lossless standard.",
    "png-vs-avif": "PNG remains the universal lossless standard for graphics and screenshots, while AVIF offers dramatically smaller files for photographic images with transparency and HDR.",
    "ico-vs-png": "ICO stores multiple icon resolutions in a single container optimized for Windows and browser favicons, while PNG is simpler and preferred for single-size modern web favicons.",
    "png-vs-ico": "PNG is simpler and preferred for single-size modern web favicons, while ICO stores multiple icon resolutions in a single container optimized for Windows and browser favicons.",
    "ico-vs-svg": "ICO is a raster container optimized for Windows and multi-resolution browser favicons, while SVG is a resolution-independent vector format preferred for scalable icons on modern devices.",
    "svg-vs-ico": "SVG is a resolution-independent vector format preferred for scalable icons on modern devices, while ICO is a raster container optimized for Windows and multi-resolution browser favicons.",
    "ico-vs-bmp": "ICO is a specialized icon container with multi-resolution support and transparency, while BMP is a simple uncompressed raster format without icon-specific features.",
}


def _t(template: str, name: str, category: str) -> str:
    """Apply template variable substitutions."""
    return template.replace("{NAME}", name).replace("{CATEGORY}", category)


def _apply_templates(
    items: list[dict[str, str]],
    name: str,
    category: str,
) -> list[dict[str, str]]:
    result = []
    for item in items:
        result.append({k: _t(v, name, category) for k, v in item.items()})
    return result


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class FormatKnowledgeGenerator:
    """Generate format knowledge payloads from canonical format master records.

    Input:  app/data/formats/{slug}.json
    Output: app/data/format_knowledge/{slug}.json
    """

    def __init__(
        self,
        formats_dir: Path | str | None = None,
        knowledge_dir: Path | str | None = None,
    ) -> None:
        self.formats_dir = Path(formats_dir or "app/data/formats")
        self.knowledge_dir = Path(knowledge_dir or "app/data/format_knowledge")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, slug: str, dry_run: bool = False) -> dict[str, Any]:
        """Generate a format knowledge payload for a single slug.

        Returns the generated (and validated) payload dict.
        Raises ValueError if the source master record is missing or invalid.
        """
        master = self._load_master(slug)
        payload = self._build_payload(master)
        errors = validate_format_knowledge(payload)
        if errors:
            raise ValueError(f"Generated payload for '{slug}' failed schema validation: {errors}")
        if not dry_run:
            self._write(slug, payload)
        return payload

    def generate_all(self, dry_run: bool = False) -> dict[str, Any]:
        """Generate knowledge files for every slug found in formats_dir.

        Returns a summary dict with 'succeeded', 'failed', and 'errors'.
        """
        slugs = self._discover_slugs()
        succeeded: list[str] = []
        failed: list[str] = []
        errors: dict[str, str] = {}

        for slug in slugs:
            try:
                self.generate(slug, dry_run=dry_run)
                succeeded.append(slug)
            except Exception as exc:  # noqa: BLE001
                failed.append(slug)
                errors[slug] = str(exc)

        return {
            "total": len(slugs),
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors,
        }

    def validate(self, slug: str) -> list[str]:
        """Validate an already-generated knowledge file against the schema.

        Returns a list of error strings (empty if valid).
        """
        path = self.knowledge_dir / f"{slug}.json"
        if not path.exists():
            return [f"Knowledge file not found: {path}"]
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            return [f"Failed to load knowledge file: {exc}"]
        return validate_format_knowledge(data)

    # ------------------------------------------------------------------
    # Internal: discovery and I/O
    # ------------------------------------------------------------------

    def _discover_slugs(self) -> list[str]:
        if not self.formats_dir.exists():
            return []
        return sorted(
            p.stem
            for p in self.formats_dir.glob("*.json")
            if not p.name.startswith("_")
        )

    def _load_master(self, slug: str) -> dict[str, Any]:
        path = self.formats_dir / f"{slug}.json"
        if not path.exists():
            raise OSError(f"Master format file not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"Master format file is not a JSON object: {path}")
        return data

    def _write(self, slug: str, payload: dict[str, Any]) -> None:
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        path = self.knowledge_dir / f"{slug}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    # ------------------------------------------------------------------
    # Internal: payload builder
    # ------------------------------------------------------------------

    @staticmethod
    def _article(word: str) -> str:
        """Return 'an' for vowel-initial words, 'a' otherwise."""
        return "an" if word[:1].lower() in "aeiou" else "a"

    def _build_payload(self, master: dict[str, Any]) -> dict[str, Any]:
        slug = str(master.get("slug", "")).strip().lower()
        name = str(master.get("name", slug.upper())).strip()
        category = str(master.get("category", "general")).strip().lower()
        description = str(master.get("description", "")).strip()
        related_formats: list[str] = [str(s) for s in (master.get("related_formats") or [])]
        related_converters: list[str] = [str(s) for s in (master.get("related_converters") or [])]

        return {
            "slug": slug,
            "name": name,
            "quick_answer": self._generate_quick_answer(name, category, description),
            "definition": self._generate_definition(name, category, description),
            "use_cases": self._generate_use_cases(name, category, slug),
            "advantages": self._generate_advantages(name, category, slug),
            "limitations": self._generate_limitations(name, category, slug),
            "comparisons": self._generate_comparisons(name, related_formats, slug),
            "related_tools": self._generate_related_tools(name, related_converters),
            "faq": self._generate_faq(name, category, slug),
        }

    # ------------------------------------------------------------------
    # Internal: section generators
    # ------------------------------------------------------------------

    def _generate_quick_answer(self, name: str, category: str, description: str) -> str:
        article = self._article(category)
        if description:
            return f"{name} — {description}"
        return (
            f"{name} is {article} widely used {category} file format with broad support "
            f"across applications and platforms."
        )

    def _generate_definition(self, name: str, category: str, description: str) -> str:
        article = self._article(category)
        if description:
            return (
                f"{name} is {article} {category} file format. {description} "
                f"It is commonly used in workflows that require reliable {category} handling "
                f"and is supported by a wide range of applications and online tools."
            )
        return (
            f"{name} is {article} standardized {category} file format with well-established support "
            f"across software, devices, and web platforms."
        )

    def _generate_use_cases(self, name: str, category: str, slug: str = "") -> list[dict[str, str]]:
        if slug and slug in _USE_CASES_BY_SLUG:
            return list(_USE_CASES_BY_SLUG[slug])
        templates = _USE_CASES_BY_CATEGORY.get(category) or _USE_CASES_BY_CATEGORY.get("document", [])
        return _apply_templates(templates, name, category)

    def _generate_advantages(self, name: str, category: str, slug: str = "") -> list[dict[str, str]]:
        if slug and slug in _ADVANTAGES_BY_SLUG:
            return list(_ADVANTAGES_BY_SLUG[slug])
        templates = _ADVANTAGES_BY_CATEGORY.get(category) or _ADVANTAGES_BY_CATEGORY.get("document", [])
        return _apply_templates(templates, name, category)

    def _generate_limitations(self, name: str, category: str, slug: str = "") -> list[dict[str, str]]:
        if slug and slug in _LIMITATIONS_BY_SLUG:
            return list(_LIMITATIONS_BY_SLUG[slug])
        templates = _LIMITATIONS_BY_CATEGORY.get(category) or _LIMITATIONS_BY_CATEGORY.get("document", [])
        return _apply_templates(templates, name, category)

    def _generate_comparisons(
        self,
        name: str,
        related_formats: list[str],
        slug: str = "",
    ) -> list[dict[str, str]]:
        comparisons = []
        for other in related_formats[:3]:
            other_name = other.upper()
            key = f"{slug}-vs-{other}" if slug else ""
            override = _COMPARISON_OVERRIDES.get(key, "")
            comparisons.append(
                {
                    "title": f"{name} vs {other_name}",
                    "text": override or (
                        f"{name} and {other_name} are both widely used file formats. "
                        f"Choosing between them depends on your compatibility needs, "
                        f"quality requirements, and the tools available in your workflow."
                    ),
                }
            )
        if not comparisons:
            comparisons.append(
                {
                    "title": f"{name} format overview",
                    "text": (
                        f"{name} is a practical format choice. Compare it to alternatives "
                        f"based on your target platform and output quality needs."
                    ),
                }
            )
        return comparisons

    def _generate_related_tools(
        self,
        name: str,
        related_converters: list[str],
    ) -> list[dict[str, str]]:
        tools = []
        for slug in related_converters[:6]:
            slug = slug.strip()
            if not slug:
                continue
            parts = slug.split("-to-", 1)
            if len(parts) == 2:
                src, tgt = parts[0].upper(), parts[1].upper()
                title = f"{src} to {tgt} Converter"
                description = f"Convert {src} files to {tgt} quickly and easily."
            else:
                label = slug.replace("-", " ").title()
                title = f"{label} Tool"
                description = f"Process files using the {label} tool."
            tools.append(
                {
                    "slug": slug,
                    "title": title,
                    "description": description,
                    "href": f"/{slug}",
                }
            )
        if not tools:
            tools.append(
                {
                    "slug": name.lower(),
                    "title": f"{name} Converter",
                    "description": f"Convert {name} files to other formats online.",
                    "href": f"/{name.lower()}",
                }
            )
        return tools

    def _generate_faq(self, name: str, category: str, slug: str = "") -> list[dict[str, str]]:
        if slug and slug in _FAQ_BY_SLUG:
            return list(_FAQ_BY_SLUG[slug])
        templates = _FAQ_BY_CATEGORY.get(category) or _DEFAULT_FAQ
        return _apply_templates(templates, name, category)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main() -> None:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate format knowledge JSON files from format master records."
    )
    parser.add_argument(
        "slugs",
        nargs="*",
        help="Specific format slugs to generate. Omit to generate all.",
    )
    parser.add_argument(
        "--formats-dir",
        default="app/data/formats",
        help="Directory containing master format JSON records.",
    )
    parser.add_argument(
        "--knowledge-dir",
        default="app/data/format_knowledge",
        help="Directory to write generated format knowledge JSON files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and generate payloads without writing files.",
    )
    args = parser.parse_args()

    generator = FormatKnowledgeGenerator(
        formats_dir=args.formats_dir,
        knowledge_dir=args.knowledge_dir,
    )

    if args.slugs:
        for slug in args.slugs:
            try:
                generator.generate(slug, dry_run=args.dry_run)
                status = "dry-run OK" if args.dry_run else "written"
                print(f"[OK] {slug}: {status}")
            except Exception as exc:  # noqa: BLE001
                print(f"[FAIL] {slug}: {exc}", file=sys.stderr)
    else:
        summary = generator.generate_all(dry_run=args.dry_run)
        print(f"Total: {summary['total']}")
        for slug in summary["succeeded"]:
            status = "dry-run OK" if args.dry_run else "written"
            print(f"[OK] {slug}: {status}")
        for slug in summary["failed"]:
            print(f"[FAIL] {slug}: {summary['errors'][slug]}", file=sys.stderr)


if __name__ == "__main__":
    _main()
