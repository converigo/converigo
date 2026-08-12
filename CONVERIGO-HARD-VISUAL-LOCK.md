# CONVERIGO HARD VISUAL LOCK

VERSION:
1.2

STATUS:
ACTIVE

PURPOSE:
Protect production visual baseline.

==================================================

# MANDATORY FIRST STEP

Before every task:

READ THIS FILE FIRST.

No exception.

The rules inside this file have priority for visual protection.

==================================================

# PRODUCTION VISUAL CORE LOCK

The following files are permanently protected.

NEVER OPEN, READ, OR MODIFY DURING LANGUAGE TASKS:

app/templates/main/converigo_main.html

app/templates/layouts/base.html

app/static/**


Including:

- CSS
- JS
- images
- icons
- SVG
- favicon
- animation files


Reason:

These files control:

- homepage layout
- logo
- icons
- animations
- spacing
- typography
- position
- visual behavior


==================================================

# LANGUAGE WORK PERMISSION

Language tasks are the only exception.

Allowed files:

ONLY:

app/templates/components/header.html

app/locales/en.json

app/locales/id.json

app/locales/ja.json


==================================================

# HEADER RESTRICTION

ALLOW ONLY:

- changing visible language option text

FORBID:

- HTML changes
- attributes
- classes
- IDs
- structure
- navigation
- logo area


==================================================

# LOCALE RESTRICTION

ALLOW ONLY:

- existing translation value replacement

FORBID:

- new keys
- deleted keys
- JSON restructuring
- text expansion causing layout change


==================================================

# LANGUAGE TASK RESTRICTIONS

Allowed:

- change translation text only in approved locale files
- change visible language option text only in header.html

Forbidden:

- changing HTML structure
- changing CSS
- changing JS
- changing classes
- changing IDs
- changing component hierarchy
- changing layout
- changing spacing
- changing typography
- changing animations
- opening or reading protected visual files during language tasks


==================================================

# LOGO PROTECTION

Never:

- replace logo
- redesign logo
- recreate logo
- modify logo asset
- modify favicon
- modify SVG icons


Logo must remain identical.


==================================================

# ANIMATION PROTECTION

Never modify:

- @keyframes
- animation property
- transition property
- morph badge
- upload animation


==================================================

# PRE EDIT CHECK

Before every modification:

Run:

git status --short

git diff --name-only

If any protected file appears:

STOP.

Return:

VISUAL LOCK VIOLATION DETECTED

Do not continue.

==================================================

# PATCH CONTROL

Before applying changes report:

FILES TO MODIFY:

- CRITICAL NOTE (2026-08-12): The `@keyframes morph` block in `app/templates/main/converigo_main.html` (lines 666-671) was previously deleted in recent commits and has been restored to maintain homepage morphing behavior. This block is CRITICAL — PREVIOUSLY DELETED, NEVER REMOVE AGAIN.

- CONVERIGO-HARD-VISUAL-LOCK.md

ARE FILES ALLOWED:

YES / NO

VISUAL IMPACT:

YES / NO


If visual impact is YES:

STOP unless explicit authorization is provided.

==================================================

# AFTER CHANGE VERIFICATION

Run:

git diff --name-only

Expected:

ONLY:
CONVERIGO-HARD-VISUAL-LOCK.md

No commit.
No push.
No deploy.

If any unexpected file appears:

STOP.

Report:

UNAUTHORIZED FILE CHANGE DETECTED


==================================================

# FINAL REPORT FORMAT

Every task must end with:

FILES CHANGED:

-

PROTECTED FILES TOUCHED:

YES / NO


LOGO:

UNCHANGED / CHANGED


ANIMATION:

UNCHANGED / CHANGED


LAYOUT:

UNCHANGED / CHANGED


POSITION:

UNCHANGED / CHANGED


RESULT:

PASS / FAIL


==================================================

END OF CONVERIGO HARD VISUAL LOCK

==================================================


STEP 4 — VERIFY CREATION

After creating the file:

Run:

git status --short

Expected:

Only:

?? CONVERIGO-HARD-VISUAL-LOCK.md


No other application files should appear.


==================================================

STEP 5 — FINAL RESPONSE

Report:

1. File created path
2. Git status result
3. Confirmation:
   - No application files modified
   - No visual files modified
   - No logo touched
   - No animation touched

STOP AFTER REPORT.

DO NOT COMMIT.
DO NOT PUSH.
DO NOT DEPLOY.
