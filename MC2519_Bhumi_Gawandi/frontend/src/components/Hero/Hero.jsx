import { Link } from "react-router-dom";

function Hero() {

  // ============================================================
  // CURRENT MONTH
  // ============================================================

  const currentMonth = new Date().toLocaleString("en-US", {
    month: "long",
  });


  // ============================================================
  // DEMO RECEIPT DATA
  // ============================================================

  const lines = [
    {
      label: "Groceries",
      amt: "₹1,200",
    },
    {
      label: "Uber ride",
      amt: "₹350",
    },
    {
      label: "Electricity bill",
      amt: "₹2,150",
    },
    {
      label: "Movie ticket",
      amt: "₹400",
    },
  ];


  const total = "₹4,100";


  return (

    <section
      id="home"
      className="
        w-full
        bg-[#F6F4EE]
        border-b
        border-[#DDD9CF]
      "
    >

      {/* ======================================================
          HERO CONTENT
      ====================================================== */}

      <div
        className="
          max-w-7xl
          mx-auto
          px-6
          lg:px-8
          pt-16
          lg:pt-20
          pb-10
          lg:pb-12
          grid
          grid-cols-1
          lg:grid-cols-2
          gap-12
          lg:gap-16
          items-center
        "
      >

        {/* ====================================================
            LEFT CONTENT
        ===================================================== */}

        <div>

          {/* AI LABEL */}

          <span
            className="
              inline-flex
              items-center
              text-[11px]
              font-semibold
              tracking-[0.18em]
              text-[#1F6F5C]
              uppercase
              mb-5
              border
              border-[#1F6F5C]/30
              rounded-full
              px-3.5
              py-1.5
              bg-[#E8F3EF]/60
            "
          >
            AI-powered expense tracking
          </span>


          {/* MAIN HEADING */}

          <h1
            className="
              text-[48px]
              md:text-[58px]
              lg:text-[62px]
              font-medium
              text-[#12172B]
              leading-[1.04]
              tracking-[-1.5px]
            "
            style={{
              fontFamily: "'Fraunces', serif",
            }}
          >

            Know exactly where

            <br />

            your money{" "}

            <span className="text-[#1F6F5C] italic">
              goes.
            </span>

          </h1>


          {/* DESCRIPTION */}

          <p
            className="
              mt-5
              text-[16px]
              text-[#6B6B63]
              max-w-lg
              leading-7
            "
          >
            Track spending, set budgets, and get
            plain-language insights from your AI
            assistant, all in one place.
          </p>


          {/* BUTTONS */}

          <div
            className="
              mt-8
              flex
              flex-wrap
              gap-3
            "
          >

            <Link
              to="/register"
              className="
                px-7
                py-3.5
                rounded-xl
                font-semibold
                text-[#F6F4EE]
                bg-[#1F6F5C]
                hover:bg-[#185A4A]
                shadow-sm
                transition
              "
            >
              Get started free
            </Link>


            <Link
              to="/login"
              className="
                px-7
                py-3.5
                rounded-xl
                font-medium
                text-[#12172B]
                border
                border-[#12172B]/20
                hover:bg-[#EBE8DE]
                transition
              "
            >
              Log in
            </Link>

          </div>


          {/* TRUST POINTS */}

          <div
            className="
              mt-7
              flex
              flex-wrap
              items-center
              gap-x-7
              gap-y-3
              text-[13px]
              text-[#6B6B63]
            "
          >

            <span
              className="
                flex
                items-center
                gap-2
              "
            >

              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#1F6F5C"
                strokeWidth="2.5"
              >
                <path d="M20 6L9 17l-5-5" />
              </svg>

              No card required

            </span>


            <span
              className="
                flex
                items-center
                gap-2
              "
            >

              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#1F6F5C"
                strokeWidth="2.5"
              >
                <path d="M20 6L9 17l-5-5" />
              </svg>

              Free forever plan

            </span>

          </div>

        </div>


        {/* ====================================================
            RIGHT RECEIPT
        ===================================================== */}

        <div
          className="
            flex
            justify-center
            lg:justify-end
          "
        >

          <div
            className="
              w-full
              max-w-[390px]
              bg-white
              border
              border-[#DDD9CF]
              shadow-[0_18px_45px_rgba(18,23,43,0.10)]
              px-7
              pt-7
              pb-6
            "
            style={{
              clipPath:
                "polygon(0% 0%,100% 0%,100% 96%,95% 100%,90% 96%,85% 100%,80% 96%,75% 100%,70% 96%,65% 100%,60% 96%,55% 100%,50% 96%,45% 100%,40% 96%,35% 100%,30% 96%,25% 100%,20% 96%,15% 100%,10% 96%,5% 100%,0% 96%)",
            }}
          >

            {/* =================================================
                RECEIPT HEADER
            ================================================== */}

            <div
              className="
                text-center
                border-b
                border-dashed
                border-[#D8D5C7]
                pb-5
                mb-5
              "
            >

              <p
                className="
                  text-[10px]
                  tracking-[0.18em]
                  text-[#9A968A]
                  uppercase
                "
              >
                This month's ledger
              </p>


              {/* CURRENT MONTH */}

              <p
                className="
                  text-[26px]
                  font-medium
                  text-[#12172B]
                  mt-1
                "
                style={{
                  fontFamily: "'Fraunces', serif",
                }}
              >
                {currentMonth} spending
              </p>

            </div>


            {/* =================================================
                EXPENSE LINES
            ================================================== */}

            <div className="space-y-4">

              {lines.map((item) => (

                <div
                  key={item.label}
                  className="
                    flex
                    justify-between
                    items-baseline
                    text-[13px]
                  "
                >

                  <span
                    className="
                      text-[#4A4A45]
                      whitespace-nowrap
                    "
                  >
                    {item.label}
                  </span>


                  <span
                    className="
                      flex-1
                      mx-2
                      border-b
                      border-dotted
                      border-[#D8D5C7]
                      translate-y-[-3px]
                    "
                  />


                  <span
                    className="
                      font-semibold
                      text-[#12172B]
                      whitespace-nowrap
                    "
                  >
                    {item.amt}
                  </span>

                </div>

              ))}

            </div>


            {/* =================================================
                TOTAL
            ================================================== */}

            <div
              className="
                flex
                justify-between
                items-center
                mt-6
                pt-5
                border-t
                border-dashed
                border-[#D8D5C7]
              "
            >

              <span
                className="
                  text-[13px]
                  font-semibold
                  text-[#12172B]
                "
              >
                Total tracked
              </span>


              <span
                className="
                  text-[19px]
                  font-semibold
                  text-[#1F6F5C]
                "
              >
                {total}
              </span>

            </div>


            {/* =================================================
                AI BADGE
            ================================================== */}

            <div
              className="
                mt-5
                inline-flex
                items-center
                gap-1.5
                text-[10px]
                font-semibold
                text-[#9B7A16]
                bg-[#C9A227]/10
                px-3
                py-1.5
                rounded-full
              "
            >

              <span>
                ✦
              </span>

              AI flagged 1 saving opportunity

            </div>

          </div>

        </div>

      </div>


      {/* ======================================================
          CENTERED TRANSITION TEXT
      ====================================================== */}

      <div
        className="
          max-w-7xl
          mx-auto
          px-6
          lg:px-8
          flex
          justify-center
          pb-8
        "
      >

        <p
          className="
            text-center
            text-[13px]
            md:text-[14px]
            text-[#7D879A]
            tracking-wide
          "
        >
          Simple tracking. Smarter decisions. Better control
          over your money.
        </p>

      </div>

    </section>

  );
}

export default Hero;