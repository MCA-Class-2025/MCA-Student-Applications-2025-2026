import axios from "axios";


// ============================================================
// API
// ============================================================

const API =
  "http://127.0.0.1:8000/api/voice";


// ============================================================
// TOKEN
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
// PARSE VOICE EXPENSE
// ============================================================

export const parseVoiceExpense = async (
  transcript
) => {

  if (!transcript?.trim()) {

    throw new Error(
      "Please speak an expense."
    );

  }


  try {

    const response =
      await axios.post(

        `${API}/parse`,

        {
          transcript:
            transcript.trim(),
        },

        {
          headers: {

            Authorization:
              `Bearer ${getToken()}`,

            "Content-Type":
              "application/json",

          },

        }

      );


    return response.data;


  } catch (error) {

    console.error(
      "Voice Expense Error:",
      error.response?.data ||
        error.message
    );

    throw error;

  }

};