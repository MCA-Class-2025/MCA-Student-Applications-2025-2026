import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import {
  ArrowLeft,
  Pencil,
  Trash2,
  CalendarDays,
  CreditCard,
  Tag,
  IndianRupee,
  FileText,
  Clock,
} from "lucide-react";

import Navbar from "../../components/dashboard/Navbar";
import Sidebar from "../../components/dashboard/Sidebar";

import {
  getExpenseById,
  deleteExpense,
} from "../../services/expenseService";

function ExpenseDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [expense, setExpense] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

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
      setLoading(true);

      const data = await getExpenseById(id);

      console.log("Expense details response:", data);

      if (data?.success === false) {
        toast.error(
          data.message || "Expense not found."
        );

        navigate("/expenses");
        return;
      }

      if (!data || !data._id) {
        toast.error("Expense details not found.");
        navigate("/expenses");
        return;
      }

      setExpense(data);

    } catch (error) {
      console.error(
        "Load expense details error:",
        error
      );

      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to load expense details.";

      toast.error(message);

      navigate("/expenses");

    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // DELETE EXPENSE
  // ============================================================

  const handleDelete = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this expense?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);

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

      setTimeout(() => {
        navigate("/expenses");
      }, 700);

    } catch (error) {
      console.error(
        "Delete expense error:",
        error
      );

      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to delete expense.";

      toast.error(message);

    } finally {
      setDeleting(false);
    }
  };

  // ============================================================
  // FORMAT CURRENCY
  // ============================================================

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(amount || 0));
  };

  // ============================================================
  // FORMAT DATE
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
        month: "long",
        year: "numeric",
      }
    );
  };

  // ============================================================
  // FORMAT DATE + TIME
  // ============================================================

  const formatDateTime = (date) => {
    if (!date) {
      return "-";
    }

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "-";
    }

    return parsedDate.toLocaleString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <div className="flex min-h-screen bg-[#F6F7F8]">

        <Sidebar />

        <div className="flex-1 min-w-0">

          <Navbar />

          <main className="p-4 sm:p-6 lg:p-8">

            <div className="max-w-5xl mx-auto">

              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-12 text-center">

                <div className="w-10 h-10 border-4 border-gray-200 border-t-[#1F6F5C] rounded-full animate-spin mx-auto">
                </div>

                <p className="text-gray-500 mt-4">
                  Loading expense details...
                </p>

              </div>

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
    <div className="flex min-h-screen bg-[#F6F7F8]">

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <Sidebar />


      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <div className="flex-1 min-w-0">

        <Navbar />

        <main className="p-4 sm:p-6 lg:p-8">

          <div className="max-w-5xl mx-auto">

            {/* ==================================================
                PAGE HEADER
            ================================================== */}

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">

              <div>

                <div className="flex items-center gap-3">

                  <button
                    type="button"
                    onClick={() =>
                      navigate("/expenses")
                    }
                    className="w-10 h-10 rounded-xl bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-[#1F6F5C] flex items-center justify-center transition"
                    title="Back to Expenses"
                  >
                    <ArrowLeft size={19} />
                  </button>

                  <div>

                    <h1 className="text-2xl sm:text-3xl font-bold text-[#1B2559]">
                      Expense Details
                    </h1>

                    <p className="text-gray-500 mt-1">
                      View complete information about this expense.
                    </p>

                  </div>

                </div>

              </div>


              {/* Header Actions */}

              <div className="flex gap-3">

                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/edit-expense/${id}`
                    )
                  }
                  className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#EAF1FF] hover:bg-[#DCE7FF] text-[#3478F6] font-semibold transition"
                >
                  <Pencil size={17} />

                  Edit
                </button>

                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                  className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#FFF0F0] hover:bg-[#FFE0E0] text-red-500 font-semibold transition disabled:opacity-50"
                >
                  <Trash2 size={17} />

                  {deleting
                    ? "Deleting..."
                    : "Delete"}
                </button>

              </div>

            </div>


            {/* ==================================================
                MAIN EXPENSE CARD
            ================================================== */}

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">

              {/* =================================================
                  EXPENSE TOP SECTION
              ================================================= */}

              <div className="p-6 sm:p-8 border-b border-gray-200">

                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">

                  <div>

                    <p className="text-sm text-gray-500 mb-2">
                      Expense Title
                    </p>

                    <h2 className="text-2xl sm:text-3xl font-bold text-[#12172B]">
                      {expense.title}
                    </h2>

                    <div className="mt-4">

                      <span className="inline-flex px-4 py-2 rounded-full bg-[#DDF7E9] text-[#07833D] text-sm font-semibold">
                        {expense.category}
                      </span>

                    </div>

                  </div>


                  {/* Amount */}

                  <div className="sm:text-right">

                    <p className="text-sm text-gray-500 mb-2">
                      Amount
                    </p>

                    <p className="text-3xl sm:text-4xl font-bold text-[#1F6F5C]">
                      {formatCurrency(
                        expense.amount
                      )}
                    </p>

                  </div>

                </div>

              </div>


              {/* =================================================
                  EXPENSE INFORMATION
              ================================================= */}

              <div className="p-6 sm:p-8">

                <h3 className="text-xl font-semibold text-[#12172B] mb-6">
                  Expense Information
                </h3>


                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">


                  {/* =================================================
                      CATEGORY
                  ================================================= */}

                  <div className="bg-[#F8FAF9] rounded-xl p-5">

                    <div className="flex items-center gap-3 mb-3">

                      <div className="w-10 h-10 rounded-lg bg-[#EAF5F1] flex items-center justify-center">

                        <Tag
                          size={19}
                          className="text-[#1F6F5C]"
                        />

                      </div>

                      <p className="text-sm text-gray-500">
                        Category
                      </p>

                    </div>

                    <p className="font-semibold text-[#252B3A]">
                      {expense.category || "-"}
                    </p>

                  </div>


                  {/* =================================================
                      PAYMENT METHOD
                  ================================================= */}

                  <div className="bg-[#F8FAF9] rounded-xl p-5">

                    <div className="flex items-center gap-3 mb-3">

                      <div className="w-10 h-10 rounded-lg bg-[#EAF5F1] flex items-center justify-center">

                        <CreditCard
                          size={19}
                          className="text-[#1F6F5C]"
                        />

                      </div>

                      <p className="text-sm text-gray-500">
                        Payment Method
                      </p>

                    </div>

                    <p className="font-semibold text-[#252B3A]">
                      {expense.payment_method || "-"}
                    </p>

                  </div>


                  {/* =================================================
                      AMOUNT
                  ================================================= */}

                  <div className="bg-[#F8FAF9] rounded-xl p-5">

                    <div className="flex items-center gap-3 mb-3">

                      <div className="w-10 h-10 rounded-lg bg-[#EAF5F1] flex items-center justify-center">

                        <IndianRupee
                          size={19}
                          className="text-[#1F6F5C]"
                        />

                      </div>

                      <p className="text-sm text-gray-500">
                        Expense Amount
                      </p>

                    </div>

                    <p className="font-semibold text-[#1F6F5C]">
                      {formatCurrency(
                        expense.amount
                      )}
                    </p>

                  </div>


                  {/* =================================================
                      EXPENSE DATE
                  ================================================= */}

                  <div className="bg-[#F8FAF9] rounded-xl p-5">

                    <div className="flex items-center gap-3 mb-3">

                      <div className="w-10 h-10 rounded-lg bg-[#EAF5F1] flex items-center justify-center">

                        <CalendarDays
                          size={19}
                          className="text-[#1F6F5C]"
                        />

                      </div>

                      <p className="text-sm text-gray-500">
                        Expense Date
                      </p>

                    </div>

                    <p className="font-semibold text-[#252B3A]">
                      {formatDate(
                        expense.date
                      )}
                    </p>

                  </div>

                </div>


                {/* =================================================
                    NOTES
                ================================================= */}

                <div className="mt-6">

                  <div className="flex items-center gap-3 mb-3">

                    <div className="w-10 h-10 rounded-lg bg-[#EAF5F1] flex items-center justify-center">

                      <FileText
                        size={19}
                        className="text-[#1F6F5C]"
                      />

                    </div>

                    <div>

                      <h3 className="font-semibold text-[#12172B]">
                        Notes
                      </h3>

                      <p className="text-xs text-gray-500">
                        Additional information
                      </p>

                    </div>

                  </div>

                  <div className="bg-[#F8FAF9] rounded-xl p-5">

                    {expense.notes ? (
                      <p className="text-gray-700 leading-7 whitespace-pre-wrap">
                        {expense.notes}
                      </p>
                    ) : (
                      <p className="text-gray-400 italic">
                        No notes added for this expense.
                      </p>
                    )}

                  </div>

                </div>


                {/* =================================================
                    CREATED / UPDATED
                ================================================= */}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mt-6">

                  {/* Created */}

                  <div className="border border-gray-200 rounded-xl p-5">

                    <div className="flex items-center gap-3">

                      <Clock
                        size={18}
                        className="text-[#1F6F5C]"
                      />

                      <div>

                        <p className="text-xs text-gray-500">
                          Created At
                        </p>

                        <p className="text-sm font-semibold text-[#252B3A] mt-1">
                          {formatDateTime(
                            expense.created_at
                          )}
                        </p>

                      </div>

                    </div>

                  </div>


                  {/* Updated */}

                  <div className="border border-gray-200 rounded-xl p-5">

                    <div className="flex items-center gap-3">

                      <Clock
                        size={18}
                        className="text-[#1F6F5C]"
                      />

                      <div>

                        <p className="text-xs text-gray-500">
                          Last Updated
                        </p>

                        <p className="text-sm font-semibold text-[#252B3A] mt-1">
                          {formatDateTime(
                            expense.updated_at
                          )}
                        </p>

                      </div>

                    </div>

                  </div>

                </div>

              </div>


              {/* =================================================
                  BOTTOM ACTIONS
              ================================================= */}

              <div className="px-6 sm:px-8 py-5 border-t border-gray-200 bg-[#FAFBFB] flex flex-col sm:flex-row sm:justify-between gap-3">

                <button
                  type="button"
                  onClick={() =>
                    navigate("/expenses")
                  }
                  className="w-full sm:w-auto px-6 py-3 rounded-xl border border-gray-300 bg-white text-gray-700 font-semibold hover:bg-gray-50 transition"
                >
                  Back to Expenses
                </button>

                <div className="flex flex-col sm:flex-row gap-3">

                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/edit-expense/${id}`
                      )
                    }
                    className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[#1F6F5C] hover:bg-[#175646] text-white font-semibold flex items-center justify-center gap-2 transition"
                  >
                    <Pencil size={17} />

                    Edit Expense
                  </button>

                </div>

              </div>

            </div>

          </div>

        </main>

      </div>

    </div>
  );
}

export default ExpenseDetails;