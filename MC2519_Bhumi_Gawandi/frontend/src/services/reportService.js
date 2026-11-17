import axios from "axios";

const API =
  "http://127.0.0.1:8000/api/reports";


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
// GET REPORT
// ============================================================

export const getReport = async (
  month,
  year,
  category = ""
) => {

  const params = {

    month: month,

    year: year,

  };


  // Add category only when selected

  if (category) {

    params.category = category;

  }


  const response = await axios.get(

    API,

    {

      ...authHeader(),

      params,

    }

  );


  console.log(
    "Report API response:",
    response.data
  );


  return response.data;

};