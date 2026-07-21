from pathlib import Path

from src.shared.utils.file_handler import load_csv, move_pending_files_to_output_dir, save_csv


def test_move_pending_files_to_output_dir_creates_pending_subfolder(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    pending_file = input_dir / "pending.csv"
    pending_file.write_text("coluna\nvalor\n", encoding="utf-8")

    moved_files = move_pending_files_to_output_dir(input_dir, output_dir, pending_folder_name="nao_processado")

    assert len(moved_files) == 1
    assert (output_dir / "nao_processado" / pending_file.name).exists()
    assert not pending_file.exists()


def test_save_csv_accepts_fields_added_after_first_row(tmp_path: Path):
    csv_path = tmp_path / "resultado.csv"
    rows = [
        {"veiculo_chassi": "111", "cliente": "A"},
        {
            "veiculo_chassi": "222",
            "cliente": "B",
            "nbs_data_emissao": "2026-07-21",
            "nbs_confirmation_message": "NF emitida",
        },
    ]

    save_csv(rows, csv_path)
    loaded_rows = load_csv(csv_path)

    assert len(loaded_rows) == 2
    assert loaded_rows[1]["nbs_data_emissao"] == "2026-07-21"
    assert loaded_rows[1]["nbs_confirmation_message"] == "NF emitida"
