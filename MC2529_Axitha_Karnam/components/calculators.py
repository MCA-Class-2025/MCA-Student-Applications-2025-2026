import streamlit as st
import requests
from datetime import date


from database import (
    initialize_database,
    add_expense,
    get_expenses,
    delete_expense,
    get_category_totals
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# SAVINGS CALCULATOR
# ============================================================

def calculate_savings(income, expenses):
    """Calculate monthly savings and savings percentage."""

    savings = income - expenses

    if income > 0:
        savings_percentage = (
            savings / income
        ) * 100
    else:
        savings_percentage = 0

    return savings, savings_percentage


# ============================================================
# SAVINGS ADVICE
# ============================================================

def generate_savings_advice(
    savings,
    savings_percentage
):
    """Generate basic savings advice."""

    if savings < 0:

        return """
❌ **Your expenses are higher than your income.**

Suggestions:

- Reduce unnecessary spending.
- Prepare a monthly budget.
- Avoid impulse purchases.
- Look for ways to increase income.
"""

    if savings_percentage < 10:

        return """
⚠️ **Your savings rate is quite low.**

Suggestions:

- Try to increase your monthly savings.
- Track your daily expenses.
- Reduce unnecessary spending.
- Build an emergency fund.
"""

    if savings_percentage < 20:

        return """
🙂 **Good progress!**

Your savings are at a moderate level.

Suggestions:

- Continue budgeting.
- Build an emergency fund.
- Consider regular investments such as SIP.
"""

    return """
🎉 **Excellent savings rate!**

Your savings rate is healthy.

Suggestions:

- Continue investing regularly.
- Diversify your investments.
- Maintain an emergency fund.
- Continue following your financial plan.
"""


# ============================================================
# MONTHLY SAVINGS CALCULATOR
# ============================================================

def render_savings_calculator(
    ask_question
):
    """Render monthly savings calculator."""

    st.header(
        "💰 Monthly Savings Calculator"
    )

    st.write(
        "Calculate your monthly savings "
        "and receive AI-based financial guidance."
    )

    # ========================================================
    # INPUTS
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        income = st.number_input(
            "💵 Monthly Income (₹)",
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            key="monthly_income"
        )

    with col2:

        expenses = st.number_input(
            "🛒 Monthly Expenses (₹)",
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            key="monthly_expenses"
        )

    # ========================================================
    # CALCULATE
    # ========================================================

    if st.button(
        "Calculate Savings",
        type="primary",
        key="calculate_savings_button"
    ):

        savings, savings_percentage = calculate_savings(
            income,
            expenses
        )

        st.subheader(
            "📊 Results"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Monthly Savings",
                f"₹ {savings:,.2f}"
            )

        with col2:

            st.metric(
                "Savings Percentage",
                f"{savings_percentage:.2f}%"
            )

        # ====================================================
        # PROGRESS
        # ====================================================

        progress = min(
            max(
                savings_percentage / 100,
                0
            ),
            1
        )

        st.progress(
            progress
        )

        # ====================================================
        # BASIC ADVICE
        # ====================================================

        st.subheader(
            "🤖 Financial Guidance"
        )

        advice = generate_savings_advice(
            savings,
            savings_percentage
        )

        st.markdown(
            advice
        )


# ============================================================
# AI EXPENSE ANALYSIS
# ============================================================

def generate_expense_analysis(
    ask_question
):
    """Analyze actual user expenses using Gemma 3."""

    expenses = get_expenses()

    if not expenses:

        st.warning(
            "📭 Add some expenses before asking AI "
            "to analyze your spending."
        )

        return

    # ========================================================
    # TOTAL EXPENSE
    # ========================================================

    total_expenses = sum(
        expense[1]
        for expense in expenses
    )

    # ========================================================
    # CATEGORY TOTALS
    # ========================================================

    category_totals = get_category_totals()

    category_text = ""

    for category, amount in category_totals:

        category_text += (
            f"- {category}: ₹{amount:,.2f}\n"
        )

    # ========================================================
    # INDIVIDUAL TRANSACTIONS
    # ========================================================

    transaction_text = ""

    for expense in expenses:

        amount = expense[1]
        category = expense[2]
        expense_date = expense[3]
        description = expense[4]

        transaction_text += (
            f"- Date: {expense_date} | "
            f"Category: {category} | "
            f"Amount: ₹{amount:,.2f} | "
            f"Description: "
            f"{description or 'No description'}\n"
        )

    # ========================================================
    # AI PROMPT
    # ========================================================

    query = f"""
You are Finance AI, an intelligent personal finance assistant.

Analyze the user's ACTUAL expense data provided below.

IMPORTANT:

- Use only the information provided.
- Do not invent transactions.
- Do not assume the user's income.
- Do not assume financial information that is not provided.

==================================================
TOTAL EXPENSES
==================================================

₹{total_expenses:,.2f}

==================================================
EXPENSES BY CATEGORY
==================================================

{category_text}

==================================================
INDIVIDUAL TRANSACTIONS
==================================================

{transaction_text}

==================================================
ANALYSIS REQUIRED
==================================================

1. Identify the highest spending category.

2. Identify the lowest spending category.

3. Identify any large or unusual expenses based only
   on the transactions provided.

4. Explain the user's spending pattern.

5. Identify categories where spending could potentially
   be reduced.

6. Suggest a practical monthly budget strategy.

7. Give 3 specific ways the user could save money.

8. Give a short summary of the user's overall spending.

9. Mention important observations from the transaction data.

==================================================
RESPONSE FORMAT
==================================================

## 📊 Spending Summary

Explain the overall spending.

## 🏆 Highest Spending Category

Mention the category and amount.

## ⚠️ Areas to Improve

Mention categories or transactions that may need attention.

## 💰 Saving Opportunities

Give practical suggestions based on the actual data.

## 📅 Suggested Budget Strategy

Suggest reasonable spending categories.

## 🤖 Finance AI Recommendation

Give a short personalized recommendation.

Remember:

- Use actual numbers from the data.
- Do not invent information.
- Do not recommend specific stocks.
- Do not recommend specific financial products.
- Give general educational financial guidance.
"""

    # ========================================================
    # SEND TO GEMMA 3
    # ========================================================

    with st.spinner(
        "🤖 Gemma 3 is analyzing your actual spending..."
    ):

        try:

            answer, docs = ask_question(
                query
            )

            st.subheader(
                "🤖 Finance AI Analysis"
            )

            st.markdown(
                answer
            )

        except Exception as error:

            st.error(
                "Unable to generate AI expense analysis."
            )

            st.exception(
                error
            )


# ============================================================
# EXPENSE TRACKER
# ============================================================

def render_expense_tracker(
    ask_question
):
    """Render expense tracker."""

    st.header(
        "📊 Expense Tracker"
    )

    st.write(
        "Track your daily expenses and understand "
        "your spending habits."
    )

    # ========================================================
    # ADD EXPENSE
    # ========================================================

    st.subheader(
        "➕ Add Expense"
    )

    col1, col2 = st.columns(2)

    with col1:

        amount = st.number_input(
            "💰 Amount (₹)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            key="expense_amount"
        )

        category = st.selectbox(
            "📂 Category",
            [
                "Food",
                "Shopping",
                "Transport",
                "Bills",
                "Entertainment",
                "Education",
                "Health",
                "Travel",
                "Other"
            ],
            key="expense_category"
        )

    with col2:

        expense_date = st.date_input(
            "📅 Date",
            value=date.today(),
            key="expense_date"
        )

        description = st.text_input(
            "📝 Description",
            placeholder="Example: Lunch",
            key="expense_description"
        )

    if st.button(
        "➕ Add Expense",
        type="primary",
        key="add_expense_button"
    ):

        if amount <= 0:

            st.error(
                "Please enter a valid expense amount."
            )

        else:

            add_expense(
                amount,
                category,
                str(expense_date),
                description
            )

            st.success(
                "✅ Expense added successfully!"
            )

            st.rerun()

    st.divider()

    # ========================================================
    # GET EXPENSES
    # ========================================================

    expenses = get_expenses()

    if not expenses:

        st.info(
            "📭 No expenses recorded yet. "
            "Add your first expense above."
        )

        return

    # ========================================================
    # TOTAL EXPENSE
    # ========================================================

    total_expenses = sum(
        expense[1]
        for expense in expenses
    )

    st.subheader(
        "📊 Expense Summary"
    )

    st.metric(
        "💸 Total Expenses",
        f"₹ {total_expenses:,.2f}"
    )

    # ========================================================
    # CATEGORY SUMMARY
    # ========================================================

    category_totals = get_category_totals()

    st.subheader(
        "📈 Spending by Category"
    )

    for category, amount in category_totals:

        st.write(
            f"**{category}** — ₹ {amount:,.2f}"
        )

    # ========================================================
    # AI EXPENSE ANALYSIS
    # ========================================================

    st.divider()

    st.subheader(
        "🤖 AI Spending Analysis"
    )

    st.write(
        "Let Gemma 3 analyze your actual spending "
        "and provide personalized suggestions."
    )

    if st.button(
        "🤖 Analyze My Expenses",
        type="primary",
        key="analyze_expenses_button"
    ):

        generate_expense_analysis(
            ask_question
        )

    # ========================================================
    # EXPENSE HISTORY
    # ========================================================

    st.divider()

    st.subheader(
        "📋 Expense History"
    )

    for expense in expenses:

        expense_id = expense[0]
        amount = expense[1]
        category = expense[2]
        expense_date = expense[3]
        description = expense[4]

        col1, col2, col3 = st.columns(
            [2, 3, 1]
        )

        with col1:

            st.write(
                f"**₹ {amount:,.2f}**"
            )

        with col2:

            st.write(
                f"{category} | {expense_date}"
            )

            if description:

                st.caption(
                    description
                )

        with col3:

            if st.button(
                "🗑️",
                key=f"delete_expense_{expense_id}"
            ):

                delete_expense(
                    expense_id
                )

                st.rerun()


# ============================================================
# CURRENCY CONVERTER
# ============================================================

def currency_converter():

    st.header(
        "💱 Currency Converter"
    )

    st.caption(
        "Convert currencies using live exchange-rate data."
    )

    # ========================================================
    # CURRENCY DATA
    # ========================================================

    currencies = {

        "INR": {
            "name": "Indian Rupee",
            "symbol": "₹",
            "flag": "🇮🇳"
        },

        "USD": {
            "name": "US Dollar",
            "symbol": "$",
            "flag": "🇺🇸"
        },

        "EUR": {
            "name": "Euro",
            "symbol": "€",
            "flag": "🇪🇺"
        },

        "GBP": {
            "name": "British Pound",
            "symbol": "£",
            "flag": "🇬🇧"
        },

        "JPY": {
            "name": "Japanese Yen",
            "symbol": "¥",
            "flag": "🇯🇵"
        },

        "AED": {
            "name": "UAE Dirham",
            "symbol": "د.إ",
            "flag": "🇦🇪"
        },

        "AUD": {
            "name": "Australian Dollar",
            "symbol": "A$",
            "flag": "🇦🇺"
        },

        "CAD": {
            "name": "Canadian Dollar",
            "symbol": "C$",
            "flag": "🇨🇦"
        },

        "CHF": {
            "name": "Swiss Franc",
            "symbol": "CHF",
            "flag": "🇨🇭"
        },

        "CNY": {
            "name": "Chinese Yuan",
            "symbol": "¥",
            "flag": "🇨🇳"
        },

        "HKD": {
            "name": "Hong Kong Dollar",
            "symbol": "HK$",
            "flag": "🇭🇰"
        },

        "SGD": {
            "name": "Singapore Dollar",
            "symbol": "S$",
            "flag": "🇸🇬"
        },

        "NZD": {
            "name": "New Zealand Dollar",
            "symbol": "NZ$",
            "flag": "🇳🇿"
        },

        "ZAR": {
            "name": "South African Rand",
            "symbol": "R",
            "flag": "🇿🇦"
        },

        "BRL": {
            "name": "Brazilian Real",
            "symbol": "R$",
            "flag": "🇧🇷"
        },

        "KRW": {
            "name": "South Korean Won",
            "symbol": "₩",
            "flag": "🇰🇷"
        },

        "THB": {
            "name": "Thai Baht",
            "symbol": "฿",
            "flag": "🇹🇭"
        },

        "MYR": {
            "name": "Malaysian Ringgit",
            "symbol": "RM",
            "flag": "🇲🇾"
        },

        "MXN": {
            "name": "Mexican Peso",
            "symbol": "Mex$",
            "flag": "🇲🇽"
        }
    }

    # ========================================================
    # SESSION STATE
    # ========================================================

    if "currency_result" not in st.session_state:

        st.session_state.currency_result = None

    if "currency_date" not in st.session_state:

        st.session_state.currency_date = None

    # ========================================================
    # CURRENCY LABEL
    # ========================================================

    def currency_label(code):

        currency = currencies[code]

        return (
            f"{currency['flag']} "
            f"{currency['name']} "
            f"({code}) — "
            f"{currency['symbol']}"
        )

    # ========================================================
    # INPUTS
    # ========================================================

    st.subheader(
        "💰 Currency Conversion"
    )

    col1, col2, col3 = st.columns(
        [1, 1.5, 1.5]
    )

    with col1:

        amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=100.00,
            step=10.00,
            format="%.2f",
            key="currency_amount"
        )

    with col2:

        from_currency = st.selectbox(
            "From Currency",
            list(currencies.keys()),
            index=0,
            format_func=currency_label,
            key="currency_from"
        )

    with col3:

        to_currency = st.selectbox(
            "To Currency",
            list(currencies.keys()),
            index=1,
            format_func=currency_label,
            key="currency_to"
        )

    # ========================================================
    # CONVERT BUTTON ONLY
    # ========================================================

    convert_button = st.button(
        "💱 Convert Currency",
        type="primary",
        use_container_width=True,
        key="convert_currency_button"
    )

    # ========================================================
    # EXCHANGE RATE API
    # ========================================================

    def get_exchange_rate(
        from_currency,
        to_currency
    ):

        # ----------------------------------------------------
        # SAME CURRENCY
        # ----------------------------------------------------

        if from_currency == to_currency:

            return (
                1.0,
                date.today().isoformat()
            )

        # ----------------------------------------------------
        # API
        # ----------------------------------------------------

        url = (
            "https://api.frankfurter.app/latest"
            f"?from={from_currency}"
            f"&to={to_currency}"
        )

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # ----------------------------------------------------
        # CHECK RESPONSE
        # ----------------------------------------------------

        if "rates" not in data:

            raise ValueError(
                "Exchange rate was not returned by the API."
            )

        if to_currency not in data["rates"]:

            raise ValueError(
                f"No exchange rate found for {to_currency}."
            )

        rate = float(
            data["rates"][to_currency]
        )

        rate_date = data.get(
            "date",
            date.today().isoformat()
        )

        return rate, rate_date

    # ========================================================
    # CONVERT
    # ========================================================

    if convert_button:

        try:

            with st.spinner(
                "🔄 Getting latest exchange rate..."
            ):

                rate, rate_date = get_exchange_rate(
                    from_currency,
                    to_currency
                )

            converted_amount = (
                amount * rate
            )

            # ------------------------------------------------
            # SAVE RESULT
            # ------------------------------------------------

            st.session_state.currency_result = {

                "amount": amount,

                "from_currency": from_currency,

                "to_currency": to_currency,

                "converted_amount": converted_amount,

                "rate": rate
            }

            st.session_state.currency_date = (
                rate_date
            )

        except requests.exceptions.RequestException:

            st.error(
                "❌ Unable to connect to the exchange-rate API."
            )

            st.caption(
                "Please check your internet connection "
                "and try again."
            )

            st.session_state.currency_result = None

        except Exception as error:

            st.error(
                "❌ Unable to convert the currency."
            )

            st.caption(
                str(error)
            )

            st.session_state.currency_result = None

    # ========================================================
    # DISPLAY RESULT
    # ========================================================

    result = st.session_state.currency_result

    if result is not None:

        result_from = (
            result["from_currency"]
        )

        result_to = (
            result["to_currency"]
        )

        from_info = currencies[
            result_from
        ]

        to_info = currencies[
            result_to
        ]

        converted = (
            result["converted_amount"]
        )

        rate = (
            result["rate"]
        )

        # ====================================================
        # RESULT
        # ====================================================

        st.divider()

        st.subheader(
            "💱 Conversion Result"
        )

        st.success(
            f"{from_info['flag']} "
            f"{from_info['symbol']}"
            f"{result['amount']:,.2f} "
            f"{result_from}"
            f"  =  "
            f"{to_info['flag']} "
            f"{to_info['symbol']}"
            f"{converted:,.2f} "
            f"{result_to}"
        )

        # ====================================================
        # DETAILS
        # ====================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "From",
                result_from
            )

            st.caption(
                f"{from_info['flag']} "
                f"{from_info['name']}"
            )

        with col2:

            st.metric(
                "Exchange Rate",
                f"{rate:.6f}"
            )

            st.caption(
                f"1 {result_from} = "
                f"{rate:.6f} {result_to}"
            )

        with col3:

            st.metric(
                "To",
                result_to
            )

            st.caption(
                f"{to_info['flag']} "
                f"{to_info['name']}"
            )

        # ====================================================
        # RATE DATE
        # ====================================================

        if st.session_state.currency_date:

            st.caption(
                f"📅 Exchange-rate date: "
                f"{st.session_state.currency_date}"
            )

    else:

        st.info(
            "💡 Select your currencies and amount, "
            "then click **Convert Currency**."
        )


# ============================================================
# MAIN FINANCIAL TOOLS
# ============================================================

def render_calculators(
    ask_question
):
    """
    Main Finance Tools page.
    """

    st.header(
        "🧮 Financial Tools"
    )

    st.caption(
        "Calculate savings, manage expenses, "
        "and convert currencies."
    )

    # ========================================================
    # SAVINGS CALCULATOR
    # ========================================================

    render_savings_calculator(
        ask_question
    )

    st.divider()

    # ========================================================
    # EXPENSE TRACKER
    # ========================================================

    render_expense_tracker(
        ask_question
    )

    st.divider()

    # ========================================================
    # CURRENCY CONVERTER
    # ========================================================

    currency_converter()

    st.divider()

    # ========================================================
    # FUTURE CALCULATORS
    # ========================================================

    st.info(
        "🚀 SIP, EMI and FD calculators "
        "can be added next."
    )