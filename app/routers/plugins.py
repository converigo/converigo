"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

Plugin API
"""

from fastapi import APIRouter

from app.plugins.registry import registry

router = APIRouter(
    prefix="/api/plugins",
    tags=["Plugins"],
)


@router.get("")
async def get_plugins():

    plugins = []

    for (source, target), plugin in registry.plugins.items():

        plugins.append(
            {
                "slug": plugin.slug,
                "source": source,
                "target": target,
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