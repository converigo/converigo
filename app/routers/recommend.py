"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation API Router

Converigo Core Architecture
"""

import logging
from fastapi import APIRouter

from app.recommendation.engine import (
    recommendation_engine,
)


router = APIRouter(
    prefix="/recommend",
    tags=["recommendation"],
)

logger = logging.getLogger("app.recommend")


@router.get("/{source_format}")
async def recommend_converter(
    source_format: str,
):
    """
    Return best converter recommendation
    based on uploaded file format.
    """

    result = recommendation_engine.recommend(
        source_format
    )


    # Build response payload. Never return 404 — frontend expects a JSON payload
    # so provide structured fallbacks when the engine has no best_choice.
    detected = result.detected_type

    if result.best_choice is None:
        # Log a warning for unsupported/unknown source formats so observability
        # surface shows these as warnings rather than errors.
        logger.warning("No production-ready recommendation for '%s'", source_format)
        # Map any existing alternatives first
        alternatives = [
            {
                "source": option.source,
                "target": option.target,
                "title": getattr(option, "title", f"Convert to {option.target}"),
                "score": getattr(option, "score", 0),
            }
            for option in result.alternatives
        ]

        # If still empty, provide a small, safe fallback so the UI can render a choice.
        if not alternatives:
            # Prefer PDF as a generic target, then plain text — keep minimal and predictable.
            alternatives = [
                {
                    "source": source_format,
                    "target": "pdf",
                    "title": "Save as PDF",
                    "score": 0.0,
                }
            ]

        return {
            "detected_type": detected,
            "best_choice": None,
            "alternatives": alternatives,
        }

    # Normal successful response with a best choice and any alternatives
    return {
        "detected_type": result.detected_type,
        "best_choice": {
            "source": result.best_choice.source,
            "target": result.best_choice.target,
            "title": result.best_choice.title,
            "description": getattr(result.best_choice, "description", None),
            "goal": getattr(result.best_choice, "goal", None),
            "score": getattr(result.best_choice, "score", 0),
            "badge": getattr(result.best_choice, "badge", None),
            "icon": getattr(result.best_choice, "icon", None),
        },
        "alternatives": [
            {
                "source": option.source,
                "target": option.target,
                "title": getattr(option, "title", f"Convert to {option.target}"),
                "score": getattr(option, "score", 0),
            }
            for option in result.alternatives
        ],
    }