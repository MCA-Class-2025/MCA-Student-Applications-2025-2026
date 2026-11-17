import { useEffect, useState } from "react";

import {
  User,
  Lock,
  Bell,
  Palette,
  ShieldCheck,
  LogOut,
  Save,
  Sun,
  Moon,
  Mail,
  Phone,
  DollarSign,
  ChevronRight,
  CheckCircle2,
  KeyRound,
  Database,
  Monitor,
} from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout/DashboardLayout";

import "./Settings.css";


function Settings() {

  /* ============================================================
     ACTIVE TAB
  ============================================================ */

  const [activeTab, setActiveTab] = useState("account");


  /* ============================================================
     ACCOUNT
  ============================================================ */

  const [formData, setFormData] = useState({
    fullName: "Bhumi",
    email: "bhumigawandi@gmail.com",
    phone: "",
    currency: "INR",
  });


  /* ============================================================
     DATE FORMAT
  ============================================================ */

  const [dateFormat, setDateFormat] = useState(
    "DD/MM/YYYY"
  );


  /* ============================================================
     APPEARANCE
  ============================================================ */

  const [appearance, setAppearance] = useState(() => {

    return (
      localStorage.getItem("settingsAppearance") ||
      "light"
    );

  });


  /* ============================================================
     NOTIFICATIONS
  ============================================================ */

  const [notifications, setNotifications] = useState({

    expenseAdded: true,

    budgetAlert: true,

    monthlyReport: true,

    aiSuggestions: true,

  });


  /* ============================================================
     MESSAGE
  ============================================================ */

  const [message, setMessage] = useState("");


  /* ============================================================
     LOAD SETTINGS
  ============================================================ */

  useEffect(() => {

    const savedSettings =
      localStorage.getItem("settings");

    if (!savedSettings) {
      return;
    }

    try {

      const parsedSettings =
        JSON.parse(savedSettings);


      if (parsedSettings.formData) {

        setFormData((previous) => ({

          ...previous,

          ...parsedSettings.formData,

        }));

      }


      if (parsedSettings.dateFormat) {

        setDateFormat(
          parsedSettings.dateFormat
        );

      }


      if (parsedSettings.appearance) {

        setAppearance(
          parsedSettings.appearance
        );

      }


      if (parsedSettings.notifications) {

        setNotifications((previous) => ({

          ...previous,

          ...parsedSettings.notifications,

        }));

      }

    } catch (error) {

      console.error(
        "Unable to load settings:",
        error
      );

    }

  }, []);


  /* ============================================================
     APPLY GLOBAL SETTINGS THEME
  ============================================================ */

  useEffect(() => {

    document.documentElement.setAttribute(
      "data-settings-theme",
      appearance
    );


    localStorage.setItem(
      "settingsAppearance",
      appearance
    );


    return () => {

      document.documentElement.removeAttribute(
        "data-settings-theme"
      );

    };

  }, [appearance]);


  /* ============================================================
     FORM CHANGE
  ============================================================ */

  const handleChange = (event) => {

    const {
      name,
      value,
    } = event.target;


    setFormData((previous) => ({

      ...previous,

      [name]: value,

    }));

  };


  /* ============================================================
     NOTIFICATION CHANGE
  ============================================================ */

  const handleNotificationChange = (name) => {

    setNotifications((previous) => ({

      ...previous,

      [name]: !previous[name],

    }));

  };


  /* ============================================================
     SAVE SETTINGS
  ============================================================ */

  const handleSave = () => {

    const settings = {

      formData,

      dateFormat,

      appearance,

      notifications,

    };


    localStorage.setItem(
      "settings",
      JSON.stringify(settings)
    );


    localStorage.setItem(
      "settingsAppearance",
      appearance
    );


    setMessage(
      "Settings saved successfully."
    );


    setTimeout(() => {

      setMessage("");

    }, 3000);

  };


  /* ============================================================
     LOGOUT
  ============================================================ */

  const handleLogout = () => {

    localStorage.removeItem("token");

    window.location.href = "/login";

  };


  /* ============================================================
     SETTINGS MENU
  ============================================================ */

  const settingsMenu = [

    {
      id: "account",
      label: "Account",
      description: "Personal information",
      icon: User,
    },

    {
      id: "security",
      label: "Security",
      description: "Password and verification",
      icon: Lock,
    },

    {
      id: "notifications",
      label: "Notifications",
      description: "Alerts and reminders",
      icon: Bell,
    },

    {
      id: "appearance",
      label: "Appearance",
      description: "Theme and preferences",
      icon: Palette,
    },

    {
      id: "privacy",
      label: "Privacy & Data",
      description: "Your data and privacy",
      icon: ShieldCheck,
    },

  ];


  const activeMenu = settingsMenu.find(
    (item) =>
      item.id === activeTab
  );


  return (

    <DashboardLayout>

      <div className="settings-page">


        {/* ======================================================
            HEADER
        ====================================================== */}

        <div className="settings-header">

          <div className="settings-eyebrow">

            <span className="settings-dot"></span>

            ACCOUNT MANAGEMENT

          </div>


          <h1>
            Settings
          </h1>


          <p>
            Manage your account, security,
            notifications, and preferences.
          </p>

        </div>


        {/* ======================================================
            MAIN SETTINGS LAYOUT
        ====================================================== */}

        <div className="settings-layout">


          {/* ====================================================
              LEFT SETTINGS MENU
          ==================================================== */}

          <aside className="settings-navigation">


            {/* PROFILE */}

            <div className="settings-profile-mini">

              <div className="settings-avatar">

                {formData.fullName
                  ? formData.fullName
                      .charAt(0)
                      .toUpperCase()
                  : "B"}

              </div>


              <div className="settings-profile-info">

                <h3>
                  {formData.fullName || "Bhumi"}
                </h3>

                <p>
                  {formData.email ||
                    "bhumigawandi@gmail.com"}
                </p>

              </div>

            </div>


            <div className="navigation-divider"></div>


            <div className="settings-navigation-title">
              SETTINGS
            </div>


            {/* MENU */}

            <div className="settings-navigation-list">

              {settingsMenu.map((item) => {

                const Icon = item.icon;


                return (

                  <button
                    key={item.id}
                    type="button"
                    className={`settings-navigation-item ${
                      activeTab === item.id
                        ? "active"
                        : ""
                    }`}
                    onClick={() =>
                      setActiveTab(item.id)
                    }
                  >

                    <span className="navigation-icon">

                      <Icon
                        size={18}
                        strokeWidth={2}
                      />

                    </span>


                    <span className="navigation-text">

                      <strong>
                        {item.label}
                      </strong>

                      <small>
                        {item.description}
                      </small>

                    </span>


                    <ChevronRight
                      className="navigation-arrow"
                      size={16}
                    />

                  </button>

                );

              })}

            </div>


            <div className="navigation-divider"></div>


            {/* LOGOUT */}

            <button
              type="button"
              className="settings-logout"
              onClick={handleLogout}
            >

              <LogOut size={18} />

              <span>
                Logout
              </span>

            </button>

          </aside>


          {/* ====================================================
              RIGHT CONTENT
          ==================================================== */}

          <main className="settings-content">


            {/* ==================================================
                CONTENT HEADER
            ================================================== */}

            <div className="settings-content-header">

              <div>

                <div className="content-section-label">

                  {activeMenu?.label}

                </div>


                <h2>

                  {activeTab === "account" &&
                    "Account Settings"}

                  {activeTab === "security" &&
                    "Account Security"}

                  {activeTab === "notifications" &&
                    "Notification Preferences"}

                  {activeTab === "appearance" &&
                    "Appearance Preferences"}

                  {activeTab === "privacy" &&
                    "Privacy & Data"}

                </h2>


                <p>

                  {activeTab === "account" &&
                    "Manage your personal information and account details."}

                  {activeTab === "security" &&
                    "Keep your SpendSmart.ai account safe and secure."}

                  {activeTab === "notifications" &&
                    "Choose which notifications you want to receive."}

                  {activeTab === "appearance" &&
                    "Customize the way SpendSmart.ai looks for you."}

                  {activeTab === "privacy" &&
                    "Understand and manage how your financial data is used."}

                </p>

              </div>


              <div className="settings-header-icon">

                {activeTab === "account" && (
                  <User size={22} />
                )}

                {activeTab === "security" && (
                  <Lock size={22} />
                )}

                {activeTab === "notifications" && (
                  <Bell size={22} />
                )}

                {activeTab === "appearance" && (
                  <Palette size={22} />
                )}

                {activeTab === "privacy" && (
                  <ShieldCheck size={22} />
                )}

              </div>

            </div>


            <div className="content-divider"></div>


            {/* ==================================================
                ACCOUNT
            ================================================== */}

            {activeTab === "account" && (

              <div className="settings-section">

                <div className="section-heading">

                  <div>

                    <span>
                      PROFILE DETAILS
                    </span>

                    <h3>
                      Personal Information
                    </h3>

                  </div>

                  <User size={20} />

                </div>


                <div className="form-grid">


                  {/* FULL NAME */}

                  <div className="settings-field">

                    <label>
                      Full Name
                    </label>

                    <div className="settings-input">

                      <User size={17} />

                      <input
                        type="text"
                        name="fullName"
                        value={formData.fullName}
                        onChange={handleChange}
                        placeholder="Enter your full name"
                      />

                    </div>

                  </div>


                  {/* EMAIL */}

                  <div className="settings-field">

                    <label>
                      Email Address
                    </label>

                    <div className="settings-input disabled">

                      <Mail size={17} />

                      <input
                        type="email"
                        value={formData.email}
                        readOnly
                      />

                    </div>

                    <small className="field-note">
                      Email cannot be changed here.
                    </small>

                  </div>


                  {/* PHONE */}

                  <div className="settings-field">

                    <label>
                      Phone Number
                    </label>

                    <div className="settings-input">

                      <Phone size={17} />

                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="Enter phone number"
                      />

                    </div>

                  </div>


                  {/* CURRENCY */}

                  <div className="settings-field">

                    <label>
                      Currency
                    </label>

                    <div className="settings-input">

                      <DollarSign size={17} />

                      <select
                        name="currency"
                        value={formData.currency}
                        onChange={handleChange}
                      >

                        <option value="INR">
                          ₹ Indian Rupee (INR)
                        </option>

                        <option value="USD">
                          $ US Dollar (USD)
                        </option>

                        <option value="EUR">
                          € Euro (EUR)
                        </option>

                        <option value="GBP">
                          £ British Pound (GBP)
                        </option>

                      </select>

                    </div>

                  </div>

                </div>


                <div className="subsection-divider"></div>


                {/* ACCOUNT STATUS */}

                <div className="section-heading">

                  <div>

                    <span>
                      ACCOUNT INFORMATION
                    </span>

                    <h3>
                      Account Status
                    </h3>

                  </div>

                  <ShieldCheck size={20} />

                </div>


                <div className="information-grid">

                  <div className="information-card">

                    <div className="information-icon">

                      <CheckCircle2 size={19} />

                    </div>

                    <div>

                      <span>
                        Account Status
                      </span>

                      <strong>
                        Active Account
                      </strong>

                    </div>

                  </div>


                  <div className="information-card">

                    <div className="information-icon">

                      <Mail size={19} />

                    </div>

                    <div>

                      <span>
                        Email Status
                      </span>

                      <strong>
                        Verified
                      </strong>

                    </div>

                  </div>

                </div>


                <div className="save-row">

                  {message && (

                    <span className="success-message">

                      <CheckCircle2 size={15} />

                      {message}

                    </span>

                  )}


                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleSave}
                  >

                    <Save size={17} />

                    Save Changes

                  </button>

                </div>

              </div>

            )}


            {/* ==================================================
                SECURITY
            ================================================== */}

            {activeTab === "security" && (

              <div className="settings-section">


                <div className="security-card">

                  <div className="security-card-icon">

                    <KeyRound size={21} />

                  </div>

                  <div className="security-card-content">

                    <h3>
                      Change Password
                    </h3>

                    <p>
                      Update your password regularly
                      to keep your SpendSmart.ai
                      account secure.
                    </p>

                  </div>

                  <button
                    type="button"
                    className="outline-button"
                  >
                    Change Password
                  </button>

                </div>


                <div className="security-card">

                  <div className="security-card-icon">

                    <Mail size={21} />

                  </div>

                  <div className="security-card-content">

                    <h3>
                      Email Verification
                    </h3>

                    <p>
                      Your email address is verified
                      and can be used for account recovery.
                    </p>

                  </div>

                  <span className="status-badge">

                    <CheckCircle2 size={14} />

                    Verified

                  </span>

                </div>


                <div className="security-card">

                  <div className="security-card-icon">

                    <ShieldCheck size={21} />

                  </div>

                  <div className="security-card-content">

                    <h3>
                      Account Protection
                    </h3>

                    <p>
                      Your account uses authentication
                      and protected access to keep
                      your data safe.
                    </p>

                  </div>

                  <span className="status-badge">
                    Protected
                  </span>

                </div>

              </div>

            )}


            {/* ==================================================
                NOTIFICATIONS
            ================================================== */}

            {activeTab === "notifications" && (

              <div className="settings-section">

                <div className="notification-box">

                  <div className="notification-box-header">

                    <div>

                      <span>
                        NOTIFICATION SETTINGS
                      </span>

                      <h3>
                        Choose what you receive
                      </h3>

                    </div>

                    <Bell size={21} />

                  </div>


                  <NotificationRow
                    title="Expense Added"
                    description="Get notified whenever a new expense is added."
                    checked={
                      notifications.expenseAdded
                    }
                    onChange={() =>
                      handleNotificationChange(
                        "expenseAdded"
                      )
                    }
                  />


                  <NotificationRow
                    title="Budget Alerts"
                    description="Receive an alert when your spending approaches a budget."
                    checked={
                      notifications.budgetAlert
                    }
                    onChange={() =>
                      handleNotificationChange(
                        "budgetAlert"
                      )
                    }
                  />


                  <NotificationRow
                    title="Monthly Reports"
                    description="Receive your monthly spending summary."
                    checked={
                      notifications.monthlyReport
                    }
                    onChange={() =>
                      handleNotificationChange(
                        "monthlyReport"
                      )
                    }
                  />


                  <NotificationRow
                    title="AI Suggestions"
                    description="Receive useful AI-powered saving suggestions."
                    checked={
                      notifications.aiSuggestions
                    }
                    onChange={() =>
                      handleNotificationChange(
                        "aiSuggestions"
                      )
                    }
                    last
                  />

                </div>


                <div className="save-row">

                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleSave}
                  >

                    <Save size={17} />

                    Save Preferences

                  </button>

                </div>

              </div>

            )}


            {/* ==================================================
                APPEARANCE
            ================================================== */}

            {activeTab === "appearance" && (

              <div className="settings-section">


                <div className="section-heading">

                  <div>

                    <span>
                      THEME
                    </span>

                    <h3>
                      Choose your appearance
                    </h3>

                  </div>

                  <Palette size={20} />

                </div>


                <div className="theme-grid">


                  {/* LIGHT */}

                  <button
                    type="button"
                    className={`theme-card ${
                      appearance === "light"
                        ? "selected"
                        : ""
                    }`}
                    onClick={() => {

                      setAppearance("light");

                    }}
                  >

                    <div className="theme-preview light-preview">

                      <div className="preview-top">

                        <span></span>

                      </div>

                      <div className="preview-content">

                        <div className="preview-line large"></div>

                        <div className="preview-line"></div>

                        <div className="preview-card"></div>

                      </div>

                    </div>


                    <div className="theme-info">

                      <div className="theme-icon light">

                        <Sun size={19} />

                      </div>


                      <div>

                        <h4>
                          Light
                        </h4>

                        <p>
                          Clean and bright interface
                        </p>

                      </div>


                      {appearance === "light" && (

                        <CheckCircle2
                          className="theme-check"
                          size={20}
                        />

                      )}

                    </div>

                  </button>


                  {/* DARK */}

                  <button
                    type="button"
                    className={`theme-card ${
                      appearance === "dark"
                        ? "selected"
                        : ""
                    }`}
                    onClick={() => {

                      setAppearance("dark");

                    }}
                  >

                    <div className="theme-preview dark-preview">

                      <div className="preview-top">

                        <span></span>

                      </div>

                      <div className="preview-content">

                        <div className="preview-line large"></div>

                        <div className="preview-line"></div>

                        <div className="preview-card"></div>

                      </div>

                    </div>


                    <div className="theme-info">

                      <div className="theme-icon dark">

                        <Moon size={19} />

                      </div>


                      <div>

                        <h4>
                          Dark
                        </h4>

                        <p>
                          Comfortable dark interface
                        </p>

                      </div>


                      {appearance === "dark" && (

                        <CheckCircle2
                          className="theme-check"
                          size={20}
                        />

                      )}

                    </div>

                  </button>

                </div>


                {/* DATE FORMAT */}

                <div className="subsection-divider"></div>


                <div className="date-format-box">

                  <div className="date-format-info">

                    <div className="settings-small-icon">

                      <Monitor size={18} />

                    </div>


                    <div>

                      <h3>
                        Date Format
                      </h3>

                      <p>
                        Choose how dates appear
                        throughout the application.
                      </p>

                    </div>

                  </div>


                  <select
                    value={dateFormat}
                    onChange={(event) =>
                      setDateFormat(
                        event.target.value
                      )
                    }
                  >

                    <option value="DD/MM/YYYY">
                      DD/MM/YYYY
                    </option>

                    <option value="MM/DD/YYYY">
                      MM/DD/YYYY
                    </option>

                    <option value="YYYY-MM-DD">
                      YYYY-MM-DD
                    </option>

                  </select>

                </div>


                <div className="save-row">

                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleSave}
                  >

                    <Save size={17} />

                    Save Preferences

                  </button>

                </div>

              </div>

            )}


            {/* ==================================================
                PRIVACY
            ================================================== */}

            {activeTab === "privacy" && (

              <div className="settings-section">


                <div className="privacy-card">

                  <div className="privacy-icon">

                    <Database size={21} />

                  </div>


                  <div>

                    <h3>
                      Your Financial Data
                    </h3>

                    <p>
                      Your expense information is used
                      to provide your financial dashboard,
                      reports, budgets, analytics and
                      AI assistance.
                    </p>

                  </div>

                </div>


                <div className="privacy-card">

                  <div className="privacy-icon">

                    <ShieldCheck size={21} />

                  </div>


                  <div>

                    <h3>
                      Data Protection
                    </h3>

                    <p>
                      SpendSmart.ai is designed to keep
                      your account information and
                      financial data protected from
                      unauthorized access.
                    </p>

                  </div>

                </div>


                <div className="privacy-card">

                  <div className="privacy-icon">

                    <User size={21} />

                  </div>


                  <div>

                    <h3>
                      Data Control
                    </h3>

                    <p>
                      You can manage your account
                      information, notification preferences
                      and application settings from this page.
                    </p>

                  </div>

                </div>

              </div>

            )}

          </main>

        </div>

      </div>

    </DashboardLayout>

  );
}


/* ============================================================
   NOTIFICATION ROW
============================================================ */

function NotificationRow({
  title,
  description,
  checked,
  onChange,
  last = false,
}) {

  return (

    <div
      className={`notification-row ${
        last ? "last" : ""
      }`}
    >

      <div className="notification-info">

        <h4>
          {title}
        </h4>

        <p>
          {description}
        </p>

      </div>


      <label className="toggle">

        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
        />

        <span className="toggle-slider"></span>

      </label>

    </div>

  );

}


export default Settings;