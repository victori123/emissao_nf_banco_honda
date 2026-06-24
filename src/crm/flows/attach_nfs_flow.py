from datetime import datetime
from pathlib import Path

from src.crm.pages.login_page import LoginPage
from src.crm.pages.main_page import MainPage
from src.crm.pages.crm_auto_page import CrmAutoPage
from src.shared.utils.file_handler import load_csv, save_csv
from src.shared.utils.logger import get_logger
from config.credentials import CRMCredentials
from config.settings import DATA_INPUT_DIR, DATA_OUTPUT_DIR

logger = get_logger(__name__)


def get_attachment_rows(csv_path: Path) -> list[dict]:
    rows = load_csv(csv_path)
    return [row for row in rows if (row.get("nbs_attachment_path") or row.get("attachment_path"))]


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


def run(driver) -> list[str]:
    logger.info("=== START: attach_nfs_flow ===")

    LoginPage(driver).open().login(CRMCredentials.USERNAME, CRMCredentials.PASSWORD)

    main_page = MainPage(driver)
    assert main_page.is_loaded(), "Main page did not load after login"
    main_page.go_to_crm_autos()

    crm_auto_page = CrmAutoPage(driver)
    assert crm_auto_page.is_loaded(), "Crm Auto page did not load"
    crm_auto_page.go_to_crm_autos()
    crm_auto_page.go_to_funil_vendas()
    crm_auto_page.search()

    attachment_csvs = find_attachment_csvs()
    if not attachment_csvs:
        logger.warning("Nenhum CSV com nbs_attachment_path encontrado para anexar ao CRM.")
        return []

    attached_files: list[str] = []

    for csv_path in attachment_csvs:
        rows = get_attachment_rows(csv_path)
        if not rows:
            continue

        for row in rows:
            pdf_path = row.get("nbs_attachment_path") or row.get("attachment_path")
            if not pdf_path:
                continue

            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                update_attachment_result(row, "failed", f"Arquivo não encontrado: {pdf_path}")
                logger.warning("PDF não encontrado para anexar: %s", pdf_path)
                continue

            logger.info("Anexando PDF ao CRM: %s", pdf_file.name)
            try:
                crm_auto_page.attach_pdf_to_current_opportunity(str(pdf_file))
                update_attachment_result(row, "success")
                attached_files.append(pdf_file.name)
            except Exception as exc:
                update_attachment_result(row, "failed", str(exc)[:512])
                logger.exception("Falha ao anexar PDF ao CRM: %s", pdf_file.name)

        save_csv(rows, csv_path)

    logger.info("=== END: attach_nfs_flow ===")
    return attached_files
