"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation API Router

Converigo Core Architecture
"""

import logging
from fastapi import APIRouter, Query

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
    operation: str | None = Query(
        default=None,
        max_length=64,
        description=(
            "Tool-page operation slug (e.g. 'pdf-compress'). /convert posts "
            "operation=<page slug>, so the recommendation must be scoped by the "
            "same key the dispatch registry uses; otherwise a chip can advertise "
            "a target this page cannot dispatch."
        ),
    ),
):
    """
    Return best converter recommendation
    based on uploaded file format.

    Eligibility is answered by the D5 target-capability authority for this
    operation; this endpoint only ranks what the authority already allows.
    """

    result = recommendation_engine.recommend(
        source_format,
        operation=operation,
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

        # Fail closed. A target we cannot dispatch must never be invented here:
        # the previous generic "Save as PDF" fallback advertised capability the
        # authority had not granted (and /convert would reject with 422).
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