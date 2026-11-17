import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import DashboardNavbar from "../../components/dashboard/DashboardNavbar";
import Sidebar from "../../components/dashboard/Sidebar";

import ExpenseTable from "../../components/expenses/ExpenseTable";
import SearchBar from "../../components/expenses/SearchBar";
import ExpenseFilters from "../../components/expenses/ExpenseFilters";

import { getExpenses } from "../../services/expenseService";

function Expenses() {
  const navigate = useNavigate();

  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  const [searchTerm, setSearchTerm] = useState("");
  const [category, setCategory] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");

  // ============================================================
  // LOAD EXPENSES
  // ============================================================

  const loadExpenses = async () => {
    try {
      setLoading(true);

      const data = await getExpenses();

      console.log("Expenses API response:", data);

      if (Array.isArray(data)) {
        setExpenses(data);
      } else {
        setExpenses([]);
      }
    } catch (error) {
      console.error("Load expenses error:", error);

      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to load expenses.";

      toast.error(message);

      setExpenses([]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOAD WHEN PAGE OPENS
  // ============================================================

  useEffect(() => {
    loadExpenses();
  }, []);

  // ============================================================
  // CLEAR FILTERS
  // ============================================================

  const clearFilters = () => {
    setSearchTerm("");
    setCategory("");
    setPaymentMethod("");
  };

  // ============================================================
  // FILTER EXPENSES
  // ============================================================

  const filteredExpenses = expenses.filter((expense) => {
    const title = expense.title?.toLowerCase() || "";

    const search = searchTerm.toLowerCase().trim();

    const matchesSearch = title.includes(search);

    const matchesCategory =
      category === "" ||
      expense.category === category;

    const matchesPayment =
      paymentMethod === "" ||
      expense.payment_method === paymentMethod;

    return (
      matchesSearch &&
      matchesCategory &&
      matchesPayment
    );
  });

  // ============================================================
  // TOTAL
  // ============================================================

  const totalAmount = filteredExpenses.reduce(
    (total, expense) =>
      total + Number(expense.amount || 0),
    0
  );

  return (
    <div className="expenses-page">

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="dashboard-sidebar">
        <Sidebar />
      </aside>

      {/* ======================================================
          RIGHT SIDE
      ====================================================== */}

      <div className="dashboard-main">

        {/* ====================================================
            NAVBAR
        ==================================================== */}

        <DashboardNavbar />

        {/* ====================================================
            CONTENT
        ==================================================== */}

        <main className="expenses-content">

          {/* ==================================================
              PAGE HEADER
          ================================================== */}

          <section className="expenses-header">

            <div>

              <p className="expenses-eyebrow">
                Financial management
              </p>

              <h1 className="expenses-title">
                Expenses
              </h1>

              <p className="expenses-subtitle">
                Manage and track all your expenses in one place.
              </p>

            </div>

            <button
              type="button"
              onClick={() => navigate("/add-expense")}
              className="add-expense-button"
            >
              <span className="add-expense-icon">
                +
              </span>

              Add Expense
            </button>

          </section>

          {/* ==================================================
              SUMMARY
          ================================================== */}

          <section className="expense-mini-summary">

            <div className="expense-mini-card">

              <div>
                <p className="mini-label">
                  Total Records
                </p>

                <p className="mini-value">
                  {filteredExpenses.length}
                </p>
              </div>

              <div className="mini-icon green">
                #
              </div>

            </div>

            <div className="expense-mini-card">

              <div>
                <p className="mini-label">
                  Total Amount
                </p>

                <p className="mini-value green-text">
                  ₹{totalAmount.toLocaleString("en-IN")}
                </p>
              </div>

              <div className="mini-icon light-green">
                ₹
              </div>

            </div>

            <div className="expense-mini-card">

              <div>
                <p className="mini-label">
                  Showing
                </p>

                <p className="mini-value">
                  {filteredExpenses.length} expenses
                </p>
              </div>

              <div className="mini-icon light">
                ✓
              </div>

            </div>

          </section>

          {/* ==================================================
              SEARCH & FILTER
          ================================================== */}

          <section className="expense-filter-card">

            <div className="filter-heading">

              <div>

                <h2>
                  Search & Filter
                </h2>

                <p>
                  Find an expense by title, category or payment method.
                </p>

              </div>

            </div>

            <div className="expense-filter-layout">

              <div className="expense-search-wrapper">

                <SearchBar
                  searchTerm={searchTerm}
                  setSearchTerm={setSearchTerm}
                />

              </div>

              <div className="expense-filters-wrapper">

                <ExpenseFilters
                  category={category}
                  setCategory={setCategory}
                  paymentMethod={paymentMethod}
                  setPaymentMethod={setPaymentMethod}
                  clearFilters={clearFilters}
                />

              </div>

            </div>

          </section>

          {/* ==================================================
              TABLE
          ================================================== */}

          {loading ? (

            <section className="expense-loading-card">

              <div className="expense-loader"></div>

              <h3>
                Loading expenses
              </h3>

              <p>
                Fetching your latest expenses...
              </p>

            </section>

          ) : (

            <ExpenseTable
              expenses={filteredExpenses}
              refreshExpenses={loadExpenses}
            />

          )}

        </main>

      </div>

    </div>
  );
}

export default Expenses;