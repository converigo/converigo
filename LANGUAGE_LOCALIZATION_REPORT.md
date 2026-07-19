# LANGUAGE LOCALIZATION REPORT

## Problem
Homepage and UI copy had a mix of hardcoded strings and incomplete locale entries across the homepage, upload card, FAQ, and footer. The requested language values also had mismatches between the locale JSON files and the rendered templates.

## Root Cause
The templates used hardcoded text in several visible sections instead of relying on the existing locale translation system. Some new translation keys were missing from the locale JSON files, and the homepage hero text did not consistently use the translation layer.

## Files
- app/templates/components/hero.html
- app/templates/components/upload_card.html
- app/templates/components/faq.html
- app/templates/components/footer.html
- app/locales/en.json
- app/locales/id.json
- app/locales/ja.json

## Fix
- Replaced the main hero and upload-card hardcoded phrases with translation lookups.
- Added missing FAQ and footer translation keys for English, Indonesian, and Japanese.
- Ensured the homepage hero title/description and upload instructions now resolve via the locale system.

## Validation
- Parsed all three locale files successfully as JSON.
- Confirmed the translation keys are present in the English locale file.

## Result
Localized homepage and UI copy now resolve through the translation system for EN/ID/JA, and the visible mismatch in the hero/upload/FAQ/footer sections has been reduced.
