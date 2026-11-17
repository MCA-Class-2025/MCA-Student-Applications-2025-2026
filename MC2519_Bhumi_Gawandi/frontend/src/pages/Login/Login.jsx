import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import Navbar from "../../components/Navbar/Navbar";
import Footer from "../../components/Footer/Footer";

import { loginUser } from "../../services/authService";

function Login() {

  const navigate = useNavigate();

  const [formData, setFormData] = useState({

    email: "",

    password: "",

  });

  const [showPassword, setShowPassword] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const handleChange = (e) => {

    setFormData({

      ...formData,

      [e.target.name]: e.target.value,

    });

  };

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      setLoading(true);

      const response =
        await loginUser(formData);

      localStorage.setItem(
        "token",
        response.access_token
      );

      localStorage.setItem(
        "user",
        JSON.stringify(response.user)
      );

      toast.success(
        response.message ||
        "Login Successful"
      );

      setTimeout(() => {

        navigate("/dashboard");

      }, 1000);

    } catch (error) {

      console.error(error);

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

  return (
    <>
  <Navbar />

  <main className="flex-1 flex items-center justify-center px-6 pt-32 pb-20">

    <div className="w-full max-w-4xl grid md:grid-cols-2 rounded-2xl overflow-hidden shadow-xl border border-[#E4E1D6] bg-white">

      {/* Left Side */}

      <div className="p-10 md:p-12">

        <h1
          className="text-3xl font-medium text-[#12172B]"
          style={{ fontFamily: "'Fraunces', serif" }}
        >
          Welcome Back
        </h1>

        <p className="mt-2 text-sm text-[#6B6B63]">
          Login to continue managing your finances.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-5"
        >

          {/* Email */}

          <div>

            <label className="block text-sm font-medium text-[#12172B] mb-2">
              Email
            </label>

            <input
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              className="w-full px-4 py-3 rounded-lg border border-[#DEDBCF] bg-[#FBFAF6] focus:outline-none focus:border-[#1F6F5C] focus:ring-1 focus:ring-[#1F6F5C]"
            />

          </div>

          {/* Password */}

          <div>

            <label className="block text-sm font-medium text-[#12172B] mb-2">
              Password
            </label>

            <div className="relative">

              <input
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                name="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
                className="w-full px-4 py-3 rounded-lg pr-16 border border-[#DEDBCF] bg-[#FBFAF6] focus:outline-none focus:border-[#1F6F5C] focus:ring-1 focus:ring-[#1F6F5C]"
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword(
                    !showPassword
                  )
                }
                className="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-[#1F6F5C]"
              >
                {showPassword
                  ? "Hide"
                  : "Show"}
              </button>

            </div>

          </div>

          {/* Remember */}

          <div className="flex justify-between items-center">

            <label className="flex items-center gap-2 text-sm">

              <input
                type="checkbox"
              />

              Remember Me

            </label>

            <button
              type="button"
              className="text-[#1F6F5C] text-sm font-medium"
            >
              Forgot Password?
            </button>

          </div>

          {/* Login Button */}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 rounded-xl bg-[#1F6F5C] hover:bg-[#175646] text-white font-semibold transition disabled:opacity-70"
          >
            {loading
              ? "Logging In..."
              : "Login"}
          </button>

          <p className="text-center text-sm">

            Don't have an account?

            <Link
              to="/register"
              className="ml-2 text-[#1F6F5C] font-semibold"
            >
              Register
            </Link>

          </p>

        </form>

      </div>
            {/* Right Side */}

      <div className="bg-[#12172B] p-10 md:p-12 flex flex-col justify-center">

        <span className="inline-block text-xs font-semibold tracking-widest uppercase text-[#4FAE93] mb-4">
          Welcome to SpendSmart.ai
        </span>

        <h2
          className="text-3xl font-medium text-[#F6F4EE] leading-snug"
          style={{ fontFamily: "'Fraunces', serif" }}
        >
          Manage your money
          <span className="italic text-[#4FAE93]">
            {" "}intelligently.
          </span>
        </h2>

        <p className="mt-4 text-sm text-[#B8B6AE] leading-7">
          Track every expense, manage budgets,
          scan receipts, use AI insights,
          and stay financially healthy with one
          modern dashboard.
        </p>

        {/* Summary Card */}

        <div className="mt-10 bg-white rounded-2xl p-6 shadow-xl">

          <p className="text-xs uppercase tracking-widest text-gray-500">
            Your Financial Overview
          </p>

          <div className="space-y-3 mt-5">

            <div className="flex justify-between">

              <span className="text-gray-500">
                Monthly Income
              </span>

              <span className="font-semibold">
                ₹80,000
              </span>

            </div>

            <div className="flex justify-between">

              <span className="text-gray-500">
                Total Expense
              </span>

              <span className="font-semibold">
                ₹28,500
              </span>

            </div>

            <div className="flex justify-between border-t pt-3">

              <span className="font-semibold">
                Savings
              </span>

              <span className="font-bold text-[#1F6F5C]">
                ₹51,500
              </span>

            </div>

          </div>

          <div className="mt-6 bg-[#F3F8F6] rounded-xl p-4">

            <p className="text-sm font-semibold text-[#1F6F5C]">
              🤖 AI Insight
            </p>

            <p className="text-sm text-gray-600 mt-2 leading-6">
              Great job! Your expenses are under
              control. Continue saving at least
              20% of your monthly income to
              achieve your financial goals.
            </p>

          </div>

        </div>

        {/* Features */}

        <div className="grid grid-cols-2 gap-4 mt-8">

          <div className="bg-[#1B2238] rounded-xl p-5">

            <h3 className="text-[#4FAE93] font-semibold">
              Smart Analytics
            </h3>

            <p className="text-gray-400 text-sm mt-2">
              Understand spending patterns.
            </p>

          </div>

          <div className="bg-[#1B2238] rounded-xl p-5">

            <h3 className="text-[#4FAE93] font-semibold">
              AI Budgeting
            </h3>

            <p className="text-gray-400 text-sm mt-2">
              Personalized budget planning.
            </p>

          </div>

          <div className="bg-[#1B2238] rounded-xl p-5">

            <h3 className="text-[#4FAE93] font-semibold">
              Receipt Scanner
            </h3>

            <p className="text-gray-400 text-sm mt-2">
              Upload receipts instantly.
            </p>

          </div>

          <div className="bg-[#1B2238] rounded-xl p-5">

            <h3 className="text-[#4FAE93] font-semibold">
              Voice Expense
            </h3>

            <p className="text-gray-400 text-sm mt-2">
              Record expenses using speech.
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

export default Login;