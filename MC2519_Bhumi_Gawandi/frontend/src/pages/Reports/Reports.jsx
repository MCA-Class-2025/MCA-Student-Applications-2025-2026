import { useEffect, useMemo, useState } from "react";

import {
  BarChart3,
  TrendingUp,
  Wallet,
  CreditCard,
  Target,
  AlertTriangle,
  Receipt,
  PieChart as PieChartIcon,
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import toast from "react-hot-toast";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import { getReport } from "../../services/reportService";
import { getCategories } from "../../services/categoryService";


// ============================================================
// COLORS
// ============================================================

const CATEGORY_COLORS = [
  "#1F6F5C",
  "#287EF5",
  "#A93BFF",
  "#C9A227",
  "#C15B3D",
  "#E85D75",
  "#00A8A8",
  "#7C5CFC",
  "#F59E0B",
  "#10B981",
];

const PAYMENT_COLORS = [
  "#1F6F5C",
  "#287EF5",
  "#A93BFF",
  "#C9A227",
  "#C15B3D",
  "#00A8A8",
];


// ============================================================
// REPORTS
// ============================================================

function Reports() {

  // ==========================================================
  // DATE
  // ==========================================================

  const currentDate = new Date();

  const currentMonth =
    currentDate.getMonth() + 1;

  const currentYear =
    currentDate.getFullYear();


  // ==========================================================
  // STATE
  // ==========================================================

  const [month, setMonth] =
    useState(currentMonth);

  const [year, setYear] =
    useState(currentYear);

  const [category, setCategory] =
    useState("");

  const [categories, setCategories] =
    useState([]);

  const [report, setReport] =
    useState(null);

  const [loading, setLoading] =
    useState(true);


  // ==========================================================
  // MONTHS
  // ==========================================================

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


  // ==========================================================
  // LOAD CATEGORIES
  // ==========================================================

  useEffect(() => {

    const loadCategories = async () => {

      try {

        const data =
          await getCategories();

        setCategories(
          Array.isArray(data)
            ? data
            : []
        );

      } catch (error) {

        console.error(
          "Category loading error:",
          error
        );

      }

    };


    loadCategories();

  }, []);


  // ==========================================================
  // LOAD REPORT
  // ==========================================================

  const loadReport = async () => {

    try {

      setLoading(true);

      const data =
        await getReport(
          month,
          year,
          category
        );

      console.log(
        "REPORT API DATA:",
        data
      );

      setReport(data);

    } catch (error) {

      console.error(
        "Report loading error:",
        error
      );

      if (
        error?.response?.status === 401
      ) {

        toast.error(
          "Session expired. Please login again."
        );

        localStorage.removeItem(
          "token"
        );

        localStorage.removeItem(
          "access_token"
        );

      } else {

        toast.error(
          error?.response?.data?.detail ||
          "Unable to load report."
        );

      }

    } finally {

      setLoading(false);

    }

  };


  // ==========================================================
  // FETCH WHEN FILTER CHANGES
  // ==========================================================

  useEffect(() => {

    loadReport();

  }, [
    month,
    year,
    category,
  ]);


  // ==========================================================
  // SAFE REPORT DATA
  // ==========================================================

  const summary =
    report?.summary || {};


  const rawCategoryData =
    Array.isArray(
      report?.category_analysis
    )
      ? report.category_analysis
      : [];


  const rawBudgetData =
    Array.isArray(
      report?.budget_analysis
    )
      ? report.budget_analysis
      : [];


  const rawDailyData =
    Array.isArray(
      report?.daily_analysis
    )
      ? report.daily_analysis
      : [];


  const rawPaymentData =
    Array.isArray(
      report?.payment_analysis
    )
      ? report.payment_analysis
      : [];


  // ==========================================================
  // MONEY FORMAT
  // ==========================================================

  const money = (value) => {

    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
      }
    ).format(
      Number(value || 0)
    );

  };


  // ==========================================================
  // SUMMARY VALUES
  // ==========================================================

  const totalExpense =
    Number(
      summary.total_expense ??
      summary.total_spent ??
      summary.amount ??
      0
    );


  const transactionCount =
    Number(
      summary.transaction_count ??
      summary.transactions ??
      summary.total_transactions ??
      0
    );


  const averageExpense =
    Number(
      summary.average_expense ??
      summary.average_transaction ??
      summary.average ??
      0
    );


  const highestCategory =
    report?.highest_spending_category;


  // ==========================================================
  // CATEGORY CHART DATA
  // ==========================================================

  const categoryChartData =
    useMemo(() => {

      return rawCategoryData
        .map((item) => {

          const name =
            item.category ??
            item.name ??
            item.category_name ??
            "Others";

          const amount =
            Number(
              item.amount ??
              item.total ??
              item.spent ??
              item.value ??
              0
            );

          return {
            category: name,
            amount,
          };

        })
        .filter(
          (item) =>
            item.amount > 0
        )
        .sort(
          (a, b) =>
            b.amount - a.amount
        );

    }, [
      rawCategoryData,
    ]);


  // ==========================================================
  // MONTHLY TREND DATA
  // ==========================================================

  const monthlyTrendData =
    useMemo(() => {

      const result =
        months.map(
          (monthName, index) => {

            const found =
              rawDailyData.find(
                (item) =>
                  Number(
                    item.month
                  ) === index + 1
              );

            return {
              month: monthName.slice(
                0,
                3
              ),

              amount:
                Number(
                  found?.amount ??
                  found?.total ??
                  0
                ),
            };

          }
        );


      /*
        If backend does not return
        monthly information, use
        budget/category data only.
      */

      if (
        result.some(
          (item) =>
            item.amount > 0
        )
      ) {

        return result;

      }


      return [];

    }, [
      rawDailyData,
    ]);


  // ==========================================================
  // DAILY DATA
  // ==========================================================

  const dailyChartData =
    useMemo(() => {

      return rawDailyData
        .map(
          (item) => ({

            day:
              item.day ??
              item.date ??
              item.label ??
              "",

            amount:
              Number(
                item.amount ??
                item.total ??
                item.spent ??
                0
              ),

          })
        )
        .filter(
          (item) =>
            item.amount > 0
        );

    }, [
      rawDailyData,
    ]);


  // ==========================================================
  // BUDGET DATA
  // ==========================================================

  const budgetChartData =
    useMemo(() => {

      return rawBudgetData
        .map(
          (item) => ({

            category:
              item.category ??
              item.name ??
              "Other",

            budget:
              Number(
                item.budget ??
                item.limit ??
                0
              ),

            spent:
              Number(
                item.spent ??
                item.actual ??
                item.amount ??
                0
              ),

          })
        )
        .filter(
          (item) =>
            item.budget > 0 ||
            item.spent > 0
        );

    }, [
      rawBudgetData,
    ]);


  // ==========================================================
  // PAYMENT DATA
  // ==========================================================

  const paymentChartData =
    useMemo(() => {

      return rawPaymentData
        .map(
          (item) => ({

            payment_method:
              item.payment_method ??
              item.method ??
              item.name ??
              "Other",

            amount:
              Number(
                item.amount ??
                item.total ??
                item.spent ??
                0
              ),

          })
        )
        .filter(
          (item) =>
            item.amount > 0
        );

    }, [
      rawPaymentData,
    ]);


  // ==========================================================
  // TOTAL CATEGORY SPENDING
  // ==========================================================

  const categoryTotal =
    categoryChartData.reduce(
      (sum, item) =>
        sum +
        Number(
          item.amount || 0
        ),
      0
    );


  // ==========================================================
  // SELECTED CATEGORY NAME
  // ==========================================================

  const selectedCategoryName =
    category
      ? category
      : "All Categories";


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (

      <div className="dashboard-layout">

        <aside className="dashboard-sidebar">

          <Sidebar />

        </aside>


        <div className="dashboard-main">

          <DashboardNavbar />

          <main className="dashboard-content">

            <div className="reports-loading">

              <div className="reports-spinner" />

              <h2>
                Loading reports...
              </h2>

              <p>
                Fetching your financial data.
              </p>

            </div>

          </main>

        </div>

      </div>

    );

  }


  // ==========================================================
  // MAIN UI
  // ==========================================================

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

        <DashboardNavbar />


        <main className="dashboard-content">

          <div className="reports-page">


            {/* ==================================================
                HEADER
            ================================================== */}

            <section className="reports-header">

              <div>

                <div className="reports-title-row">

                  <div className="reports-title-icon">

                    <BarChart3 size={23} />

                  </div>

                  <div>

                    <h1>
                      Reports
                    </h1>

                    <p>
                      Understand your spending and
                      financial patterns.
                    </p>

                  </div>

                </div>

              </div>


              {/* FILTERS */}

              <div className="reports-filters">

                <select
                  value={month}
                  onChange={(e) =>
                    setMonth(
                      Number(
                        e.target.value
                      )
                    )
                  }
                >

                  {months.map(
                    (monthName, index) => (

                      <option
                        key={monthName}
                        value={index + 1}
                      >
                        {monthName}
                      </option>

                    )
                  )}

                </select>


                <select
                  value={year}
                  onChange={(e) =>
                    setYear(
                      Number(
                        e.target.value
                      )
                    )
                  }
                >

                  <option value={currentYear - 2}>
                    {currentYear - 2}
                  </option>

                  <option value={currentYear - 1}>
                    {currentYear - 1}
                  </option>

                  <option value={currentYear}>
                    {currentYear}
                  </option>

                  <option value={currentYear + 1}>
                    {currentYear + 1}
                  </option>

                </select>


                <select
                  value={category}
                  onChange={(e) =>
                    setCategory(
                      e.target.value
                    )
                  }
                >

                  <option value="">
                    All Categories
                  </option>

                  {categories.map(
                    (item) => (

                      <option
                        key={
                          item._id ||
                          item.id ||
                          item.name
                        }
                        value={
                          item.name
                        }
                      >
                        {item.name}
                      </option>

                    )
                  )}

                </select>

              </div>

            </section>


            {/* ==================================================
                FILTER INFORMATION
            ================================================== */}

            <div className="reports-filter-info">

              <span>
                Showing report for
              </span>

              <strong>
                {months[month - 1]} {year}
              </strong>

              <span>
                •
              </span>

              <strong>
                {selectedCategoryName}
              </strong>

            </div>


            {/* ==================================================
                SUMMARY CARDS
            ================================================== */}

            <section className="reports-summary-grid">


              {/* TOTAL */}

              <div className="reports-summary-card green-card">

                <div>

                  <span>
                    Total Spending
                  </span>

                  <h2>
                    {money(
                      totalExpense
                    )}
                  </h2>

                  <p>
                    Total expenses for selected period
                  </p>

                </div>

                <div className="reports-summary-icon green">

                  <Wallet size={21} />

                </div>

              </div>


              {/* TRANSACTIONS */}

              <div className="reports-summary-card blue-card">

                <div>

                  <span>
                    Transactions
                  </span>

                  <h2>
                    {transactionCount}
                  </h2>

                  <p>
                    Recorded transactions
                  </p>

                </div>

                <div className="reports-summary-icon blue">

                  <Receipt size={21} />

                </div>

              </div>


              {/* AVERAGE */}

              <div className="reports-summary-card purple-card">

                <div>

                  <span>
                    Average Expense
                  </span>

                  <h2>
                    {money(
                      averageExpense
                    )}
                  </h2>

                  <p>
                    Average transaction amount
                  </p>

                </div>

                <div className="reports-summary-icon purple">

                  <TrendingUp size={21} />

                </div>

              </div>


              {/* HIGHEST CATEGORY */}

              <div className="reports-summary-card orange-card">

                <div>

                  <span>
                    Highest Category
                  </span>

                  <h2 className="category-summary-name">

                    {highestCategory?.category ||
                     highestCategory?.name ||
                     "No data"}

                  </h2>

                  <p>
                    Highest spending category
                  </p>

                </div>

                <div className="reports-summary-icon orange">

                  <Target size={21} />

                </div>

              </div>

            </section>


            {/* ==================================================
                CATEGORY + PAYMENT
            ================================================== */}

            <section className="reports-two-column">


              {/* =================================================
                  CATEGORY PIE
              ================================================= */}

              <div className="reports-card">

                <div className="reports-card-header">

                  <div>

                    <h2>
                      Spending by Category
                    </h2>

                    <p>
                      Breakdown of your spending
                    </p>

                  </div>

                  <PieChartIcon
                    size={21}
                    className="reports-header-icon"
                  />

                </div>


                {categoryChartData.length === 0 ? (

                  <div className="reports-empty-chart">

                    <PieChartIcon size={35} />

                    <p>
                      No category data available.
                    </p>

                  </div>

                ) : (

                  <div className="reports-pie-wrapper">

                    <ResponsiveContainer
                      width="100%"
                      height={350}
                    >

                      <PieChart>

                        <Pie
                          data={
                            categoryChartData
                          }
                          dataKey="amount"
                          nameKey="category"
                          cx="50%"
                          cy="50%"
                          innerRadius={75}
                          outerRadius={125}
                          paddingAngle={3}
                        >

                          {categoryChartData.map(
                            (item, index) => (

                              <Cell
                                key={
                                  `category-${index}`
                                }
                                fill={
                                  CATEGORY_COLORS[
                                    index %
                                    CATEGORY_COLORS.length
                                  ]
                                }
                              />

                            )
                          )}

                        </Pie>


                        <Tooltip
                          formatter={(value) =>
                            money(value)
                          }
                        />


                        <Legend />

                      </PieChart>

                    </ResponsiveContainer>


                    <div className="reports-pie-total">

                      <span>
                        Total
                      </span>

                      <strong>
                        {money(
                          categoryTotal
                        )}
                      </strong>

                    </div>

                  </div>

                )}

              </div>


              {/* =================================================
                  PAYMENT METHODS
              ================================================= */}

              <div className="reports-card">

                <div className="reports-card-header">

                  <div>

                    <h2>
                      Spending by Payment Method
                    </h2>

                    <p>
                      Where your money is being spent
                    </p>

                  </div>

                  <CreditCard
                    size={21}
                    className="reports-header-icon"
                  />

                </div>


                {paymentChartData.length === 0 ? (

                  <div className="reports-empty-chart">

                    <CreditCard size={35} />

                    <p>
                      No payment data available.
                    </p>

                  </div>

                ) : (

                  <div className="reports-payment-chart">

                    <ResponsiveContainer
                      width="100%"
                      height={350}
                    >

                      <PieChart>

                        <Pie
                          data={
                            paymentChartData
                          }
                          dataKey="amount"
                          nameKey="payment_method"
                          cx="50%"
                          cy="50%"
                          outerRadius={115}
                          paddingAngle={3}
                          label
                        >

                          {paymentChartData.map(
                            (item, index) => (

                              <Cell
                                key={
                                  `payment-${index}`
                                }
                                fill={
                                  PAYMENT_COLORS[
                                    index %
                                    PAYMENT_COLORS.length
                                  ]
                                }
                              />

                            )
                          )}

                        </Pie>


                        <Tooltip
                          formatter={(value) =>
                            money(value)
                          }
                        />


                        <Legend />

                      </PieChart>

                    </ResponsiveContainer>

                  </div>

                )}

              </div>

            </section>


            {/* ==================================================
                DAILY SPENDING
            ================================================== */}

            <section className="reports-card reports-chart-card">

              <div className="reports-card-header">

                <div>

                  <h2>
                    Daily Spending
                  </h2>

                  <p>
                    Spending activity during{" "}
                    {months[month - 1]} {year}
                  </p>

                </div>

                <div className="reports-chart-badge">

                  {money(
                    totalExpense
                  )}

                </div>

              </div>


              {dailyChartData.length === 0 ? (

                <div className="reports-empty-chart large">

                  <BarChart3 size={40} />

                  <p>
                    No daily expense data available.
                  </p>

                </div>

              ) : (

                <div className="reports-large-chart">

                  <ResponsiveContainer
                    width="100%"
                    height={370}
                  >

                    <BarChart
                      data={
                        dailyChartData
                      }
                      margin={{
                        top: 15,
                        right: 20,
                        left: 10,
                        bottom: 10,
                      }}
                    >

                      <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="#E5E7EB"
                      />


                      <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        tick={{
                          fill: "#64748B",
                          fontSize: 12,
                        }}
                      />


                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{
                          fill: "#64748B",
                          fontSize: 12,
                        }}
                        tickFormatter={(value) =>
                          `₹${Number(
                            value
                          ).toLocaleString(
                            "en-IN"
                          )}`
                        }
                      />


                      <Tooltip
                        formatter={(value) => [
                          money(value),
                          "Spent",
                        ]}
                        contentStyle={{
                          border:
                            "1px solid #E5E7EB",
                          borderRadius:
                            "12px",
                          boxShadow:
                            "0 8px 25px rgba(0,0,0,0.08)",
                        }}
                      />


                      <Bar
                        dataKey="amount"
                        name="Spent"
                        fill="#287EF5"
                        radius={[
                          7,
                          7,
                          0,
                          0,
                        ]}
                        maxBarSize={38}
                      />

                    </BarChart>

                  </ResponsiveContainer>

                </div>

              )}

            </section>


            {/* ==================================================
                BUDGET VS ACTUAL
            ================================================== */}

            <section className="reports-card reports-chart-card">

              <div className="reports-card-header">

                <div>

                  <h2>
                    Budget vs Actual
                  </h2>

                  <p>
                    Compare your budget with actual spending
                  </p>

                </div>

                <Target
                  size={21}
                  className="reports-header-icon"
                />

              </div>


              {budgetChartData.length === 0 ? (

                <div className="reports-empty-chart large">

                  <Target size={40} />

                  <p>
                    No budget data available.
                  </p>

                </div>

              ) : (

                <div className="reports-large-chart">

                  <ResponsiveContainer
                    width="100%"
                    height={390}
                  >

                    <BarChart
                      data={
                        budgetChartData
                      }
                      margin={{
                        top: 15,
                        right: 20,
                        left: 10,
                        bottom: 10,
                      }}
                    >

                      <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="#E5E7EB"
                      />


                      <XAxis
                        dataKey="category"
                        axisLine={false}
                        tickLine={false}
                        tick={{
                          fill: "#64748B",
                          fontSize: 12,
                        }}
                      />


                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{
                          fill: "#64748B",
                          fontSize: 12,
                        }}
                        tickFormatter={(value) =>
                          `₹${Number(
                            value
                          ).toLocaleString(
                            "en-IN"
                          )}`
                        }
                      />


                      <Tooltip
                        formatter={(value) =>
                          money(value)
                        }
                        contentStyle={{
                          border:
                            "1px solid #E5E7EB",
                          borderRadius:
                            "12px",
                        }}
                      />


                      <Legend />


                      <Bar
                        dataKey="budget"
                        name="Budget"
                        fill="#A93BFF"
                        radius={[
                          6,
                          6,
                          0,
                          0,
                        ]}
                        maxBarSize={32}
                      />


                      <Bar
                        dataKey="spent"
                        name="Actual Spent"
                        fill="#C15B3D"
                        radius={[
                          6,
                          6,
                          0,
                          0,
                        ]}
                        maxBarSize={32}
                      />

                    </BarChart>

                  </ResponsiveContainer>

                </div>

              )}

            </section>


            {/* ==================================================
                CATEGORY TABLE
            ================================================== */}

            <section className="reports-card">

              <div className="reports-card-header">

                <div>

                  <h2>
                    Category Breakdown
                  </h2>

                  <p>
                    Detailed spending by category
                  </p>

                </div>

              </div>


              {categoryChartData.length === 0 ? (

                <div className="reports-empty-table">

                  No category data available.

                </div>

              ) : (

                <div className="reports-table-wrapper">

                  <table className="reports-table">

                    <thead>

                      <tr>

                        <th>
                          Category
                        </th>

                        <th>
                          Amount
                        </th>

                        <th>
                          Percentage
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {categoryChartData.map(
                        (item, index) => {

                          const percentage =
                            categoryTotal > 0
                              ? (
                                  item.amount /
                                  categoryTotal
                                ) *
                                100
                              : 0;


                          return (

                            <tr
                              key={
                                item.category
                              }
                            >

                              <td>

                                <div className="reports-category-name">

                                  <span
                                    className="reports-color-dot"
                                    style={{
                                      background:
                                        CATEGORY_COLORS[
                                          index %
                                          CATEGORY_COLORS.length
                                        ],
                                    }}
                                  />

                                  <strong>
                                    {item.category}
                                  </strong>

                                </div>

                              </td>


                              <td className="reports-amount">

                                {money(
                                  item.amount
                                )}

                              </td>


                              <td>

                                <div className="reports-percentage-cell">

                                  <span>
                                    {percentage.toFixed(
                                      1
                                    )}%
                                  </span>

                                  <div className="reports-mini-progress">

                                    <div
                                      style={{
                                        width:
                                          `${percentage}%`,
                                        background:
                                          CATEGORY_COLORS[
                                            index %
                                            CATEGORY_COLORS.length
                                          ],
                                      }}
                                    />

                                  </div>

                                </div>

                              </td>

                            </tr>

                          );

                        }
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </section>


            {/* ==================================================
                BUDGET TABLE
            ================================================== */}

            <section className="reports-card">

              <div className="reports-card-header">

                <div>

                  <h2>
                    Budget Analysis
                  </h2>

                  <p>
                    Budget performance by category
                  </p>

                </div>

              </div>


              {budgetChartData.length === 0 ? (

                <div className="reports-empty-table">

                  No budget data available.

                </div>

              ) : (

                <div className="reports-table-wrapper">

                  <table className="reports-table">

                    <thead>

                      <tr>

                        <th>
                          Category
                        </th>

                        <th>
                          Budget
                        </th>

                        <th>
                          Actual
                        </th>

                        <th>
                          Difference
                        </th>

                        <th>
                          Status
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {budgetChartData.map(
                        (item) => {

                          const difference =
                            item.budget -
                            item.spent;

                          const exceeded =
                            difference < 0;


                          return (

                            <tr
                              key={
                                item.category
                              }
                            >

                              <td>

                                <strong>
                                  {item.category}
                                </strong>

                              </td>


                              <td>
                                {money(
                                  item.budget
                                )}
                              </td>


                              <td>
                                {money(
                                  item.spent
                                )}
                              </td>


                              <td
                                className={
                                  exceeded
                                    ? "reports-danger"
                                    : "reports-success"
                                }
                              >

                                {money(
                                  Math.abs(
                                    difference
                                  )
                                )}

                              </td>


                              <td>

                                <span
                                  className={
                                    exceeded
                                      ? "reports-status danger"
                                      : "reports-status success"
                                  }
                                >

                                  {exceeded
                                    ? "Exceeded"
                                    : "Within Budget"}

                                </span>

                              </td>

                            </tr>

                          );

                        }
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </section>


            {/* ==================================================
                PAYMENT METHOD TABLE
            ================================================== */}

            <section className="reports-card">

              <div className="reports-card-header">

                <div>

                  <h2>
                    Payment Method Analysis
                  </h2>

                  <p>
                    Spending distribution by payment method
                  </p>

                </div>

                <CreditCard
                  size={21}
                  className="reports-header-icon"
                />

              </div>


              {paymentChartData.length === 0 ? (

                <div className="reports-empty-table">

                  No payment data available.

                </div>

              ) : (

                <div className="reports-table-wrapper">

                  <table className="reports-table">

                    <thead>

                      <tr>

                        <th>
                          Payment Method
                        </th>

                        <th>
                          Amount
                        </th>

                        <th>
                          Percentage
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {paymentChartData.map(
                        (item, index) => {

                          const paymentTotal =
                            paymentChartData.reduce(
                              (sum, current) =>
                                sum +
                                current.amount,
                              0
                            );

                          const percentage =
                            paymentTotal > 0
                              ? (
                                  item.amount /
                                  paymentTotal
                                ) *
                                100
                              : 0;


                          return (

                            <tr
                              key={
                                item.payment_method
                              }
                            >

                              <td>

                                <div className="reports-category-name">

                                  <span
                                    className="reports-color-dot"
                                    style={{
                                      background:
                                        PAYMENT_COLORS[
                                          index %
                                          PAYMENT_COLORS.length
                                        ],
                                    }}
                                  />

                                  <strong>
                                    {
                                      item.payment_method
                                    }
                                  </strong>

                                </div>

                              </td>


                              <td className="reports-amount">

                                {money(
                                  item.amount
                                )}

                              </td>


                              <td>

                                {percentage.toFixed(
                                  1
                                )}%

                              </td>

                            </tr>

                          );

                        }
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </section>


            {/* ==================================================
                HIGHEST CATEGORY
            ================================================== */}

            {highestCategory && (

              <section className="reports-highest-card">

                <div className="reports-highest-icon">

                  <AlertTriangle
                    size={23}
                  />

                </div>


                <div>

                  <span>
                    Highest Spending Category
                  </span>

                  <h2>

                    {highestCategory.category ||
                     highestCategory.name ||
                     "No category"}

                  </h2>

                  <p>

                    {money(
                      highestCategory.amount ||
                      highestCategory.total ||
                      0
                    )}

                    {" "}spent in this category.

                  </p>

                </div>

              </section>

            )}

          </div>

        </main>

      </div>

    </div>

  );

}


export default Reports;