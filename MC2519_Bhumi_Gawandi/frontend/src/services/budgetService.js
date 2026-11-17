import axios from "axios";


// ============================================================
// API URL
// ============================================================

const API =
  "http://127.0.0.1:8000/api/budgets";


// ============================================================
// GET TOKEN
// ============================================================

const getToken = () => {

  return localStorage.getItem(
    "token"
  );
};


// ============================================================
// AUTH HEADERS
// ============================================================

const authHeader = () => {

  const token =
    getToken();

  if (!token) {

    throw new Error(
      "No authentication token found. Please login again."
    );
  }

  return {
    headers: {
      Authorization:
        `Bearer ${token}`,

      "Content-Type":
        "application/json",
    },
  };
};


// ============================================================
// GET ALL BUDGETS
// ============================================================

export const getBudgets =
  async () => {

    const response =
      await axios.get(
        `${API}/`,
        authHeader()
      );

    return response.data;
  };


// ============================================================
// GET SINGLE BUDGET
// ============================================================

export const getBudgetById =
  async (id) => {

    const response =
      await axios.get(
        `${API}/${id}`,
        authHeader()
      );

    return response.data;
  };


// ============================================================
// CREATE BUDGET
// ============================================================

export const createBudget =
  async (budget) => {

    const response =
      await axios.post(
        `${API}/`,
        budget,
        authHeader()
      );

    return response.data;
  };


// ============================================================
// UPDATE BUDGET
// ============================================================

export const updateBudget =
  async (
    id,
    budget
  ) => {

    const response =
      await axios.put(
        `${API}/${id}`,
        budget,
        authHeader()
      );

    return response.data;
  };


// ============================================================
// DELETE BUDGET
// ============================================================

export const deleteBudget =
  async (id) => {

    const response =
      await axios.delete(
        `${API}/${id}`,
        authHeader()
      );

    return response.data;
  };


// ============================================================
// REQUEST BUDGET UPGRADE
//
// Sends OTP to logged-in user's email.
// ============================================================

export const requestBudgetUpgrade =
  async (
    id,
    data
  ) => {

    const response =
      await axios.post(
        `${API}/${id}/upgrade/request`,
        data,
        authHeader()
      );

    return response.data;
  };


// ============================================================
// VERIFY BUDGET UPGRADE OTP
// ============================================================

export const verifyBudgetUpgrade =
  async (
    id,
    data
  ) => {

    const response =
      await axios.post(
        `${API}/${id}/upgrade/verify`,
        data,
        authHeader()
      );

    return response.data;
  };