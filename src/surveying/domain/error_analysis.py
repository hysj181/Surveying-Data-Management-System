from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass

from .leveling import LevelingResult
from .models import DomainError, QualityLevel


@dataclass(frozen=True)
class Outlier:
    index: int
    value: float
    deviation: float


@dataclass(frozen=True)
class ObservationStats:
    values: tuple[float, ...]
    count: int
    mean: float
    median: float
    std_dev: float
    standard_error: float
    minimum: float
    maximum: float
    rmse: float
    relative_std: float | None
    target: float | None
    outlier_sigma: float
    outliers: tuple[Outlier, ...]

    @property
    def range_value(self) -> float:
        return self.maximum - self.minimum

    @property
    def has_outliers(self) -> bool:
        return bool(self.outliers)


@dataclass(frozen=True)
class ClosureAssessment:
    closure_mm: float
    allowable_mm: float
    utilization: float | None
    is_within_tolerance: bool
    quality_level: QualityLevel
    ratio_text: str
    correction_rms_mm: float
    max_abs_correction_mm: float


def parse_observation_text(text: str) -> list[float]:
    cleaned = text.strip()
    if not cleaned:
        raise DomainError("请先输入观测值，每行一个或用逗号分隔。")
    tokens = [token for token in re.split(r"[\s,，;；]+", cleaned) if token]
    values: list[float] = []
    for position, token in enumerate(tokens, start=1):
        try:
            value = float(token)
        except ValueError as exc:
            raise DomainError(f"第 {position} 个观测值“{token}”不是有效数字。") from exc
        if not math.isfinite(value):
            raise DomainError(f"第 {position} 个观测值不是有限数字。")
        values.append(value)
    return values


def analyze_observations(
    values: list[float] | tuple[float, ...],
    target: float | None = None,
    outlier_sigma: float = 3.0,
) -> ObservationStats:
    if not values:
        raise DomainError("至少需要一个观测值。")
    if outlier_sigma <= 0:
        raise DomainError("粗差判定倍数必须大于 0。")
    numeric_values = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in numeric_values):
        raise DomainError("观测值必须全部为有限数字。")

    count = len(numeric_values)
    mean = statistics.fmean(numeric_values)
    median = statistics.median(numeric_values)
    std_dev = statistics.stdev(numeric_values) if count > 1 else 0.0
    standard_error = std_dev / math.sqrt(count)
    minimum = min(numeric_values)
    maximum = max(numeric_values)

    if target is not None and not math.isfinite(target):
        raise DomainError("参考值必须是有限数字。")

    reference = target if target is not None else mean
    rmse = math.sqrt(sum((value - reference) ** 2 for value in numeric_values) / count)
    relative_std = abs(std_dev / mean) if abs(mean) > 1e-12 else None

    outliers: list[Outlier] = []
    if std_dev > 0:
        for index, value in enumerate(numeric_values, start=1):
            deviation = value - mean
            if abs(deviation) > outlier_sigma * std_dev + 1e-12:
                outliers.append(Outlier(index=index, value=value, deviation=deviation))

    return ObservationStats(
        values=numeric_values,
        count=count,
        mean=mean,
        median=median,
        std_dev=std_dev,
        standard_error=standard_error,
        minimum=minimum,
        maximum=maximum,
        rmse=rmse,
        relative_std=relative_std,
        target=target,
        outlier_sigma=outlier_sigma,
        outliers=tuple(outliers),
    )


def assess_closure(result: LevelingResult) -> ClosureAssessment:
    return ClosureAssessment(
        closure_mm=result.closure_error_mm,
        allowable_mm=result.allowable_closure_mm,
        utilization=result.closure_utilization,
        is_within_tolerance=result.is_within_tolerance,
        quality_level=result.quality_level,
        ratio_text=result.misclosure_ratio_text,
        correction_rms_mm=result.correction_rms_m * 1000.0,
        max_abs_correction_mm=result.max_abs_correction_m * 1000.0,
    )
