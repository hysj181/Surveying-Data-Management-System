from __future__ import annotations

from datetime import date

from surveying.domain.models import LevelingGrade, LevelingProject, LevelingSegment, RouteType


def create_sample_project() -> LevelingProject:
    return LevelingProject(
        name="滨河路四等水准测量",
        route_type=RouteType.CLOSED,
        grade=LevelingGrade.FOURTH,
        observer="张工",
        survey_date=date.today().isoformat(),
        start_point="BM-A",
        start_elevation_m=50.000,
        end_point="BM-A",
        end_elevation_m=50.000,
        notes="闭合环示例数据，闭合差 -8.0 mm。",
        segments=[
            LevelingSegment("BM-A", "TP1", 320.0, 1.524),
            LevelingSegment("TP1", "TP2", 280.0, -2.386),
            LevelingSegment("TP2", "TP3", 360.0, 0.842),
            LevelingSegment("TP3", "TP4", 300.0, -1.467),
            LevelingSegment("TP4", "BM-A", 260.0, 1.479),
        ],
    )


def sample_observation_text() -> str:
    return "\n".join(
        [
            "1.5234",
            "1.5241",
            "1.5238",
            "1.5236",
            "1.5240",
            "1.5239",
            "1.5235",
            "1.5242",
            "1.5237",
            "1.5238",
        ]
    )


def sample_observation_target() -> float:
    return 1.5238
