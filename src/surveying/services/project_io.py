from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from surveying.domain.models import DomainError, LevelingProject


FORMAT_NAME = "surveying-data-manager"
SCHEMA_VERSION = 1


@dataclass
class ProjectSession:
    project: LevelingProject
    observation_values: list[float] = field(default_factory=list)
    observation_target: float | None = None


class ProjectStorage:
    @staticmethod
    def save(path: str | Path, session: ProjectSession) -> None:
        destination = Path(path)
        payload: dict[str, Any] = {
            "format": FORMAT_NAME,
            "schema_version": SCHEMA_VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "project": session.project.to_dict(),
            "observations": session.observation_values,
            "observation_target": session.observation_target,
        }
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise DomainError(f"保存工程失败：{exc}") from exc

    @staticmethod
    def load(path: str | Path) -> ProjectSession:
        source = Path(path)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except OSError as exc:
            raise DomainError(f"打开工程失败：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise DomainError(f"工程文件格式错误：第 {exc.lineno} 行无法解析。") from exc

        if not isinstance(payload, dict) or payload.get("format") != FORMAT_NAME:
            raise DomainError("所选文件不是本软件的工程文件。")
        version = payload.get("schema_version")
        if version != SCHEMA_VERSION:
            raise DomainError(f"不支持的工程文件版本：{version}")

        try:
            project = LevelingProject.from_dict(payload["project"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainError(f"工程数据不完整或不合法：{exc}") from exc

        raw_values = payload.get("observations", [])
        if not isinstance(raw_values, list):
            raise DomainError("工程文件中的观测数据格式不正确。")
        try:
            observation_values = [float(value) for value in raw_values]
        except (TypeError, ValueError) as exc:
            raise DomainError("工程文件中的观测数据包含非法数字。") from exc
        if any(not math.isfinite(value) for value in observation_values):
            raise DomainError("工程文件中的观测数据包含无效数字。")

        target_raw = payload.get("observation_target")
        if target_raw is None:
            observation_target = None
        else:
            try:
                observation_target = float(target_raw)
            except (TypeError, ValueError) as exc:
                raise DomainError("工程文件中的参考值格式不正确。") from exc
            if not math.isfinite(observation_target):
                raise DomainError("工程文件中的参考值无效。")

        return ProjectSession(
            project=project,
            observation_values=observation_values,
            observation_target=observation_target,
        )
