"""Apply SEO Content Enhancement to all converter JSON files."""
from pathlib import Path
from app.services.seo_content_enhancement_service import SeoContentEnhancementService

service = SeoContentEnhancementService(Path("app/data/converters"))
result = service.enhance_all_converters()
print(f"Scanned: {result['total_files_scanned']}")
print(f"Enhanced: {result['files_enhanced']}")
for change in result["changes"]:
    print(f"  {change['slug']}: {change['changes']}")
print("Done.")

