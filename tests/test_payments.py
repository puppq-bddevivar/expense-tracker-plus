import sys
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

# Add project root to path
sys.path.insert(0, ".")

from pages import payments


@pytest.fixture
def mock_payment_helpers(mocker):
    """Mock helper functions used by the payments page."""
    mock_list_unpaid = mocker.patch("pages.payments.list_unpaid_bills")
    mock_add_payment = mocker.patch("pages.payments.add_payment")
    mock_list_history = mocker.patch("pages.payments.list_payment_history")
    return mock_list_unpaid, mock_add_payment, mock_list_history


def create_mock_unpaid_bill(id, biller_name, amount, balance):
    """Helper to create a mock unpaid Bill object."""
    bill = MagicMock()
    bill.id = id
    bill.biller = MagicMock()
    bill.biller.name = biller_name
    bill.amount = Decimal(amount)
    bill.balance_amount = Decimal(balance)
    bill.status = "unpaid"
    return bill


def test_payments_no_unpaid_bills(mock_payment_helpers):
    """Test the payments page when there are no unpaid bills."""
    mock_list_unpaid, _, mock_list_history = mock_payment_helpers
    mock_list_unpaid.return_value = []
    mock_list_history.return_value = []

    at = AppTest.from_function(payments.show).run()

    assert at.header[0].value == "Payments"
    assert at.info[0].value == "No unpaid bills to pay."


def test_payments_form_submission(mock_payment_helpers):
    """Test submitting the payment form for a partial payment."""
    mock_list_unpaid, mock_add_payment, mock_list_history = mock_payment_helpers

    # Setup mock data
    mock_bill = create_mock_unpaid_bill(1, "Meralco", "1500.00", "1500.00")
    mock_list_unpaid.return_value = [mock_bill]
    mock_list_history.return_value = []

    at = AppTest.from_function(payments.show).run()

    # The first selectbox (at.selectbox[0]) is for selecting the bill.
    # Since there's only one mock bill, we assume it's the default.
    # We then interact with the rest of the form.
    at.number_input[0].set_value(500.0)
    at.selectbox[1].set_value("GCash")  # Method
    at.selectbox[2].set_value("Partial Payment")  # Status
    at.text_input[0].set_value("REF123")

    # Submit the form
    at.form[0].submit().run()

    # Verify add_payment was called with correct arguments
    mock_add_payment.assert_called_once()
    call_args, call_kwargs = mock_add_payment.call_args

    assert call_args[0] == 1  # bill_id
    assert call_args[1] == Decimal("500.0")  # amount
    assert call_args[2] == date.today()  # paid_on
    assert call_args[3] == "GCash"  # method
    assert call_args[4] == "REF123"  # ref
    assert call_args[6] == "Partial Payment"  # status

    assert at.success[0].value == "Payment recorded successfully"
