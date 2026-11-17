import { useEffect, useRef, useState } from "react";

import {
  Search,
  Bell,
  ChevronDown,
  User,
  Settings,
  LogOut,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import axios from "axios";


function DashboardNavbar() {

  const navigate = useNavigate();

  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const [user, setUser] = useState(null);

  const profileRef = useRef(null);


  /* ============================================================
     GET TOKEN
  ============================================================ */

  const getToken = () => {

    return (
      localStorage.getItem("access_token") ||
      localStorage.getItem("token")
    );

  };


  /* ============================================================
     FETCH CURRENT LOGGED-IN USER
  ============================================================ */

  useEffect(() => {

    const fetchCurrentUser = async () => {

      try {

        const token = getToken();


        /* ======================================================
           NO TOKEN
        ====================================================== */

        if (!token) {

          navigate("/login");

          return;

        }


        /* ======================================================
           GET USER FROM BACKEND
        ====================================================== */

        const response = await axios.get(
          "http://127.0.0.1:8000/api/auth/me",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );


        console.log(
          "REAL USER DATA:",
          response.data
        );


        /* ======================================================
           HANDLE DIFFERENT BACKEND RESPONSE FORMATS
        ====================================================== */

        const responseData = response.data;


        let actualUser = responseData;


        /*
          Case:

          {
            user: {
              name: "Bhumi Gawandi",
              email: "bhumi@gmail.com"
            }
          }
        */

        if (
          responseData?.user &&
          typeof responseData.user === "object"
        ) {

          actualUser = responseData.user;

        }


        /*
          Case:

          {
            data: {
              name: "Bhumi Gawandi"
            }
          }
        */

        else if (
          responseData?.data &&
          typeof responseData.data === "object"
        ) {

          actualUser = responseData.data;

        }


        /*
          Case:

          {
            result: {
              name: "Bhumi Gawandi"
            }
          }
        */

        else if (
          responseData?.result &&
          typeof responseData.result === "object"
        ) {

          actualUser = responseData.result;

        }


        console.log(
          "NORMALIZED USER:",
          actualUser
        );


        setUser(actualUser);


        /* ======================================================
           SAVE USER LOCALLY
        ====================================================== */

        localStorage.setItem(
          "user",
          JSON.stringify(actualUser)
        );

      } catch (error) {

        console.error(
          "Failed to fetch current user:",
          error
        );


        /* ======================================================
           TRY LOCAL STORAGE USER
        ====================================================== */

        try {

          const savedUser =
            localStorage.getItem("user");


          if (savedUser) {

            const parsedUser =
              JSON.parse(savedUser);


            setUser(parsedUser);

          }

        } catch (storageError) {

          console.error(
            "Could not read saved user:",
            storageError
          );

        }


        /* ======================================================
           INVALID TOKEN
        ====================================================== */

        if (
          error.response?.status === 401
        ) {

          localStorage.removeItem(
            "access_token"
          );

          localStorage.removeItem(
            "token"
          );

          localStorage.removeItem(
            "user"
          );

          navigate("/login");

        }

      }

    };


    fetchCurrentUser();

  }, [navigate]);


  /* ============================================================
     GET REAL USER NAME
  ============================================================ */

  const getUserName = () => {

    if (!user) {
      return "User";
    }


    return (
      user.name ||
      user.full_name ||
      user.fullName ||
      user.username ||
      user.user_name ||
      user.display_name ||
      user.displayName ||
      user.first_name ||
      user.firstName ||
      user.name_of_user ||
      user.fullName ||
      "User"
    );

  };


  /* ============================================================
     GET REAL USER EMAIL
  ============================================================ */

  const getUserEmail = () => {

    if (!user) {
      return "";
    }


    return (
      user.email ||
      user.email_address ||
      user.emailAddress ||
      ""
    );

  };


  /* ============================================================
     USER VALUES
  ============================================================ */

  const userName = getUserName();

  const userEmail = getUserEmail();


  const userInitial =
    userName &&
    userName !== "User"
      ? userName
          .trim()
          .charAt(0)
          .toUpperCase()
      : "U";


  /* ============================================================
     CLOSE DROPDOWN WHEN CLICKING OUTSIDE
  ============================================================ */

  useEffect(() => {

    const handleClickOutside = (event) => {

      if (
        profileRef.current &&
        !profileRef.current.contains(event.target)
      ) {

        setIsProfileOpen(false);

      }

    };


    document.addEventListener(
      "mousedown",
      handleClickOutside
    );


    return () => {

      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );

    };

  }, []);


  /* ============================================================
     PROFILE
  ============================================================ */

  const handleProfile = () => {

    setIsProfileOpen(false);

    navigate("/profile");

  };


  /* ============================================================
     SETTINGS
  ============================================================ */

  const handleSettings = () => {

    setIsProfileOpen(false);

    navigate("/settings");

  };


  /* ============================================================
     LOGOUT
  ============================================================ */

  const handleLogout = () => {

    setIsProfileOpen(false);


    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "token"
    );

    localStorage.removeItem(
      "user"
    );


    navigate("/login");

  };


  return (

    <header className="dashboard-navbar">

      <div className="dashboard-navbar-inner">


        {/* ======================================================
            DASHBOARD TITLE
        ======================================================= */}

        <h1 className="dashboard-navbar-title">
          Dashboard
        </h1>


        {/* ======================================================
            SEARCH
        ======================================================= */}

        <div className="dashboard-search">

          <Search
            size={19}
            color="#9A968A"
            style={{
              position: "absolute",
              left: "15px",
              top: "12px",
              zIndex: 2,
            }}
          />


          <input
            type="text"
            placeholder="Search expenses, categories, merchants..."
          />

        </div>


        {/* ======================================================
            RIGHT SIDE
        ======================================================= */}

        <div className="dashboard-navbar-actions">


          {/* ====================================================
              NOTIFICATION
          ===================================================== */}

          <button
            type="button"
            className="dashboard-notification"
            aria-label="Notifications"
          >

            <Bell
              size={22}
              strokeWidth={1.8}
            />


            <span
              style={{
                position: "absolute",
                top: "8px",
                right: "8px",
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "#C24444",
              }}
            />

          </button>


          {/* ====================================================
              PROFILE
          ===================================================== */}

          <div
            ref={profileRef}
            style={{
              position: "relative",
            }}
          >


            {/* ==================================================
                PROFILE BUTTON
            =================================================== */}

            <button
              type="button"
              className="dashboard-profile"
              onClick={() =>
                setIsProfileOpen(
                  (previous) =>
                    !previous
                )
              }
              aria-expanded={isProfileOpen}
            >


              {/* ================================================
                  USER AVATAR
              ================================================= */}

              <div className="dashboard-profile-avatar">

                {userInitial}

              </div>


              {/* ================================================
                  USER INFORMATION
              ================================================= */}

              <div className="dashboard-profile-info">

                <p className="dashboard-profile-name">

                  {userName}

                </p>


                <p className="dashboard-profile-email">

                  {userEmail}

                </p>

              </div>


              {/* ================================================
                  DROPDOWN ARROW
              ================================================= */}

              <ChevronDown
                size={16}
                color="#9A968A"
                style={{
                  transition:
                    "transform 0.2s ease",

                  transform:
                    isProfileOpen
                      ? "rotate(180deg)"
                      : "rotate(0deg)",
                }}
              />

            </button>


            {/* ==================================================
                DROPDOWN MENU
            =================================================== */}

            {isProfileOpen && (

              <div
                style={{
                  position: "absolute",
                  top: "calc(100% + 10px)",
                  right: 0,
                  width: "230px",
                  background: "#FFFFFF",
                  border:
                    "1px solid #D8D5C7",
                  borderRadius: "12px",
                  boxShadow:
                    "0 12px 30px rgba(18,23,43,0.14)",
                  overflow: "hidden",
                  zIndex: 999,
                }}
              >


                {/* =================================================
                    DROPDOWN USER HEADER
                ================================================== */}

                <div
                  style={{
                    padding: "16px",
                    borderBottom:
                      "1px dashed #D8D5C7",
                  }}
                >

                  <p
                    style={{
                      fontFamily:
                        "'Fraunces', serif",

                      fontSize: "18px",

                      color: "#12172B",
                    }}
                  >

                    {userName}

                  </p>


                  <p
                    style={{
                      marginTop: "4px",

                      fontFamily:
                        "'Manrope', sans-serif",

                      fontSize: "12px",

                      color: "#6B6B63",

                      wordBreak:
                        "break-word",
                    }}
                  >

                    {userEmail}

                  </p>

                </div>


                {/* =================================================
                    PROFILE BUTTON
                ================================================== */}

                <button
                  type="button"
                  onClick={handleProfile}
                  style={{
                    width: "100%",

                    display: "flex",

                    alignItems: "center",

                    gap: "12px",

                    padding:
                      "13px 16px",

                    border: "none",

                    background:
                      "transparent",

                    color: "#12172B",

                    fontFamily:
                      "'Manrope', sans-serif",

                    fontSize: "14px",

                    textAlign: "left",

                    cursor: "pointer",
                  }}

                  onMouseEnter={(e) => {

                    e.currentTarget.style.background =
                      "rgba(31,111,92,0.08)";

                  }}

                  onMouseLeave={(e) => {

                    e.currentTarget.style.background =
                      "transparent";

                  }}
                >

                  <User
                    size={18}
                    color="#1F6F5C"
                  />

                  <span>
                    Profile
                  </span>

                </button>


                {/* =================================================
                    SETTINGS BUTTON
                ================================================== */}

                <button
                  type="button"
                  onClick={handleSettings}
                  style={{
                    width: "100%",

                    display: "flex",

                    alignItems: "center",

                    gap: "12px",

                    padding:
                      "13px 16px",

                    border: "none",

                    background:
                      "transparent",

                    color: "#12172B",

                    fontFamily:
                      "'Manrope', sans-serif",

                    fontSize: "14px",

                    textAlign: "left",

                    cursor: "pointer",
                  }}

                  onMouseEnter={(e) => {

                    e.currentTarget.style.background =
                      "rgba(31,111,92,0.08)";

                  }}

                  onMouseLeave={(e) => {

                    e.currentTarget.style.background =
                      "transparent";

                  }}
                >

                  <Settings
                    size={18}
                    color="#1F6F5C"
                  />

                  <span>
                    Settings
                  </span>

                </button>


                {/* =================================================
                    DIVIDER
                ================================================== */}

                <div
                  style={{
                    margin: "4px 12px",

                    borderTop:
                      "1px dashed #D8D5C7",
                  }}
                />


                {/* =================================================
                    LOGOUT BUTTON
                ================================================== */}

                <button
                  type="button"
                  onClick={handleLogout}
                  style={{
                    width: "100%",

                    display: "flex",

                    alignItems: "center",

                    gap: "12px",

                    padding:
                      "13px 16px",

                    border: "none",

                    background:
                      "transparent",

                    color: "#C15B3D",

                    fontFamily:
                      "'Manrope', sans-serif",

                    fontSize: "14px",

                    fontWeight: "600",

                    textAlign: "left",

                    cursor: "pointer",
                  }}

                  onMouseEnter={(e) => {

                    e.currentTarget.style.background =
                      "rgba(193,91,61,0.08)";

                  }}

                  onMouseLeave={(e) => {

                    e.currentTarget.style.background =
                      "transparent";

                  }}
                >

                  <LogOut
                    size={18}
                    color="#C15B3D"
                  />

                  <span>
                    Logout
                  </span>

                </button>

              </div>

            )}

          </div>

        </div>

      </div>

    </header>

  );

}


export default DashboardNavbar;