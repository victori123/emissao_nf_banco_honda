import csv
import json
import shutil
from pathlib import Path
from typing import Any

def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def load_csv(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def move_pending_files_to_output_dir(source_dir: Path, output_dir: Path, pending_folder_name: str = "nao_processado") -> list[Path]:
    pending_dir = output_dir / pending_folder_name
    pending_dir.mkdir(parents=True, exist_ok=True)

    moved_files: list[Path] = []
    for file_path in sorted(source_dir.glob("*")):
        if not file_path.is_file():
            continue

        target_path = pending_dir / file_path.name
        if target_path.exists():
            target_path.unlink()

        shutil.move(str(file_path), str(target_path))
        moved_files.append(target_path)

    return moved_files
