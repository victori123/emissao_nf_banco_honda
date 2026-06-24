from pathlib import Path

from main import build_parser
from src.crm.flows.attach_nfs_flow import get_attachment_rows, update_attachment_result
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
