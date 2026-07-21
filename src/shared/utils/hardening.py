from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timedelta
from pathlib import Path

from config.credentials import CRMCredentials, LogisticsCredentials
from config.settings import (
    BASE_DIR,
    BROWSER,
    DATA_INPUT_DIR,
    DATA_OUTPUT_DIR,
    HEADLESS,
    LOGISTICS_BASE_SERVER,
    LOGISTICS_NFS_SERVER,
    LOGS_DIR,
)


class HardeningError(RuntimeError):
    """Raised when preflight checks fail."""


def _is_windows_interactive_session() -> bool:
    if os.name != "nt":
        return True

    try:
        import ctypes

        user32 = ctypes.windll.user32
        desktop_handle = user32.OpenInputDesktop(0, False, 0x0100)
        if desktop_handle:
            user32.CloseDesktop(desktop_handle)
            return True
    except Exception:
        pass

    session_name = (os.getenv("SESSIONNAME") or "").lower()
    return bool(session_name and not session_name.startswith("service"))


def _ensure_writable_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    probe = path / ".write_probe"
    try:
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
    finally:
        if probe.exists():
            probe.unlink()


def _expand_selected_bots(selected_bots: list[str]) -> set[str]:
    bots = set(selected_bots)
    if "all" in bots:
        bots.update({"crm", "logistics", "crm-attach"})
    return bots


def validate_runtime_requirements(selected_bots: list[str]) -> None:
    bots = _expand_selected_bots(selected_bots)
    errors: list[str] = []

    if BROWSER not in {"chrome", "firefox"}:
        errors.append(f"Valor inválido para BROWSER: '{BROWSER}'. Use 'chrome' ou 'firefox'.")

    if not (BASE_DIR / ".env").exists():
        errors.append(f"Arquivo .env não encontrado em {BASE_DIR}.")

    try:
        _ensure_writable_dir(DATA_INPUT_DIR)
        _ensure_writable_dir(DATA_OUTPUT_DIR)
        _ensure_writable_dir(LOGS_DIR)
    except Exception as exc:
        errors.append(f"Sem permissão de escrita em diretórios de dados/logs: {exc}")

    is_interactive = _is_windows_interactive_session()

    if "crm" in bots or "crm-attach" in bots:
        if not CRMCredentials.USERNAME or not CRMCredentials.PASSWORD:
            errors.append("Credenciais CRM ausentes (CRM_USERNAME/CRM_PASSWORD).")
        if not HEADLESS and not is_interactive:
            errors.append("Fluxo CRM em modo não headless requer sessão interativa ativa.")

    if "logistics" in bots:
        if not LogisticsCredentials.USERNAME or not LogisticsCredentials.PASSWORD:
            errors.append("Credenciais de logística ausentes (LOGISTICS_USERNAME/LOGISTICS_PASSWORD).")
        if not LogisticsCredentials.SERVER:
            errors.append("Variável LOGISTICS_SERVER ausente.")
        if not LogisticsCredentials.NFS_SERVER:
            errors.append("Variável LOGISTICS_NFS_SERVER ausente.")

        if not Path(LOGISTICS_BASE_SERVER).exists():
            errors.append(f"Caminho LOGISTICS_BASE_SERVER não encontrado: {LOGISTICS_BASE_SERVER}")
        if not Path(LOGISTICS_NFS_SERVER).exists():
            errors.append(f"Caminho LOGISTICS_NFS_SERVER não encontrado: {LOGISTICS_NFS_SERVER}")

        if not is_interactive:
            errors.append("Fluxo de logística requer sessão interativa do Windows (desktop desbloqueado).")

    if errors:
        formatted = "\n".join(f"- {msg}" for msg in errors)
        raise HardeningError(f"Preflight de hardening falhou:\n{formatted}")


def acquire_single_instance_lock(lock_name: str) -> Path:
    lock_dir = LOGS_DIR / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{lock_name}.lock"

    ttl_hours = int(os.getenv("HARDENING_LOCK_TTL_HOURS", "12"))
    stale_before = datetime.now() - timedelta(hours=ttl_hours)

    if lock_path.exists():
        last_update = datetime.fromtimestamp(lock_path.stat().st_mtime)
        if last_update < stale_before:
            lock_path.unlink(missing_ok=True)

    payload = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise HardeningError(
            f"Outra execução já está em andamento. Lock ativo: {lock_path}"
        ) from exc

    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True)

    return lock_path


def release_single_instance_lock(lock_path: Path | None) -> None:
    if lock_path is None:
        return
    lock_path.unlink(missing_ok=True)
