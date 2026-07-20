from app.plugins.registry import registry

# Get some sample plugins
plugins_jpg = registry.get_plugins_by_source('jpg')
if plugins_jpg:
    p = plugins_jpg[0]
    print(f"Plugin: {p.slug}")
    print(f"Has source_formats: {hasattr(p, 'source_formats')}")
    print(f"Has target_formats: {hasattr(p, 'target_formats')}")
    print(f"Attributes: {[a for a in dir(p) if not a.startswith('_')]}")
