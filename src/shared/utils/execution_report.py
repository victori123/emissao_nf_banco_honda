import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import REPORT_DIR

REPORT_COLUMNS = [
    "data_execucao",
    "hora_inicio",
    "hora_ultimo_evento",
    "bot",
    "arquivo_processado",
    "etapa_atual",
    "status",
    "quantidade_processada",
    "quantidade_nao_processada",
    "mensagem",
    "arquivo_log",
]

CHASSIS_REPORT_COLUMNS = [
    "chassi",
    "data",
    "status",
    "observacao",
]


def get_execution_report_path(report_path: str | Path | None = None) -> Path:
    if report_path is not None:
        path = Path(report_path)
    else:
        path = REPORT_DIR / "execution_report.csv"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_execution_report(report_row: dict[str, Any], report_path: str | Path | None = None) -> Path:
    path = get_execution_report_path(report_path)
    normalized_row = {
        "data_execucao": (report_row.get("data_execucao") or datetime.now().strftime("%Y-%m-%d")),
        "hora_inicio": report_row.get("hora_inicio") or "",
        "hora_ultimo_evento": report_row.get("hora_ultimo_evento") or datetime.now().strftime("%H:%M:%S"),
        "bot": report_row.get("bot") or "",
        "arquivo_processado": report_row.get("arquivo_processado") or "",
        "etapa_atual": report_row.get("etapa_atual") or "",
        "status": report_row.get("status") or "",
        "quantidade_processada": report_row.get("quantidade_processada") or 0,
        "quantidade_nao_processada": report_row.get("quantidade_nao_processada") or 0,
        "mensagem": report_row.get("mensagem") or "",
        "arquivo_log": report_row.get("arquivo_log") or f"{datetime.now():%Y-%m-%d}.log",
    }

    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(normalized_row)

    return path


def get_chassis_report_path(report_path: str | Path | None = None) -> Path:
    if report_path is not None:
        path = Path(report_path)
    else:
        path = REPORT_DIR / "chassis_processing_report.csv"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_chassis_report_row(report_row: dict[str, Any]) -> dict[str, str]:
    return {
        "chassi": str(report_row.get("chassi") or "").strip(),
        "data": str(report_row.get("data") or datetime.now().strftime("%Y-%m-%d")).strip(),
        "status": str(report_row.get("status") or "").strip(),
        "observacao": str(report_row.get("observacao") or "").strip(),
    }


def upsert_chassis_processing_report(report_row: dict[str, Any], report_path: str | Path | None = None) -> Path:
    path = get_chassis_report_path(report_path)
    normalized_row = _normalize_chassis_report_row(report_row)

    chassi = normalized_row["chassi"]
    if not chassi:
        return path

    existing_rows: list[dict[str, str]] = []
    if path.exists():
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(
                    {
                        "chassi": (row.get("chassi") or "").strip(),
                        "data": (row.get("data") or "").strip(),
                        "status": (row.get("status") or "").strip(),
                        "observacao": (row.get("observacao") or "").strip(),
                    }
                )

    updated = False
    for index, row in enumerate(existing_rows):
        if (row.get("chassi") or "").strip() == chassi:
            existing_rows[index] = normalized_row
            updated = True
            break

    if not updated:
        existing_rows.append(normalized_row)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHASSIS_REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(existing_rows)

    return path
