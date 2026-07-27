# Converigo AI Brain

## Purpose
Converigo AI Brain is the internal metadata platform that prepares repository context for future AI workflows. It is designed to maximize project understanding quality while remaining fully isolated from runtime business logic.

## Platform Scope
Current scope is metadata generation and metadata validation only.

Out of scope in this phase:
- RAG implementation
- Embeddings
- Vector databases
- Model integration

## Folder Responsibilities
- knowledge/: Human-maintained AI knowledge documents and governance context.
- memory/: Structured JSON memory contracts for durable AI-facing state.
- generated/: Machine-generated metadata outputs produced by scanners/builders.
- prompts/: Prompt assets and instruction packs for AI operations.
- scripts/: Metadata scanners, builders, validators, and orchestration utilities.
- rag/: Retrieval design assets reserved for future phases.
- config/: Declarative scanner and metadata pipeline configuration.

## Script Catalog

### Project Scanner
File: scripts/project_scanner.py

Responsibilities:
- Scan repository files using path-based metadata only.
- Generate project_index.json.
- Generate file_tree.json.
- Generate import_map.json from Python AST import statements.

### Project Map
File: scripts/project_map.py

Responsibilities:
- Organize repository paths into top-level architecture categories using folder structure.
- Generate project_map.json.

### Knowledge Builder
File: scripts/knowledge_builder.py

Responsibilities:
- Read generated metadata files.
- Produce metadata-only aggregate summary.
- Generate knowledge_summary.json.

### Module Summary
File: scripts/module_summary.py

Responsibilities:
- Read module_index.json.
- Produce module_summary.md with module metadata fields only.

### Route Scanner
File: scripts/route_scanner.py

Responsibilities:
- Discover FastAPI route decorators via Python AST.
- Collect router, endpoint, HTTP method, and source file.
- Generate routes.json.

### Service Scanner
File: scripts/service_scanner.py

Responsibilities:
- Scan app/services.
- Collect service name, source file, and public methods.
- Generate services.json.

### Converter Scanner
File: scripts/converter_scanner.py

Responsibilities:
- Scan converter plugin files.
- Collect converter name, category, and source file.
- Generate converters.json.

### Context Builder
File: scripts/context_builder.py

Responsibilities:
- Read every JSON metadata file from generated/.
- Combine project overview, maps, modules, services, routes, converters, and imports.
- Generate context.json.

### Health Check
File: scripts/health_check.py

Responsibilities:
- Validate required generated metadata file presence.
- Validate JSON readability for required artifacts.
- Emit readable validation report to stdout and generated/health_report.txt.

### Runner
File: scripts/build_ai_brain.py

Responsibilities:
- Execute AI_BRAIN metadata pipeline in deterministic order.
- Print step progress and status.
- Continue gracefully when individual steps fail unless stop-on-error is enabled.

## Execution Order
1. project_scanner
2. project_map
3. knowledge_builder
4. module_summary
5. route_scanner
6. service_scanner
7. converter_scanner
8. context_builder
9. health_check

## Primary Outputs
- generated/project_index.json
- generated/file_tree.json
- generated/import_map.json
- generated/project_map.json
- generated/routes.json
- generated/services.json
- generated/converters.json
- generated/knowledge_summary.json
- generated/module_summary.md
- generated/context.json
- generated/health_report.txt

## Operating Principles
- Metadata-only extraction.
- No source code modification.
- Deterministic output formats.
- Python 3.11+ standard-library-only implementation.
- Strict separation from application runtime behavior.
