import axios from "axios";


// ============================================================
// AI API BASE URL
// ============================================================

const API =
  "http://127.0.0.1:8000/api/ai";


// ============================================================
// GET TOKEN
// ============================================================

const getToken = () => {

  const token =
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("accessToken");

  if (!token) {

    throw new Error(
      "No authentication token found. Please login again."
    );

  }

  return token;
};


// ============================================================
// AUTH HEADERS
// ============================================================

const authHeader = () => {

  const token = getToken();

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
// 1. AI CHAT
// ============================================================

export const sendAIMessage = async (

  message,

  conversationId = null

) => {

  try {

    console.log(
      "========================================"
    );

    console.log(
      "AI CHAT REQUEST"
    );

    console.log(
      "Message:",
      message
    );

    console.log(
      "Conversation ID:",
      conversationId
    );


    const response =
      await axios.post(

        `${API}/chat`,

        {

          message:
            message,

          /*
           * IMPORTANT
           * First message sends null.
           * Backend should create the conversation.
           */

          conversation_id:
            conversationId || null,

        },

        authHeader()

      );


    console.log(
      "AI CHAT RESPONSE:",
      response.data
    );


    return response.data;


  } catch (error) {

    console.error(
      "========================================"
    );

    console.error(
      "AI CHAT ERROR"
    );

    console.error(
      "STATUS:",
      error.response?.status
    );

    console.error(
      "BACKEND RESPONSE:",
      error.response?.data
    );

    console.error(
      "BACKEND DETAIL:",
      error.response?.data?.detail
    );

    console.error(
      "ERROR MESSAGE:",
      error.message
    );

    console.error(
      "========================================"
    );


    /*
     * Convert FastAPI error into a normal Error
     * so AIAssistant.jsx can display the real problem.
     */

    const backendError =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "AI service request failed.";


    throw new Error(
      backendError
    );

  }

};


// ============================================================
// 2. FINANCIAL NEWS
// ============================================================

export const getFinancialNews = async (

  query =
    "personal finance India"

) => {

  try {

    const response =
      await axios.post(

        `${API}/news`,

        {

          query:
            query,

        },

        authHeader()

      );


    console.log(
      "NEWS RESPONSE:",
      response.data
    );


    return response.data;


  } catch (error) {

    console.error(
      "Financial News Error:",
      error.response?.data ||
      error.message
    );

    throw new Error(
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Financial news request failed."
    );

  }

};


// ============================================================
// 3. CURRENCY CONVERSION
// ============================================================

export const convertCurrency = async (

  base,

  target,

  amount

) => {

  try {

    const response =
      await axios.post(

        `${API}/currency`,

        {

          base:
            base,

          target:
            target,

          amount:
            Number(amount),

        },

        authHeader()

      );


    console.log(
      "CURRENCY RESPONSE:",
      response.data
    );


    return response.data;


  } catch (error) {

    console.error(
      "Currency Conversion Error:",
      error.response?.data ||
      error.message
    );

    throw new Error(
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Currency conversion failed."
    );

  }

};


// ============================================================
// 4. WEATHER
// ============================================================

export const getWeather = async (

  latitude,

  longitude

) => {

  try {

    const response =
      await axios.post(

        `${API}/weather`,

        {

          latitude:
            Number(latitude),

          longitude:
            Number(longitude),

        },

        authHeader()

      );


    console.log(
      "WEATHER RESPONSE:",
      response.data
    );


    return response.data;


  } catch (error) {

    console.error(
      "Weather Error:",
      error.response?.data ||
      error.message
    );

    throw new Error(
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Weather request failed."
    );

  }

};


// ============================================================
// 5. EXCHANGE RATE
// ============================================================

export const getExchangeRate = async (

  base,

  target

) => {

  try {

    console.log(
      "Getting exchange rate:",
      base,
      "→",
      target
    );


    const response =
      await axios.get(

        `${API}/exchange-rate`,

        {

          ...authHeader(),

          params: {

            base:
              base,

            target:
              target,

          },

        }

      );


    console.log(
      "EXCHANGE RATE RESPONSE:",
      response.data
    );


    return response.data;


  } catch (error) {

    console.error(
      "Exchange Rate Error:",
      error.response?.data ||
      error.message
    );

    throw new Error(
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Exchange rate request failed."
    );

  }

};