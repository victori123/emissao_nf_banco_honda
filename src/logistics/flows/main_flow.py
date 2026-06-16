from datetime import datetime
from pathlib import Path

from src.logistics.components.nbs_session import NBSSession
from src.logistics.flows.login_flow import LoginFlow
from src.logistics.flows.chassis_search_flow import ChassisSearchFlow
from src.logistics.flows.nf_emission_flow import NFEmissionFlow
from src.shared.utils.file_handler import load_csv, save_csv
from src.shared.utils.logger import get_logger
from config.settings import LOGISTICS_BASE_URL, DATA_INPUT_DIR, DATA_OUTPUT_DIR

from pywinauto import Desktop, Application
logger = get_logger(__name__)


class NBSMainFlow:
    def __init__(self, app_path=LOGISTICS_BASE_URL):
        self.session = NBSSession(app_path)

    def run(self, user, password, server):
        window = self.session.start()

        LoginFlow(window).execute(user, password, server)
        self._process_input_files(window)

    def _process_input_files(self, window):
        input_files = sorted(DATA_INPUT_DIR.glob("*.csv"))
        if not input_files:
            logger.info("Nenhum arquivo CSV encontrado em input. Nada a processar.")
            return

        for input_file in input_files:
            self._process_csv_file(input_file, window)

    def _process_csv_file(self, input_file: Path, window):
        logger.info(f"Processando arquivo de input: {input_file.name}")

        rows = load_csv(input_file)
        if not rows:
            logger.warning(f"Arquivo {input_file.name} está vazio. Movendo para output sem processamento.")
            self._move_file_to_output(input_file)
            return

        updated_rows = []
        for row in rows:
            chassis = (row.get("veiculo_chassi") or "").strip()
            ficha_observacao = (row.get("ficha_observacao") or "").strip()
            row["logistics_processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not chassis:
                logger.warning(f"Linha sem chassis encontrada em {input_file.name}. Pulando.")
                row["logistics_status"] = "missing_chassis"
                row["logistics_error"] = "Chassi não encontrado na linha"
                updated_rows.append(row)
                continue

            try:
                search_result = ChassisSearchFlow(window).execute(chassis)
                nova_handle = next((w.handle for w in Desktop(backend="win32").windows() if "Propostas" in w.window_text()), None)
                app = Application(backend="uia").connect(handle=nova_handle)
                window = app.window(handle=nova_handle)
                NFEmissionFlow(window).execute(ficha_observacao)

                row["logistics_status"] = "success"
                row["logistics_error"] = ""
                if isinstance(search_result, dict):
                    for key, value in search_result.items():
                        row[f"logistics_{key}"] = value

                logger.info(f"Chassis {chassis} processado com sucesso.")

            except Exception as exc:
                row["logistics_status"] = "failed"
                row["logistics_error"] = str(exc)[:512]
                logger.error(f"Erro ao processar chassis {chassis}: {exc}", exc_info=True)

            updated_rows.append(row)

        output_file = DATA_OUTPUT_DIR / input_file.name
        if output_file.exists():
            output_file = DATA_OUTPUT_DIR / f"{output_file.stem}_{datetime.now():%Y%m%d_%H%M%S}{output_file.suffix}"

        save_csv(updated_rows, output_file)
        logger.info(f"Arquivo atualizado salvo em {output_file}")

        input_file.unlink()
        logger.info(f"Arquivo movido para output: {output_file.name}")

    def _move_file_to_output(self, input_file: Path):
        output_file = DATA_OUTPUT_DIR / input_file.name
        if output_file.exists():
            output_file = DATA_OUTPUT_DIR / f"{output_file.stem}_{datetime.now():%Y%m%d_%H%M%S}{output_file.suffix}"
        input_file.replace(output_file)
        logger.info(f"Arquivo vazio movido para output: {output_file.name}")
