"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation API Router

Convertin Core Architecture
"""

from fastapi import APIRouter, HTTPException

from app.recommendation.engine import (
    recommendation_engine,
)


router = APIRouter(
    prefix="/recommend",
    tags=["recommendation"],
)


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


    if result.best_choice is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No recommendation found "
                f"for {source_format}"
            ),
        )


    return {

        "detected_type": result.detected_type,


        "best_choice": {

            "source": result.best_choice.source,

            "target": result.best_choice.target,

            "title": result.best_choice.title,

            "description": result.best_choice.description,

            "goal": result.best_choice.goal,

            "score": result.best_choice.score,

            "badge": result.best_choice.badge,

            "icon": result.best_choice.icon,

        },


        "alternatives": [

            {

                "source": option.source,

                "target": option.target,

                "title": option.title,

                "score": option.score,

            }

            for option in result.alternatives

        ],

    }