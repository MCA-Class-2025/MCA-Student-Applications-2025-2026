import {
  Eye,
  Pencil,
  Trash2,
  WalletCards,
} from "lucide-react";

import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import { deleteExpense } from "../../services/expenseService";

function ExpenseTable({
  expenses = [],
  refreshExpenses,
}) {
  const navigate = useNavigate();

  // ============================================================
  // DELETE
  // ============================================================

  const handleDelete = async (id) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this expense?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      const response = await deleteExpense(id);

      if (response?.success === false) {
        toast.error(
          response.message || "Delete failed."
        );

        return;
      }

      toast.success(
        response?.message ||
          "Expense deleted successfully."
      );

      if (refreshExpenses) {
        await refreshExpenses();
      }

    } catch (error) {
      console.error(
        "Delete expense error:",
        error
      );

      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Delete failed.";

      toast.error(message);
    }
  };

  // ============================================================
  // CURRENCY
  // ============================================================

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Number(amount || 0));
  };

  // ============================================================
  // DATE
  // ============================================================

  const formatDate = (date) => {
    if (!date) {
      return "-";
    }

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "-";
    }

    return parsedDate.toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };

  // ============================================================
  // EMPTY
  // ============================================================

  if (expenses.length === 0) {
    return (
      <section className="expense-empty-card">

        <div className="expense-empty-icon">
          <WalletCards size={28} />
        </div>

        <h2>
          No Expenses Found
        </h2>

        <p>
          You haven't added any expenses yet.
        </p>

        <button
          type="button"
          onClick={() =>
            navigate("/add-expense")
          }
          className="add-expense-button empty-button"
        >
          + Add Expense
        </button>

      </section>
    );
  }

  return (
    <section className="expense-table-card">

      {/* HEADER */}

      <div className="expense-table-header">

        <div>

          <h2>
            Expense List
          </h2>

          <p>
            Your latest recorded expenses
          </p>

        </div>

        <div className="expense-count">
          {expenses.length} records
        </div>

      </div>

      {/* TABLE */}

      <div className="expense-table-scroll">

        <table className="expense-table">

          <thead>

            <tr>
              <th>Title</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Payment Method</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>

          </thead>

          <tbody>

            {expenses.map((expense) => (

              <tr key={expense._id}>

                {/* TITLE */}

                <td>

                  <div className="expense-title-cell">

                    <p
                      title={expense.title}
                    >
                      {expense.title}
                    </p>

                    {expense.notes && (
                      <span
                        title={expense.notes}
                      >
                        {expense.notes}
                      </span>
                    )}

                  </div>

                </td>

                {/* CATEGORY */}

                <td>

                  <span className="category-badge">
                    {expense.category}
                  </span>

                </td>

                {/* AMOUNT */}

                <td>

                  <span className="expense-amount">
                    {formatCurrency(
                      expense.amount
                    )}
                  </span>

                </td>

                {/* PAYMENT */}

                <td>

                  <span className="payment-method">
                    {expense.payment_method}
                  </span>

                </td>

                {/* DATE */}

                <td>

                  <span className="expense-date">
                    {formatDate(
                      expense.date
                    )}
                  </span>

                </td>

                {/* ACTIONS */}

                <td>

                  <div className="expense-actions">

                    <button
                      type="button"
                      title="View Expense"
                      onClick={() =>
                        navigate(
                          `/expense-details/${expense._id}`
                        )
                      }
                      className="expense-action view"
                    >
                      <Eye size={17} />
                    </button>

                    <button
                      type="button"
                      title="Edit Expense"
                      onClick={() =>
                        navigate(
                          `/edit-expense/${expense._id}`
                        )
                      }
                      className="expense-action edit"
                    >
                      <Pencil size={17} />
                    </button>

                    <button
                      type="button"
                      title="Delete Expense"
                      onClick={() =>
                        handleDelete(
                          expense._id
                        )
                      }
                      className="expense-action delete"
                    >
                      <Trash2 size={17} />
                    </button>

                  </div>

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </section>
  );
}

export default ExpenseTable;