function BudgetProgress({ expenses }) {
  // Temporary Monthly Budgets
  // Later these will come from the Budget Module API

  const budgetLimits = {
    Food: 10000,
    Shopping: 8000,
    Travel: 5000,
    Bills: 7000,
    Entertainment: 6000,
    Health: 4000,
    Education: 10000,
    Others: 5000,
  };

  // Calculate category-wise spending
  const categoryTotals = {};

  expenses.forEach((expense) => {
    const category = expense.category;

    if (!categoryTotals[category]) {
      categoryTotals[category] = 0;
    }

    categoryTotals[category] += Number(expense.amount);
  });

  const getColor = (percentage) => {
    if (percentage <= 50) return "bg-green-500";
    if (percentage <= 80) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getEmoji = (category) => {
    switch (category) {
      case "Food":
        return "🍔";

      case "Shopping":
        return "🛍️";

      case "Travel":
        return "🚕";

      case "Bills":
        return "💡";

      case "Entertainment":
        return "🎬";

      case "Health":
        return "🏥";

      case "Education":
        return "📚";

      default:
        return "📦";
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-2xl font-bold text-[#12172B]">
        Budget Progress
      </h2>

      <p className="text-gray-500 mt-1">
        Monthly category spending
      </p>

      <div className="mt-8 space-y-7">
        {Object.entries(budgetLimits).map(([category, limit]) => {
          const spent = categoryTotals[category] || 0;

          const percentage = Math.min(
            (spent / limit) * 100,
            100
          );

          return (
            <div key={category}>
              <div className="flex justify-between mb-2">
                <span className="font-medium">
                  {getEmoji(category)} {category}
                </span>

                <span className="text-sm text-gray-500">
                  ₹{spent.toLocaleString()} / ₹
                  {limit.toLocaleString()}
                </span>
              </div>

              <div className="w-full h-3 bg-gray-200 rounded-full">
                <div
                  className={`${getColor(
                    percentage
                  )} h-3 rounded-full transition-all duration-500`}
                  style={{
                    width: `${percentage}%`,
                  }}
                />
              </div>

              <div className="flex justify-between mt-2 text-xs">
                <span className="text-gray-500">
                  {percentage.toFixed(0)}% Used
                </span>

                <span
                  className={
                    spent > limit
                      ? "text-red-600 font-semibold"
                      : "text-green-600 font-semibold"
                  }
                >
                  {spent > limit
                    ? "Budget Exceeded"
                    : `₹${(
                        limit - spent
                      ).toLocaleString()} Left`}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default BudgetProgress;