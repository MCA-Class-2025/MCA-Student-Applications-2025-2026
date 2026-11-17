import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import Navbar from "../../components/Navbar/Navbar";
import Footer from "../../components/Footer/Footer";

import { registerUser } from "../../services/authService";

function Register() {

  const navigate = useNavigate();

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    monthlyIncome: "",
    currency: "INR",
  });

  const [showPassword, setShowPassword] =
    useState(false);

  const [showConfirm, setShowConfirm] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const handleChange = (field) => (e) => {
    setForm({
      ...form,
      [field]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {

    e.preventDefault();

    setError("");

    if (
      form.password !== form.confirmPassword
    ) {

      setError("Passwords don't match.");

      return;

    }

    try {

      setLoading(true);

      const payload = {

        full_name: form.fullName,

        email: form.email,

        password: form.password,

        monthly_income: Number(
          form.monthlyIncome
        ),

        preferred_currency:
          form.currency,

      };

      const response =
        await registerUser(payload);

      toast.success(
        response.message ||
          "Registration Successful"
      );

      setTimeout(() => {

        navigate("/login");

      }, 1500);

    } catch (error) {

      console.log(error);

      if (error.response) {

        toast.error(
          error.response.data.detail
        );

      } else {

        toast.error(
          "Server not responding"
        );

      }

    } finally {

      setLoading(false);

    }

  };

  const inputClass =
    "w-full px-4 py-3 rounded-lg border border-[#DEDBCF] bg-[#FBFAF6] text-sm text-[#12172B] placeholder:text-[#A6A398] focus:outline-none focus:border-[#1F6F5C] focus:ring-1 focus:ring-[#1F6F5C] transition-colors";

  const labelClass =
    "block text-sm font-medium text-[#12172B] mb-1.5 text-left";

  return (
        <>
      <Navbar />

      <main className="flex-1 flex items-center justify-center px-6 pt-32 pb-20">
        <div className="w-full max-w-4xl grid md:grid-cols-2 rounded-2xl overflow-hidden shadow-xl border border-[#E4E1D6] bg-white">

          {/* Left Side */}

          <div className="p-10 md:p-12">

            <h1
              className="text-3xl font-medium text-[#12172B] text-left"
              style={{ fontFamily: "'Fraunces', serif" }}
            >
              Create your account
            </h1>

            <p className="mt-2 text-sm text-[#6B6B63] text-left">
              Start managing your expenses with AI-powered insights.
            </p>

            <form
              onSubmit={handleSubmit}
              className="mt-8 space-y-5"
            >

              {/* Full Name */}

              <div>

                <label
                  htmlFor="fullName"
                  className={labelClass}
                >
                  Full Name
                </label>

                <input
                  id="fullName"
                  type="text"
                  required
                  placeholder="Rahul Sharma"
                  value={form.fullName}
                  onChange={handleChange("fullName")}
                  className={inputClass}
                />

              </div>

              {/* Email */}

              <div>

                <label
                  htmlFor="email"
                  className={labelClass}
                >
                  Email
                </label>

                <input
                  id="email"
                  type="email"
                  required
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange("email")}
                  className={inputClass}
                />

              </div>

              {/* Password */}

              <div>

                <label
                  htmlFor="password"
                  className={labelClass}
                >
                  Password
                </label>

                <div className="relative">

                  <input
                    id="password"
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    required
                    minLength={8}
                    placeholder="At least 8 characters"
                    value={form.password}
                    onChange={handleChange("password")}
                    className={`${inputClass} pr-16`}
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword(!showPassword)
                    }
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-[#1F6F5C]"
                  >
                    {showPassword
                      ? "Hide"
                      : "Show"}
                  </button>

                </div>

              </div>

              {/* Confirm Password */}

              <div>

                <label
                  htmlFor="confirmPassword"
                  className={labelClass}
                >
                  Confirm Password
                </label>

                <div className="relative">

                  <input
                    id="confirmPassword"
                    type={
                      showConfirm
                        ? "text"
                        : "password"
                    }
                    required
                    placeholder="Re-enter password"
                    value={form.confirmPassword}
                    onChange={handleChange("confirmPassword")}
                    className={`${inputClass} pr-16`}
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowConfirm(!showConfirm)
                    }
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-[#1F6F5C]"
                  >
                    {showConfirm
                      ? "Hide"
                      : "Show"}
                  </button>

                </div>

              </div>

              {/* Income & Currency */}

              <div className="grid grid-cols-2 gap-4">

                <div>

                  <label
                    htmlFor="monthlyIncome"
                    className={labelClass}
                  >
                    Monthly Income
                  </label>

                  <input
                    id="monthlyIncome"
                    type="number"
                    required
                    placeholder="50000"
                    value={form.monthlyIncome}
                    onChange={handleChange("monthlyIncome")}
                    className={inputClass}
                  />

                </div>

                <div>

                  <label
                    htmlFor="currency"
                    className={labelClass}
                  >
                    Currency
                  </label>

                  <select
                    id="currency"
                    value={form.currency}
                    onChange={handleChange("currency")}
                    className={inputClass}
                  >
                    <option value="INR">
                      INR
                    </option>

                    <option value="USD">
                      USD
                    </option>

                    <option value="EUR">
                      EUR
                    </option>

                    <option value="GBP">
                      GBP
                    </option>

                  </select>

                </div>

              </div>

              {error && (

                <p className="text-red-500 text-sm">

                  {error}

                </p>

              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#1F6F5C] hover:bg-[#175646] text-white py-4 rounded-xl font-semibold transition disabled:opacity-70"
              >
                {loading
                  ? "Creating Account..."
                  : "Create Account"}
              </button>

              <p className="text-center text-sm">

                Already have an account?{" "}

                <Link
                  to="/login"
                  className="text-[#1F6F5C] font-semibold"
                >
                  Login
                </Link>

              </p>
                          </form>

          </div>

          {/* Right Side */}

          <div className="bg-[#12172B] p-10 md:p-12 flex flex-col justify-center">

            <span className="inline-block text-xs font-semibold tracking-widest uppercase text-[#4FAE93] mb-4">
              Why SpendSmart.ai
            </span>

            <h2
              className="text-3xl font-medium text-[#F6F4EE] leading-snug"
              style={{ fontFamily: "'Fraunces', serif" }}
            >
              Everything you need to spend{" "}
              <span className="italic text-[#4FAE93]">
                smarter.
              </span>
            </h2>

            <p className="mt-4 text-sm text-[#B8B6AE] leading-7">
              AI-powered budgeting, receipt scanning,
              voice expense entry, beautiful analytics,
              smart insights and complete financial
              management in one dashboard.
            </p>

            {/* Summary Card */}

            <div className="mt-10 bg-white rounded-2xl p-6 shadow-xl">

              <p className="text-xs uppercase tracking-widest text-gray-500">
                Monthly Summary
              </p>

              <div className="space-y-3 mt-5">

                <div className="flex justify-between">

                  <span className="text-gray-500">
                    Income
                  </span>

                  <span className="font-semibold">
                    ₹80,000
                  </span>

                </div>

                <div className="flex justify-between">

                  <span className="text-gray-500">
                    Expense
                  </span>

                  <span className="font-semibold">
                    ₹28,500
                  </span>

                </div>

                <div className="border-t pt-3 flex justify-between">

                  <span className="font-semibold">
                    Savings
                  </span>

                  <span className="font-bold text-[#1F6F5C]">
                    ₹51,500
                  </span>

                </div>

              </div>

              <div className="mt-6 bg-[#F3F8F6] rounded-xl p-4">

                <p className="text-sm font-medium text-[#1F6F5C]">
                  💡 AI Insight
                </p>

                <p className="text-sm text-gray-600 mt-2 leading-6">
                  You can save nearly ₹5,000 every month
                  by reducing food delivery expenses and
                  increasing your monthly savings.
                </p>

              </div>

            </div>

            {/* Features */}

            <div className="grid grid-cols-2 gap-4 mt-8">

              <div className="bg-[#1B2238] rounded-xl p-5">

                <h3 className="text-[#4FAE93] font-semibold">
                  AI Insights
                </h3>

                <p className="text-gray-400 text-sm mt-2">
                  Personalized financial suggestions.
                </p>

              </div>

              <div className="bg-[#1B2238] rounded-xl p-5">

                <h3 className="text-[#4FAE93] font-semibold">
                  Smart Budget
                </h3>

                <p className="text-gray-400 text-sm mt-2">
                  Track your monthly spending goals.
                </p>

              </div>

              <div className="bg-[#1B2238] rounded-xl p-5">

                <h3 className="text-[#4FAE93] font-semibold">
                  Receipt OCR
                </h3>

                <p className="text-gray-400 text-sm mt-2">
                  Scan receipts instantly.
                </p>

              </div>

              <div className="bg-[#1B2238] rounded-xl p-5">

                <h3 className="text-[#4FAE93] font-semibold">
                  Voice Entry
                </h3>

                <p className="text-gray-400 text-sm mt-2">
                  Add expenses using voice.
                </p>

              </div>

            </div>

          </div>

        </div>

      </main>

      <Footer />

    </>

  );

}

export default Register;