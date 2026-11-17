import { useEffect, useMemo, useState } from "react";

import {
  Wallet,
  TrendingUp,
  CalendarDays,
  Receipt,
  ArrowDownRight,
  Search,
} from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout/DashboardLayout";

import {
  getCurrentUser,
  getExpenses,
} from "../../services/dashboardService";


// ============================================================
// CATEGORY COLORS
// ============================================================

const CATEGORY_COLORS = [
  "#1F6F5C",
  "#C9A227",
  "#C15B3D",
  "#4A6FA5",
  "#A6A06D",
  "#B89B7A",
  "#6F8B75",
];


// ============================================================
// DASHBOARD
// ============================================================

function Dashboard() {

  // ==========================================================
  // STATE
  // ==========================================================

  const [user, setUser] = useState(null);

  const [expenses, setExpenses] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");


  // ==========================================================
  // LOAD REAL DATA
  // ==========================================================

  useEffect(() => {

    const loadDashboard = async () => {

      try {

        setLoading(true);
        setError("");

        // ----------------------------------------------------
        // GET LOGGED-IN USER
        // ----------------------------------------------------

        const userData =
          await getCurrentUser();

        console.log(
          "Current user:",
          userData
        );

        setUser(userData);


        // ----------------------------------------------------
        // GET LOGGED-IN USER EXPENSES
        // ----------------------------------------------------

        const expenseData =
          await getExpenses();

        console.log(
          "Dashboard expenses:",
          expenseData
        );

        const expenseList =
          Array.isArray(expenseData)
            ? expenseData
            : expenseData?.expenses || [];

        setExpenses(expenseList);

      } catch (err) {

        console.error(
          "Dashboard loading error:",
          err
        );

        setError(
          err?.response?.data?.detail ||
          err?.response?.data?.message ||
          "Unable to load your dashboard data."
        );

      } finally {

        setLoading(false);

      }

    };

    loadDashboard();

  }, []);


  // ==========================================================
  // CURRENT DATE
  // ==========================================================

  const today = new Date();

  const currentYear =
    today.getFullYear();

  const currentMonth =
    today.getMonth();


  // ==========================================================
  // DATE HELPER
  // ==========================================================

  const getExpenseDate = (expense) => {

    if (!expense?.date) {
      return null;
    }

    const date =
      new Date(expense.date);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return null;
    }

    return date;

  };


  // ==========================================================
  // CURRENCY
  // ==========================================================

  const currency =
    user?.preferred_currency ||
    user?.currency ||
    "INR";


  // ==========================================================
  // FORMAT CURRENCY
  // ==========================================================

  const formatCurrency = (amount) => {

    try {

      return new Intl.NumberFormat(
        "en-IN",
        {
          style: "currency",
          currency,
          maximumFractionDigits: 0,
        }
      ).format(
        Number(amount || 0)
      );

    } catch {

      return `₹${Number(
        amount || 0
      ).toLocaleString("en-IN")}`;

    }

  };


  // ==========================================================
  // TOTAL EXPENSE
  // ==========================================================

  const totalExpense = useMemo(() => {

    return expenses.reduce(
      (total, expense) =>
        total +
        Number(
          expense.amount || 0
        ),
      0
    );

  }, [expenses]);


  // ==========================================================
  // CURRENT MONTH EXPENSE
  // ==========================================================

  const monthlyExpense = useMemo(() => {

    return expenses
      .filter((expense) => {

        const date =
          getExpenseDate(expense);

        if (!date) {
          return false;
        }

        return (
          date.getFullYear() ===
            currentYear &&
          date.getMonth() ===
            currentMonth
        );

      })
      .reduce(
        (total, expense) =>
          total +
          Number(
            expense.amount || 0
          ),
        0
      );

  }, [
    expenses,
    currentYear,
    currentMonth,
  ]);


  // ==========================================================
  // TODAY EXPENSE
  // ==========================================================

  const todayExpense = useMemo(() => {

    return expenses
      .filter((expense) => {

        const date =
          getExpenseDate(expense);

        if (!date) {
          return false;
        }

        return (
          date.getFullYear() ===
            today.getFullYear() &&
          date.getMonth() ===
            today.getMonth() &&
          date.getDate() ===
            today.getDate()
        );

      })
      .reduce(
        (total, expense) =>
          total +
          Number(
            expense.amount || 0
          ),
        0
      );

  }, [expenses]);


  // ==========================================================
  // TRANSACTION COUNT
  // ==========================================================

  const transactionCount =
    expenses.length;


  // ==========================================================
  // NORMALIZE CATEGORY
  // ==========================================================

  const normalizeCategory = (
    category
  ) => {

    if (!category) {
      return "Other";
    }

    const value =
      String(category)
        .trim()
        .toLowerCase();

    const categoryMap = {

      food: "Food",

      shopping: "Shopping",

      travel: "Travel",

      bills: "Bills",

      "bills & utilities":
        "Bills",

      entertainment:
        "Entertainment",

      health: "Health",

      education: "Education",

      transport: "Transport",

      transportation:
        "Transport",

      other: "Other",

      others: "Other",

    };

    return (
      categoryMap[value] ||
      String(category)
        .trim()
        .replace(
          /\b\w/g,
          (char) =>
            char.toUpperCase()
        )
    );

  };


  // ==========================================================
  // SPENDING BY CATEGORY
  // CURRENT MONTH
  // ==========================================================

  const categoryData = useMemo(() => {

    const totals = {};

    expenses
      .filter((expense) => {

        const date =
          getExpenseDate(expense);

        if (!date) {
          return false;
        }

        return (
          date.getFullYear() ===
            currentYear &&
          date.getMonth() ===
            currentMonth
        );

      })
      .forEach((expense) => {

        const category =
          normalizeCategory(
            expense.category
          );

        if (!totals[category]) {
          totals[category] = 0;
        }

        totals[category] +=
          Number(
            expense.amount || 0
          );

      });

    return Object.entries(
      totals
    )
      .map(
        ([name, value]) => ({
          name,
          value,
        })
      )
      .sort(
        (a, b) =>
          b.value - a.value
      );

  }, [
    expenses,
    currentYear,
    currentMonth,
  ]);


  // ==========================================================
  // FILTERED RECENT TRANSACTIONS
  // ==========================================================

  const filteredTransactions =
    useMemo(() => {

      const search =
        searchTerm
          .trim()
          .toLowerCase();


      const sortedExpenses =
        [...expenses].sort(
          (a, b) => {

            const dateA =
              getExpenseDate(a)
                ?.getTime() || 0;

            const dateB =
              getExpenseDate(b)
                ?.getTime() || 0;

            return (
              dateB - dateA
            );

          }
        );


      if (!search) {

        return sortedExpenses
          .slice(0, 8);

      }


      return sortedExpenses
        .filter((expense) => {

          const title =
            expense.title ||
            expense.description ||
            "";

          const category =
            expense.category ||
            "";

          const payment =
            expense.payment_method ||
            "";

          return (
            title
              .toLowerCase()
              .includes(search) ||

            category
              .toLowerCase()
              .includes(search) ||

            payment
              .toLowerCase()
              .includes(search)
          );

        })
        .slice(0, 8);

    }, [
      expenses,
      searchTerm,
    ]);


  // ==========================================================
  // USER NAME
  // ==========================================================

  const userName =
    user?.name ||
    user?.full_name ||
    user?.username ||
    user?.first_name ||
    "User";


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (

      <DashboardLayout>

        <div className="dashboard-loading">

          <div className="dashboard-loading-card">

            <div className="dashboard-loading-line large" />

            <div className="dashboard-loading-line" />

            <div className="dashboard-loading-grid">

              <div />
              <div />
              <div />
              <div />

            </div>

          </div>

        </div>

      </DashboardLayout>

    );

  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error) {

    return (

      <DashboardLayout>

        <div className="dashboard-error">

          <div className="dashboard-error-card">

            <h2>
              We couldn't load your dashboard
            </h2>

            <p>
              {error}
            </p>

            <button
              onClick={() =>
                window.location.reload()
              }
              className="dashboard-primary-button"
            >
              Try again
            </button>

          </div>

        </div>

      </DashboardLayout>

    );

  }


  // ==========================================================
  // MAIN DASHBOARD
  // ==========================================================

  return (

    <DashboardLayout>

      <div className="dashboard-page">


        {/* ==================================================
            IMPROVED WELCOME HEADER
        =================================================== */}

        <section className="dashboard-page-header">

          {/* ==================================================
              LEFT SIDE
          =================================================== */}

          <div className="dashboard-welcome">

            {/* EYEBROW */}

            <div className="dashboard-eyebrow-row">

              <span className="dashboard-eyebrow-dot">
              </span>

              <p className="dashboard-eyebrow">
                Financial overview
              </p>

            </div>


            {/* TITLE */}

            <h1 className="dashboard-page-title">

              Welcome back,

              <span className="dashboard-user-name">
                {" "}
                {userName}
              </span>

              {/* <span className="dashboard-wave">
                👋
              </span> */}

            </h1>


            {/* SUBTITLE */}

            <p className="dashboard-page-subtitle">
              Here's your financial overview for today.
            </p>

          </div>


          {/* ==================================================
              DATE CARD
          =================================================== */}

          <div className="dashboard-date-card">

            <div className="dashboard-date-icon">

              <CalendarDays
                size={20}
              />

            </div>


            <div className="dashboard-date-content">

              <span className="dashboard-date-label">
                Today
              </span>

              <span className="dashboard-date-value">

                {today.toLocaleDateString(
                  "en-IN",
                  {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                  }
                )}

              </span>

            </div>

          </div>

        </section>


        {/* ==================================================
            SUMMARY CARDS
        =================================================== */}

        <section className="dashboard-summary-grid">


          {/* TOTAL SPENT */}

          <div className="dashboard-summary-card expense-card">

            <div className="summary-card-top">

              <div>

                <p className="summary-card-label">
                  Total Spent
                </p>

                <h2 className="summary-card-value expense-value">
                  {formatCurrency(
                    totalExpense
                  )}
                </h2>

              </div>


              <div className="summary-icon expense-icon">

                <Wallet
                  size={21}
                />

              </div>

            </div>


            <div className="summary-card-bottom">

              <ArrowDownRight
                size={15}
              />

              <span>
                All recorded expenses
              </span>

            </div>

          </div>


          {/* THIS MONTH */}

          <div className="dashboard-summary-card income-card">

            <div className="summary-card-top">

              <div>

                <p className="summary-card-label">
                  This Month
                </p>

                <h2 className="summary-card-value">
                  {formatCurrency(
                    monthlyExpense
                  )}
                </h2>

              </div>


              <div className="summary-icon green-icon">

                <TrendingUp
                  size={21}
                />

              </div>

            </div>


            <div className="summary-card-bottom green-text">

              <TrendingUp
                size={15}
              />

              <span>
                Current month spending
              </span>

            </div>

          </div>


          {/* TODAY */}

          <div className="dashboard-summary-card neutral-card">

            <div className="summary-card-top">

              <div>

                <p className="summary-card-label">
                  Today
                </p>

                <h2 className="summary-card-value">
                  {formatCurrency(
                    todayExpense
                  )}
                </h2>

              </div>


              <div className="summary-icon blue-icon">

                <CalendarDays
                  size={21}
                />

              </div>

            </div>


            <div className="summary-card-bottom">

              <span>
                Expenses recorded today
              </span>

            </div>

          </div>


          {/* TRANSACTIONS */}

          <div className="dashboard-summary-card transaction-card">

            <div className="summary-card-top">

              <div>

                <p className="summary-card-label">
                  Transactions
                </p>

                <h2 className="summary-card-value">
                  {transactionCount}
                </h2>

              </div>


              <div className="summary-icon gold-icon">

                <Receipt
                  size={21}
                />

              </div>

            </div>


            <div className="summary-card-bottom">

              <span>
                Total recorded transactions
              </span>

            </div>

          </div>

        </section>


        {/* ==================================================
            SPENDING BY CATEGORY
        =================================================== */}

        <section className="dashboard-card category-table-card">

          <div className="dashboard-card-header">

            <div>

              <h2 className="dashboard-card-title">
                Spending by Category
              </h2>

              <p className="dashboard-card-description">
                This month's spending
              </p>

            </div>


            <div className="chart-total">

              {formatCurrency(
                monthlyExpense
              )}

            </div>

          </div>


          {categoryData.length === 0 ? (

            <div className="dashboard-empty-chart">

              <Receipt
                size={35}
              />

              <p>
                No expenses this month
              </p>

              <span>
                Add an expense to see
                your category breakdown.
              </span>

            </div>

          ) : (

            <div className="category-table-wrapper">

              <table className="category-table">

                <thead>

                  <tr>

                    <th>
                      Category
                    </th>

                    <th>
                      Amount
                    </th>

                    <th>
                      Percentage
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {categoryData.map(
                    (category, index) => {

                      const percentage =
                        monthlyExpense > 0
                          ? (
                              (
                                category.value /
                                monthlyExpense
                              ) * 100
                            )
                          : 0;


                      return (

                        <tr
                          key={
                            category.name
                          }
                        >

                          <td>

                            <div className="category-name">

                              <span
                                className="category-dot"
                                style={{
                                  backgroundColor:
                                    CATEGORY_COLORS[
                                      index %
                                        CATEGORY_COLORS.length
                                    ],
                                }}
                              />

                              <span>
                                {
                                  category.name
                                }
                              </span>

                            </div>

                          </td>


                          <td>

                            <strong>
                              {formatCurrency(
                                category.value
                              )}
                            </strong>

                          </td>


                          <td>

                            <span>
                              {percentage.toFixed(
                                1
                              )}
                              %
                            </span>

                          </td>

                        </tr>

                      );

                    }
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>


        {/* ==================================================
            RECENT TRANSACTIONS
        =================================================== */}

        <section className="dashboard-card transactions-card">

          <div className="dashboard-card-header">

            <div>

              <h2 className="dashboard-card-title">
                Recent Transactions
              </h2>

              <p className="dashboard-card-description">
                Your latest recorded expenses
              </p>

            </div>


            <div className="transaction-search">

              <Search
                size={16}
              />

              <input
                type="text"
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={(e) =>
                  setSearchTerm(
                    e.target.value
                  )
                }
              />

            </div>

          </div>


          {filteredTransactions.length === 0 ? (

            <div className="dashboard-empty-state">

              <div className="empty-icon">

                <Receipt
                  size={24}
                />

              </div>

              <h3>
                No transactions yet
              </h3>

              <p>
                Your expenses will appear
                here after you add them.
              </p>

            </div>

          ) : (

            <div className="transactions-table-wrapper">

              <table className="transactions-table">

                <thead>

                  <tr>

                    <th>
                      Date
                    </th>

                    <th>
                      Description
                    </th>

                    <th>
                      Category
                    </th>

                    <th>
                      Payment Method
                    </th>

                    <th className="amount-column">
                      Amount
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {filteredTransactions.map(
                    (expense, index) => {

                      const date =
                        getExpenseDate(
                          expense
                        );


                      return (

                        <tr
                          key={
                            expense.id ||
                            expense._id ||
                            index
                          }
                        >

                          <td>

                            {date
                              ? date.toLocaleDateString(
                                  "en-IN",
                                  {
                                    day: "2-digit",
                                    month: "short",
                                    year: "numeric",
                                  }
                                )
                              : "-"}

                          </td>


                          <td>

                            <div className="transaction-title">

                              {expense.title ||
                                expense.description ||
                                "Expense"}

                            </div>

                          </td>


                          <td>

                            <span className="category-badge">

                              {normalizeCategory(
                                expense.category
                              )}

                            </span>

                          </td>


                          <td>

                            <span className="payment-method">

                              {expense.payment_method ||
                                "Not specified"}

                            </span>

                          </td>


                          <td className="amount-column">

                            <strong className="expense-amount">

                              -
                              {formatCurrency(
                                expense.amount
                              )}

                            </strong>

                          </td>

                        </tr>

                      );

                    }
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>

      </div>

    </DashboardLayout>

  );
}


export default Dashboard;