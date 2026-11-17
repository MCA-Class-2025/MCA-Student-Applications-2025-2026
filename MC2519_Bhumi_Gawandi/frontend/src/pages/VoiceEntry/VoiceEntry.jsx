import { useEffect, useRef, useState } from "react";

import {
  Mic,
  MicOff,
  CheckCircle,
  RotateCcw,
  IndianRupee,
  Tag,
  CreditCard,
  CalendarDays,
  Volume2,
} from "lucide-react";

import toast from "react-hot-toast";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import { parseVoiceExpense } from "../../services/voiceService";
import { createExpense } from "../../services/expenseService";

import "./VoiceEntry.css";

function VoiceEntry() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [supported, setSupported] = useState(true);

  const recognitionRef = useRef(null);

  // ==========================================================
  // BROWSER SUPPORT
  // ==========================================================

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";

      for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
      ) {
        const text =
          event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalText += text;
        } else {
          interimText += text;
        }
      }

      setTranscript(
        finalText || interimText
      );
    };

    recognition.onerror = (event) => {
      console.error(
        "Speech recognition error:",
        event.error
      );

      setIsListening(false);

      if (event.error === "not-allowed") {
        toast.error(
          "Please allow microphone access."
        );
      } else {
        toast.error(
          "Unable to recognize your voice."
        );
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch (error) {
        console.log(error);
      }
    };
  }, []);

  // ==========================================================
  // START / STOP RECORDING
  // ==========================================================

  const toggleRecording = () => {
    if (!supported) {
      toast.error(
        "Voice recognition is not supported in this browser."
      );
      return;
    }

    if (!recognitionRef.current) {
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    setTranscript("");
    setResult(null);

    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error(
        "Start recording error:",
        error
      );
    }
  };

  // ==========================================================
  // UNDERSTAND EXPENSE
  // ==========================================================

  const handleUnderstand = async () => {
    if (!transcript.trim()) {
      toast.error(
        "Please record an expense first."
      );
      return;
    }

    try {
      setLoading(true);

      const response =
        await parseVoiceExpense(
          transcript
        );

      console.log(
        "Voice parse response:",
        response
      );

      if (!response?.success) {
        toast.error(
          "Unable to understand the expense."
        );
        return;
      }

      const data = response.data || {};

      setResult({
        title: data.title || "",
        amount: data.amount || "",
        category:
          data.category || "Other",
        payment_method:
          data.payment_method || "Other",
        date:
          data.date ||
          new Date()
            .toISOString()
            .split("T")[0],
        notes: data.notes || "",
      });

      toast.success(
        "Expense details extracted."
      );
    } catch (error) {
      console.error(
        "Voice processing error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
          error?.response?.data?.message ||
          "Unable to process your voice."
      );
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================
  // UPDATE RESULT
  // ==========================================================

  const updateResult = (
    field,
    value
  ) => {
    setResult((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  // ==========================================================
  // SAVE EXPENSE
  // ==========================================================

  const handleSave = async () => {
    if (!result) {
      toast.error(
        "Please understand the expense first."
      );
      return;
    }

    if (
      !result.title?.trim()
    ) {
      toast.error(
        "Please enter an expense title."
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
      return;
    }

    try {
      setSaving(true);

      const expenseData = {
        title: result.title.trim(),

        amount: Number(result.amount),

        category:
          result.category || "Other",

        payment_method:
          result.payment_method || "Other",

        date:
          result.date ||
          new Date()
            .toISOString()
            .split("T")[0],

        notes:
          result.notes ||
          "Added using Voice Entry",
      };

      console.log(
        "Voice expense data:",
        expenseData
      );

      await createExpense(
        expenseData
      );

      toast.success(
        "Expense added successfully!",
        {
          duration: 3000,
          position: "top-right",
        }
      );

      setTranscript("");
      setResult(null);
    } catch (error) {
      console.error(
        "Save voice expense error:",
        error
      );

      const detail =
        error?.response?.data?.detail;

      let message =
        "Unable to add expense.";

      if (Array.isArray(detail)) {
        message =
          detail[0]?.msg ||
          message;
      } else if (
        typeof detail === "string"
      ) {
        message = detail;
      } else if (
        error?.response?.data?.message
      ) {
        message =
          error.response.data.message;
      }

      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  // ==========================================================
  // RESET
  // ==========================================================

  const handleReset = () => {
    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch (error) {
        console.log(error);
      }
    }

    setTranscript("");
    setResult(null);
    setIsListening(false);
  };

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div className="voice-dashboard-layout">

      {/* ====================================================
          SIDEBAR
      ==================================================== */}

      <aside className="voice-sidebar">
        <Sidebar />
      </aside>

      {/* ====================================================
          MAIN
      ==================================================== */}

      <div className="voice-dashboard-main">

        {/* ==================================================
            NAVBAR
        ================================================== */}

        <div className="voice-navbar-wrapper">
          <DashboardNavbar />
        </div>

        {/* ==================================================
            PAGE
        ================================================== */}

        <main className="voice-page">

          {/* HEADER */}

          <div className="voice-header">

            <div className="voice-title-icon">
              <Mic size={25} />
            </div>

            <div>
              <h1>
                Voice Expense Entry
              </h1>

              <p>
                Add an expense using your voice
              </p>
            </div>

          </div>

          {/* WARNING */}

          {!supported && (
            <div className="voice-warning">
              Voice recognition is not supported
              in this browser. Please use Google
              Chrome or Microsoft Edge.
            </div>
          )}

          {/* GRID */}

          <div className="voice-grid">

            {/* =================================================
                RECORD CARD
            ================================================= */}

            <section className="voice-card">

              <div className="voice-card-heading">

                <div>
                  <h2>
                    Speak your expense
                  </h2>

                  <p>
                    Example: "I spent 500 rupees
                    on dinner using UPI"
                  </p>
                </div>

                <Volume2
                  size={21}
                  color="#1F6F5C"
                />

              </div>

              {/* RECORDER */}

              <div className="voice-recorder">

                <button
                  type="button"
                  className={
                    isListening
                      ? "voice-mic-button listening"
                      : "voice-mic-button"
                  }
                  onClick={
                    toggleRecording
                  }
                  disabled={!supported}
                >
                  {isListening ? (
                    <MicOff size={38} />
                  ) : (
                    <Mic size={38} />
                  )}
                </button>

                <h3>
                  {isListening
                    ? "Listening..."
                    : "Click to speak"}
                </h3>

                <p>
                  {isListening
                    ? "Tell me about your expense"
                    : "Speak clearly and include the amount"}
                </p>

              </div>

              {/* TRANSCRIPT */}

              <div className="transcript-box">

                <label>
                  Your voice
                </label>

                <textarea
                  value={transcript}
                  onChange={(event) =>
                    setTranscript(
                      event.target.value
                    )
                  }
                  placeholder='Example: "I spent 500 rupees on dinner using UPI"'
                  rows={4}
                />

              </div>

              {/* ACTIONS */}

              <div className="voice-actions">

                <button
                  type="button"
                  className="understand-button"
                  onClick={
                    handleUnderstand
                  }
                  disabled={
                    !transcript.trim() ||
                    loading
                  }
                >
                  {loading
                    ? "Understanding..."
                    : "Understand Expense"}
                </button>

                <button
                  type="button"
                  className="reset-voice-button"
                  onClick={
                    handleReset
                  }
                >
                  <RotateCcw size={16} />
                  Reset
                </button>

              </div>

            </section>

            {/* =================================================
                RESULT CARD
            ================================================= */}

            <section className="voice-card">

              <div className="voice-card-heading">

                <div>
                  <h2>
                    Expense Details
                  </h2>

                  <p>
                    Review the information before saving
                  </p>
                </div>

              </div>

              {!result ? (

                <div className="voice-empty">

                  <Mic size={40} />

                  <h3>
                    No expense detected
                  </h3>

                  <p>
                    Record your expense and click
                    Understand Expense.
                  </p>

                </div>

              ) : (

                <div className="voice-result">

                  {/* TITLE */}

                  <div className="voice-field">

                    <Tag size={18} />

                    <div>
                      <label>
                        Title
                      </label>

                      <input
                        type="text"
                        value={
                          result.title || ""
                        }
                        onChange={(event) =>
                          updateResult(
                            "title",
                            event.target.value
                          )
                        }
                      />
                    </div>

                  </div>

                  {/* AMOUNT */}

                  <div className="voice-field">

                    <IndianRupee
                      size={18}
                    />

                    <div>
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

                  {/* CATEGORY */}

                  <div className="voice-field">

                    <Tag size={18} />

                    <div>
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

                  <div className="voice-field">

                    <CreditCard
                      size={18}
                    />

                    <div>
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

                        <option value="Other">
                          Other
                        </option>
                      </select>
                    </div>

                  </div>

                  {/* DATE */}

                  <div className="voice-field">

                    <CalendarDays
                      size={18}
                    />

                    <div>
                      <label>
                        Date
                      </label>

                      <input
                        type="date"
                        value={
                          result.date ||
                          new Date()
                            .toISOString()
                            .split("T")[0]
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

                  {/* SAVE */}

                  <button
                    type="button"
                    className="save-voice-button"
                    onClick={
                      handleSave
                    }
                    disabled={saving}
                  >
                    <CheckCircle
                      size={18}
                    />

                    {saving
                      ? "Saving..."
                      : "Add Expense"}
                  </button>

                </div>
              )}

            </section>

          </div>

        </main>

      </div>

    </div>
  );
}

export default VoiceEntry;