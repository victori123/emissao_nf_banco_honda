from pathlib import Path

from src.shared.utils.file_handler import move_pending_files_to_output_dir


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
