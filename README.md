# Personal Finance Tracker

A beginner-friendly command-line application for recording income and expenses, reviewing financial reports, and exporting transaction history. The project was created for the InternStudio Python Development Internship and stores data locally in SQLite.

## Problem Statement

It can be difficult to keep track of everyday income and expenses using memory or scattered notes. Without an organized record, it is harder to see where money is going, compare monthly spending, and understand the current balance.

## Project Objectives

- Record, view, edit, and delete income and expense transactions.
- Validate amounts, dates, types, and categories before saving.
- Keep transaction records between application runs using SQLite.
- Summarize finances overall and by month or expense category.
- Export transaction data to a spreadsheet-friendly CSV file.
- Practice modular Python, database operations, and automated testing.

## Features

- Separate income and expense transaction types.
- Categories: Food, Education, Transport, Shopping, Entertainment, Salary, and Other.
- Transaction amounts, dates, and optional descriptions.
- Complete transaction management with input validation.
- Overall income, expenses, balance, and highest expense category.
- Monthly income, expenses, balance, and expense categories.
- Category-wise expense totals.
- UTF-8 CSV export.
- Automatic local database and table creation.
- Pytest tests that use temporary databases rather than personal data.

## Technologies Used

- Python 3
- SQLite (`sqlite3`, included with Python)
- CSV (`csv`, included with Python)
- Pytest (the only third-party dependency)

## Project Folder Structure

```text
personal_finance_tracker/
├── main.py                 # Interactive command-line menu
├── database.py             # SQLite connection and table setup
├── transactions.py         # Transaction validation and CRUD operations
├── reports.py              # Financial summaries and expense reports
├── export.py               # CSV export
├── requirements.txt        # Pytest dependency
├── README.md
├── .gitignore
├── data/
│   └── .gitkeep            # Keeps the initially empty data folder in Git
└── tests/
    ├── __init__.py
    ├── test_transactions.py
    └── test_reports.py
```

The application creates `data/finance.db` the first time it runs. The local database and CSV exports are intentionally excluded from Git.

## Installation

Install Python 3 from [python.org](https://www.python.org/downloads/) and enable the option to add Python to PATH during installation. In Windows Command Prompt or the VS Code terminal, move to the project folder:

```bat
cd path\to\personal_finance_tracker
```

Create and activate a virtual environment in **Command Prompt**:

```bat
py -m venv .venv
.venv\Scripts\activate
```

In the **VS Code PowerShell terminal**, activate it with:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, you can run the application and tests without activating the virtual environment by using `.venv\Scripts\python.exe` instead of `python`.

Install the project dependency:

```bat
py -m pip install -r requirements.txt
```

## How to Run

Start the application from the project folder:

```bat
py main.py
```

Choose a numbered menu option and follow the prompts. Dates use `YYYY-MM-DD`; pressing Enter at the date prompt for a new transaction uses today's date. Category names are shown when adding a transaction.

### Example Program Output

```text
=== Personal Finance Tracker ===
1. Add Income
2. Add Expense
3. View Transactions
4. Edit Transaction
5. Delete Transaction
6. View Financial Summary
7. Monthly Report
8. Category-wise Report
9. Export to CSV
10. Exit
Enter your choice: 6

Financial Summary
Total income:   $2500.00
Total expenses: $137.50
Current balance:   $2362.50
Highest expense category: Food ($100.00)
```

The values above are illustrative only. The project includes no sample transactions or personal financial data.

## Testing

Install dependencies as described above, then run all tests from the project folder:

```bat
py -m pytest
```

Tests create SQLite databases under pytest's temporary directory. They do not read or modify `data/finance.db`.

## How the Project Works

`main.py` displays the menu and gathers user input. It calls functions in the other modules rather than containing the database and reporting logic itself.

`database.py` chooses the default local database path, opens SQLite connections, and creates the table and date index if they are missing. SQLite stores the data in a file, so transactions remain after the program closes. Money is stored internally as integer cents to avoid common floating-point rounding errors.

`transactions.py` checks transaction types, positive amounts, supported categories, and ISO-formatted dates before writing data. It provides functions to add, list, edit, and delete transaction records.

`reports.py` uses SQLite aggregation queries to calculate overall and monthly totals, category expense totals, and the highest expense category.

`export.py` writes transaction records to a CSV file that can be opened in spreadsheet software. By default, the menu saves it as `data/transactions.csv`.

`tests/` verifies transaction operations, validation, reports, and CSV export using isolated temporary databases.

## Future Enhancements

- Add user-defined categories.
- Add date-range filters and budget limits.
- Add charts using a plotting library.
- Add configurable currency and recurring transactions.
- Add an optional data backup and restore workflow.

## Conclusion

This project provides a complete, local-first starting point for tracking personal finances. Its small modules make the application approachable to learn, test, and extend, while SQLite and CSV keep it usable without a server or paid service.

## GitHub Submission

To prepare a repository, create a GitHub repository named `internstudio_pythondevelopment_task1`, then open a terminal in this project folder and run:

```bat
git init
git add .
git commit -m "Add personal finance tracker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/internstudio_pythondevelopment_task1.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Review `git status` before pushing; the `.gitignore` excludes the local database, CSV exports, virtual environment, and Python caches.
