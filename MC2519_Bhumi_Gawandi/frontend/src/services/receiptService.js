import axios from "axios";

// ============================================================
// RECEIPT API
// ============================================================

const API =
  "http://127.0.0.1:8000/api/receipts";


// ============================================================
// GET TOKEN
// ============================================================

const getToken = () => {

  const token =
    localStorage.getItem("token");

  if (!token) {

    throw new Error(
      "No authentication token found. Please login again."
    );

  }

  return token;
};


// ============================================================
// SCAN RECEIPT
// ============================================================

export const scanReceipt = async (file) => {

  try {

    // --------------------------------------------------------
    // CHECK FILE
    // --------------------------------------------------------

    if (!file) {

      throw new Error(
        "Please select a receipt image."
      );

    }


    // --------------------------------------------------------
    // CREATE FORM DATA
    // --------------------------------------------------------

    const formData =
      new FormData();

    formData.append(
      "file",
      file
    );


    // --------------------------------------------------------
    // API REQUEST
    // --------------------------------------------------------

    const response =
      await axios.post(

        `${API}/scan`,

        formData,

        {
          headers: {

            Authorization:
              `Bearer ${getToken()}`,

          },

        }

      );


    // --------------------------------------------------------
    // DEBUG
    // --------------------------------------------------------

    console.log(
      "Receipt Scan Response:",
      response.data
    );


    // --------------------------------------------------------
    // RETURN RESPONSE
    // --------------------------------------------------------

    return response.data;


  } catch (error) {

    console.error(
      "Receipt Scan Error:",
      error.response?.data ||
      error.message
    );


    throw error;

  }

};