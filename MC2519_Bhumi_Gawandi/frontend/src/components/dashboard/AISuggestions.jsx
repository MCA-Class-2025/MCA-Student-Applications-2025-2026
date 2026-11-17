import {
  Bot,
  TrendingUp,
  Wallet,
  Lightbulb,
} from "lucide-react";

function AISuggestions({ expenses }) {
  const totalExpense = expenses.reduce(
    (sum, expense) => sum + Number(expense.amount),
    0
  );

  const categoryTotals = {};

  expenses.forEach((expense) => {
    if (!categoryTotals[expense.category]) {
      categoryTotals[expense.category] = 0;
    }

    categoryTotals[expense.category] += Number(expense.amount);
  });

  const sortedCategories = Object.entries(categoryTotals).sort(
    (a, b) => b[1] - a[1]
  );

  const highestCategory =
    sortedCategories.length > 0
      ? sortedCategories[0][0]
      : "No Category";

  const highestAmount =
    sortedCategories.length > 0
      ? sortedCategories[0][1]
      : 0;

  const foodExpense = categoryTotals["Food"] || 0;
  const shoppingExpense = categoryTotals["Shopping"] || 0;

  const suggestions = [];

  if (foodExpense > totalExpense * 0.30) {
    suggestions.push({
      icon: <TrendingUp size={20} />,
      title: "Reduce Food Spending",
      text: `You spent ₹${foodExpense.toLocaleString()} on Food. Consider cooking at home more often.`,
    });
  }

  if (shoppingExpense > totalExpense * 0.25) {
    suggestions.push({
      icon: <Wallet size={20} />,
      title: "Shopping Alert",
      text: `Shopping expenses reached ₹${shoppingExpense.toLocaleString()}. Reducing impulse purchases can improve savings.`,
    });
  }

  suggestions.push({
    icon: <Lightbulb size={20} />,
    title: "Highest Spending Category",
    text: `${highestCategory} is your highest expense category with ₹${highestAmount.toLocaleString()} spent.`,
  });

  if (suggestions.length < 3) {
    suggestions.push({
      icon: <Wallet size={20} />,
      title: "Great Job!",
      text: "Your spending pattern looks balanced this month.",
    });
  }

  const healthScore =
    totalExpense < 20000
      ? 95
      : totalExpense < 40000
      ? 85
      : totalExpense < 60000
      ? 75
      : 65;

  return (
    <div className="bg-[#12172B] rounded-3xl p-6 text-white h-full">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-[#1F6F5C] flex items-center justify-center">
          <Bot size={28} />
        </div>

        <div>
          <h2 className="text-2xl font-bold">
            AI Financial Assistant
          </h2>

          <p className="text-gray-400 text-sm">
            Personalized recommendations
          </p>
        </div>
      </div>

      <div className="mt-8 space-y-5">
        {suggestions.map((item) => (
          <div
            key={item.title}
            className="bg-[#1A2136] rounded-2xl p-5"
          >
            <div className="flex items-center gap-3 text-[#2CC295]">
              {item.icon}

              <h3 className="font-semibold">
                {item.title}
              </h3>
            </div>

            <p className="text-gray-300 mt-3 leading-7">
              {item.text}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-[#1F6F5C] rounded-2xl p-6">
        <p className="text-lg font-semibold">
          Financial Health Score
        </p>

        <h1 className="text-5xl font-bold mt-3">
          {healthScore}%
        </h1>

        <p className="mt-3">
          {healthScore >= 90
            ? "Excellent! Your spending habits are healthy."
            : healthScore >= 80
            ? "Good financial management. Keep it up!"
            : healthScore >= 70
            ? "Your spending is increasing. Monitor your expenses."
            : "Your expenses are quite high. Consider reducing unnecessary spending."}
        </p>
      </div>
    </div>
  );
}

export default AISuggestions;