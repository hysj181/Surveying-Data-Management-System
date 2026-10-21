from __future__ import annotations

import math

import pytest

from surveying.domain.leveling import calculate_leveling
from surveying.domain.models import DomainError, LevelingGrade, LevelingProject, LevelingSegment, RouteType
from surveying.services.samples import create_sample_project


def test_closed_leveling_adjustment() -> None:
    result = calculate_leveling(create_sample_project())

    assert result.route_type is RouteType.CLOSED
    assert result.total_distance_m == pytest.approx(1520.0)
    assert result.closure_error_m == pytest.approx(-0.008)
    assert result.allowable_closure_m == pytest.approx(0.020 * math.sqrt(1.52))
    assert result.is_within_tolerance
    assert result.correction_sum_m == pytest.approx(0.008)
    assert result.computed_end_elevation_m == pytest.approx(50.0, abs=1e-9)
    assert result.target_end_elevation_m == pytest.approx(50.0)
    assert result.quality_level.value == "优"
    assert len(result.segments) == 5
    assert sum(item.correction_m for item in result.segments) == pytest.approx(0.008)
    assert result.segments[0].correction_mm == pytest.approx(1.684, abs=0.001)
    assert result.misclosure_ratio == pytest.approx(1520.0 / 0.008)


def test_attached_leveling_adjustment() -> None:
    project = LevelingProject(
        name="附合路线",
        route_type=RouteType.ATTACHED,
        grade=LevelingGrade.THIRD,
        start_point="BM-A",
        start_elevation_m=100.0,
        end_point="BM-B",
        end_elevation_m=102.0,
        segments=[
            LevelingSegment("BM-A", "TP1", 500.0, 1.000),
            LevelingSegment("TP1", "BM-B", 500.0, 0.998),
        ],
    )

    result = calculate_leveling(project)

    assert result.closure_error_m == pytest.approx(-0.002)
    assert result.allowable_closure_m == pytest.approx(0.012 * math.sqrt(1.0))
    assert result.correction_sum_m == pytest.approx(0.002)
    assert result.computed_end_elevation_m == pytest.approx(102.0, abs=1e-9)
    assert result.segments[0].correction_m == pytest.approx(0.001)
    assert result.segments[1].correction_m == pytest.approx(0.001)


def test_closure_out_of_tolerance() -> None:
    project = LevelingProject(
        start_point="A",
        start_elevation_m=10.0,
        segments=[LevelingSegment("A", "A", 100.0, 0.100)],
    )

    result = calculate_leveling(project)

    assert not result.is_within_tolerance
    assert result.quality_level.value == "超限"
    assert any("超过容许值" in warning for warning in result.warnings)


def test_invalid_projects_raise_domain_error() -> None:
    with pytest.raises(DomainError, match="至少添加一个测段"):
        calculate_leveling(LevelingProject(segments=[]))

    with pytest.raises(DomainError, match="距离必须大于 0"):
        calculate_leveling(
            LevelingProject(segments=[LevelingSegment("A", "B", 0.0, 1.0)])
        )

    with pytest.raises(DomainError, match="起点名称"):
        calculate_leveling(
            LevelingProject(start_point="", segments=[LevelingSegment("A", "B", 100.0, 1.0)])
        )


def test_discontinuous_route_adds_warning() -> None:
    project = LevelingProject(
        segments=[
            LevelingSegment("A", "B", 100.0, 0.1),
            LevelingSegment("C", "D", 100.0, 0.1),
        ]
    )

    result = calculate_leveling(project)

    assert any("不连续" in warning for warning in result.warnings)
