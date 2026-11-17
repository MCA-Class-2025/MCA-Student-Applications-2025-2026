import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api";


// ============================================================
// GET AUTH TOKEN
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

const getHeaders = () => {
  const token = getToken();

  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  };
};


// ============================================================
// GET CURRENT LOGGED-IN USER
// ============================================================

export const getCurrentUser = async () => {

  const token = getToken();

  if (!token) {
    throw new Error("Authentication token not found.");
  }

  const response = await axios.get(
    `${API_URL}/auth/me`,
    getHeaders()
  );

  console.log("AUTH /ME RESPONSE:", response.data);

  // Handles both:
  //
  // { name: "Bhumi", email: "..." }
  //
  // and:
  //
  // { user: { name: "Bhumi", email: "..." } }
  //
  return response.data?.user || response.data;
};


// ============================================================
// GET ALL EXPENSES
// ============================================================

export const getExpenses = async () => {

  const token = getToken();

  if (!token) {
    throw new Error("Authentication token not found.");
  }

  const response = await axios.get(
    `${API_URL}/expenses/`,
    getHeaders()
  );

  console.log("EXPENSE API RESPONSE:", response.data);

  if (Array.isArray(response.data)) {
    return response.data;
  }

  return response.data?.expenses || [];
};