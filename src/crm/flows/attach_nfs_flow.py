from datetime import datetime
from pathlib import Path
import shutil
from typing import Optional

from src.crm.pages.login_page import LoginPage
from src.crm.pages.main_page import MainPage
from src.crm.pages.crm_auto_page import CrmAutoPage
from src.shared.utils.file_handler import load_csv, save_csv
from src.shared.utils.logger import get_logger
from src.shared.utils.retry import retry
from src.shared.utils.execution_report import append_execution_report, upsert_chassis_processing_report
from config.credentials import CRMCredentials
from config.settings import DATA_INPUT_DIR, DATA_OUTPUT_DIR

logger = get_logger(__name__)
PROCESSED_PDF_DIR = DATA_OUTPUT_DIR / "processado"
PROCESSED_CSV_DIR = DATA_OUTPUT_DIR / "processado"


def get_attachment_rows(csv_path: Path) -> list[dict]:
    rows = load_csv(csv_path)
    return [row for row in rows if (row.get("nbs_attachment_path") or row.get("attachment_path"))]


def is_attachment_success(row: dict) -> bool:
    return str(row.get("crm_attachment_status") or "").strip().lower() == "success"


def get_pending_attachment_rows(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if (row.get("nbs_attachment_path") or row.get("attachment_path")) and not is_attachment_success(row)
    ]


def all_attachment_rows_succeeded(rows: list[dict]) -> bool:
    attachment_rows = [row for row in rows if (row.get("nbs_attachment_path") or row.get("attachment_path"))]
    return bool(attachment_rows) and all(is_attachment_success(row) for row in attachment_rows)


