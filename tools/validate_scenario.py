#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telegram_bot.scenario import ACT_RANGES, get_scenes  # noqa: E402


def main() -> int:
    scenes = get_scenes()
    errors = []
    expected_total = sum(end - start + 1 for start, end in ACT_RANGES.values())
    if len(scenes) != expected_total:
        errors.append(f"Expected {expected_total} scenes, got {len(scenes)}")
    for sid, scene in scenes.items():
        if not scene.get("title"):
            errors.append(f"{sid}: missing title")
        if not scene.get("text"):
            errors.append(f"{sid}: missing text")
        for choice in scene.get("choices", []):
            nxt = choice.get("next")
            effects = choice.get("effects", {})
            if nxt and nxt not in scenes:
                errors.append(f"{sid}/{choice.get('id')}: broken next {nxt}")
            if not nxt and not (effects.get("complete_act") or effects.get("complete_game")):
                errors.append(f"{sid}/{choice.get('id')}: terminal choice without completion")
    if errors:
        print("Scenario validation failed:")
        for err in errors[:50]:
            print("-", err)
        if len(errors) > 50:
            print(f"... and {len(errors) - 50} more")
        return 1
    print(f"OK: {len(scenes)} scenes validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
