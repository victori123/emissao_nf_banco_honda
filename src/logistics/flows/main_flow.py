from datetime import datetime
from pathlib import Path
import os
from src.logistics.components.nbs_session import NBSSession
from src.logistics.flows.login_flow import LoginFlow
from src.logistics.flows.chassis_search_flow import ChassisSearchFlow
from src.logistics.flows.nf_emission_flow import NFEmissionFlow
from src.logistics.flows.renave_emission_flow import RenaveEmissionFlow
from src.logistics.flows.print_nf_flow import PrintNFFlow
from src.shared.utils.file_handler import load_csv, save_csv
from src.shared.utils.logger import get_logger
from config.settings import LOGISTICS_BASE_SERVER, DATA_INPUT_DIR, DATA_OUTPUT_DIR

from pywinauto import Desktop, Application
logger = get_logger(__name__)


class NBSMainFlow:
    # Indicadores de erro para heurística de status
    ERRO_INDICADORES = (
        "erro",
        "falha",
        "falhou",
        "não",
        "nao",
        "cancelado",
        "não autorizado",
        "nao autorizado",
    )

    def __init__(self, app_path=LOGISTICS_BASE_SERVER):
        self.session = NBSSession(app_path)

    def run(self, user, password, server):
        # keep credentials for flows that run per-row (ex: impressão em outro servidor)
        self.user = user
        self.password = password
        self.server = server

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
            ficha_codigo_cfop = (row.get("ficha_codigo_cfop") or "").strip()
            observacao_nbs = (row.get("observacao_nbs") or "").strip()
            complemento_nbs = (row.get("complemento_nbs") or "").strip()
            veiculo_seminovo = (row.get("veiculo_siminovo") or "").strip()
            file_name = (row.get("cliente") or "").strip() + ".pdf"
            download_path = os.path.join(DATA_OUTPUT_DIR, file_name)
            row["nbs_processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not chassis:
                logger.warning(f"Linha sem chassis encontrada em {input_file.name}. Pulando.")
                row["nbs_status"] = "missing_chassis"
                row["nbs_error"] = "Chassi não encontrado na linha"
                updated_rows.append(row)
                continue

            nf_main_page = ChassisSearchFlow(window)
            renave = RenaveEmissionFlow(window)
            try:
                search_result = nf_main_page.execute(chassis)
                nova_handle = next((w.handle for w in Desktop(backend="win32").windows() if "Propostas" in w.window_text()), None)
                app = Application(backend="uia").connect(handle=nova_handle)
                window = app.window(handle=nova_handle)
                confirmacao_mensagem = NFEmissionFlow(window).execute(
                    ficha_observacao, 
                    ficha_codigo_cfop, 
                    observacao_nbs, 
                    complemento_nbs,
                    veiculo_seminovo)

                row["nbs_status"] = "success"
                row["nbs_error"] = ""
                if confirmacao_mensagem:
                    row["nbs_confirmation_message"] = confirmacao_mensagem
                if isinstance(search_result, dict):
                    for key, value in search_result.items():
                        row[f"nbs_{key}"] = value

                logger.info(f"Chassis {chassis} processado com sucesso.")
                nf_main_page.close_propostas_window()

                # Executa renave e registra resultado
                self._execute_and_record_flow(
                    row,
                    "renave",
                    lambda: renave.execute(chassis),
                    chassis,
                    "Erro na emissão do Renave"
                )

                # Após execução do renave, iniciar fluxo de impressão da NF (PDF)
                self._execute_and_record_flow(
                    row,
                    "print_nf",
                    lambda: PrintNFFlow().execute(chassis, download_path),
                    chassis,
                    "Falha na impressão da NF"
                )

                if os.path.exists(download_path):
                    row["nbs_attachment_path"] = str(download_path)
                    row["nbs_attachment_file_name"] = os.path.basename(download_path)
                else:
                    row["nbs_attachment_path"] = ""
                    row["nbs_attachment_file_name"] = ""

            except Exception as exc:
                row["nbs_status"] = "failed"
                row["nbs_error"] = str(exc)[:512]
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

    def _execute_and_record_flow(self, row: dict, flow_name: str, callable_fn, chassis: str, logger_msg: str):
        try:
            resultado = callable_fn()
            row[f"nbs_{flow_name}_message"] = resultado or ""
            texto = (resultado or "").lower()
            row[f"nbs_{flow_name}_status"] = "failed" if any(e in texto for e in self.ERRO_INDICADORES) else "success"
        except Exception as exc:
            row[f"nbs_{flow_name}_status"] = "failed"
            row[f"nbs_{flow_name}_message"] = str(exc)[:512]
            logger.warning(f"{logger_msg} para chassis {chassis}: {exc}")
