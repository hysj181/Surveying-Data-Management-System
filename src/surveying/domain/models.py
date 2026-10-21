from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class DomainError(ValueError):
    pass


class RouteType(str, Enum):
    CLOSED = "闭合"
    ATTACHED = "附合"

    @property
    def label(self) -> str:
        return f"{self.value}水准路线"

    @classmethod
    def from_value(cls, value: str) -> "RouteType":
        for item in cls:
            if value in (item.value, item.label):
                return item
        raise DomainError(f"未知的路线类型：{value}")


class LevelingGrade(str, Enum):
    THIRD = "三等"
    FOURTH = "四等"
    ROOT = "图根"

    @property
    def coefficient_mm_per_sqrt_km(self) -> float:
        return {
            LevelingGrade.THIRD: 12.0,
            LevelingGrade.FOURTH: 20.0,
            LevelingGrade.ROOT: 40.0,
        }[self]

    @classmethod
    def from_value(cls, value: str) -> "LevelingGrade":
        for item in cls:
            if item.value == value:
                return item
        raise DomainError(f"未知的等级：{value}")


class QualityLevel(str, Enum):
    EXCELLENT = "优"
    GOOD = "良"
    PASS = "合格"
    FAILED = "超限"


@dataclass
class LevelingSegment:
    from_point: str
    to_point: str
    distance_m: float
    observed_difference_m: float
    remark: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_point": self.from_point,
            "to_point": self.to_point,
            "distance_m": self.distance_m,
            "observed_difference_m": self.observed_difference_m,
            "remark": self.remark,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LevelingSegment":
        return cls(
            from_point=str(data.get("from_point", "")),
            to_point=str(data.get("to_point", "")),
            distance_m=float(data["distance_m"]),
            observed_difference_m=float(data["observed_difference_m"]),
            remark=str(data.get("remark", "")),
        )


@dataclass
class LevelingProject:
    name: str = "新建水准工程"
    route_type: RouteType = RouteType.CLOSED
    grade: LevelingGrade = LevelingGrade.FOURTH
    observer: str = ""
    survey_date: str = field(default_factory=lambda: date.today().isoformat())
    start_point: str = "BM-A"
    start_elevation_m: float = 100.0
    end_point: str = "BM-A"
    end_elevation_m: float = 100.0
    notes: str = ""
    segments: list[LevelingSegment] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "route_type": self.route_type.value,
            "grade": self.grade.value,
            "observer": self.observer,
            "survey_date": self.survey_date,
            "start_point": self.start_point,
            "start_elevation_m": self.start_elevation_m,
            "end_point": self.end_point,
            "end_elevation_m": self.end_elevation_m,
            "notes": self.notes,
            "segments": [segment.to_dict() for segment in self.segments],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LevelingProject":
        segments = [
            LevelingSegment.from_dict(item) for item in data.get("segments", [])
        ]
        return cls(
            name=str(data.get("name", "新建水准工程")),
            route_type=RouteType.from_value(str(data.get("route_type", RouteType.CLOSED.value))),
            grade=LevelingGrade.from_value(str(data.get("grade", LevelingGrade.FOURTH.value))),
            observer=str(data.get("observer", "")),
            survey_date=str(data.get("survey_date", date.today().isoformat())),
            start_point=str(data.get("start_point", "BM-A")),
            start_elevation_m=float(data.get("start_elevation_m", 100.0)),
            end_point=str(data.get("end_point", "BM-A")),
            end_elevation_m=float(data.get("end_elevation_m", 100.0)),
            notes=str(data.get("notes", "")),
            segments=segments,
        )
