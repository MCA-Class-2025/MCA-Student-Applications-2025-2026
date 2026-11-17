import { RotateCcw } from "lucide-react";

function ExpenseFilters({
  category,
  setCategory,
  paymentMethod,
  setPaymentMethod,
  clearFilters,
}) {
  return (
    <div className="expense-filter-fields">

      {/* CATEGORY */}

      <div className="expense-field">

        <label>
          Category
        </label>

        <select
          value={category}
          onChange={(e) =>
            setCategory(e.target.value)
          }
        >
          <option value="">
            All Categories
          </option>

          <option value="Food">
            Food
          </option>

          <option value="Travel">
            Travel
          </option>

          <option value="Shopping">
            Shopping
          </option>

          <option value="Bills">
            Bills
          </option>

          <option value="Entertainment">
            Entertainment
          </option>

          <option value="Health">
            Health
          </option>

          <option value="Education">
            Education
          </option>

          <option value="Others">
            Others
          </option>
        </select>

      </div>

      {/* PAYMENT METHOD */}

      <div className="expense-field">

        <label>
          Payment Method
        </label>

        <select
          value={paymentMethod}
          onChange={(e) =>
            setPaymentMethod(e.target.value)
          }
        >
          <option value="">
            All Methods
          </option>

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
        </select>

      </div>

      {/* CLEAR */}

      <div className="expense-clear-wrapper">

        <button
          type="button"
          onClick={clearFilters}
          className="expense-clear-button"
        >
          <RotateCcw size={17} />

          Clear Filters
        </button>

      </div>

    </div>
  );
}

export default ExpenseFilters;