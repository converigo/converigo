# Repository Intelligence Brain

## Purpose
The AI_BRAIN brain layer transforms generated repository metadata into structured semantic knowledge for model reasoning. It operates on metadata artifacts only and does not inspect implementation internals.

## Architecture
The brain layer is organized as independent engines that each produce one explicit output artifact.

### Relationship Engine
Creates cross-entity relationship records between modules, services, routers, converters, and plugins based on generated metadata associations.

### Dependency Engine
Converts import metadata into internal and external dependency views, with deterministic JSON structures suitable for downstream reasoning.

### Pattern Engine
Detects repository layer patterns from metadata evidence such as folder categories and generated entity inventories.

### Semantic Engine
Builds module-level semantic objects by merging relationship, dependency, test, and documentation metadata into a single structured knowledge set.

### Reasoning Context
Produces a consolidated context artifact that summarizes architecture, dependencies, patterns, relationships, and semantic knowledge for prompt-ready AI consumption.

## Supporting Engines
Additional mappers enrich the semantic layer:
- test mapping engine
- documentation mapping engine

## Data Contracts
Inputs are generated JSON metadata files in AI_BRAIN/generated.
Outputs are generated JSON intelligence artifacts in AI_BRAIN/generated.
