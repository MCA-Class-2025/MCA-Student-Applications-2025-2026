import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="w-full bg-[#12172B] border-b border-[#252B40]">
      
      <div
        className="
          max-w-[1536px]
          mx-auto
          h-[78px]
          px-8
          lg:px-12
          flex
          items-center
          justify-between
        "
      >

        {/* =====================================================
            LEFT - LOGO
        ====================================================== */}

        <Link
          to="/"
          className="
            flex
            items-center
            gap-3
            shrink-0
          "
        >

          <div
            className="
              w-[50px]
              h-[50px]
              rounded-[14px]
              bg-[#1F6F5C]
              flex
              items-center
              justify-center
              text-white
              font-semibold
              text-xl
            "
          >
            ₹
          </div>


          <h1
            className="
              text-[30px]
              lg:text-[32px]
              font-bold
              text-[#F6F4EE]
              whitespace-nowrap
            "
            style={{
              fontFamily: "'Fraunces', serif",
            }}
          >
            SpendSmart
            <span className="text-[#1F6F5C]">
              .ai
            </span>
          </h1>

        </Link>


        {/* =====================================================
            RIGHT SIDE
        ====================================================== */}

        <div
          className="
            flex
            items-center
            ml-auto
            gap-12
          "
        >

          {/* =================================================
              MENU
          ================================================== */}

          <div
            className="
              hidden
              lg:flex
              items-center
              gap-10
              text-[15px]
              font-medium
              text-[#D9DCE5]
            "
          >

            <a
              href="#home"
              className="
                hover:text-[#5CC9A7]
                transition-colors
                duration-200
              "
            >
              Home
            </a>


            <a
              href="#features"
              className="
                hover:text-[#5CC9A7]
                transition-colors
                duration-200
              "
            >
              Features
            </a>


            <a
              href="#about"
              className="
                hover:text-[#5CC9A7]
                transition-colors
                duration-200
              "
            >
              About
            </a>


            <a
              href="#contact"
              className="
                hover:text-[#5CC9A7]
                transition-colors
                duration-200
              "
            >
              Contact
            </a>

          </div>


          {/* =================================================
              AUTH BUTTONS
          ================================================== */}

          <div
            className="
              flex
              items-center
              gap-6
              shrink-0
            "
          >

            <Link
              to="/login"
              className="
                text-[15px]
                font-semibold
                text-[#F6F4EE]
                hover:text-[#5CC9A7]
                transition-colors
                duration-200
                whitespace-nowrap
              "
            >
              Login
            </Link>


            <Link
              to="/register"
              className="
                bg-[#1F6F5C]
                text-white
                px-6
                py-3
                rounded-xl
                text-[14px]
                font-semibold
                hover:bg-[#185A4A]
                transition
                duration-200
                shadow-sm
                whitespace-nowrap
              "
            >
              Get Started
            </Link>

          </div>

        </div>

      </div>

    </nav>
  );
}

export default Navbar;