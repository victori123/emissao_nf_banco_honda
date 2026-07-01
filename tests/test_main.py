from pathlib import Path

from main import build_parser
from src.crm.flows.attach_nfs_flow import get_attachment_rows, update_attachment_result
from src.logistics.flows.main_flow import NBSMainFlow
from src.shared.utils.file_handler import save_csv


def test_build_parser_accepts_crm_attach():
    parser = build_parser()
    args = parser.parse_args(["--bot", "crm-attach"])

    assert args.bot == "crm-attach"


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
    input_file.write_text("veiculo_chassi\n123456\n", encoding="utf-8")

    called = {}

    def fake_execute_nf_emission(*args, **kwargs):
        called["nf_emission"] = True
        return "ok"

    def fake_execute_renave(*args, **kwargs):
        called["renave"] = True
        return "ok"

    def fake_execute_print(*args, **kwargs):
        called["print"] = True
        return "ok"

    def fake_execute_search(*args, **kwargs):
        raise Exception("Chassi não encontrado")

    monkeypatch.setattr("src.logistics.flows.main_flow.DATA_INPUT_DIR", input_dir)
    monkeypatch.setattr("src.logistics.flows.main_flow.DATA_OUTPUT_DIR", output_dir)
    monkeypatch.setattr(flow, "_execute_and_record_flow", lambda row, flow_name, callable_fn, chassis, logger_msg: called.setdefault(flow_name, True) or callable_fn())
    monkeypatch.setattr("src.logistics.flows.main_flow.ChassisSearchFlow", lambda window: type("FakeSearchFlow", (), {"execute": fake_execute_search, "close_propostas_window": lambda self: None})())
    monkeypatch.setattr("src.logistics.flows.main_flow.RenaveEmissionFlow", lambda window: type("FakeRenaveFlow", (), {"execute": fake_execute_renave})())
    monkeypatch.setattr("src.logistics.flows.main_flow.PrintNFFlow", lambda: type("FakePrintFlow", (), {"execute": fake_execute_print})())
    monkeypatch.setattr("src.logistics.flows.main_flow.NFEmissionFlow", lambda window: type("FakeNfFlow", (), {"execute": fake_execute_nf_emission})())

    flow._process_csv_file(input_file, window=None)

    assert called.get("renave") is True
    assert called.get("print") is True
    assert called.get("nf_emission") is None
