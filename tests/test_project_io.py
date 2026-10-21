from __future__ import annotations

import json
from pathlib import Path

import pytest

from surveying.domain.models import DomainError, RouteType
from surveying.services.project_io import ProjectSession, ProjectStorage
from surveying.services.samples import create_sample_project


def test_project_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "project.json"
    session = ProjectSession(
        project=create_sample_project(),
        observation_values=[1.5234, 1.5238, 1.5240],
        observation_target=1.5238,
    )

    ProjectStorage.save(path, session)
    loaded = ProjectStorage.load(path)

    assert loaded.project.name == session.project.name
    assert loaded.project.route_type is RouteType.CLOSED
    assert len(loaded.project.segments) == 5
    assert loaded.project.segments[0].distance_m == pytest.approx(320.0)
    assert loaded.observation_values == pytest.approx([1.5234, 1.5238, 1.5240])
    assert loaded.observation_target == pytest.approx(1.5238)


def test_load_rejects_foreign_file(tmp_path: Path) -> None:
    path = tmp_path / "other.json"
    path.write_text(json.dumps({"format": "other"}), encoding="utf-8")

    with pytest.raises(DomainError, match="不是本软件"):
        ProjectStorage.load(path)


def test_save_reports_bad_directory(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")

    with pytest.raises(DomainError, match="保存工程失败"):
        ProjectStorage.save(blocker / "project.json", ProjectSession(create_sample_project()))
