from pathlib import Path

from src.shared.utils.execution_report import append_execution_report, upsert_chassis_processing_report


def test_append_execution_report_creates_csv_with_expected_columns(tmp_path: Path) -> None:
    report_path = tmp_path / "execution_report.csv"

    row = {
        "data_execucao": "2026-07-14",
        "hora_inicio": "10:00:00",
        "hora_ultimo_evento": "10:05:00",
        "bot": "logistics",
        "arquivo_processado": "crm_nfs_20260714_100000.csv",
        "etapa_atual": "emissao_nf",
        "status": "SUCESSO",
        "quantidade_processada": 15,
        "quantidade_nao_processada": 0,
        "mensagem": "Execução concluída",
        "arquivo_log": "2026-07-14.log",
    }

    append_execution_report(row, report_path)

    assert report_path.exists()
    contents = report_path.read_text(encoding="utf-8")
    assert "data_execucao" in contents
    assert "logistics" in contents
    assert "Execução concluída" in contents


def test_upsert_chassis_processing_report_creates_file(tmp_path: Path) -> None:
    report_path = tmp_path / "chassis_processing_report.csv"

    upsert_chassis_processing_report(
        {
            "chassi": "9BWZZZ377VT004251",
            "data": "2026-07-23",
            "status": "SUCESSO",
            "observacao": "Processado com sucesso",
        },
        report_path,
    )

    assert report_path.exists()
    contents = report_path.read_text(encoding="utf-8")
    assert "chassi,data,status,observacao" in contents
    assert "9BWZZZ377VT004251" in contents
    assert "SUCESSO" in contents


def test_upsert_chassis_processing_report_updates_existing_chassis(tmp_path: Path) -> None:
    report_path = tmp_path / "chassis_processing_report.csv"
    chassi = "9BWZZZ377VT004251"

    upsert_chassis_processing_report(
        {
            "chassi": chassi,
            "data": "2026-07-23",
            "status": "NAO_PROCESSADO",
            "observacao": "Erro inicial",
        },
        report_path,
    )
    upsert_chassis_processing_report(
        {
            "chassi": chassi,
            "data": "2026-07-24",
            "status": "SUCESSO",
            "observacao": "Reprocessado com sucesso",
        },
        report_path,
    )

    lines = report_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert chassi in lines[1]
    assert "2026-07-24" in lines[1]
    assert "SUCESSO" in lines[1]
    assert "Reprocessado com sucesso" in lines[1]
