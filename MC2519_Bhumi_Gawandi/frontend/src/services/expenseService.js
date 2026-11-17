import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/expenses";

// ============================================================
// GET TOKEN
// ============================================================

const getToken = () => {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token")
  );
};

// ============================================================
// AUTH HEADERS
// ============================================================

const authHeader = () => {
  const token = getToken();

  return {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  };
};

// ============================================================
// GET ALL EXPENSES
// ============================================================

export const getExpenses = async () => {
  const response = await axios.get(
    `${API_URL}/`,
    authHeader()
  );

  return response.data;
};

// ============================================================
// GET SINGLE EXPENSE
// ============================================================

export const getExpenseById = async (id) => {
  const response = await axios.get(
    `${API_URL}/${id}`,
    authHeader()
  );

  return response.data;
};

// ============================================================
// CREATE EXPENSE
// ============================================================

export const createExpense = async (expense) => {
  const response = await axios.post(
    `${API_URL}/`,
    expense,
    authHeader()
  );

  return response.data;
};

// ============================================================
// UPDATE EXPENSE
// ============================================================

export const updateExpense = async (id, expense) => {
  const response = await axios.put(
    `${API_URL}/${id}`,
    expense,
    authHeader()
  );

  return response.data;
};

// ============================================================
// DELETE EXPENSE
// ============================================================

export const deleteExpense = async (id) => {
  const response = await axios.delete(
    `${API_URL}/${id}`,
    authHeader()
  );

  return response.data;
};