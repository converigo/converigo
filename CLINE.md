# Converigo Engineering Rules

## Mission

Converigo is a production-ready online file conversion platform focused on:

- Performance
- SEO
- Scalability
- Reliability
- Mobile-first UX

Primary goal:

Google Search → Organic Traffic → Google AdSense → Revenue

---

# General Rules

- Always analyze before coding.
- Never modify files without approval.
- Explain the implementation plan before editing.
- Keep changes as small as possible.
- Never remove working features.
- Preserve backward compatibility whenever possible.

---

# Response Style

For simple analysis tasks:

- Do not create todo lists.
- Do not explain your plan.
- Read requested files immediately.
- Return the final answer directly.

Only create a plan if explicitly requested.

For implementation tasks:

1. Explain implementation plan.
2. Wait for approval.
3. Implement.
4. Validate.
5. Report.

---

# Architecture

Always preserve:

- Plugin architecture
- Conversion pipeline
- SEO system
- Localization (i18n)
- Mobile-first UI
- Dynamic tool system

Prefer reusable components.

Avoid duplicated logic.

---

# Plugin Rules

New converters must:

- Use the existing plugin architecture.
- Register automatically.
- Never modify unrelated plugins.
- Follow the ConverterPlugin interface.
- Be production-ready.

---

# SEO Rules

Never break:

- Sitemap
- robots.txt
- Meta tags
- Open Graph
- Structured Data
- Canonical URLs

Every new converter must support SEO.

---

# Localization Rules

Never hardcode user-facing text.

Always use the localization system.

Support existing languages.

---

# Code Quality

Write production-ready code.

Keep functions small.

Write readable code.

Handle errors properly.

Avoid unnecessary complexity.

---

# Validation

Before finishing:

- Run syntax validation.
- Run available tests.
- Verify affected routes.
- Verify plugin discovery.
- Report validation results.

Never claim success without verification.

---

# Git Rules

One feature = one commit.

Commit message format:

Sprint XX - Feature Name

Example:

Sprint 17 - Word to PDF Plugin

---

# Before Finishing

Always provide:

1. Summary
2. Files modified
3. Why
4. Risks
5. Validation
6. Next recommendation

---

# Never Do

- Break SEO.
- Break localization.
- Break plugin discovery.
- Break existing routes.
- Remove production functionality.
- Change architecture without explanation.
- Edit files without approval.