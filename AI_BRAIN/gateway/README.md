# AI Gateway v1

This directory contains a lightweight AI gateway for Converigo `AI_BRAIN`.

## Purpose

The gateway prepares optimized text prompts for AI models using generated repository metadata. It does not call any AI model or external service.

## Components

- `context_loader.py`: Loads generated metadata artifacts.
- `context_ranker.py`: Selects the most relevant modules, services, routes, and converters for a user task.
- `task_detector.py`: Classifies user requests into task categories.
- `prompt_builder.py`: Builds a structured prompt with summary, task details, relevant context, and coding rules.
- `gateway.py`: Exposes `build_prompt_for_task(user_task)` to generate the final prompt.

## Usage

Run the gateway from the AI_BRAIN root:

```bash
python AI_BRAIN/gateway/gateway.py
```

Or integrate in code:

```python
from AI_BRAIN.gateway.gateway import build_prompt_for_task

prompt = build_prompt_for_task("Fix the upload crash when converting large PDF documents.")
print(prompt)
```

## Requirements

- Python 3.11
- Standard library only
- Works from the `AI_BRAIN` repository root
