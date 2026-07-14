import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import LOGS_DIR

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


def get_execution_report_path(report_path: str | Path | None = None) -> Path:
    if report_path is not None:
        path = Path(report_path)
    else:
        path = LOGS_DIR / "execution_report.csv"

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
