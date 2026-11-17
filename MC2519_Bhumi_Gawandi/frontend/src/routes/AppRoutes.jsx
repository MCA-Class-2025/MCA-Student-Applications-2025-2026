import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

// ============================================================
// PAGES
// ============================================================

import Landing
  from "../pages/Landing/Landing";

import Login
  from "../pages/Login/Login";

import Register
  from "../pages/Register/Register";

import Dashboard
  from "../pages/Dashboard/Dashboard";

import Expenses
  from "../pages/Expenses/Expenses";

import AddExpense
  from "../pages/AddExpense/AddExpense";

import EditExpense
  from "../pages/EditExpense/EditExpense";

import ExpenseDetails
  from "../pages/ExpenseDetails/ExpenseDetails";

import Budget
  from "../pages/Budget/Budget";

import Categories
  from "../pages/Categories/Categories";

import Reports
  from "../pages/Reports/Reports";

import AIAssistant
  from "../pages/AIAssistant/AIAssistant";

import ReceiptScanner
  from "../pages/ReceiptScanner/ReceiptScanner";

import VoiceEntry
  from "../pages/VoiceEntry/VoiceEntry";

import Profile
  from "../pages/Profile/Profile";

import Settings
  from "../pages/Settings/Settings";

// ============================================================
// DATA & ANALYTICS
// ============================================================

import DataAnalytics
  from "../pages/DataAnalytics/DataAnalytics";


// ============================================================
// ROUTES
// ============================================================

function AppRoutes() {

  return (

    <BrowserRouter>

      <Routes>

        {/* ==================================================
            LANDING
        ================================================== */}

        <Route
          path="/"
          element={
            <Landing />
          }
        />


        {/* ==================================================
            AUTHENTICATION
        ================================================== */}

        <Route
          path="/login"
          element={
            <Login />
          }
        />

        <Route
          path="/register"
          element={
            <Register />
          }
        />


        {/* ==================================================
            DASHBOARD
        ================================================== */}

        <Route
          path="/dashboard"
          element={
            <Dashboard />
          }
        />


        {/* ==================================================
            EXPENSES
        ================================================== */}

        <Route
          path="/expenses"
          element={
            <Expenses />
          }
        />


        {/* ==================================================
            ADD EXPENSE
        ================================================== */}

        <Route
          path="/add-expense"
          element={
            <AddExpense />
          }
        />


        {/* ==================================================
            EDIT EXPENSE
        ================================================== */}

        <Route
          path="/edit-expense/:id"
          element={
            <EditExpense />
          }
        />


        {/* ==================================================
            EXPENSE DETAILS
        ================================================== */}

        <Route
          path="/expense-details/:id"
          element={
            <ExpenseDetails />
          }
        />


        {/* ==================================================
            BUDGET
        ================================================== */}

        <Route
          path="/budget"
          element={
            <Budget />
          }
        />


        {/* ==================================================
            CATEGORIES
        ================================================== */}

        <Route
          path="/categories"
          element={
            <Categories />
          }
        />


        {/* ==================================================
            REPORTS
        ================================================== */}

        <Route
          path="/reports"
          element={
            <Reports />
          }
        />


        {/* ==================================================
            DATA & ANALYTICS
        ================================================== */}

        <Route
          path="/data-analytics"
          element={
            <DataAnalytics />
          }
        />


        {/* ==================================================
            AI ASSISTANT
        ================================================== */}

        <Route
          path="/ai-assistant"
          element={
            <AIAssistant />
          }
        />


        {/* ==================================================
            RECEIPT SCANNER
        ================================================== */}

        <Route
          path="/receipt-scanner"
          element={
            <ReceiptScanner />
          }
        />


        {/* ==================================================
            VOICE ENTRY
        ================================================== */}

        <Route
          path="/voice-entry"
          element={
            <VoiceEntry />
          }
        />


        {/* ==================================================
            PROFILE
        ================================================== */}

        <Route
          path="/profile"
          element={
            <Profile />
          }
        />


        {/* ==================================================
            SETTINGS
        ================================================== */}

        <Route
          path="/settings"
          element={
            <Settings />
          }
        />

      </Routes>

    </BrowserRouter>

  );
}

export default AppRoutes;