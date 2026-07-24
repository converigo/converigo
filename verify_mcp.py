import json
import pathlib
import sys
from pprint import pprint
repo = pathlib.Path('.').resolve()
sys.path.insert(0, str(repo))
from AI_BRAIN.mcp_server.server import list_tool_names, list_resource_uris, invoke_tool, build_context_tool
path = repo / '.continue' / 'mcpServers' / 'AI_BRAIN.json'
print('AI_BRAIN.json exists:', path.exists())
d = json.loads(path.read_text(encoding='utf-8'))
print('Top keys:', list(d.keys()))
print('mcpServers entries:', len(d.get('mcpServers', [])))
pprint(d.get('mcpServers', []))
print('\nRegistered tools:')
print(list_tool_names())
print('\nRegistered resources:')
print(list_resource_uris())
print('\nInvoking find_service(DownloadService)')
print(invoke_tool('find_service', {'name': 'DownloadService'}))
print('\nInvoking find_converter(PDF)')
print(invoke_tool('find_converter', {'name': 'PDF'}))
print('\nInvoking find_converter(HEIC)')
print(invoke_tool('find_converter', {'name': 'HEIC'}))
print('\nInvoking architecture_summary(summary)')
print(invoke_tool('architecture_summary', {'detail_level': 'summary'}))
print('\nInvoking implementation_plan(Explain upload flow)')
print(invoke_tool('implementation_plan', {'task': 'Explain upload flow'}))
print('\nInvoking build_context_tool(Where is DownloadService?)')
print(build_context_tool('Where is DownloadService?'))
