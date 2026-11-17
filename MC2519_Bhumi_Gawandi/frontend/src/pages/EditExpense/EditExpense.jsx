import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, Save } from "lucide-react";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import {
  getExpenseById,
  updateExpense,
} from "../../services/expenseService";

function EditExpense() {
  const { id } = useParams();
  const navigate = useNavigate();

  // ============================================================
  // STATES
  // ============================================================

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  const [formData, setFormData] = useState({
    title: "",
    amount: "",
    category: "Food",
    payment_method: "UPI",
    date: "",
    notes: "",
  });

  // ============================================================
  // LOAD EXPENSE
  // ============================================================

  useEffect(() => {
    if (!id) {
      toast.error("Invalid expense ID.");
      navigate("/expenses");
      return;
    }

    loadExpense();
  }, [id]);

  const loadExpense = async () => {
    try {
      setFetching(true);

      const data = await getExpenseById(id);

      console.log("Edit expense API response:", data);

      if (data?.success === false) {
        toast.error(
          data.message || "Expense not found."
        );

        navigate("/expenses");
        return;
      }

      if (!data) {
        toast.error("Expense data not found.");
        navigate("/expenses");
        return;
      }

      // ========================================================
      // DATE FORMAT
      // ========================================================

      let formattedDate = "";

      if (data.date) {
        const parsedDate = new Date(data.date);

        if (!Number.isNaN(parsedDate.getTime())) {
          formattedDate = parsedDate
            .toISOString()
            .split("T")[0];
        }
      }

      // ========================================================
      // SET FORM DATA
      // ========================================================

      setFormData({
        title: data.title || "",

        amount:
          data.amount !== undefined &&
          data.amount !== null
            ? String(data.amount)
            : "",

        category:
          data.category || "Food",

        payment_method:
          data.payment_method || "UPI",

        date: formattedDate,

        notes: data.notes || "",
      });

    } catch (error) {
      console.error(
        "Load expense error:",
        error
      );

      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to load expense.";

      toast.error(message);

      navigate("/expenses");

    } finally {
      setFetching(false);
    }
  };

  // ============================================================
  // HANDLE CHANGE
  // ============================================================

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  // ============================================================
  // VALIDATION
  // ============================================================

  const validateForm = () => {
    if (!formData.title.trim()) {
      toast.error(
        "Please enter expense title."
      );

      return false;
    }

    if (!formData.amount) {
      toast.error(
        "Please enter expense amount."
      );

      return false;
    }

    if (Number(formData.amount) <= 0) {
      toast.error(
        "Amount must be greater than zero."
      );

      return false;
    }

    if (!formData.category) {
      toast.error(
        "Please select a category."
      );

      return false;
    }

    if (!formData.payment_method) {
      toast.error(
        "Please select a payment method."
      );

      return false;
    }

    if (!formData.date) {
      toast.error(
        "Please select expense date."
      );

      return false;
    }

    return true;
  };

  // ============================================================
  // UPDATE EXPENSE
  // ============================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loading) {
      return;
    }

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      const expenseData = {
        title: formData.title.trim(),

        amount: Number(
          formData.amount
        ),

        category: formData.category,

        payment_method:
          formData.payment_method,

        date: new Date(
          `${formData.date}T00:00:00`
        ).toISOString(),

        notes: formData.notes.trim(),
      };

      console.log(
        "Updating expense:",
        expenseData
      );

      const response =
        await updateExpense(
          id,
          expenseData
        );

      console.log(
        "Update expense response:",
        response
      );

      if (response?.success === false) {
        toast.error(
          response.message ||
            "Unable to update expense."
        );

        return;
      }

      toast.success(
        response?.message ||
          "Expense updated successfully."
      );

      setTimeout(() => {
        navigate("/expenses");
      }, 700);

    } catch (error) {
      console.error(
        "Update expense error:",
        error
      );

      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Update failed.";

      toast.error(message);

    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // CANCEL
  // ============================================================

  const handleCancel = () => {
    if (loading) {
      return;
    }

    navigate("/expenses");
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (fetching) {
    return (
      <div className="edit-expense-page">

        <aside className="dashboard-sidebar">
          <Sidebar />
        </aside>

        <div className="dashboard-main">

          <DashboardNavbar />

          <main className="edit-expense-content">

            <div className="edit-expense-loading">

              <div className="edit-expense-loader"></div>

              <h2>
                Loading expense...
              </h2>

              <p>
                Please wait while we load the expense details.
              </p>

            </div>

          </main>

        </div>

      </div>
    );
  }

  // ============================================================
  // MAIN UI
  // ============================================================

  return (
    <div className="edit-expense-page">

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="dashboard-sidebar">
        <Sidebar />
      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <div className="dashboard-main">

        {/* ====================================================
            NAVBAR
        ==================================================== */}

        <DashboardNavbar />


        {/* ====================================================
            CONTENT
        ==================================================== */}

        <main className="edit-expense-content">

          <div className="edit-expense-container">

            {/* ==================================================
                HEADER
            ================================================== */}

            <section className="edit-expense-header">

              <div>

                <p className="edit-expense-eyebrow">
                  Financial management
                </p>

                <div className="edit-expense-title-row">

                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={loading}
                    className="edit-back-button"
                    title="Back to Expenses"
                  >
                    <ArrowLeft size={19} />
                  </button>

                  <h1>
                    Edit Expense
                  </h1>

                </div>

                <p className="edit-expense-subtitle">
                  Update your expense details and keep your records accurate.
                </p>

              </div>

            </section>


            {/* ==================================================
                FORM CARD
            ================================================== */}

            <section className="edit-expense-card">

              {/* CARD HEADER */}

              <div className="edit-expense-card-header">

                <div>

                  <h2>
                    Expense Information
                  </h2>

                  <p>
                    Modify the details below and save your changes.
                  </p>

                </div>

                <div className="edit-status">
                  Editing
                </div>

              </div>


              {/* =================================================
                  FORM
              ================================================= */}

              <form
                onSubmit={handleSubmit}
                className="edit-expense-form"
              >

                {/* =================================================
                    BASIC INFORMATION
                ================================================= */}

                <div className="edit-form-grid">

                  {/* TITLE */}

                  <div className="edit-field">

                    <label htmlFor="title">
                      Expense Title
                      <span>*</span>
                    </label>

                    <input
                      id="title"
                      type="text"
                      name="title"
                      value={formData.title}
                      onChange={handleChange}
                      placeholder="Enter expense title"
                      disabled={loading}
                    />

                  </div>


                  {/* AMOUNT */}

                  <div className="edit-field">

                    <label htmlFor="amount">
                      Amount
                      <span>*</span>
                    </label>

                    <div className="edit-amount-wrapper">

                      <span>
                        ₹
                      </span>

                      <input
                        id="amount"
                        type="number"
                        name="amount"
                        min="0"
                        step="0.01"
                        value={formData.amount}
                        onChange={handleChange}
                        placeholder="0.00"
                        disabled={loading}
                      />

                    </div>

                  </div>


                  {/* CATEGORY */}

                  <div className="edit-field">

                    <label htmlFor="category">
                      Category
                      <span>*</span>
                    </label>

                    <select
                      id="category"
                      name="category"
                      value={formData.category}
                      onChange={handleChange}
                      disabled={loading}
                    >

                      <option value="Food">
                        Food
                      </option>

                      <option value="Travel">
                        Travel
                      </option>

                      <option value="Shopping">
                        Shopping
                      </option>

                      <option value="Bills">
                        Bills
                      </option>

                      <option value="Entertainment">
                        Entertainment
                      </option>

                      <option value="Health">
                        Health
                      </option>

                      <option value="Education">
                        Education
                      </option>

                      <option value="Others">
                        Others
                      </option>

                    </select>

                  </div>


                  {/* PAYMENT */}

                  <div className="edit-field">

                    <label htmlFor="payment_method">
                      Payment Method
                      <span>*</span>
                    </label>

                    <select
                      id="payment_method"
                      name="payment_method"
                      value={
                        formData.payment_method
                      }
                      onChange={handleChange}
                      disabled={loading}
                    >

                      <option value="UPI">
                        UPI
                      </option>

                      <option value="Cash">
                        Cash
                      </option>

                      <option value="Credit Card">
                        Credit Card
                      </option>

                      <option value="Debit Card">
                        Debit Card
                      </option>

                      <option value="Net Banking">
                        Net Banking
                      </option>

                    </select>

                  </div>


                  {/* DATE */}

                  <div className="edit-field">

                    <label htmlFor="date">
                      Expense Date
                      <span>*</span>
                    </label>

                    <input
                      id="date"
                      type="date"
                      name="date"
                      value={formData.date}
                      onChange={handleChange}
                      disabled={loading}
                    />

                  </div>

                </div>


                {/* =================================================
                    NOTES
                ================================================= */}

                <div className="edit-field edit-notes">

                  <label htmlFor="notes">
                    Notes
                  </label>

                  <textarea
                    id="notes"
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    rows={5}
                    placeholder="Add additional notes about this expense..."
                    disabled={loading}
                  />

                  <small>
                    Optional
                  </small>

                </div>


                {/* =================================================
                    ACTIONS
                ================================================= */}

                <div className="edit-expense-actions">

                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={loading}
                    className="edit-cancel-button"
                  >
                    Cancel
                  </button>


                  <button
                    type="submit"
                    disabled={loading}
                    className="edit-save-button"
                  >

                    {loading ? (
                      <>
                        <span className="edit-button-loader"></span>
                        Updating...
                      </>
                    ) : (
                      <>
                        <Save size={18} />
                        Update Expense
                      </>
                    )}

                  </button>

                </div>

              </form>

            </section>

          </div>

        </main>

      </div>

    </div>
  );
}

export default EditExpense;