# Converigo Authority Database

## Overview

The Converigo Authority Database is the first implementation of the authority layer for file formats. It provides structured, deterministic content for each known file format so the platform can treat every converter as a format authority hub.

## Purpose

- Expose a reusable authority payload for each file format
- Enable landing and knowledge experiences to consume format authority data
- Support audit and dashboard coverage for format authority completeness
- Reuse existing services without changing the landing, knowledge, or SEO engines

## Scope

The authority payload is generated for each format discovered in active converter contracts, including formats used as input or output.

## Required Sections

Each authority payload contains the following sections:

- `history`
- `specification`
- `developer_maintainer`
- `mime_type`
- `file_extension`
- `category`
- `compression`
- `encoding`
- `metadata`
- `typical_file_size`
- `compatibility`
- `operating_system_support`
- `software_support`
- `advantages`
- `disadvantages`
- `security_considerations`
- `accessibility`
- `performance`
- `common_problems`
- `troubleshooting`
- `alternatives`
- `comparison`
- `best_practices`
- `glossary`
- `references`

## Implementation

- `app/services/authority_service.py`
  - Generates deterministic `AuthorityService.generate_payload(format_name)` and `generate_all()` output
  - Uses active converter contracts from `app/services/converter_registry_service.py`
  - Reuses category inference and format metadata from existing converter contracts

- `tests/test_authority_service.py`
  - Verifies every known format emits an authority payload
  - Verifies required sections exist
  - Verifies deterministic output
  - Verifies no duplicate sections

## Format Discovery

The authority service discovers formats from active converter contracts by reading `input_formats` and `output_formats` from each contract.

## Integration Strategy

- No landing engine rewrite required
- No knowledge engine rewrite required
- No SEO engine rewrite required
- Uses existing registry, landing, and audit services for compatibility

## Coverage

Authority payload generation is now regression-tested and integrated with the existing contract lifecycle model.
