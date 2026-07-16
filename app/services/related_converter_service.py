from __future__ import annotations

from typing import Any

from app.services.converter_data_service import ConverterDataService


class RelatedConverterService:
    def __init__(self, converter_data_service: ConverterDataService) -> None:
        self.converter_data_service = converter_data_service

    def get_related_converters(self, converter: dict[str, Any], limit: int = 4) -> list[dict[str, Any]]:
        if not converter:
            return []

        all_converters = self.converter_data_service.list_supported_converters()
        current_slug = str(converter.get("slug") or "").strip()
        current_source = str(converter.get("source") or "").lower()
        current_target = str(converter.get("target") or "").lower()
        current_cluster = str(converter.get("cluster") or self._infer_cluster(converter)).lower()
        current_output_category = str(converter.get("output_category") or self._infer_output_category(converter)).lower()

        candidates: list[dict[str, Any]] = []
        for candidate in all_converters:
            candidate_slug = str(candidate.get("slug") or "").strip()
            if not candidate_slug or candidate_slug == current_slug:
                continue

            candidate_source = str(candidate.get("source") or "").lower()
            candidate_target = str(candidate.get("target") or "").lower()
            candidate_cluster = str(candidate.get("cluster") or self._infer_cluster(candidate)).lower()
            candidate_output_category = str(candidate.get("output_category") or self._infer_output_category(candidate)).lower()

            same_input = bool(current_source and candidate_source and current_source == candidate_source)
            same_output_category = bool(current_output_category and candidate_output_category and current_output_category == candidate_output_category)
            same_cluster = bool(current_cluster and candidate_cluster and current_cluster == candidate_cluster)

            if not (same_input or same_output_category or same_cluster):
                continue

            score = 0
            if same_input:
                score += 4
            if same_output_category:
                score += 3
            if same_cluster:
                score += 2
            if current_target and candidate_target and current_target == candidate_target:
                score += 1

            candidate_copy = dict(candidate)
            candidate_copy["_score"] = score
            candidate_copy["_match_reasons"] = {
                "same_input": same_input,
                "same_output_category": same_output_category,
                "same_cluster": same_cluster,
            }
            candidates.append(candidate_copy)

        candidates.sort(key=lambda item: (-int(item.get("_score", 0)), str(item.get("title") or "")))

        unique_candidates: list[dict[str, Any]] = []
        seen_slugs: set[str] = set()
        for candidate in candidates:
            slug = str(candidate.get("slug") or "").strip()
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            unique_candidates.append({
                "slug": slug,
                "title": candidate.get("title") or slug.replace("-", " ").title(),
                "description": candidate.get("description") or "",
                "source": candidate.get("source"),
                "target": candidate.get("target"),
                "category": candidate.get("category"),
                "cluster": str(candidate.get("cluster") or self._infer_cluster(candidate)).lower(),
                "match_reasons": candidate.get("_match_reasons"),
            })

        if len(unique_candidates) < limit:
            fallback = [
                item for item in all_converters
                if str(item.get("slug") or "").strip() != current_slug and str(item.get("slug") or "").strip() not in seen_slugs
            ]
            for item in fallback:
                slug = str(item.get("slug") or "").strip()
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                unique_candidates.append({
                    "slug": slug,
                    "title": item.get("title") or slug.replace("-", " ").title(),
                    "description": item.get("description") or "",
                    "source": item.get("source"),
                    "target": item.get("target"),
                    "category": item.get("category"),
                    "cluster": str(item.get("cluster") or self._infer_cluster(item)).lower(),
                    "match_reasons": {},
                })
                if len(unique_candidates) >= limit:
                    break

        return unique_candidates[:limit]

    def _infer_cluster(self, converter: dict[str, Any]) -> str:
        source = str(converter.get("source") or "").lower()
        target = str(converter.get("target") or "").lower()

        if self._is_video(source) and self._is_audio(target):
            return "video-audio"
        if self._is_audio(source) and self._is_video(target):
            return "video-audio"
        if self._is_image(source) and self._is_image(target):
            return "image"
        if self._is_audio(source) and self._is_audio(target):
            return "audio"
        if self._is_video(source) and self._is_video(target):
            return "video"
        if self._is_document(source) and self._is_document(target):
            return "document"

        return str(converter.get("category") or "").lower()

    def _infer_output_category(self, converter: dict[str, Any]) -> str:
        target = str(converter.get("target") or "").lower()
        if self._is_audio(target):
            return "audio"
        if self._is_image(target):
            return "image"
        if self._is_video(target):
            return "video"
        if self._is_document(target):
            return "document"
        return str(converter.get("category") or "").lower()

    def _is_audio(self, value: str) -> bool:
        return value in {"mp3", "wav", "flac", "ogg", "m4a", "aac", "opus"}

    def _is_image(self, value: str) -> bool:
        return value in {"jpg", "jpeg", "png", "webp", "bmp", "gif", "ico", "svg"}

    def _is_video(self, value: str) -> bool:
        return value in {"mp4", "mov", "avi", "mkv", "webm", "mpeg", "mpg", "wmv"}

    def _is_document(self, value: str) -> bool:
        return value in {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "odt", "rtf"}
