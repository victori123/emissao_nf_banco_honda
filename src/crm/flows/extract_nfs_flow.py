from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from src.crm.pages.login_page import LoginPage
from src.crm.pages.main_page import MainPage
from src.crm.pages.crm_auto_page import CrmAutoPage
from src.shared.utils.file_handler import move_pending_files_to_output_dir, save_csv
from src.shared.utils.logger import get_logger
from src.shared.utils.retry import retry
from src.shared.utils.execution_report import append_execution_report, upsert_chassis_processing_report
from config.credentials import CRMCredentials
from config.settings import DATA_INPUT_DIR, DATA_OUTPUT_DIR
from datetime import datetime

logger = get_logger(__name__)


def _upsert_pending_chassis(rows: list[dict]) -> None:
    report_date = datetime.now().strftime("%Y-%m-%d")
    for row in rows:
        chassi = str(row.get("veiculo_chassi") or "").strip()
        if not chassi:
            continue

        upsert_chassis_processing_report(
            {
                "chassi": chassi,
                "data": report_date,
                "status": "Pendente",
                "observacao": "Extraido no CRM e aguardando Emissao de NF no NBS",
            }
        )

@retry()
def run(driver: Any) -> list[dict]:
    logger.info("=== START: extract_nfs_flow ===")

    pending_files = move_pending_files_to_output_dir(DATA_INPUT_DIR, DATA_OUTPUT_DIR)
    if pending_files:
        logger.info("Arquivos pendentes movidos para %s: %s", DATA_OUTPUT_DIR / "nao_processado", ", ".join(str(path.name) for path in pending_files))

    # Step 1 – Login
    LoginPage(driver).open().login(CRMCredentials.USERNAME, CRMCredentials.PASSWORD)

    # Step 2 – Confirm main page loaded
    main_page = MainPage(driver)
    assert main_page.is_loaded(), "Main page did not load after login"
    main_page.go_to_crm_autos()

    # Step 3 – Navigate to Gerenciamento Menu
    crm_auto_page = CrmAutoPage(driver)
    assert crm_auto_page.is_loaded(), "Crm Auto page did not load"
    crm_auto_page.go_to_crm_autos()
    crm_auto_page.go_to_funil_vendas()
    crm_auto_page.search()

    all_nfs: list[dict] = []
    
    all_nfs.extend(crm_auto_page.extract_rows())

    logger.info(f"Total NFs collected: {len(all_nfs)}")

    # Step 4 – Persist results
    output_path = DATA_INPUT_DIR / f"crm_nfs_{datetime.now():%Y%m%d_%H%M%S}.csv"
    save_csv(all_nfs, output_path)
    _upsert_pending_chassis(all_nfs)
    append_execution_report(
        {
            "data_execucao": datetime.now().strftime("%Y-%m-%d"),
            "hora_inicio": datetime.now().strftime("%H:%M:%S"),
            "hora_ultimo_evento": datetime.now().strftime("%H:%M:%S"),
            "bot": "crm",
            "arquivo_processado": output_path.name,
            "etapa_atual": "extract_nfs",
            "status": "SUCESSO",
            "quantidade_processada": len(all_nfs),
            "quantidade_nao_processada": 0,
            "mensagem": "Extração concluída",
            "arquivo_log": f"{datetime.now():%Y-%m-%d}.log",
        }
    )
    logger.info(f"Nfs saved to {output_path}")
    logger.info("=== END: extract_nfs_flow ===")

    return all_nfs