def update_attachment_result(row: dict, status: str, error: str = "") -> None:
    row["crm_attachment_status"] = status
    row["crm_attachment_error"] = error
    row["crm_attachment_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def find_attachment_csvs() -> list[Path]:
    candidates = []
    for base_dir in (DATA_OUTPUT_DIR, DATA_INPUT_DIR):
        for csv_path in sorted(base_dir.glob("*.csv")):
            rows = get_attachment_rows(csv_path)
            if rows:
                candidates.append(csv_path)
    return candidates

def execution_report_row(input_file: Optional[str], total_rows: int, failed_rows: int, message: Optional[str] = None) -> dict:
    return {
        "data_execucao": datetime.now().strftime("%Y-%m-%d"),
        "hora_inicio": datetime.now().strftime("%H:%M:%S"),
        "hora_ultimo_evento": datetime.now().strftime("%H:%M:%S"),
        "bot": "crm-attach",
        "arquivo_processado": input_file if input_file else "N/A",
        "etapa_atual": "attach_nfs",
        "status": "SUCESSO" if failed_rows == 0 else "ERRO",
        "quantidade_processada": total_rows - failed_rows,
        "quantidade_nao_processada": failed_rows,
        "mensagem": message or ("Anexação concluída" if failed_rows == 0 else "Alguns anexos falharam"),
        "arquivo_log": f"{datetime.now():%Y-%m-%d}.log",
    }


def move_pdf_to_processed(pdf_file: Path) -> Path:
    PROCESSED_PDF_DIR.mkdir(parents=True, exist_ok=True)
    destination = PROCESSED_PDF_DIR / pdf_file.name

    if destination.exists():
        destination = PROCESSED_PDF_DIR / f"{pdf_file.stem}_{datetime.now():%Y%m%d_%H%M%S}{pdf_file.suffix}"

    shutil.move(str(pdf_file), str(destination))
    return destination


def move_csv_to_processed(csv_file: Path) -> Path:
    PROCESSED_CSV_DIR.mkdir(parents=True, exist_ok=True)
    destination = PROCESSED_CSV_DIR / csv_file.name

    if destination.exists():
        destination = PROCESSED_CSV_DIR / f"{csv_file.stem}_{datetime.now():%Y%m%d_%H%M%S}{csv_file.suffix}"

    shutil.move(str(csv_file), str(destination))
    return destination


def _upsert_attachment_chassis_status(chassi: str, status: str, observacao: str) -> None:
    normalized_chassi = str(chassi or "").strip()
    if not normalized_chassi:
        return

    upsert_chassis_processing_report(
        {
            "chassi": normalized_chassi,
            "data": datetime.now().strftime("%Y-%m-%d"),
            "status": status,
            "observacao": observacao,
        }
    )

@retry()
def run(driver) -> list[str]:
    logger.info("=== START: attach_nfs_flow ===")

    attached_files: list[str] = []
    total_rows = 0
    failed_rows = 0

    attachment_csvs = find_attachment_csvs()
    if not attachment_csvs:
        logger.warning("Nenhum CSV com nbs_attachment_path encontrado para anexar ao CRM.")
        append_execution_report(execution_report_row(None, 0, 0, "Nenhum CSV com nbs_attachment_path encontrado"))
        return []

    csv_contexts: list[tuple[Path, list[dict], list[dict]]] = []
    for csv_path in attachment_csvs:
        all_rows = load_csv(csv_path)
        pending_rows = get_pending_attachment_rows(all_rows)
        csv_contexts.append((csv_path, all_rows, pending_rows))

    pending_total = sum(len(pending_rows) for _, _, pending_rows in csv_contexts)
    if pending_total == 0:
        moved_csvs: list[str] = []
        for csv_path, all_rows, _ in csv_contexts:
            if all_attachment_rows_succeeded(all_rows):
                moved_path = move_csv_to_processed(csv_path)
                moved_csvs.append(moved_path.name)
                logger.info("CSV sem pendencias movido para processados: %s", moved_path)

        message = (
            "Sem anexos pendentes; CSVs movidos para processados"
            if moved_csvs
            else "Sem anexos pendentes para envio"
        )
        append_execution_report(execution_report_row(", ".join(sorted(csv_path.name for csv_path in attachment_csvs)), 0, 0, message))
        logger.info("=== END: attach_nfs_flow ===")
        return []

    LoginPage(driver).open().login(CRMCredentials.USERNAME, CRMCredentials.PASSWORD)

    main_page = MainPage(driver)
    assert main_page.is_loaded(), "Main page did not load after login"
    main_page.go_to_crm_autos()

    crm_auto_page = CrmAutoPage(driver)
    assert crm_auto_page.is_loaded(), "Crm Auto page did not load"
    crm_auto_page.go_to_crm_autos()


    for csv_path, all_rows, rows in csv_contexts:
        if not rows:
            if all_attachment_rows_succeeded(all_rows):
                moved_path = move_csv_to_processed(csv_path)
                logger.info("CSV com anexos ja concluidos movido para processados: %s", moved_path)
            continue

        for row in rows:
            total_rows += 1
            pdf_path = row.get("nbs_attachment_path") or row.get("attachment_path")
            chassi = str(row.get("veiculo_chassi") or "")
            numero_evento = str(row.get("numero") or "")
            if not pdf_path:
                _upsert_attachment_chassis_status(chassi, "Erro", "Caminho do PDF nao informado para anexacao")
                continue

            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                update_attachment_result(row, "failed", f"Arquivo não encontrado: {pdf_path}")
                _upsert_attachment_chassis_status(chassi, "Erro", f"Arquivo nao encontrado: {pdf_path}")
                failed_rows += 1
                logger.warning("PDF não encontrado para anexar: %s", pdf_path)
                continue

            logger.info("Anexando PDF ao CRM: %s", pdf_file.name)
            try:
                crm_auto_page.attach_pdf_to_current_opportunity(str(pdf_file), chassi, numero_evento)
                crm_auto_page.close_opened_tabs_after_attachment()
                update_attachment_result(row, "success")
                try:
                    processed_pdf = move_pdf_to_processed(pdf_file)
                    row["nbs_attachment_path"] = str(processed_pdf)
                    logger.info("PDF movido para processado: %s", processed_pdf)
                except Exception as move_exc:
                    row["crm_attachment_error"] = f"Anexo concluido; falha ao mover PDF: {str(move_exc)[:256]}"
                    logger.warning("Falha ao mover PDF %s para processado: %s", pdf_file, move_exc)
                _upsert_attachment_chassis_status(chassi, "Concluido", "Anexo no CRM concluido com sucesso")
                attached_files.append(pdf_file.name)
            except Exception as exc:
                update_attachment_result(row, "failed", str(exc)[:512])
                _upsert_attachment_chassis_status(chassi, "Erro", str(exc)[:512])
                failed_rows += 1
                logger.exception("Falha ao anexar PDF ao CRM: %s", pdf_file.name)

        save_csv(all_rows, csv_path)

        if all_attachment_rows_succeeded(all_rows):
            moved_path = move_csv_to_processed(csv_path)
            logger.info("CSV movido para processados apos concluir anexos: %s", moved_path)

    append_execution_report(execution_report_row(", ".join(sorted(csv_path.name for csv_path in attachment_csvs)), total_rows, failed_rows))

    logger.info("=== END: attach_nfs_flow ===")
    return attached_files
