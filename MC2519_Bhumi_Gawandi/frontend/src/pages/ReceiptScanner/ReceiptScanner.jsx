import React, { useEffect, useState } from "react";

import {
  Upload,
  ScanLine,
  CheckCircle,
  RotateCcw,
  FileText,
  Store,
  IndianRupee,
  CalendarDays,
  Tag,
  CreditCard,
} from "lucide-react";

import toast from "react-hot-toast";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import { scanReceipt } from "../../services/receiptService";
import { createExpense } from "../../services/expenseService";

import "./ReceiptScanner.css";

function ReceiptScanner() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");

  // ============================================================
  // CLEANUP PREVIEW
  // ============================================================

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  // ============================================================
  // SELECT RECEIPT
  // ============================================================

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    const allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "image/webp",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      toast.error(
        "Please upload a JPG, PNG or WEBP receipt."
      );

      setMessage(
        "Please upload a JPG, PNG or WEBP receipt."
      );

      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      toast.error(
        "Receipt image must be smaller than 10 MB."
      );

      setMessage(
        "Receipt image must be smaller than 10 MB."
      );

      return;
    }

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    const imageUrl =
      URL.createObjectURL(selectedFile);

    setFile(selectedFile);
    setPreview(imageUrl);
    setResult(null);
    setMessage("");
  };

  // ============================================================
  // SCAN RECEIPT
  // ============================================================

  const handleScan = async () => {
    if (!file) {
      toast.error(
        "Please select a receipt first."
      );

      setMessage(
        "Please select a receipt first."
      );

      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await scanReceipt(file);

      console.log(
        "Receipt OCR response:",
        response
      );

      if (!response?.success) {
        const errorMessage =
          response?.message ||
          "Unable to scan receipt.";

        toast.error(errorMessage);
        setMessage(errorMessage);

        return;
      }

      setResult({
        merchant:
          response.merchant || "",

        amount:
          response.amount || "",

        date:
          response.date || "",

        category:
          response.category || "Other",

        payment_method:
          response.payment_method || "Other",

        ...response,
      });

      toast.success(
        "Receipt scanned successfully!",
        {
          duration: 2500,
          position: "top-right",
        }
      );

      setMessage(
        "Receipt scanned successfully. Please check the details."
      );
    } catch (error) {
      console.error(
        "Receipt scan error:",
        error
      );

      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Unable to scan receipt.";

      toast.error(errorMessage);
      setMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // UPDATE RESULT
  // ============================================================

  const updateResult = (field, value) => {
    setResult((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  // ============================================================
  // SAVE EXPENSE
  // ============================================================

  const handleSaveExpense = async () => {
    if (!result) {
      toast.error(
        "Please scan a receipt first."
      );

      return;
    }

    if (
      !result.amount ||
      Number(result.amount) <= 0
    ) {
      toast.error(
        "Please enter a valid amount."
      );

      setMessage(
        "Please enter a valid amount."
      );

      return;
    }

    if (!result.merchant?.trim()) {
      toast.error(
        "Please enter the merchant name."
      );

      setMessage(
        "Please enter the merchant name."
      );

      return;
    }

    if (!result.date) {
      toast.error(
        "Please select the receipt date."
      );

      setMessage(
        "Please select the receipt date."
      );

      return;
    }

    try {
      setSaving(true);
      setMessage("");

      const expenseData = {
        title: result.merchant.trim(),

        amount: Number(result.amount),

        category:
          result.category || "Other",

        payment_method:
          result.payment_method || "Other",

        date: new Date(
          `${result.date}T00:00:00`
        ).toISOString(),

        notes:
          "Added using Receipt Scanner",
      };

      console.log(
        "Sending expense:",
        expenseData
      );

      const response =
        await createExpense(expenseData);

      console.log(
        "Expense API response:",
        response
      );

      if (response?.success === false) {
        const errorMessage =
          response?.message ||
          "Unable to add expense.";

        toast.error(errorMessage, {
          duration: 3000,
          position: "top-right",
        });

        setMessage(errorMessage);

        return;
      }

      toast.success(
        "Expense added successfully!",
        {
          duration: 3000,
          position: "top-right",
        }
      );

      setMessage(
        "Expense added successfully."
      );

      setTimeout(() => {
        handleReset();
      }, 1200);
    } catch (error) {
      console.error(
        "Save expense error:",
        error
      );

      const detail =
        error?.response?.data?.detail;

      let errorMessage =
        "Unable to add expense.";

      if (Array.isArray(detail)) {
        errorMessage =
          detail[0]?.msg ||
          errorMessage;
      } else if (
        typeof detail === "string"
      ) {
        errorMessage = detail;
      } else if (
        error?.response?.data?.message
      ) {
        errorMessage =
          error.response.data.message;
      } else if (error?.message) {
        errorMessage = error.message;
      }

      toast.error(errorMessage, {
        duration: 3000,
        position: "top-right",
      });

      setMessage(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // ============================================================
  // RESET
  // ============================================================

  const handleReset = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setFile(null);
    setPreview("");
    setResult(null);
    setMessage("");
  };

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="receipt-dashboard-layout">

      {/* SIDEBAR */}

      <aside className="receipt-sidebar">
        <Sidebar />
      </aside>

      {/* MAIN */}

      <div className="receipt-dashboard-main">

        {/* NAVBAR */}

        <div className="receipt-navbar-wrapper">
          <DashboardNavbar />
        </div>

        {/* PAGE */}

        <main className="receipt-page">

          {/* HEADER */}

          <section className="receipt-header">

            <div className="receipt-title-row">

              <div className="receipt-title-icon">
                <ScanLine
                  size={24}
                  strokeWidth={2}
                />
              </div>

              <div>

                <h1>
                  Receipt Scanner
                </h1>

                <p>
                  Scan a receipt and turn
                  it into an expense
                </p>

              </div>

            </div>

          </section>

          {/* CONTENT */}

          <section className="receipt-layout">

            {/* UPLOAD CARD */}

            <div className="receipt-card">

              <div className="card-heading">

                <div>
                  <h2>
                    Upload Receipt
                  </h2>

                  <p>
                    JPG, PNG or WEBP
                  </p>
                </div>

              </div>

              {!preview ? (

                <label className="upload-box">

                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.webp"
                    onChange={handleFileChange}
                    hidden
                  />

                  <div className="upload-icon">

                    <Upload
                      size={28}
                      strokeWidth={1.8}
                    />

                  </div>

                  <h3>
                    Choose a receipt image
                  </h3>

                  <p>
                    Click here to upload
                    your receipt
                  </p>

                  <span className="upload-hint">
                    Maximum file size: 10 MB
                  </span>

                </label>

              ) : (

                <div className="preview-wrapper">

                  <div className="preview-label">
                    Receipt Preview
                  </div>

                  <img
                    src={preview}
                    alt="Receipt preview"
                  />

                  <button
                    type="button"
                    className="reset-button"
                    onClick={handleReset}
                  >

                    <RotateCcw size={15} />

                    Choose another

                  </button>

                </div>

              )}

              <button
                type="button"
                className="scan-button"
                onClick={handleScan}
                disabled={!file || loading}
              >

                <ScanLine size={17} />

                {loading
                  ? "Scanning..."
                  : "Scan Receipt"}

              </button>

              {message && (

                <div
                  className={`receipt-message ${
                    message.includes(
                      "successfully"
                    )
                      ? "success-message"
                      : ""
                  }`}
                >
                  {message}
                </div>

              )}

            </div>

            {/* RESULT CARD */}

            <div className="receipt-card">

              <div className="card-heading">

                <div>

                  <h2>
                    Extracted Details
                  </h2>

                  <p>
                    Review before adding
                    the expense
                  </p>

                </div>

                <div className="result-heading-icon">

                  <FileText size={20} />

                </div>

              </div>

              {!result ? (

                <div className="empty-result">

                  <div className="empty-result-icon">

                    <ScanLine size={34} />

                  </div>

                  <h3>
                    No receipt scanned yet
                  </h3>

                  <p>
                    Upload a receipt and
                    click "Scan Receipt"
                    to extract the
                    expense details.
                  </p>

                </div>

              ) : (

                <div className="result-fields">

                  {/* MERCHANT */}

                  <div className="result-field">

                    <div className="field-icon">
                      <Store size={17} />
                    </div>

                    <div className="field-content">

                      <label>
                        Merchant
                      </label>

                      <input
                        type="text"
                        value={
                          result.merchant || ""
                        }
                        onChange={(event) =>
                          updateResult(
                            "merchant",
                            event.target.value
                          )
                        }
                      />

                    </div>

                  </div>

                  {/* AMOUNT */}

                  <div className="result-field">

                    <div className="field-icon">
                      <IndianRupee size={17} />
                    </div>

                    <div className="field-content">

                      <label>
                        Amount
                      </label>

                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={
                          result.amount ?? ""
                        }
                        onChange={(event) =>
                          updateResult(
                            "amount",
                            event.target.value
                          )
                        }
                      />

                    </div>

                  </div>

                  {/* DATE */}

                  <div className="result-field">

                    <div className="field-icon">
                      <CalendarDays size={17} />
                    </div>

                    <div className="field-content">

                      <label>
                        Date
                      </label>

                      <input
                        type="date"
                        value={
                          result.date || ""
                        }
                        onChange={(event) =>
                          updateResult(
                            "date",
                            event.target.value
                          )
                        }
                      />

                    </div>

                  </div>

                  {/* CATEGORY */}

                  <div className="result-field">

                    <div className="field-icon">
                      <Tag size={17} />
                    </div>

                    <div className="field-content">

                      <label>
                        Category
                      </label>

                      <select
                        value={
                          result.category ||
                          "Other"
                        }
                        onChange={(event) =>
                          updateResult(
                            "category",
                            event.target.value
                          )
                        }
                      >

                        <option value="Food">
                          Food
                        </option>

                        <option value="Groceries">
                          Groceries
                        </option>

                        <option value="Shopping">
                          Shopping
                        </option>

                        <option value="Travel">
                          Travel
                        </option>

                        <option value="Transport">
                          Transport
                        </option>

                        <option value="Fuel">
                          Fuel
                        </option>

                        <option value="Healthcare">
                          Healthcare
                        </option>

                        <option value="Entertainment">
                          Entertainment
                        </option>

                        <option value="Bills">
                          Bills
                        </option>

                        <option value="Education">
                          Education
                        </option>

                        <option value="Other">
                          Other
                        </option>

                      </select>

                    </div>

                  </div>

                  {/* PAYMENT */}

                  <div className="result-field">

                    <div className="field-icon">
                      <CreditCard size={17} />
                    </div>

                    <div className="field-content">

                      <label>
                        Payment Method
                      </label>

                      <select
                        value={
                          result.payment_method ||
                          "Other"
                        }
                        onChange={(event) =>
                          updateResult(
                            "payment_method",
                            event.target.value
                          )
                        }
                      >

                        <option value="UPI">
                          UPI
                        </option>

                        <option value="Card">
                          Card
                        </option>

                        <option value="Cash">
                          Cash
                        </option>

                        <option value="Other">
                          Other
                        </option>

                      </select>

                    </div>

                  </div>

                  {/* SAVE */}

                  <button
                    type="button"
                    className="save-expense-button"
                    onClick={handleSaveExpense}
                    disabled={saving}
                  >

                    <CheckCircle size={17} />

                    {saving
                      ? "Saving..."
                      : "Add Expense"}

                  </button>

                </div>

              )}

            </div>

          </section>

        </main>

      </div>

    </div>
  );
}

export default ReceiptScanner;