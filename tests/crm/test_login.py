"""Unit tests for LoginPage (uses mocks — no real browser needed)."""
import pytest
from unittest.mock import MagicMock, patch
from src.crm.pages.login_page import LoginPage
from src.shared.exceptions.rpa_exceptions import LoginFailedException

@pytest.fixture
def mock_driver():
    return MagicMock()

def test_login_raises_on_error_message(mock_driver):
    page = LoginPage(mock_driver)
    page.fill = MagicMock()
    page.click = MagicMock()
    page.is_visible = MagicMock(return_value=True)   # error banner visible
    page.text_of = MagicMock(return_value="Credenciais inválidas")

    with pytest.raises(LoginFailedException):
        page.login("user", "wrong_pass")

def test_login_succeeds_when_no_error(mock_driver):
    page = LoginPage(mock_driver)
    page.fill = MagicMock()
    page.click = MagicMock()
    page.is_visible = MagicMock(return_value=False)  # no error banner

    page.login("user", "correct_pass")  # should not raise
