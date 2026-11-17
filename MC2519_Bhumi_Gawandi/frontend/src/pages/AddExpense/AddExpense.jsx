import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { PlusCircle, Save } from "lucide-react";

import DashboardNavbar from "../../components/dashboard/DashboardNavbar";
import Sidebar from "../../components/dashboard/Sidebar";

import { createExpense } from "../../services/expenseService";
import { getCategories } from "../../services/categoryService";

function AddExpense() {
  const navigate = useNavigate();

  // ============================================================
  // FORM STATE
  // ============================================================

  const [formData, setFormData] = useState({
    title: "",
    amount: "",
    category: "",
    payment_method: "UPI",
    date: "",
    notes: "",
  });

  // ============================================================
  // CATEGORIES
  // ============================================================

  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] =
    useState(true);

  // ============================================================
  // GENERAL LOADING
  // ============================================================

  const [loading, setLoading] = useState(false);

  // ============================================================
  // LOAD CATEGORIES
  // ============================================================

  useEffect(() => {
    const loadCategories = async () => {
      try {
        setCategoriesLoading(true);

        const data = await getCategories();

        const categoryList =
          Array.isArray(data) ? data : [];

        setCategories(categoryList);

        if (categoryList.length > 0) {
          setFormData((previous) => ({
            ...previous,
            category:
              previous.category ||
              categoryList[0].name,
          }));
        }
      } catch (error) {
        console.error(
          "Category loading error:",
          error
        );

        if (
          error?.response?.status === 401
        ) {
          toast.error(
            "Session expired. Please login again."
          );

          localStorage.removeItem("token");
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");

          navigate("/login");

          return;
        }

        toast.error(
          "Unable to load categories."
        );
      } finally {
        setCategoriesLoading(false);
      }
    };

    loadCategories();
  }, [navigate]);

  // ============================================================
  // HANDLE INPUT CHANGE
  // ============================================================

  const handleChange = (e) => {
    const {
      name,
      value,
    } = e.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // ============================================================
  // SUBMIT EXPENSE
  // ============================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    // ==========================================================
    // VALIDATION
    // ==========================================================

    if (!formData.title.trim()) {
      toast.error(
        "Please enter an expense title."
      );
      return;
    }

    if (
      !formData.amount ||
      Number(formData.amount) <= 0
    ) {
      toast.error(
        "Please enter a valid amount."
      );
      return;
    }

    if (!formData.category) {
      toast.error(
        "Please select a category."
      );
      return;
    }

    if (!formData.payment_method) {
      toast.error(
        "Please select a payment method."
      );
      return;
    }

    if (!formData.date) {
      toast.error(
        "Please select an expense date."
      );
      return;
    }

    // ==========================================================
    // SAVE
    // ==========================================================

    try {
      setLoading(true);

      const expenseData = {
        title:
          formData.title.trim(),

        amount:
          Number(formData.amount),

        category:
          formData.category,

        payment_method:
          formData.payment_method,

        date:
          new Date(
            `${formData.date}T00:00:00`
          ).toISOString(),

        notes:
          formData.notes.trim(),
      };

      console.log(
        "Sending expense to backend:",
        expenseData
      );

      // ========================================================
      // API
      // ========================================================

      const response =
        await createExpense(
          expenseData
        );

      console.log(
        "Backend response:",
        response
      );

      // ========================================================
      // ERROR RESPONSE
      // ========================================================

      if (
        response?.success === false
      ) {
        toast.error(
          response.message ||
          "Failed to add expense."
        );

        return;
      }

      // ========================================================
      // SUCCESS
      // ========================================================

      toast.success(
        response?.message ||
        "Expense added successfully!"
      );

      // ========================================================
      // RESET FORM
      // ========================================================

      setFormData({
        title: "",
        amount: "",
        category:
          categories.length > 0
            ? categories[0].name
            : "",
        payment_method: "UPI",
        date: "",
        notes: "",
      });

      // ========================================================
      // NAVIGATE TO EXPENSES
      // ========================================================

      setTimeout(() => {
        navigate("/expenses");
      }, 700);

    } catch (error) {
      console.error(
        "Create expense error:",
        error
      );

      if (error?.response) {
        console.error(
          "Status:",
          error.response.status
        );

        console.error(
          "Response:",
          error.response.data
        );

        const detail =
          error.response.data?.detail;

        if (Array.isArray(detail)) {
          toast.error(
            detail[0]?.msg ||
            "Invalid expense data."
          );

        } else if (
          typeof detail === "string"
        ) {
          toast.error(detail);

        } else {
          toast.error(
            `Failed to add expense. Server returned ${error.response.status}.`
          );
        }

      } else if (error?.request) {
        toast.error(
          "Backend server is not responding."
        );

      } else {
        toast.error(
          "Something went wrong while adding the expense."
        );
      }

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
  // UI
  // ============================================================

  return (
    <div className="add-expense-page">

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="dashboard-sidebar">
        <Sidebar />
      </aside>


      {/* ======================================================
          MAIN AREA
      ====================================================== */}

      <div className="dashboard-main">

        {/* ====================================================
            NAVBAR
        ==================================================== */}

        <DashboardNavbar />


        {/* ====================================================
            CONTENT
        ==================================================== */}

        <main className="add-expense-content">

          <div className="add-expense-container">

            {/* ==================================================
                PAGE HEADER
            ================================================== */}

            <section className="add-expense-header">

              <div>

                <p className="add-expense-eyebrow">
                  Financial management
                </p>

                <div className="add-expense-title-row">

                  {/* ADD EXPENSE ICON */}

                  <div
                    className="add-expense-title-icon"
                    aria-hidden="true"
                  >
                    <PlusCircle size={32} />
                  </div>

                  <h1>
                    Add Expense
                  </h1>

                </div>

                <p className="add-expense-subtitle">
                  Record a new expense and keep your
                  financial records updated.
                </p>

              </div>

            </section>


            {/* ==================================================
                FORM CARD
            ================================================== */}

            <section className="add-expense-card">

              {/* =================================================
                  CARD HEADER
              ================================================= */}

              <div className="add-expense-card-header">

                <div>

                  <h2>
                    Expense Information
                  </h2>

                  <p>
                    Enter the details of your expense below.
                  </p>

                </div>

                <div className="add-expense-status">
                  New Expense
                </div>

              </div>


              {/* =================================================
                  FORM
              ================================================= */}

              <form
                onSubmit={handleSubmit}
                className="add-expense-form"
              >

                {/* =================================================
                    FORM GRID
                ================================================= */}

                <div className="add-form-grid">

                  {/* =================================================
                      TITLE
                  ================================================= */}

                  <div className="add-field">

                    <label htmlFor="title">
                      Expense Title
                      <span>*</span>
                    </label>

                    <input
                      id="title"
                      name="title"
                      type="text"
                      value={formData.title}
                      onChange={handleChange}
                      placeholder="e.g. Grocery shopping"
                      disabled={loading}
                    />

                  </div>


                  {/* =================================================
                      AMOUNT
                  ================================================= */}

                  <div className="add-field">

                    <label htmlFor="amount">
                      Amount
                      <span>*</span>
                    </label>

                    <div className="add-amount-wrapper">

                      <span>
                        ₹
                      </span>

                      <input
                        id="amount"
                        name="amount"
                        type="number"
                        min="0"
                        step="0.01"
                        value={formData.amount}
                        onChange={handleChange}
                        placeholder="0.00"
                        disabled={loading}
                      />

                    </div>

                  </div>


                  {/* =================================================
                      CATEGORY
                  ================================================= */}

                  <div className="add-field">

                    <label htmlFor="category">
                      Category
                      <span>*</span>
                    </label>

                    <select
                      id="category"
                      name="category"
                      value={formData.category}
                      onChange={handleChange}
                      disabled={
                        categoriesLoading ||
                        categories.length === 0 ||
                        loading
                      }
                    >

                      {categoriesLoading ? (

                        <option value="">
                          Loading categories...
                        </option>

                      ) : categories.length === 0 ? (

                        <option value="">
                          No categories available
                        </option>

                      ) : (

                        categories.map(
                          (category) => (
                            <option
                              key={category._id}
                              value={category.name}
                            >
                              {category.name}
                            </option>
                          )
                        )

                      )}

                    </select>

                    {!categoriesLoading &&
                      categories.length === 0 && (
                        <p className="add-category-warning">
                          Please create a category first
                          from the Categories page.
                        </p>
                      )}

                  </div>


                  {/* =================================================
                      PAYMENT METHOD
                  ================================================= */}

                  <div className="add-field">

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


                  {/* =================================================
                      DATE
                  ================================================= */}

                  <div className="add-field">

                    <label htmlFor="date">
                      Expense Date
                      <span>*</span>
                    </label>

                    <input
                      id="date"
                      name="date"
                      type="date"
                      value={formData.date}
                      onChange={handleChange}
                      disabled={loading}
                    />

                  </div>

                </div>


                {/* =================================================
                    NOTES
                ================================================= */}

                <div className="add-field add-notes">

                  <label htmlFor="notes">
                    Notes
                  </label>

                  <textarea
                    id="notes"
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    rows={5}
                    placeholder="Add any additional notes about this expense..."
                    disabled={loading}
                  />

                  <small>
                    Optional
                  </small>

                </div>


                {/* =================================================
                    FOOTER ACTIONS
                ================================================= */}

                <div className="add-expense-actions">

                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={loading}
                    className="add-cancel-button"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={
                      loading ||
                      categoriesLoading ||
                      categories.length === 0
                    }
                    className="add-save-button"
                  >

                    {loading ? (
                      <>
                        <span className="add-button-loader"></span>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save size={18} />
                        Save Expense
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

export default AddExpense;