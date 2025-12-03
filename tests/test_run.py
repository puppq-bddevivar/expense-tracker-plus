import sys
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

# Add project root to path to allow imports from lib and pages
sys.path.insert(0, ".")

from run import main, setup_application


@pytest.fixture
def mock_pages(mocker):
    """Fixture to mock all page modules."""
    mocker.patch("run.dashboard")
    mocker.patch("run.billers")
    mocker.patch("run.bills")
    mocker.patch("run.payments")


@patch("run.init_db")
def test_setup_application_initializes_db(mock_init_db):
    """Test that setup_application calls init_db."""
    # Clear the cache before the test
    setup_application.clear()
    setup_application()
    mock_init_db.assert_called_once()


def test_main_router_navigation(mock_pages):
    """Test that the router correctly calls page show() functions."""
    at = AppTest.from_function(main).run()

    # Dashboard is the default
    assert at.radio[0].value == "Dashboard"
    from run import dashboard

    dashboard.show.assert_called_once()

    # Select another page
    at.radio[0].set_value("Payments").run()
    from run import payments

    payments.show.assert_called_once()
