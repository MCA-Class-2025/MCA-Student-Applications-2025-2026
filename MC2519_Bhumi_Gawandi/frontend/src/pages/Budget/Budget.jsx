import { useEffect, useState } from "react";

import {
  Plus,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  ArrowUpCircle,
  X,
  ShieldCheck,
  Wallet,
} from "lucide-react";

import toast from "react-hot-toast";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import {
  getBudgets,
  createBudget,
  deleteBudget,
  requestBudgetUpgrade,
  verifyBudgetUpgrade,
} from "../../services/budgetService";


function Budget() {

  // ============================================================
  // STATE
  // ============================================================

  const [budgets, setBudgets] = useState([]);

  const [loading, setLoading] = useState(true);

  const [showCreateModal, setShowCreateModal] =
    useState(false);

  const [showUpgradeModal, setShowUpgradeModal] =
    useState(false);

  const [selectedBudget, setSelectedBudget] =
    useState(null);

  const [creating, setCreating] =
    useState(false);

  const [sendingOtp, setSendingOtp] =
    useState(false);

  const [verifyingOtp, setVerifyingOtp] =
    useState(false);


  // ============================================================
  // CREATE FORM
  // ============================================================

  const [createForm, setCreateForm] = useState({
    category: "Food",
    amount: "",
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
  });


  // ============================================================
  // UPGRADE FORM
  // ============================================================

  const [upgradeAmount, setUpgradeAmount] =
    useState("");

  const [otp, setOtp] =
    useState("");

  const [otpSent, setOtpSent] =
    useState(false);


  // ============================================================
  // LOAD BUDGETS
  // ============================================================

  useEffect(() => {
    loadBudgets();
  }, []);


  const loadBudgets = async () => {

    try {

      setLoading(true);

      const data = await getBudgets();

      setBudgets(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (error) {

      console.error(
        "Load budgets error:",
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

        window.location.href = "/login";

        return;
      }

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to load budgets."
      );

    } finally {

      setLoading(false);

    }
  };


  // ============================================================
  // CREATE BUDGET
  // ============================================================

  const handleCreateBudget = async (e) => {

    e.preventDefault();

    if (!createForm.amount) {

      toast.error(
        "Please enter a budget amount."
      );

      return;
    }

    if (
      Number(createForm.amount) <= 0
    ) {

      toast.error(
        "Budget amount must be greater than 0."
      );

      return;
    }

    try {

      setCreating(true);

      const response =
        await createBudget({
          category:
            createForm.category,

          amount:
            Number(createForm.amount),

          month:
            Number(createForm.month),

          year:
            Number(createForm.year),
        });


      if (
        response?.success === false
      ) {

        toast.error(
          response.message ||
          "Unable to create budget."
        );

        return;
      }


      toast.success(
        response?.message ||
        "Budget created successfully."
      );


      setShowCreateModal(false);

      setCreateForm({
        category: "Food",
        amount: "",
        month:
          new Date().getMonth() + 1,
        year:
          new Date().getFullYear(),
      });


      await loadBudgets();

    } catch (error) {

      console.error(
        "Create budget error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to create budget."
      );

    } finally {

      setCreating(false);

    }
  };


  // ============================================================
  // DELETE BUDGET
  // ============================================================

  const handleDelete = async (budgetId) => {

    const confirmed =
      window.confirm(
        "Are you sure you want to delete this budget?"
      );

    if (!confirmed) {
      return;
    }

    try {

      const response =
        await deleteBudget(
          budgetId
        );


      if (
        response?.success === false
      ) {

        toast.error(
          response.message ||
          "Unable to delete budget."
        );

        return;
      }


      toast.success(
        "Budget deleted successfully."
      );

      await loadBudgets();

    } catch (error) {

      console.error(
        "Delete budget error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
        "Unable to delete budget."
      );

    }
  };


  // ============================================================
  // OPEN UPGRADE MODAL
  // ============================================================

  const openUpgradeModal = (budget) => {

    setSelectedBudget(
      budget
    );

    setUpgradeAmount("");

    setOtp("");

    setOtpSent(false);

    setShowUpgradeModal(true);
  };


  // ============================================================
  // CLOSE UPGRADE MODAL
  // ============================================================

  const closeUpgradeModal = () => {

    setShowUpgradeModal(false);

    setSelectedBudget(null);

    setUpgradeAmount("");

    setOtp("");

    setOtpSent(false);
  };


  // ============================================================
  // REQUEST UPGRADE OTP
  // ============================================================

  const handleRequestUpgrade = async () => {

    if (!selectedBudget) {
      return;
    }

    if (!upgradeAmount) {

      toast.error(
        "Please enter the new budget amount."
      );

      return;
    }

    const newAmount =
      Number(upgradeAmount);

    if (
      newAmount <=
      Number(selectedBudget.amount)
    ) {

      toast.error(
        "New budget must be greater than the current budget."
      );

      return;
    }


    try {

      setSendingOtp(true);

      const response =
        await requestBudgetUpgrade(
          selectedBudget._id,
          {
            new_amount:
              newAmount,
          }
        );


      if (
        response?.success === false
      ) {

        toast.error(
          response.message ||
          "Unable to send OTP."
        );

        return;
      }


      setOtpSent(true);

      toast.success(
        "OTP sent to your registered email."
      );

    } catch (error) {

      console.error(
        "Request upgrade error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to send OTP."
      );

    } finally {

      setSendingOtp(false);

    }
  };


  // ============================================================
  // VERIFY OTP
  // ============================================================

  const handleVerifyOtp = async () => {

    if (!selectedBudget) {
      return;
    }

    if (!otp) {

      toast.error(
        "Please enter the OTP."
      );

      return;
    }

    if (otp.length !== 6) {

      toast.error(
        "OTP must contain 6 digits."
      );

      return;
    }


    try {

      setVerifyingOtp(true);

      const response =
        await verifyBudgetUpgrade(
          selectedBudget._id,
          {
            otp: otp,
          }
        );


      if (
        response?.success === false
      ) {

        toast.error(
          response.message ||
          "Invalid OTP."
        );

        return;
      }


      toast.success(
        "Budget increased successfully."
      );

      closeUpgradeModal();

      await loadBudgets();

    } catch (error) {

      console.error(
        "Verify OTP error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "OTP verification failed."
      );

    } finally {

      setVerifyingOtp(false);

    }
  };


  // ============================================================
  // CURRENCY
  // ============================================================

  const formatCurrency = (amount) => {

    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
      }
    ).format(
      Number(amount || 0)
    );
  };


  // ============================================================
  // MONTH
  // ============================================================

  const getMonthName = (month) => {

    const months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];

    return (
      months[
        Number(month) - 1
      ] || "-"
    );
  };


  // ============================================================
  // TOTALS
  // ============================================================

  const totalBudget =
    budgets.reduce(
      (sum, budget) =>
        sum +
        Number(
          budget.amount || 0
        ),
      0
    );


  const totalSpent =
    budgets.reduce(
      (sum, budget) =>
        sum +
        Number(
          budget.spent || 0
        ),
      0
    );


  const exceededCount =
    budgets.filter(
      (budget) =>
        budget.is_exceeded
    ).length;


  const remaining =
    totalBudget -
    totalSpent;


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {

    return (

      <div className="dashboard-layout">

        <aside className="dashboard-sidebar">
          <Sidebar />
        </aside>

        <div className="dashboard-main">

          <DashboardNavbar />

          <main className="dashboard-content">

            <div className="budget-loading">

              <div className="budget-spinner" />

              <p>
                Loading budgets...
              </p>

            </div>

          </main>

        </div>

      </div>
    );
  }


  // ============================================================
  // UI
  // ============================================================

  return (

    <div className="dashboard-layout">

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

        <main className="dashboard-content">

          <div className="budget-page">


            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="budget-page-header">

              <div>

                <div className="budget-title-row">

                  <div className="budget-title-icon">

                    <Target
                      size={23}
                      strokeWidth={2}
                    />

                  </div>

                  <h1>
                    Budget
                  </h1>

                </div>

                <p>
                  Set spending limits and keep
                  your expenses under control.
                </p>

              </div>


              <button
                type="button"
                onClick={() =>
                  setShowCreateModal(true)
                }
                className="budget-create-button"
              >

                <Plus size={18} />

                Create Budget

              </button>

            </div>


            {/* ==================================================
                SUMMARY CARDS
            ================================================== */}

            <div className="budget-summary-grid">


              {/* Total Budget */}

              <div className="budget-summary-card">

                <div>

                  <p>
                    Total Budget
                  </p>

                  <h2>
                    {formatCurrency(
                      totalBudget
                    )}
                  </h2>

                </div>

                <div className="budget-summary-icon green">

                  <Wallet size={20} />

                </div>

              </div>


              {/* Total Spent */}

              <div className="budget-summary-card">

                <div>

                  <p>
                    Total Spent
                  </p>

                  <h2 className="red">
                    {formatCurrency(
                      totalSpent
                    )}
                  </h2>

                </div>

                <div className="budget-summary-icon red">

                  <TrendingUp size={20} />

                </div>

              </div>


              {/* Remaining */}

              <div className="budget-summary-card">

                <div>

                  <p>
                    Remaining
                  </p>

                  <h2
                    className={
                      remaining < 0
                        ? "red"
                        : "green-text"
                    }
                  >
                    {formatCurrency(
                      remaining
                    )}
                  </h2>

                </div>

                <div className="budget-summary-icon blue">

                  <Wallet size={20} />

                </div>

              </div>


              {/* Exceeded */}

              <div className="budget-summary-card">

                <div>

                  <p>
                    Budgets Exceeded
                  </p>

                  <h2 className="orange">
                    {exceededCount}
                  </h2>

                </div>

                <div className="budget-summary-icon orange">

                  <AlertTriangle size={20} />

                </div>

              </div>

            </div>


            {/* ==================================================
                BUDGET LIST
            ================================================== */}

            {budgets.length === 0 ? (

              <div className="budget-empty">

                <div className="budget-empty-icon">

                  <Target size={32} />

                </div>

                <h2>
                  No budgets yet
                </h2>

                <p>
                  Create your first category budget
                  to start tracking your spending.
                </p>

                <button
                  type="button"
                  onClick={() =>
                    setShowCreateModal(true)
                  }
                  className="budget-create-button"
                >
                  <Plus size={18} />
                  Create Your First Budget
                </button>

              </div>

            ) : (

              <div className="budget-list">

                {budgets.map((budget) => {

                  const amount =
                    Number(
                      budget.amount || 0
                    );

                  const spent =
                    Number(
                      budget.spent || 0
                    );

                  const percentage =
                    amount > 0
                      ? Math.min(
                          100,
                          Math.max(
                            0,
                            (spent / amount) *
                              100
                          )
                        )
                      : 0;

                  const isExceeded =
                    spent > amount;

                  const remainingAmount =
                    amount - spent;

                  const displayPercentage =
                    amount > 0
                      ? Math.round(
                          (spent / amount) *
                            100
                        )
                      : 0;


                  return (

                    <div
                      key={budget._id}
                      className="budget-card"
                    >

                      {/* Card Header */}

                      <div className="budget-card-header">

                        <div className="budget-card-title">

                          <div
                            className={
                              isExceeded
                                ? "budget-category-icon danger"
                                : "budget-category-icon"
                            }
                          >

                            {isExceeded ? (
                              <AlertTriangle size={21} />
                            ) : (
                              <Target size={21} />
                            )}

                          </div>

                          <div>

                            <h3>
                              {budget.category}
                            </h3>

                            <p>
                              {getMonthName(
                                budget.month
                              )}{" "}
                              {budget.year}
                            </p>

                          </div>

                        </div>


                        <button
                          type="button"
                          onClick={() =>
                            handleDelete(
                              budget._id
                            )
                          }
                          className="budget-delete-button"
                          title="Delete budget"
                        >

                          <Trash2 size={17} />

                        </button>

                      </div>


                      {/* Amount */}

                      <div className="budget-amount-row">

                        <div>

                          <span>
                            SPENT
                          </span>

                          <strong
                            className={
                              isExceeded
                                ? "danger-text"
                                : ""
                            }
                          >
                            {formatCurrency(
                              spent
                            )}
                          </strong>

                        </div>


                        <div className="budget-amount-right">

                          <span>
                            BUDGET
                          </span>

                          <strong className="green-text">
                            {formatCurrency(
                              amount
                            )}
                          </strong>

                        </div>

                      </div>


                      {/* Progress */}

                      <div className="budget-progress-section">

                        <div className="budget-progress-label">

                          <span>
                            Budget usage
                          </span>

                          <strong
                            className={
                              isExceeded
                                ? "danger-text"
                                : displayPercentage >= 80
                                  ? "orange-text"
                                  : "green-text"
                            }
                          >
                            {displayPercentage}%
                          </strong>

                        </div>


                        <div className="budget-progress-track">

                          <div
                            className={
                              isExceeded
                                ? "budget-progress-bar danger"
                                : displayPercentage >= 80
                                  ? "budget-progress-bar warning"
                                  : "budget-progress-bar"
                            }
                            style={{
                              width:
                                `${percentage}%`,
                            }}
                          />

                        </div>

                      </div>


                      {/* Status */}

                      <div
                        className={
                          isExceeded
                            ? "budget-status danger"
                            : displayPercentage >= 80
                              ? "budget-status warning"
                              : "budget-status success"
                        }
                      >

                        {isExceeded ? (

                          <AlertTriangle size={17} />

                        ) : displayPercentage >= 80 ? (

                          <AlertTriangle size={17} />

                        ) : (

                          <CheckCircle2 size={17} />

                        )}


                        <div>

                          <strong>

                            {isExceeded
                              ? "Budget exceeded"
                              : displayPercentage >= 80
                                ? "Approaching limit"
                                : "Within budget"}

                          </strong>

                          <p>

                            {isExceeded
                              ? `${formatCurrency(
                                  Math.abs(
                                    remainingAmount
                                  )
                                )} over budget`
                              : `${formatCurrency(
                                  remainingAmount
                                )} remaining`}

                          </p>

                        </div>

                      </div>


                      {/* Upgrade */}

                      {isExceeded && (

                        <button
                          type="button"
                          onClick={() =>
                            openUpgradeModal(
                              budget
                            )
                          }
                          className="budget-upgrade-button"
                        >

                          <ArrowUpCircle
                            size={18}
                          />

                          Increase Budget

                        </button>

                      )}

                    </div>

                  );

                })}

              </div>

            )}

          </div>

        </main>

      </div>


      {/* ========================================================
          CREATE BUDGET MODAL
      ======================================================== */}

      {showCreateModal && (

        <div className="budget-modal-overlay">

          <div className="budget-modal">

            <div className="budget-modal-header">

              <div>

                <h2>
                  Create Budget
                </h2>

                <p>
                  Set a spending limit for a category.
                </p>

              </div>

              <button
                type="button"
                onClick={() =>
                  setShowCreateModal(false)
                }
                className="budget-modal-close"
              >
                <X size={19} />
              </button>

            </div>


            <form
              onSubmit={
                handleCreateBudget
              }
              className="budget-modal-form"
            >

              {/* Category */}

              <div className="budget-form-field">

                <label>
                  Category
                </label>

                <select
                  value={
                    createForm.category
                  }
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      category:
                        e.target.value,
                    })
                  }
                >

                  <option value="Food">
                    Food
                  </option>

                  <option value="Transport">
                    Transport
                  </option>

                  <option value="Shopping">
                    Shopping
                  </option>

                  <option value="Entertainment">
                    Entertainment
                  </option>

                  <option value="Bills">
                    Bills
                  </option>

                  <option value="Healthcare">
                    Healthcare
                  </option>

                  <option value="Education">
                    Education
                  </option>

                  <option value="Travel">
                    Travel
                  </option>

                  <option value="Other">
                    Other
                  </option>

                </select>

              </div>


              {/* Amount */}

              <div className="budget-form-field">

                <label>
                  Budget Amount
                </label>

                <div className="budget-input-money">

                  <span>
                    ₹
                  </span>

                  <input
                    type="number"
                    min="1"
                    value={
                      createForm.amount
                    }
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        amount:
                          e.target.value,
                      })
                    }
                    placeholder="5000"
                  />

                </div>

              </div>


              {/* Month Year */}

              <div className="budget-form-two">

                <div className="budget-form-field">

                  <label>
                    Month
                  </label>

                  <select
                    value={
                      createForm.month
                    }
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        month:
                          Number(
                            e.target.value
                          ),
                      })
                    }
                  >

                    {[
                      "January",
                      "February",
                      "March",
                      "April",
                      "May",
                      "June",
                      "July",
                      "August",
                      "September",
                      "October",
                      "November",
                      "December",
                    ].map(
                      (month, index) => (

                        <option
                          key={month}
                          value={index + 1}
                        >
                          {month}
                        </option>

                      )
                    )}

                  </select>

                </div>


                <div className="budget-form-field">

                  <label>
                    Year
                  </label>

                  <input
                    type="number"
                    value={
                      createForm.year
                    }
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        year:
                          Number(
                            e.target.value
                          ),
                      })
                    }
                  />

                </div>

              </div>


              {/* Buttons */}

              <div className="budget-modal-actions">

                <button
                  type="button"
                  onClick={() =>
                    setShowCreateModal(false)
                  }
                  className="budget-cancel-button"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={creating}
                  className="budget-submit-button"
                >

                  {creating
                    ? "Creating..."
                    : "Create Budget"}

                </button>

              </div>

            </form>

          </div>

        </div>

      )}


      {/* ========================================================
          UPGRADE MODAL
      ======================================================== */}

      {showUpgradeModal &&
        selectedBudget && (

        <div className="budget-modal-overlay">

          <div className="budget-modal upgrade-modal">

            <div className="budget-modal-header">

              <div className="upgrade-modal-title">

                <div className="upgrade-icon">

                  <ShieldCheck size={21} />

                </div>

                <div>

                  <h2>
                    Increase Budget
                  </h2>

                  <p>
                    {selectedBudget.category}
                  </p>

                </div>

              </div>

              <button
                type="button"
                onClick={
                  closeUpgradeModal
                }
                className="budget-modal-close"
              >
                <X size={19} />
              </button>

            </div>


            <div className="budget-upgrade-body">

              {/* Current */}

              <div className="current-budget-box">

                <span>
                  Current budget
                </span>

                <strong>
                  {formatCurrency(
                    selectedBudget.amount
                  )}
                </strong>

              </div>


              {/* New Amount */}

              <div className="budget-form-field">

                <label>
                  New Budget Amount
                </label>

                <div className="budget-input-money">

                  <span>
                    ₹
                  </span>

                  <input
                    type="number"
                    min={
                      Number(
                        selectedBudget.amount
                      ) + 1
                    }
                    value={
                      upgradeAmount
                    }
                    onChange={(e) =>
                      setUpgradeAmount(
                        e.target.value
                      )
                    }
                    placeholder="10000"
                    disabled={otpSent}
                  />

                </div>

              </div>


              {!otpSent ? (

                <>

                  <div className="upgrade-security-info">

                    <ShieldCheck
                      size={19}
                    />

                    <p>
                      For security, a verification
                      OTP will be sent to your
                      registered email address.
                    </p>

                  </div>


                  <button
                    type="button"
                    onClick={
                      handleRequestUpgrade
                    }
                    disabled={
                      sendingOtp
                    }
                    className="budget-submit-button full"
                  >

                    {sendingOtp
                      ? "Sending OTP..."
                      : "Send Verification OTP"}

                  </button>

                </>

              ) : (

                <>

                  <div className="upgrade-security-info">

                    <ShieldCheck
                      size={19}
                    />

                    <div>

                      <p>
                        OTP sent successfully to
                        your registered email.
                      </p>

                      <small>
                        Enter the 6-digit OTP to
                        confirm the budget increase.
                      </small>

                    </div>

                  </div>


                  <div className="budget-form-field">

                    <label>
                      Verification OTP
                    </label>

                    <input
                      type="text"
                      inputMode="numeric"
                      maxLength={6}
                      value={otp}
                      onChange={(e) =>
                        setOtp(
                          e.target.value.replace(
                            /\D/g,
                            ""
                          )
                        )
                      }
                      placeholder="Enter 6-digit OTP"
                      className="otp-input"
                    />

                  </div>


                  <button
                    type="button"
                    onClick={
                      handleVerifyOtp
                    }
                    disabled={
                      verifyingOtp
                    }
                    className="budget-submit-button full"
                  >

                    {verifyingOtp
                      ? "Verifying..."
                      : "Verify & Increase Budget"}

                  </button>

                </>

              )}

            </div>

          </div>

        </div>

      )}

    </div>
  );
}


export default Budget;