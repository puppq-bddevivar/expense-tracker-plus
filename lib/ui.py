import logging

import pandas as pd
import streamlit as st

# Configure logger for UI helpers
logger = logging.getLogger(__name__)


def data_frame_from_models(rows, columns):
    """
    Efficiently converts a list of SQLAlchemy model instances to a pandas DataFrame.

    Args:
        rows: List of SQLAlchemy model instances.
        columns: List of string attribute names to extract.
    """
    if not rows:
        return pd.DataFrame(columns=columns)

    data = []
    for r in rows:
        row_data = {}
        for col in columns:
            # Use getattr but allow it to fail strictly or log if needed.
            # Using default=None is safe for optional fields, but we check existence first
            # to catch typos in column names during development.
            if not hasattr(r, col):
                logger.warning(f"Attribute '{col}' not found in model instance {r}")
            row_data[col] = getattr(r, col, None)
        data.append(row_data)

    return pd.DataFrame(data)


def two_column_form(left_label, right_label, left_widget, right_widget, ratio=(1, 1)):
    """
    Renders a two-column layout for form inputs.

    Args:
        left_label: Label for the left column (unused in current logic but good for a11y if needed).
        right_label: Label for the right column.
        left_widget: Callable that renders the left widget.
        right_widget: Callable that renders the right widget.
        ratio: Tuple or list defining column widths (default 1:1).
    """
    col1, col2 = st.columns(ratio)
    with col1:
        left_widget()
    with col2:
        right_widget()
