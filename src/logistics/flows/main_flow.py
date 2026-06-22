from datetime import datetime
from pathlib import Path

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
                confirmacao_mensagem = NFEmissionFlow(window).execute(ficha_observacao, ficha_codigo_cfop)

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
                try:
                    renave_msg = renave.execute(chassis)
                    row["nbs_renave_message"] = renave_msg or ""
                    # heurística simples para inferir status a partir da mensagem
                    texto = (renave_msg or "").lower()
                    erro_indicadores = (
                        "erro",
                        "falha",
                        "falhou",
                        "não",
                        "nao",
                        "cancelado",
                        "não autorizado",
                        "nao autorizado",
                    )
                    row["nbs_renave_status"] = "failed" if any(e in texto for e in erro_indicadores) else "success"

                except Exception as exc:
                    row["nbs_renave_status"] = "failed"
                    row["nbs_renave_message"] = str(exc)[:512]
                    logger.warning(f"Erro na emissão do Renave para chassis {chassis}: {exc}")

                # Após execução do renave, iniciar fluxo de impressão da NF (PDF)
                try:
                    print_nf_msg = PrintNFFlow(window).execute(chassis)
                    row["nbs_print_nf_message"] = print_nf_msg or ""
                    # heurística simples para inferir status a partir da mensagem
                    texto = (print_nf_msg or "").lower()
                    erro_indicadores = (
                        "erro",
                        "falha",
                        "falhou",
                        "não",
                        "nao",
                        "cancelado",
                        "não autorizado",
                        "nao autorizado",
                    )
                    row["nbs_print_nf_status"] = "failed" if any(e in texto for e in erro_indicadores) else "success"
                except Exception as exc:
                    row["nbs_print_nf_status"] = "failed"
                    row["nbs_print_nf_message"] = str(exc)[:512]
                    logger.warning(f"Falha na impressão da NF para chassis {chassis}: {exc}")


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
