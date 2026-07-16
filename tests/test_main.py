import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

pywinauto_module = types.ModuleType("pywinauto")
pywinauto_module.__path__ = []
pywinauto_module.Desktop = MagicMock()
pywinauto_module.Application = MagicMock()
sys.modules.setdefault("pywinauto", pywinauto_module)

pywinauto_keyboard_module = types.ModuleType("pywinauto.keyboard")
pywinauto_keyboard_module.send_keys = MagicMock()
sys.modules.setdefault("pywinauto.keyboard", pywinauto_keyboard_module)

pywinauto_mouse_module = types.ModuleType("pywinauto.mouse")
pywinauto_mouse_module.click = MagicMock()
sys.modules.setdefault("pywinauto.mouse", pywinauto_mouse_module)

from main import build_parser
from src.crm.flows.attach_nfs_flow import get_attachment_rows, update_attachment_result
from src.logistics.flows.main_flow import NBSMainFlow
from src.shared.utils.file_handler import save_csv


def test_build_parser_accepts_crm_attach():
    parser = build_parser()
    args = parser.parse_args(["--bot", "crm-attach"])

    assert args.bot == ["crm-attach"]


def test_attachment_row_is_updated_from_csv(tmp_path: Path):
    csv_path = tmp_path / "processamento.csv"
    save_csv([
        {"cliente": "Acme", "nbs_attachment_path": str(tmp_path / "nf.pdf")}
    ], csv_path)

    rows = get_attachment_rows(csv_path)
    update_attachment_result(rows[0], "success")

    assert rows[0]["crm_attachment_status"] == "success"
    assert rows[0]["crm_attachment_error"] == ""


def test_should_skip_nf_emission_when_chassis_search_fails_with_missing_vehicle(monkeypatch, tmp_path):
    flow = NBSMainFlow.__new__(NBSMainFlow)
    flow.ERRO_INDICADORES = NBSMainFlow.ERRO_INDICADORES

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    input_file = input_dir / "dummy.csv"
    input_file.write_text(
        "veiculo_chassi,cliente,ficha_observacao,ficha_codigo_cfop,observacao_nbs,proposta_nbs,alienacao_nbs,veiculo_siminovo,renvam_informado\n"
        "111,Cliente A,obs,cfop,obsnbs,prop,alienacao,sim,ren1\n"
        "222,Cliente B,obs,cfop,obsnbs,prop,alienacao,sim,ren2\n",
        encoding="utf-8",
    )

    calls = []

    def fake_execute_and_record_flow(row, flow_name, callable_fn, chassis, logger_msg):
        calls.append(f"record:{flow_name}:{chassis}")
        return callable_fn()

    def fake_execute_nf_emission(*args, **kwargs):
        calls.append("nf_emission")
        return "ok"

    def fake_execute_renave(*args, **kwargs):
        calls.append("renave")
        return "ok"

    def fake_execute_print(*args, **kwargs):
        calls.append("print")
        return "ok"

    monkeypatch.setattr("src.logistics.flows.main_flow.DATA_INPUT_DIR", input_dir)
    monkeypatch.setattr("src.logistics.flows.main_flow.DATA_OUTPUT_DIR", output_dir)
    monkeypatch.setattr(
        "src.logistics.flows.main_flow.ChassisSearchFlow",
        lambda window: type(
            "FakeSearchFlow",
            (),
            {
                "execute": lambda self, chassis: calls.append(f"search:{chassis}") or {"chassi": chassis},
                "close_propostas_window": lambda self: None,
            },
        )(),
    )
    monkeypatch.setattr(
        "src.logistics.flows.main_flow.RenaveEmissionFlow",
        lambda window: type(
            "FakeRenaveFlow",
            (),
            {"execute": lambda self, chassis: fake_execute_renave()},
        )(),
    )
    monkeypatch.setattr(
        "src.logistics.flows.main_flow.PrintNFFlow",
        lambda: type(
            "FakePrintFlow",
            (),
            {"execute": lambda self, chassis, download_path: fake_execute_print()},
        )(),
    )
    monkeypatch.setattr(
        "src.logistics.flows.main_flow.NFEmissionFlow",
        lambda window: type(
            "FakeNfFlow",
            (),
            {"execute": lambda self, *args, **kwargs: fake_execute_nf_emission()},
        )(),
    )

    class FakeDesktop:
        def windows(self):
            return [type("FakeWindow", (), {"handle": 1, "window_text": lambda self: "Propostas"})()]

    class FakeApp:
        def window(self, handle):
            return object()

    monkeypatch.setattr("src.logistics.flows.main_flow.Desktop", lambda backend=None: FakeDesktop())
    monkeypatch.setattr("src.logistics.flows.main_flow.Application", type("FakeApplication", (), {"__init__": lambda self, backend=None: None, "connect": lambda self, handle: FakeApp()}))
    monkeypatch.setattr(flow, "_execute_and_record_flow", fake_execute_and_record_flow)

    flow._process_csv_file(input_file, window=None)

    assert calls[:2] == ["search:111", "nf_emission"]
    assert calls[2:4] == ["search:222", "nf_emission"]
    assert calls[4:6] == ["renave", "renave"]
    assert calls[6:8] == ["print", "print"]

    output_files = list(output_dir.glob("dummy.csv"))
    assert output_files
    rows = output_files[0].read_text(encoding="utf-8")
    assert "nbs_etapa_processamento" in rows
