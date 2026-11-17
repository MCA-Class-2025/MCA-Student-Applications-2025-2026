import {
  ReceiptText,
  Wallet,
  Bot,
  ScanLine,
  Mic,
  BarChart3,
} from "lucide-react";


function Features() {

  const features = [
    {
      name: "Expense tracking",
      desc:
        "Log every transaction in seconds and see it categorized instantly.",
      icon: ReceiptText,
    },

    {
      name: "Budget planner",
      desc:
        "Set monthly limits per category and get warned before you overspend.",
      icon: Wallet,
    },

    {
      name: "AI assistant",
      desc:
        "Ask plain questions like where did I overspend and get real answers.",
      icon: Bot,
    },

    {
      name: "Receipt scanning",
      desc:
        "Snap a photo and let OCR pull the merchant, amount, and date for you.",
      icon: ScanLine,
    },

    {
      name: "Voice entry",
      desc:
        "Say your expense out loud and it lands in your ledger, categorized.",
      icon: Mic,
    },

    {
      name: "Analytics dashboard",
      desc:
        "Spot trends across months with charts built for quick decisions.",
      icon: BarChart3,
    },
  ];


  return (

    <section
      id="features"
      className="
        w-full
        bg-[#F6F4EE]
        pt-8
        pb-20
        lg:pt-10
        lg:pb-24
      "
    >

      <div
        className="
          max-w-6xl
          mx-auto
          px-6
          lg:px-8
        "
      >

        {/* ==================================================
            CENTER HEADING
        =================================================== */}

        <div className="text-center mb-11">

          <span
            className="
              text-[11px]
              font-semibold
              tracking-[0.18em]
              text-[#1F6F5C]
              uppercase
            "
          >
            What's included
          </span>


          <h2
            className="
              text-[38px]
              md:text-[45px]
              font-medium
              text-[#12172B]
              mt-3
              tracking-[-0.7px]
            "
            style={{
              fontFamily: "'Fraunces', serif",
            }}
          >
            Everything on your statement
          </h2>


          <p
            className="
              max-w-2xl
              mx-auto
              mt-3
              text-[14px]
              text-[#7D879A]
              leading-6
            "
          >
            Everything you need to understand, manage,
            and improve your everyday spending.
          </p>

        </div>


        {/* ==================================================
            FEATURE CARD
        =================================================== */}

        <div
          className="
            bg-white
            border
            border-[#DDD9CF]
            rounded-2xl
            overflow-hidden
            shadow-[0_8px_25px_rgba(18,23,43,0.05)]
          "
        >

          {features.map((feature, index) => {

            const Icon = feature.icon;

            return (

              <div
                key={feature.name}
                className={`
                  flex
                  items-center
                  gap-5
                  px-6
                  md:px-8
                  py-6
                  hover:bg-[#FAF9F5]
                  transition-colors
                  ${
                    index !== features.length - 1
                      ? "border-b border-dashed border-[#DDD9CF]"
                      : ""
                  }
                `}
              >

                {/* ICON */}

                <div
                  className="
                    w-11
                    h-11
                    rounded-xl
                    bg-[#E8F3EF]
                    border
                    border-[#CCEAE2]
                    flex
                    items-center
                    justify-center
                    shrink-0
                  "
                >

                  <Icon
                    size={19}
                    strokeWidth={1.8}
                    className="text-[#1F6F5C]"
                  />

                </div>


                {/* TEXT */}

                <div className="flex-1 min-w-0">

                  <h3
                    className="
                      text-[15px]
                      font-semibold
                      text-[#12172B]
                    "
                  >
                    {feature.name}
                  </h3>

                  <p
                    className="
                      text-[13px]
                      text-[#6B6B63]
                      mt-1
                      leading-5
                    "
                  >
                    {feature.desc}
                  </p>

                </div>


                {/* BADGE */}

                <span
                  className="
                    hidden
                    sm:inline-flex
                    text-[10px]
                    font-semibold
                    text-[#1F6F5C]
                    bg-[#E8F3EF]
                    border
                    border-[#CCEAE2]
                    px-3
                    py-1.5
                    rounded-full
                    shrink-0
                  "
                >
                  Included
                </span>

              </div>

            );

          })}

        </div>

      </div>

    </section>
  );
}

export default Features;