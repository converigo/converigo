# AI_BRAIN MCP Server v1

This directory implements a minimal MCP server for AI_BRAIN.

## Files

- `server.py`: Exposes tool registration, invocation, and resource loading.
- `tools.py`: Implements the MCP tools.
- `resources.py`: Loads generated JSON artifacts from `AI_BRAIN/generated`.
- `prompts.py`: Provides prompt helper templates.
- `README.md`: This document.

## Tools

- `project_summary()`: Returns a repository architecture summary.
- `find_module(module_name)`: Finds semantic module metadata matching a name fragment.
- `related_modules(module_name)`: Returns closely related modules.
- `build_context(task)`: Builds an AI prompt for a task using AI_BRAIN gateway logic.

## Resources

- `semantic_knowledge.json`
- `relationships.json`
- `dependency_graph.json`
- `reasoning_context.json`

## Example

```bash
python AI_BRAIN/mcp_server/server.py
```

```python
from AI_BRAIN.mcp_server.server import invoke_tool, list_tools, list_resources

print(list_tools())
print(list_resources())
result = invoke_tool("project_summary")
print(result.data)
```
