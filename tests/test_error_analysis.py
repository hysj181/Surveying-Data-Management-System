from __future__ import annotations

import math

import pytest

from surveying.domain.error_analysis import (
    analyze_observations,
    assess_closure,
    parse_observation_text,
)
from surveying.domain.leveling import calculate_leveling
from surveying.domain.models import DomainError
from surveying.services.samples import create_sample_project


def test_observation_statistics() -> None:
    stats = analyze_observations([1.0, 2.0, 3.0, 4.0, 5.0])

    assert stats.count == 5
    assert stats.mean == pytest.approx(3.0)
    assert stats.median == pytest.approx(3.0)
    assert stats.std_dev == pytest.approx(math.sqrt(2.5))
    assert stats.standard_error == pytest.approx(math.sqrt(2.5) / math.sqrt(5))
    assert stats.minimum == pytest.approx(1.0)
    assert stats.maximum == pytest.approx(5.0)
    assert stats.range_value == pytest.approx(4.0)
    assert stats.rmse == pytest.approx(math.sqrt(2.0))
    assert not stats.has_outliers


def test_outlier_detection() -> None:
    values = [10.0000, 10.0002, 9.9998, 10.0001, 9.9999] * 6 + [10.0500]
    stats = analyze_observations(values)

    assert stats.has_outliers
    assert stats.outliers[0].index == 31
    assert stats.outliers[0].value == pytest.approx(10.05)


def test_target_rmse_and_relative_std() -> None:
    stats = analyze_observations([9.8, 10.0, 10.2], target=10.0)

    assert stats.rmse == pytest.approx(math.sqrt((0.04 + 0.0 + 0.04) / 3))
    assert stats.relative_std is not None
    assert stats.target == pytest.approx(10.0)


def test_zero_variance_has_no_outliers() -> None:
    stats = analyze_observations([2.0, 2.0, 2.0])

    assert stats.std_dev == 0.0
    assert not stats.has_outliers


def test_parse_observation_text() -> None:
    values = parse_observation_text("1.2, 1.3，1.4;1.5\n1.6")
    assert values == pytest.approx([1.2, 1.3, 1.4, 1.5, 1.6])

    with pytest.raises(DomainError, match="不是有效数字"):
        parse_observation_text("1.2\nabc")
    with pytest.raises(DomainError, match="请先输入"):
        parse_observation_text("  ")


def test_closure_assessment() -> None:
    result = calculate_leveling(create_sample_project())
    assessment = assess_closure(result)

    assert assessment.closure_mm == pytest.approx(-8.0)
    assert assessment.allowable_mm == pytest.approx(20.0 * math.sqrt(1.52))
    assert assessment.is_within_tolerance
    assert assessment.quality_level.value == "优"
    assert assessment.ratio_text.startswith("1/")
