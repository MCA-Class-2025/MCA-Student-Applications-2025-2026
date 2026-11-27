import sqlite3


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_NAME = "finance.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a connection to the SQLite database.
    """

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """
    Create the required database tables if they do not exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # EXPENSES TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            description TEXT
        )
        """
    )

    # --------------------------------------------------------
    # INCOME TABLE
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            income_date TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# EXPENSE FUNCTIONS
# ============================================================

def add_expense(
    amount,
    category,
    expense_date,
    description
):
    """
    Add a new expense to the database.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO expenses
        (
            amount,
            category,
            expense_date,
            description
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            amount,
            category,
            expense_date,
            description
        )
    )

    connection.commit()

    connection.close()


def get_expenses():
    """
    Get all expenses.

    Returns:
        List of tuples in the format:

        (
            id,
            amount,
            category,
            expense_date,
            description
        )
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            amount,
            category,
            expense_date,
            description
        FROM expenses
        ORDER BY expense_date DESC, id DESC
        """
    )

    expenses = cursor.fetchall()

    connection.close()

    return expenses


def delete_expense(
    expense_id
):
    """
    Delete an expense using its ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id = ?
        """,
        (expense_id,)
    )

    connection.commit()

    connection.close()


def get_category_totals():
    """
    Get total expenses grouped by category.

    Returns:
        List of tuples:

        (
            category,
            total_amount
        )
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            category,
            SUM(amount) AS total_amount
        FROM expenses
        GROUP BY category
        ORDER BY total_amount DESC
        """
    )

    category_totals = cursor.fetchall()

    connection.close()

    return category_totals


# ============================================================
# INCOME FUNCTIONS
# ============================================================

def save_income(
    amount,
    income_date
):
    """
    Save a new income record.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO income
        (
            amount,
            income_date
        )
        VALUES (?, ?)
        """,
        (
            amount,
            income_date
        )
    )

    connection.commit()

    connection.close()


def get_total_income():
    """
    Get the total income stored in the database.

    Returns:
        Total income as a float.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0)
        FROM income
        """
    )

    result = cursor.fetchone()

    connection.close()

    return float(result[0])


# ============================================================
# GET ALL INCOME
# ============================================================

def get_income():
    """
    Get all income records.

    Returns:

        (
            id,
            amount,
            income_date
        )
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            amount,
            income_date
        FROM income
        ORDER BY income_date DESC, id DESC
        """
    )

    income_records = cursor.fetchall()

    connection.close()

    return income_records


# ============================================================
# DELETE INCOME
# ============================================================

def delete_income(
    income_id
):
    """
    Delete an income record using its ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM income
        WHERE id = ?
        """,
        (income_id,)
    )

    connection.commit()

    connection.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

# Initialize the database automatically when this module
# is imported.

initialize_database()