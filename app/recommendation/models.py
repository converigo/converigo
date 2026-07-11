"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation Models

Single Source of Truth
for Recommendation Engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class RecommendationOption:
    """
    One possible conversion recommendation.
    """

    source: str

    target: str

    title: str

    description: str

    category: str

    goal: str

    priority: int

    quality: int

    compatibility: int

    estimated_saving: int

    score: float = 0.0

    badge: str = ""

    icon: str = "📄"


@dataclass(slots=True)
class RecommendationResult:
    """
    Final response from Recommendation Engine.
    """

    detected_type: str

    best_choice: Optional[RecommendationOption]

    alternatives: List[RecommendationOption]