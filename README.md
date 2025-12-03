# Bills & Expenses Tracker

A simple yet powerful web application built with Streamlit to help you track your bills, manage billers, and record payments. Keep your personal finances organized with an easy-to-use interface.

![Dashboard Screenshot](https://user-images.githubusercontent.com/12345/placeholder.png) <!-- TODO: Add a real screenshot -->

## ✨ Features

This application is organized into four main sections:

*   **Dashboard**: Get a high-level overview of your financial status.
    *   Key metrics: Total outstanding amount, number of pending bills, and registered billers.
    *   A pie chart visualizing outstanding debt broken down by biller.
    *   Quick access to a directory of all your billers and a list of recent payments.
*   **Billers**: Manage the entities you pay.
    *   Add, view, and manage companies or services (e.g., electricity provider, internet service, credit card).
*   **Bills**: Keep track of all your incoming bills.
    *   Add new bills with details like amount, due date, and billing period.
    *   View a comprehensive list of all recorded bills.
    *   Edit or delete existing bills.
*   **Payments**: Record payments made against your bills.
    *   Select an unpaid bill and record a full or partial payment.
    *   Specify payment details like date, method, and reference number.
    *   View a complete history of all payments made.

## 🛠️ Tech Stack

*   **Framework**: [Streamlit](https://streamlit.io/)
*   **Language**: Python
*   **Data Manipulation**: [Pandas](https://pandas.pydata.org/)
*   **Charting**: [Plotly Express](https://plotly.com/python/plotly-express/)
*   **Database**: SQLite (via SQLAlchemy ORM)

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### 1. Prerequisites

*   Python 3.8+
*   A virtual environment tool (like `venv`)

### 2. Installation

Clone the repository and install the dependencies.

```bash
# Clone the repository
git clone <your-repo-url>
cd expense-tracker-plus

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Database & Secrets

The application uses a local SQLite database and requires a Streamlit secrets file for configuration, even if it's just for local development.

1.  **Create the secrets directory:**
    ```bash
    mkdir -p .streamlit
    ```

2.  **Create a secrets file** at `.streamlit/secrets.toml`. Add the following content, which configures the app to use a local SQLite database file named `main.db`.

    ```toml
    # .streamlit/secrets.toml
    [database]
    url = "sqlite:///main.db"
    ```

The database file (`main.db`) will be created automatically the first time you run the application.

### 4. Running the Application

With your virtual environment active, run the Streamlit app:

```bash
streamlit run run.py
```

Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).