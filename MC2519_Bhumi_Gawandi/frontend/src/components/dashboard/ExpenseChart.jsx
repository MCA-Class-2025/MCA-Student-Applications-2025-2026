import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function ExpenseChart({ expenses = [] }) {
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  const currentYear = new Date().getFullYear();

  // ============================================================
  // MONTHLY DATA
  // ============================================================

  const monthlyData = months.map(
    (month, index) => {
      const total = expenses
        .filter((expense) => {
          if (!expense.date) {
            return false;
          }

          const date = new Date(
            expense.date
          );

          return (
            date.getFullYear() ===
              currentYear &&
            date.getMonth() === index
          );
        })
        .reduce(
          (sum, expense) =>
            sum +
            Number(
              expense.amount || 0
            ),
          0
        );

      return {
        month,
        expense: total,
      };
    }
  );

  // ============================================================
  // TOOLTIP
  // ============================================================

  const formatTooltip = (value) => {
    return `₹${Number(value).toLocaleString(
      "en-IN"
    )}`;
  };

  // ============================================================
  // TOTAL YEAR EXPENSE
  // ============================================================

  const yearlyExpense = monthlyData.reduce(
    (sum, item) =>
      sum + Number(item.expense || 0),
    0
  );

  return (
    <section
      className="
        w-full
        bg-white
        rounded-[24px]
        border
        border-[#E5E7EB]
        shadow-[0_4px_18px_rgba(18,23,43,0.04)]
        p-7
        md:p-8
      "
    >

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div
        className="
          flex
          flex-col
          md:flex-row
          md:items-center
          md:justify-between
          gap-4
          mb-8
        "
      >

        <div>

          <h2
            className="
              text-[27px]
              font-bold
              text-[#12172B]
            "
          >
            Monthly Expense
          </h2>

          <p
            className="
              text-[16px]
              text-[#64748B]
              mt-2
            "
          >
            Your spending trend for {currentYear}
          </p>

        </div>

        <div className="flex items-center gap-3">

          <div
            className="
              px-5
              py-3
              rounded-xl
              bg-[#EAF5F1]
              text-[#1F6F5C]
              font-semibold
              text-[15px]
            "
          >
            Year: {currentYear}
          </div>

          <div
            className="
              px-5
              py-3
              rounded-xl
              bg-[#1F6F5C]
              text-white
              font-semibold
              text-[15px]
            "
          >
            ₹{yearlyExpense.toLocaleString(
              "en-IN"
            )}
          </div>

        </div>

      </div>

      {/* ======================================================
          CHART
      ====================================================== */}

      <div className="w-full h-[400px]">

        <ResponsiveContainer
          width="100%"
          height="100%"
        >

          <BarChart
            data={monthlyData}
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
              dataKey="month"
              tick={{
                fill: "#64748B",
                fontSize: 14,
              }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              tick={{
                fill: "#64748B",
                fontSize: 13,
              }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) =>
                `₹${value}`
              }
            />

            <Tooltip
              formatter={formatTooltip}
              cursor={{
                fill: "#F3F7F5",
              }}
              contentStyle={{
                borderRadius: "12px",
                border:
                  "1px solid #E5E7EB",
                boxShadow:
                  "0 8px 25px rgba(0,0,0,0.10)",
              }}
            />

            <Bar
              dataKey="expense"
              fill="#1F6F5C"
              radius={[
                8,
                8,
                0,
                0,
              ]}
              barSize={42}
            />

          </BarChart>

        </ResponsiveContainer>

      </div>

    </section>
  );
}

export default ExpenseChart;