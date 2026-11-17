import axios from "axios";

const API = "http://127.0.0.1:8000/api/categories";


// ============================================================
// GET TOKEN
// ============================================================

const getToken = () => {
  return localStorage.getItem("token");
};


// ============================================================
// AUTH HEADERS
// ============================================================

const authHeader = () => {

  const token = getToken();

  if (!token) {
    throw new Error(
      "No authentication token found. Please login again."
    );
  }

  return {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  };
};


// ============================================================
// GET ALL CATEGORIES
// ============================================================

export const getCategories = async () => {

  const response = await axios.get(
    `${API}/`,
    authHeader()
  );

  return response.data;
};


// ============================================================
// GET SINGLE CATEGORY
// ============================================================

export const getCategoryById = async (id) => {

  const response = await axios.get(
    `${API}/${id}`,
    authHeader()
  );

  return response.data;
};


// ============================================================
// CREATE CATEGORY
// ============================================================

export const createCategory = async (category) => {

  const response = await axios.post(
    `${API}/`,
    category,
    authHeader()
  );

  return response.data;
};


// ============================================================
// UPDATE CATEGORY
// ============================================================

export const updateCategory = async (
  id,
  category
) => {

  const response = await axios.put(
    `${API}/${id}`,
    category,
    authHeader()
  );

  return response.data;
};


// ============================================================
// DELETE CATEGORY
// ============================================================

export const deleteCategory = async (id) => {

  const response = await axios.delete(
    `${API}/${id}`,
    authHeader()
  );

  return response.data;
};