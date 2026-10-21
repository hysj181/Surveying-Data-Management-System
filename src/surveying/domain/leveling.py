from __future__ import annotations

import math
from dataclasses import dataclass

from .models import DomainError, LevelingProject, LevelingSegment, QualityLevel, RouteType


@dataclass(frozen=True)
class SegmentResult:
    index: int
    segment: LevelingSegment
    correction_m: float
    corrected_difference_m: float
    from_elevation_m: float
    to_elevation_m: float

    @property
    def correction_mm(self) -> float:
        return self.correction_m * 1000.0


@dataclass(frozen=True)
class LevelingResult:
    project_name: str
    route_type: RouteType
    grade: str
    grade_coefficient_mm_per_sqrt_km: float
    start_point: str
    end_point: str
    start_elevation_m: float
    target_end_elevation_m: float
    computed_end_elevation_m: float
    total_distance_m: float
    observed_difference_sum_m: float
    correction_sum_m: float
    corrected_difference_sum_m: float
    closure_error_m: float
    allowable_closure_m: float
    is_within_tolerance: bool
    quality_level: QualityLevel
    misclosure_ratio: float | None
    correction_rms_m: float
    max_abs_correction_m: float
    segments: tuple[SegmentResult, ...]
    warnings: tuple[str, ...]

    @property
    def total_distance_km(self) -> float:
        return self.total_distance_m / 1000.0

    @property
    def closure_error_mm(self) -> float:
        return self.closure_error_m * 1000.0

    @property
    def allowable_closure_mm(self) -> float:
        return self.allowable_closure_m * 1000.0

    @property
    def closure_utilization(self) -> float | None:
        if self.allowable_closure_m <= 0:
            return None
        return abs(self.closure_error_m) / self.allowable_closure_m

    @property
    def misclosure_ratio_text(self) -> str:
        if self.misclosure_ratio is None:
            return "闭合差为零"
        return f"1/{self.misclosure_ratio:,.0f}"


def _validate_project(project: LevelingProject) -> None:
    if not project.segments:
        raise DomainError("请至少添加一个测段后再进行计算。")
    if not project.start_point.strip():
        raise DomainError("起点名称不能为空。")
    if project.route_type is RouteType.ATTACHED and not project.end_point.strip():
        raise DomainError("附合路线必须填写终点名称。")
    if not math.isfinite(project.start_elevation_m):
        raise DomainError("起点高程必须是有效数字。")
    if project.route_type is RouteType.ATTACHED and not math.isfinite(project.end_elevation_m):
        raise DomainError("终点高程必须是有效数字。")
    for index, segment in enumerate(project.segments, start=1):
        if not segment.from_point.strip() or not segment.to_point.strip():
            raise DomainError(f"第 {index} 个测段的起点或终点名称为空。")
        if not math.isfinite(segment.distance_m) or segment.distance_m <= 0:
            raise DomainError(f"第 {index} 个测段的距离必须大于 0。")
        if not math.isfinite(segment.observed_difference_m):
            raise DomainError(f"第 {index} 个测段的观测高差无效。")


def _quality_level(utilization: float, within_tolerance: bool) -> QualityLevel:
    if not within_tolerance:
        return QualityLevel.FAILED
    if utilization <= 0.5:
        return QualityLevel.EXCELLENT
    if utilization <= 0.75:
        return QualityLevel.GOOD
    return QualityLevel.PASS


def calculate_leveling(project: LevelingProject) -> LevelingResult:
    _validate_project(project)

    total_distance_m = sum(segment.distance_m for segment in project.segments)
    if total_distance_m <= 0:
        raise DomainError("路线总距离必须大于 0。")

    observed_sum_m = sum(segment.observed_difference_m for segment in project.segments)
    if project.route_type is RouteType.CLOSED:
        target_end_elevation_m = project.start_elevation_m
        known_difference_m = 0.0
    else:
        target_end_elevation_m = project.end_elevation_m
        known_difference_m = target_end_elevation_m - project.start_elevation_m

    closure_error_m = observed_sum_m - known_difference_m
    coefficient = project.grade.coefficient_mm_per_sqrt_km
    allowable_closure_m = coefficient * math.sqrt(total_distance_m / 1000.0) / 1000.0
    within_tolerance = abs(closure_error_m) <= allowable_closure_m + 1e-12
    utilization = abs(closure_error_m) / allowable_closure_m if allowable_closure_m else 0.0

    segment_results: list[SegmentResult] = []
    current_elevation_m = project.start_elevation_m
    for index, segment in enumerate(project.segments, start=1):
        correction_m = -closure_error_m * (segment.distance_m / total_distance_m)
        corrected_difference_m = segment.observed_difference_m + correction_m
        next_elevation_m = current_elevation_m + corrected_difference_m
        segment_results.append(
            SegmentResult(
                index=index,
                segment=segment,
                correction_m=correction_m,
                corrected_difference_m=corrected_difference_m,
                from_elevation_m=current_elevation_m,
                to_elevation_m=next_elevation_m,
            )
        )
        current_elevation_m = next_elevation_m

    corrected_sum_m = sum(item.corrected_difference_m for item in segment_results)
    correction_sum_m = sum(item.correction_m for item in segment_results)
    computed_end_elevation_m = project.start_elevation_m + corrected_sum_m
    correction_rms_m = math.sqrt(
        sum(item.correction_m**2 for item in segment_results) / len(segment_results)
    )
    max_abs_correction_m = max(abs(item.correction_m) for item in segment_results)
    misclosure_ratio = (
        None if abs(closure_error_m) < 1e-12 else total_distance_m / abs(closure_error_m)
    )

    warnings: list[str] = []
    for previous, current in zip(project.segments, project.segments[1:]):
        if previous.to_point.strip() != current.from_point.strip():
            warnings.append(
                f"测段“{previous.from_point}→{previous.to_point}”与"
                f"“{current.from_point}→{current.to_point}”的点名不连续。"
            )
    if project.route_type is RouteType.CLOSED:
        last_point = project.segments[-1].to_point.strip()
        if last_point != project.start_point.strip():
            warnings.append("闭合路线的最后一个测段终点与起点名称不一致。")
    if not within_tolerance:
        warnings.append("闭合差超过容许值，成果不得直接使用。")

    return LevelingResult(
        project_name=project.name,
        route_type=project.route_type,
        grade=project.grade.value,
        grade_coefficient_mm_per_sqrt_km=coefficient,
        start_point=project.start_point,
        end_point=project.start_point if project.route_type is RouteType.CLOSED else project.end_point,
        start_elevation_m=project.start_elevation_m,
        target_end_elevation_m=target_end_elevation_m,
        computed_end_elevation_m=computed_end_elevation_m,
        total_distance_m=total_distance_m,
        observed_difference_sum_m=observed_sum_m,
        correction_sum_m=correction_sum_m,
        corrected_difference_sum_m=corrected_sum_m,
        closure_error_m=closure_error_m,
        allowable_closure_m=allowable_closure_m,
        is_within_tolerance=within_tolerance,
        quality_level=_quality_level(utilization, within_tolerance),
        misclosure_ratio=misclosure_ratio,
        correction_rms_m=correction_rms_m,
        max_abs_correction_m=max_abs_correction_m,
        segments=tuple(segment_results),
        warnings=tuple(warnings),
    )
