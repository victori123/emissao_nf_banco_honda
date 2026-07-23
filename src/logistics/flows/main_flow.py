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
from src.shared.utils.execution_report import append_execution_report, upsert_chassis_processing_report
from config.settings import LOGISTICS_BASE_SERVER, DATA_INPUT_DIR, DATA_OUTPUT_DIR, LOGS_DIR

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

        self.window = None 

        self._process_input_files()

    def _process_input_files(self):
        input_files = sorted(DATA_INPUT_DIR.glob("*.csv"))
        if not input_files:
            logger.info("Nenhum arquivo CSV encontrado em input. Nada a processar.")
            self._append_report_row(
                input_file=Path("N/A"),
                etapa_atual="processamento",
                status="SUCESSO",
                quantidade_processada=0,
                quantidade_nao_processada=0,
                mensagem="Sem arquivo para processamento",
            )
            return

        try:
            self.window = self.session.start()
            LoginFlow(self.window).execute(self.user, self.password, self.server)
            for input_file in input_files:
                self._process_csv_file(input_file, self.window)
        finally:
            self._close_nbs_application()

    def _close_nbs_application(self):
        try:
            if self.window is not None:
                self.window.close()
        except Exception as exc:
            logger.warning(f"Falha ao fechar janela principal do NBS: {exc}")

        try:
            app = getattr(getattr(self.session, "driver", None), "app", None)
            if app and app.is_process_running():
                app.kill(soft=False)
        except Exception as exc:
            logger.warning(f"Falha ao encerrar processo do NBS: {exc}")
        finally:
            self.window = None

    @staticmethod
    def _is_missing_or_emitted_nf_error(exc: Exception) -> bool:
        message = str(exc).lower()
        has_chassis_reference = "chassi" in message
        has_missing_terms = (
            "não localizada" in message
            or "nao encontrado" in message
            or "não localizado" in message
            or "nao localizado" in message
            or "já emitida" in message
            or "ja emitida" in message
            or "not found" in message
        )
        return has_chassis_reference and has_missing_terms

    def _process_csv_file(self, input_file: Path, window):
        logger.info(f"Processando arquivo de input: {input_file.name}")

        rows = load_csv(input_file)
        if not rows:
            logger.warning(f"Arquivo {input_file.name} está vazio. Movendo para output sem processamento.")
            self._append_report_row(
                input_file=input_file,
                etapa_atual="processamento",
                status="SUCESSO",
                quantidade_processada=0,
                quantidade_nao_processada=0,
                mensagem="Arquivo vazio; movido para output sem processamento",
            )
            self._move_file_to_output(input_file)
            return

        row_contexts = self._preprocess_rows(rows, input_file)

        self._run_emission_pass(row_contexts, window)
        self._run_postprocessing_pass(row_contexts, window)

        updated_rows = []
        for context in row_contexts:
            row = context["row"]
            self._finalize_row_status(row, context["download_path"])
            self._upsert_chassis_report(row)
            updated_rows.append(row)

        processed_count = sum(1 for row in updated_rows if row.get("nbs_status") == "success")
        skipped_count = len(updated_rows) - processed_count

        output_file = DATA_OUTPUT_DIR / input_file.name
        if output_file.exists():
            output_file = DATA_OUTPUT_DIR / f"{output_file.stem}_{datetime.now():%Y%m%d_%H%M%S}{output_file.suffix}"

        save_csv(updated_rows, output_file)
        logger.info(f"Arquivo atualizado salvo em {output_file}")

        self._append_report_row(
            input_file=input_file,
            etapa_atual="emissao_nf",
            status="SUCESSO" if skipped_count == 0 else "ERRO",
            quantidade_processada=processed_count,
            quantidade_nao_processada=skipped_count,
            mensagem="Execução concluída" if skipped_count == 0 else f"Processamento com {skipped_count} item(ns) não processado(s)",
        )

        input_file.unlink()
        logger.info(f"Arquivo movido para output: {output_file.name}")

    def _preprocess_rows(self, rows: list[dict], input_file: Path) -> list[dict]:
        row_contexts = []

        for row in rows:
            chassis = (row.get("veiculo_chassi") or "").strip()
            ficha_observacao = (row.get("ficha_observacao") or "").strip()
            ficha_codigo_cfop = (row.get("ficha_codigo_cfop") or "").strip()
            observacao_nbs = (row.get("observacao_nbs") or "").strip()
            proposta_nbs = (row.get("proposta_nbs") or "").strip()
            alienacao_nbs = (row.get("alienacao_nbs") or "").strip()
            veiculo_seminovo = (row.get("veiculo_siminovo") or "").strip().lower() == "true"
            novo_renavan = (row.get("renvam_informado") or "").strip()
            file_name = (row.get("cliente") or "").strip() + f"_{chassis[-4:]}.pdf"
            download_path = os.path.join(DATA_OUTPUT_DIR, file_name)
            row["nbs_processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row["nbs_etapa_processamento"] = "aguardando_nf_emissao"

            if not chassis:
                logger.warning(f"Linha sem chassis encontrada em {input_file.name}. Pulando.")
                row["nbs_status"] = "missing_chassis"
                row["nbs_error"] = "Chassi não encontrado na linha"
                row["nbs_etapa_processamento"] = "sem_chassi"
                row_contexts.append({"row": row, "chassis": chassis, "download_path": download_path})
                continue

            row_contexts.append(
                {
                    "row": row,
                    "chassis": chassis,
                    "download_path": download_path,
                    "ficha_observacao": ficha_observacao,
                    "ficha_codigo_cfop": ficha_codigo_cfop,
                    "observacao_nbs": observacao_nbs,
                    "proposta_nbs": proposta_nbs,
                    "alienacao_nbs": alienacao_nbs,
                    "veiculo_seminovo": veiculo_seminovo,
                    "novo_renavan": novo_renavan,
                }
            )

        return row_contexts

    def _run_emission_pass(self, row_contexts: list[dict], window):
        self._process_nf_emission_stage(row_contexts, window)

    def _run_postprocessing_pass(self, row_contexts: list[dict], window):
        self._process_renave_stage(row_contexts, window)
        self._process_print_stage(row_contexts)

    def _process_nf_emission_stage(self, row_contexts: list[dict], window):
        for context in row_contexts:
            row = context["row"]
            chassis = context["chassis"]
            veiculo_seminovo = context["veiculo_seminovo"]

            if not chassis:
                continue

            self._upsert_chassis_report_raw(
                chassis=chassis,
                status="Processando",
                observacao="Iniciado emissão de NF no NBS",
                report_date=self._row_report_date(row),
            )

            row["nbs_etapa_processamento"] = "nf_emissao"
            nf_main_page = ChassisSearchFlow(window)
            try:
                search_result = nf_main_page.execute(chassis, veiculo_seminovo)
                nova_handle = next((w.handle for w in Desktop(backend="win32").windows() if "Propostas" in w.window_text()), None)
                app = Application(backend="uia").connect(handle=nova_handle)
                propostas_window = app.window(handle=nova_handle)
                confirmacao_mensagem = NFEmissionFlow(propostas_window).execute(
                    context["ficha_observacao"],
                    context["ficha_codigo_cfop"],
                    context["observacao_nbs"],
                    context["proposta_nbs"],
                    context["alienacao_nbs"],
                    context["veiculo_seminovo"],
                    context["novo_renavan"],
                )

                row["nbs_nf_emission_status"] = "success"
                row["nbs_nf_emission_message"] = confirmacao_mensagem or ""
                if isinstance(search_result, dict):
                    for key, value in search_result.items():
                        row[f"nbs_{key}"] = value
                if confirmacao_mensagem:
                    row["nbs_confirmation_message"] = confirmacao_mensagem

                logger.info(f"Chassis {chassis} processado na etapa de emissão de NF.")
            except Exception as exc:
                if self._is_missing_or_emitted_nf_error(exc):
                    row["nbs_nf_emission_status"] = "skipped"
                    row["nbs_nf_emission_message"] = "NF já emitida ou chassi não localizado na tela de propostas"
                    logger.info(f"Pulando emissão de NF para chassis {chassis}: {exc}")
                else:
                    row["nbs_nf_emission_status"] = "failed"
                    row["nbs_nf_emission_message"] = str(exc)[:512]
                    logger.error(f"Erro na emissão de NF para chassis {chassis}: {exc}", exc_info=True)
            finally:
                try:
                    nf_main_page.close_propostas_window()
                except Exception:
                    pass

            row["nbs_etapa_processamento"] = "aguardando_renave"

    def _process_renave_stage(self, row_contexts: list[dict], window):
        renave = RenaveEmissionFlow(window)
        renave.page.clicar_renave()
        for context in row_contexts:
            row = context["row"]
            chassis = context["chassis"]

            if not chassis:
                continue

            row["nbs_etapa_processamento"] = "renave"
            try:
                resultado = renave.execute(chassis)
                row["nbs_renave_message"] = resultado or ""
                texto = (resultado or "").lower()
                row["nbs_renave_status"] = "failed" if any(e in texto for e in self.ERRO_INDICADORES) else "success"
            except Exception as exc:
                row["nbs_renave_status"] = "failed"
                row["nbs_renave_message"] = str(exc)[:512]
                logger.warning(f"Erro na emissão do Renave para chassis {chassis}: {exc}")

            row["nbs_etapa_processamento"] = "aguardando_impressao"

        renave.page.close()

    def _process_print_stage(self, row_contexts: list[dict]):
        print_flow = PrintNFFlow()
        for context in row_contexts:
            row = context["row"]
            chassis = context["chassis"]
            download_path = context["download_path"]

            if not chassis:
                continue

            row["nbs_etapa_processamento"] = "print_nf"
            try:
                resultado = print_flow.execute(chassis, download_path)
                row["nbs_print_nf_message"] = resultado or ""
                texto = (resultado or "").lower()
                row["nbs_print_nf_status"] = "failed" if any(e in texto for e in self.ERRO_INDICADORES) else "success"
            except Exception as exc:
                row["nbs_print_nf_status"] = "failed"
                row["nbs_print_nf_message"] = str(exc)[:512]
                logger.warning(f"Falha na impressão da NF para chassis {chassis}: {exc}")

            row["nbs_etapa_processamento"] = "concluido"
            
        try:
            print_flow.close_print_window()
        except Exception:
            pass


    def _finalize_row_status(self, row: dict, download_path: str):
        if row.get("nbs_status") == "missing_chassis":
            row.setdefault("nbs_attachment_path", "")
            row.setdefault("nbs_attachment_file_name", "")
            return

        stage_statuses = [
            row.get("nbs_nf_emission_status"),
            row.get("nbs_renave_status"),
            row.get("nbs_print_nf_status"),
        ]

        if any(status == "failed" for status in stage_statuses):
            row["nbs_status"] = "failed"
            row.setdefault("nbs_error", "")
        elif row.get("nbs_nf_emission_status") == "skipped":
            row["nbs_status"] = "skipped_nf_emission"
            row.setdefault("nbs_error", "")
        else:
            row["nbs_status"] = "success"
            row["nbs_error"] = ""

        if row.get("nbs_print_nf_status") == "success" and os.path.exists(download_path):
            row["nbs_attachment_path"] = str(download_path)
            row["nbs_attachment_file_name"] = os.path.basename(download_path)
        else:
            row.setdefault("nbs_attachment_path", "")
            row.setdefault("nbs_attachment_file_name", "")

    def _move_file_to_output(self, input_file: Path):
        output_file = DATA_OUTPUT_DIR / input_file.name
        if output_file.exists():
            output_file = DATA_OUTPUT_DIR / f"{output_file.stem}_{datetime.now():%Y%m%d_%H%M%S}{output_file.suffix}"
        input_file.replace(output_file)
        logger.info(f"Arquivo vazio movido para output: {output_file.name}")

    def _build_chassis_report_status(self, row: dict) -> str:
        return "Processando" if row.get("nbs_status") == "success" else "Erro"

    def _build_chassis_report_observation(self, row: dict) -> str:
        if row.get("nbs_status") == "success":
            return "Emissão de NF no NBS concluida. Aguardando anexacao no CRM"

        prioritized_messages = [
            row.get("nbs_error"),
            row.get("nbs_nf_emission_message"),
            row.get("nbs_renave_message"),
            row.get("nbs_print_nf_message"),
            row.get("nbs_confirmation_message"),
        ]

        for message in prioritized_messages:
            if message:
                return str(message)[:512]

        return "Erro durante processamento na NBS"

    def _row_report_date(self, row: dict) -> str:
        processed_at = str(row.get("nbs_processed_at") or "")
        return processed_at.split(" ")[0] if processed_at else datetime.now().strftime("%Y-%m-%d")

    def _upsert_chassis_report_raw(self, chassis: str, status: str, observacao: str, report_date: str):
        upsert_chassis_processing_report(
            {
                "chassi": chassis,
                "data": report_date,
                "status": status,
                "observacao": observacao,
            },
            LOGS_DIR / "chassis_processing_report.csv",
        )

    def _upsert_chassis_report(self, row: dict):
        chassi = (row.get("veiculo_chassi") or "").strip()
        if not chassi:
            return

        self._upsert_chassis_report_raw(
            chassis=chassi,
            status=self._build_chassis_report_status(row),
            observacao=self._build_chassis_report_observation(row),
            report_date=self._row_report_date(row),
        )

    def _append_report_row(self, input_file: Path, etapa_atual: str, status: str, quantidade_processada: int, quantidade_nao_processada: int, mensagem: str):
        append_execution_report(
            {
                "data_execucao": datetime.now().strftime("%Y-%m-%d"),
                "hora_inicio": datetime.now().strftime("%H:%M:%S"),
                "hora_ultimo_evento": datetime.now().strftime("%H:%M:%S"),
                "bot": "logistics",
                "arquivo_processado": input_file.name,
                "etapa_atual": etapa_atual,
                "status": status,
                "quantidade_processada": quantidade_processada,
                "quantidade_nao_processada": quantidade_nao_processada,
                "mensagem": mensagem,
                "arquivo_log": f"{datetime.now():%Y-%m-%d}.log",
            },
            LOGS_DIR / "execution_report.csv",
        )

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
            raise
