"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.1.0

Plugin API
"""

from fastapi import APIRouter, Query

from app.plugins.registry import registry

router = APIRouter(
    prefix="/api/plugins",
    tags=["Plugins"],
)


def normalize_format(file_format: str) -> str:
    """
    Normalize format aliases.
    """

    aliases = {
        "jpeg": "jpg",
    }

    return aliases.get(
        file_format.lower(),
        file_format.lower(),
    )


@router.get("")
async def get_plugins(

    source: str | None = Query(
        default=None,
        description="Filter by source format",
    ),

):

    plugins = []

    seen = set()

    for (plugin_source, plugin_target), plugin in registry.plugins.items():

        normalized_source = normalize_format(
            plugin_source
        )

        normalized_target = normalize_format(
            plugin_target
        )

        if source is not None:

            if normalized_source != normalize_format(source):

                continue

        key = (
            normalized_source,
            normalized_target,
        )

        if key in seen:
            continue

        seen.add(key)

        plugins.append(
            {
                "slug": plugin.slug,
                "title": plugin.slug.replace(
                    "-",
                    " ",
                ).upper(),
                "category": getattr(
                    plugin,
                    "category",
                    "general",
                ),
                "source": normalized_source,
                "target": normalized_target,
            }
        )

    plugins.sort(
        key=lambda item: (
            item["source"],
            item["target"],
        )
    )

    return {
        "total": len(plugins),
        "plugins": plugins,
    }