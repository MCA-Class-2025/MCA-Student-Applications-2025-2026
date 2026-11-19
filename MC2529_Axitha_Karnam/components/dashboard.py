import streamlit as st

from database import (
    get_expenses,
    get_category_totals,
    get_total_income
)


def render_dashboard():
    """
    Render the Finance AI dashboard.

    Dashboard contains:
    - Income
    - Expenses
    - Savings
    - Savings rate
    - Spending breakdown
    - Financial health
    - Budgeting and saving overview
    """

    st.header("📊 Finance Dashboard")

    st.caption(
        "Overview of your income, expenses, savings and spending habits."
    )

    # ============================================================
    # GET DATA
    # ============================================================

    expenses = get_expenses()

    total_income = get_total_income()

    total_expenses = sum(
        expense[1]
        for expense in expenses
    )

    savings = total_income - total_expenses

    if total_income > 0:

        savings_percentage = (
            savings / total_income
        ) * 100

    else:

        savings_percentage = 0


    # ============================================================
    # TOP FINANCIAL SUMMARY
    # ============================================================

    st.subheader("💰 Financial Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💵 Total Income",
            f"₹ {total_income:,.2f}"
        )

    with col2:

        st.metric(
            "💸 Total Expenses",
            f"₹ {total_expenses:,.2f}"
        )

    with col3:

        st.metric(
            "💰 Savings",
            f"₹ {savings:,.2f}"
        )

    with col4:

        st.metric(
            "📊 Savings Rate",
            f"{savings_percentage:.1f}%"
        )


    st.divider()


    # ============================================================
    # SPENDING BREAKDOWN
    # ============================================================

    st.subheader("📈 Spending Breakdown")

    category_totals = get_category_totals()

    if category_totals:

        categories = [
            item[0]
            for item in category_totals
        ]

        amounts = [
            item[1]
            for item in category_totals
        ]

        chart_data = {
            "Category": categories,
            "Amount": amounts
        }

        st.bar_chart(
            chart_data,
            x="Category",
            y="Amount"
        )

    else:

        st.info(
            "📭 No expense data available yet."
        )


    st.divider()


    # ============================================================
    # TOP SPENDING CATEGORY
    # ============================================================

    st.subheader("🏆 Highest Spending Category")

    if category_totals:

        highest_category = category_totals[0]

        category_name = highest_category[0]
        category_amount = highest_category[1]

        st.success(
            f"Your highest spending category is "
            f"**{category_name}** with "
            f"**₹ {category_amount:,.2f}**."
        )

    else:

        st.info(
            "Add expenses to identify your highest "
            "spending category."
        )


    st.divider()


    # ============================================================
    # FINANCIAL HEALTH
    # ============================================================

    st.subheader("❤️ Financial Health")

    if total_income <= 0:

        st.warning(
            "Add your monthly income in the "
            "Monthly Savings Calculator to evaluate "
            "your financial health."
        )

    elif savings < 0:

        st.error(
            "⚠️ Your expenses are currently higher "
            "than your recorded income."
        )

    elif savings_percentage < 10:

        st.warning(
            "⚠️ Your current savings rate is below 10%. "
            "Try reducing unnecessary expenses."
        )

    elif savings_percentage < 20:

        st.info(
            "🙂 Your savings rate is moderate. "
            "Continue tracking your expenses and "
            "try to increase your savings gradually."
        )

    else:

        st.success(
            "🎉 Your savings rate is healthy. "
            "Continue maintaining your spending habits "
            "and building your savings."
        )


    st.divider()


    # ============================================================
    # SAVING & BUDGETING
    # ============================================================

    st.subheader("💡 Saving & Budgeting Overview")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            ### 💰 Saving

            - Track your expenses regularly.
            - Try to increase your monthly savings.
            - Build an emergency fund.
            - Avoid unnecessary spending.
            """
        )

    with col2:

        st.markdown(
            """
            ### 📋 Budgeting

            - Prioritize essential expenses.
            - Set limits for non-essential spending.
            - Review your spending by category.
            - Adjust your budget based on actual expenses.
            """
        )


    st.divider()


    # ============================================================
    # DASHBOARD SUMMARY
    # ============================================================

    st.subheader("📝 Financial Summary")

    if total_income > 0:

        st.write(
            f"""
            You have recorded **₹ {total_income:,.2f}** in income
            and **₹ {total_expenses:,.2f}** in expenses.

            Your current recorded savings are
            **₹ {savings:,.2f}**, giving you a savings rate of
            **{savings_percentage:.1f}%**.
            """
        )

    else:

        st.info(
            "Enter your income in the Monthly Savings Calculator "
            "and add expenses to see your complete financial summary."
        )