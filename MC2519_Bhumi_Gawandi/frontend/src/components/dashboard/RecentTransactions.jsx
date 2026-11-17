import { ArrowRight, WalletCards } from "lucide-react";
import { useNavigate } from "react-router-dom";

function RecentTransactions({ expenses = [] }) {
  const navigate = useNavigate();

  const recentExpenses = [...expenses]
    .sort(
      (a, b) =>
        new Date(b.date || 0) -
        new Date(a.date || 0)
    )
    .slice(0, 8);

  const formatCurrency = (amount) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Number(amount || 0));

  const formatDate = (date) => {
    if (!date) return "-";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "-";
    }

    return parsedDate.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <section
      className="
        w-full
        bg-white
        rounded-[24px]
        border
        border-[#E5E7EB]
        shadow-[0_4px_18px_rgba(18,23,43,0.04)]
        overflow-hidden
      "
    >

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div
        className="
          px-8
          py-7
          flex
          items-center
          justify-between
          gap-6
          border-b
          border-[#E8EAED]
        "
      >

        <div>
          <h2
            className="
              text-[26px]
              font-bold
              text-[#12172B]
              leading-tight
            "
          >
            Recent Transactions
          </h2>

          <p
            className="
              mt-2
              text-[15px]
              text-[#64748B]
            "
          >
            Your latest recorded expenses
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/expenses")}
          className="
            shrink-0
            flex
            items-center
            gap-2
            px-6
            py-3
            rounded-xl
            bg-[#1F6F5C]
            text-white
            font-semibold
            text-[15px]
            hover:bg-[#175646]
            transition
          "
        >
          View All

          <ArrowRight
            size={18}
          />
        </button>

      </div>


      {/* =====================================================
          EMPTY STATE
      ====================================================== */}

      {recentExpenses.length === 0 ? (

        <div
          className="
            py-20
            px-6
            text-center
          "
        >

          <div
            className="
              w-16
              h-16
              mx-auto
              rounded-2xl
              bg-[#EAF5F1]
              text-[#1F6F5C]
              flex
              items-center
              justify-center
            "
          >
            <WalletCards
              size={30}
            />
          </div>

          <h3
            className="
              mt-5
              text-xl
              font-bold
              text-[#12172B]
            "
          >
            No expenses yet
          </h3>

          <p
            className="
              mt-2
              text-[15px]
              text-[#64748B]
            "
          >
            Add your first expense to see it here.
          </p>

          <button
            type="button"
            onClick={() =>
              navigate("/add-expense")
            }
            className="
              mt-6
              px-6
              py-3
              rounded-xl
              bg-[#1F6F5C]
              text-white
              font-semibold
              hover:bg-[#175646]
              transition
            "
          >
            Add Expense
          </button>

        </div>

      ) : (

        <>
          {/* =================================================
              DESKTOP TABLE
          ================================================== */}

          <div
            className="
              hidden
              md:block
              w-full
            "
          >

            <table
              className="
                w-full
                table-fixed
                border-collapse
              "
            >

              <thead>

                <tr
                  className="
                    bg-[#FAFBFA]
                    border-b
                    border-[#E5E7EB]
                  "
                >

                  <th
                    className="
                      w-[34%]
                      px-8
                      py-5
                      text-left
                      text-[13px]
                      font-bold
                      uppercase
                      tracking-[0.08em]
                      text-[#64748B]
                    "
                  >
                    Transaction
                  </th>

                  <th
                    className="
                      w-[18%]
                      px-5
                      py-5
                      text-left
                      text-[13px]
                      font-bold
                      uppercase
                      tracking-[0.08em]
                      text-[#64748B]
                    "
                  >
                    Category
                  </th>

                  <th
                    className="
                      w-[16%]
                      px-5
                      py-5
                      text-left
                      text-[13px]
                      font-bold
                      uppercase
                      tracking-[0.08em]
                      text-[#64748B]
                    "
                  >
                    Payment
                  </th>

                  <th
                    className="
                      w-[16%]
                      px-5
                      py-5
                      text-left
                      text-[13px]
                      font-bold
                      uppercase
                      tracking-[0.08em]
                      text-[#64748B]
                    "
                  >
                    Date
                  </th>

                  <th
                    className="
                      w-[16%]
                      px-8
                      py-5
                      text-right
                      text-[13px]
                      font-bold
                      uppercase
                      tracking-[0.08em]
                      text-[#64748B]
                    "
                  >
                    Amount
                  </th>

                </tr>

              </thead>


              <tbody>

                {recentExpenses.map(
                  (expense, index) => (

                    <tr
                      key={
                        expense._id ||
                        expense.id ||
                        index
                      }
                      className="
                        border-b
                        border-[#EEF0F2]
                        last:border-b-0
                        hover:bg-[#FAFCFB]
                        transition
                      "
                    >

                      {/* Transaction */}

                      <td
                        className="
                          px-8
                          py-5
                        "
                      >

                        <div
                          className="
                            flex
                            items-center
                            gap-4
                            min-w-0
                          "
                        >

                          <div
                            className="
                              w-12
                              h-12
                              rounded-xl
                              bg-[#EAF5F1]
                              text-[#1F6F5C]
                              flex
                              items-center
                              justify-center
                              shrink-0
                            "
                          >

                            <WalletCards
                              size={21}
                            />

                          </div>


                          <div
                            className="
                              min-w-0
                            "
                          >

                            <p
                              className="
                                text-[16px]
                                font-bold
                                text-[#12172B]
                                truncate
                              "
                            >
                              {expense.title ||
                                "Untitled Expense"}
                            </p>


                            {expense.notes ? (

                              <p
                                className="
                                  mt-1
                                  text-[13px]
                                  text-[#64748B]
                                  truncate
                                "
                              >
                                {expense.notes}
                              </p>

                            ) : (

                              <p
                                className="
                                  mt-1
                                  text-[13px]
                                  text-[#94A3B8]
                                "
                              >
                                No notes
                              </p>

                            )}

                          </div>

                        </div>

                      </td>


                      {/* Category */}

                      <td
                        className="
                          px-5
                          py-5
                        "
                      >

                        <span
                          className="
                            inline-flex
                            max-w-full
                            px-4
                            py-2
                            rounded-full
                            bg-[#E4F8EC]
                            text-[#078A47]
                            text-[13px]
                            font-semibold
                            truncate
                          "
                        >
                          {expense.category ||
                            "Other"}
                        </span>

                      </td>


                      {/* Payment */}

                      <td
                        className="
                          px-5
                          py-5
                          text-[15px]
                          font-medium
                          text-[#475569]
                          truncate
                        "
                      >
                        {expense.payment_method ||
                          "-"}
                      </td>


                      {/* Date */}

                      <td
                        className="
                          px-5
                          py-5
                          text-[15px]
                          text-[#64748B]
                          whitespace-nowrap
                        "
                      >
                        {formatDate(
                          expense.date
                        )}
                      </td>


                      {/* Amount */}

                      <td
                        className="
                          px-8
                          py-5
                          text-right
                          whitespace-nowrap
                        "
                      >

                        <span
                          className="
                            text-[16px]
                            font-bold
                            text-[#1F6F5C]
                          "
                        >
                          {formatCurrency(
                            expense.amount
                          )}
                        </span>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>


          {/* =================================================
              MOBILE LIST
          ================================================== */}

          <div
            className="
              md:hidden
              divide-y
              divide-[#EEF0F2]
            "
          >

            {recentExpenses.map(
              (expense, index) => (

                <div
                  key={
                    expense._id ||
                    expense.id ||
                    index
                  }
                  className="
                    px-5
                    py-5
                  "
                >

                  <div
                    className="
                      flex
                      items-center
                      gap-4
                    "
                  >

                    <div
                      className="
                        w-11
                        h-11
                        rounded-xl
                        bg-[#EAF5F1]
                        text-[#1F6F5C]
                        flex
                        items-center
                        justify-center
                        shrink-0
                      "
                    >
                      <WalletCards
                        size={19}
                      />
                    </div>


                    <div
                      className="
                        min-w-0
                        flex-1
                      "
                    >

                      <p
                        className="
                          text-[15px]
                          font-bold
                          text-[#12172B]
                          truncate
                        "
                      >
                        {expense.title ||
                          "Untitled Expense"}
                      </p>

                      <p
                        className="
                          mt-1
                          text-[13px]
                          text-[#64748B]
                        "
                      >
                        {expense.category ||
                          "Other"}

                        {" · "}

                        {formatDate(
                          expense.date
                        )}
                      </p>

                    </div>


                    <span
                      className="
                        text-[15px]
                        font-bold
                        text-[#1F6F5C]
                        whitespace-nowrap
                      "
                    >
                      {formatCurrency(
                        expense.amount
                      )}
                    </span>

                  </div>


                  <div
                    className="
                      mt-3
                      ml-[60px]
                      flex
                      items-center
                      justify-between
                    "
                  >

                    <span
                      className="
                        text-[12px]
                        font-medium
                        text-[#64748B]
                      "
                    >
                      Payment
                    </span>

                    <span
                      className="
                        text-[13px]
                        font-semibold
                        text-[#475569]
                      "
                    >
                      {expense.payment_method ||
                        "-"}
                    </span>

                  </div>

                </div>

              )
            )}

          </div>

        </>
      )}

    </section>
  );
}

export default RecentTransactions;