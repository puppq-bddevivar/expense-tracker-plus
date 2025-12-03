import sys
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

# Add project root to path
sys.path.insert(0, ".")

from pages import dashboard


@pytest.fixture
def mock_db_calls(mocker):
    """Fixture to mock all database calls made by the dashboard."""
    mock_list_billers = mocker.patch("pages.dashboard.list_billers")
    mock_list_bills = mocker.patch("pages.dashboard.list_bills")
    mock_list_payments = mocker.patch("pages.dashboard.list_payments")
    return mock_list_billers, mock_list_bills, mock_list_payments


def create_mock_bill(id, biller_name, amount, balance, status):
    """Helper to create a mock Bill object with a nested biller mock."""
    bill = MagicMock()
    bill.id = id
    bill.biller = MagicMock()  # Mock the related biller object
    bill.biller.name = biller_name
    bill.amount = Decimal(amount)
    bill.balance_amount = Decimal(balance)
    bill.status = status
    return bill


def test_dashboard_empty_state(mock_db_calls):
    """Test the dashboard when there is no data."""
    mock_list_billers, mock_list_bills, mock_list_payments = mock_db_calls
    mock_list_billers.return_value = []
    mock_list_bills.return_value = []
    mock_list_payments.return_value = []

    at = AppTest.from_function(dashboard.show).run()

    assert at.header[0].value == "Dashboard"
    assert at.metric[0].value == "0"
    assert at.metric[1].value == "₱0.00"
    assert at.metric[2].value == "0"
    assert at.info[0].value == "No billers registered."
    assert at.info[1].value == "No bills to analyze."
    assert at.info[2].value == "No payments recorded yet."


def test_dashboard_with_data(mock_db_calls):
    """Test the dashboard with mock data."""
    mock_list_billers, mock_list_bills, mock_list_payments = mock_db_calls

    mock_biller = MagicMock()
    mock_biller.name = "Meralco"
    mock_list_billers.return_value = [mock_biller]

    mock_bills = [
        create_mock_bill(1, "Meralco", "1000.00", "1000.00", "unpaid"),
        create_mock_bill(2, "Converge", "2500.00", "500.50", "partial payment"),
        create_mock_bill(3, "BPI", "5000.00", "0.00", "paid"),
    ]
    mock_list_bills.return_value = mock_bills

    mock_payment = MagicMock()
    mock_payment.amount = Decimal("2000.00")
    mock_list_payments.return_value = [mock_payment]

    at = AppTest.from_function(dashboard.show).run()

    assert at.metric[0].value == "1"
    assert at.metric[1].value == "₱1,500.50"
    assert at.metric[2].value == "2"
    assert len(at.plotly_chart) == 1


def test_dashboard_all_paid(mock_db_calls):
    """Test the dashboard when all bills are paid."""
    mock_list_billers, mock_list_bills, mock_list_payments = mock_db_calls

    mock_list_billers.return_value = [MagicMock()]
    mock_bills = [
        create_mock_bill(1, "Meralco", "1000.00", "0.00", "paid"),
    ]
    mock_list_bills.return_value = mock_bills
    mock_list_payments.return_value = []

    at = AppTest.from_function(dashboard.show).run()

    assert at.metric[1].value == "₱0.00"
    assert at.metric[2].value == "0"
    assert at.success[0].value == "All bills are paid! 🎉"
