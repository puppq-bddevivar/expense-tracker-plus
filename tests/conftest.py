from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db_session(mocker):
    """Fixture to mock the database session."""
    mock_session = MagicMock()
    mocker.patch("lib.db.SessionLocal", return_value=mock_session)
    return mock_session


@pytest.fixture(autouse=True)
def patch_st_secrets(mocker):
    """
    Automatically mock st.secrets for all tests to prevent errors
    when it's not configured in the test environment.
    """
    mocker.patch("streamlit.secrets", new_callable=mocker.PropertyMock, return_value={})
