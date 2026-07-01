import sys
import types
from unittest.mock import MagicMock

pywinauto_module = types.ModuleType("pywinauto")
pywinauto_module.Desktop = MagicMock()
pywinauto_module.Application = MagicMock()
sys.modules.setdefault("pywinauto", pywinauto_module)

pywinauto_mouse_module = types.ModuleType("pywinauto.mouse")
pywinauto_mouse_module.click = MagicMock()
sys.modules.setdefault("pywinauto.mouse", pywinauto_mouse_module)

pywinauto_keyboard_module = types.ModuleType("pywinauto.keyboard")
pywinauto_keyboard_module.send_keys = MagicMock()
sys.modules.setdefault("pywinauto.keyboard", pywinauto_keyboard_module)

from src.logistics.flows.renave_emission_flow import RenaveEmissionFlow


def test_execute_closes_page_after_success():
    flow = RenaveEmissionFlow.__new__(RenaveEmissionFlow)
    flow.page = MagicMock()
    flow.page.processar_operacao.return_value = "Renave ok"

    result = flow.execute("ABC123")

    assert result == "Renave ok"
    flow.page.clicar_renave.assert_called_once_with()
    flow.page.processar_operacao.assert_called_once_with("ABC123")
    flow.page.close.assert_called_once_with()
