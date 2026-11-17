import {
  Wallet,
  TrendingUp,
  CalendarDays,
  Receipt,
} from "lucide-react";


function SummaryCards({
  expenses = [],
  user,
}) {


  /* ============================================================
     CURRENCY
  ============================================================ */

  const currency =
    user?.preferred_currency || "INR";


  /* ============================================================
     DATE
  ============================================================ */

  const today = new Date();


  const isToday = (date) => {

    if (!date) return false;

    const d = new Date(date);

    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
    );

  };


  const isCurrentMonth = (date) => {

    if (!date) return false;

    const d = new Date(date);

    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth()
    );

  };


  /* ============================================================
     TOTAL EXPENSE
  ============================================================ */

  const totalExpense = expenses.reduce(
    (sum, expense) =>
      sum + Number(expense.amount || 0),
    0
  );


  /* ============================================================
     MONTHLY EXPENSE
  ============================================================ */

  const monthlyExpense = expenses
    .filter((expense) =>
      isCurrentMonth(expense.date)
    )
    .reduce(
      (sum, expense) =>
        sum + Number(expense.amount || 0),
      0
    );


  /* ============================================================
     TODAY
  ============================================================ */

  const todayExpense = expenses
    .filter((expense) =>
      isToday(expense.date)
    )
    .reduce(
      (sum, expense) =>
        sum + Number(expense.amount || 0),
      0
    );


  /* ============================================================
     TRANSACTIONS
  ============================================================ */

  const transactionCount =
    expenses.length;


  /* ============================================================
     INCOME
  ============================================================ */

  const income =
    Number(user?.monthly_income || 0);


  /* ============================================================
     REMAINING
  ============================================================ */

  const remaining =
    Math.max(
      income - monthlyExpense,
      0
    );


  /* ============================================================
     FORMAT
  ============================================================ */

  const formatCurrency = (amount) => {

    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
      }
    ).format(amount);

  };


  /* ============================================================
     CARDS
  ============================================================ */

  const cards = [

    {
      title: "Total Spent",
      value: formatCurrency(totalExpense),
      description: "All recorded expenses",
      icon: Wallet,
      type: "expense",
    },

    {
      title: "Total Income",
      value: formatCurrency(income),
      description: "Your monthly income",
      icon: TrendingUp,
      type: "income",
    },

    {
      title: "Budget Remaining",
      value: formatCurrency(remaining),
      description:
        income > 0
          ? `${Math.round(
              (monthlyExpense / income) * 100
            )}% of income used`
          : "Add your income to track this",
      icon: Wallet,
      type: "budget",
    },

    {
      title: "Today",
      value: formatCurrency(todayExpense),
      description:
        `${transactionCount} transactions recorded`,
      icon: CalendarDays,
      type: "today",
    },

  ];


  return (

    <>

      {cards.map((card) => {

        const Icon = card.icon;

        return (

          <div
            key={card.title}
            className={`dashboard-summary-card ${card.type}`}
          >

            <div>

              <p className="summary-card-label">
                {card.title}
              </p>

              <h2 className="summary-card-value">
                {card.value}
              </h2>

              <p className="summary-card-description">
                {card.description}
              </p>

            </div>


            <div className="summary-card-icon">

              <Icon
                size={21}
                strokeWidth={1.8}
              />

            </div>

          </div>

        );

      })}

    </>

  );

}


export default SummaryCards;