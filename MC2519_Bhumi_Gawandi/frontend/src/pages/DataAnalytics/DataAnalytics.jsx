import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Database,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Activity,
  Bot,
  RefreshCw,
  Download,
  User,
  History,
  Send,
  MessageSquare,
  Trash2,
  Plus,
  Search,
  Sigma,
  GitBranch,
  Table2,
  Brain,
} from "lucide-react";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import "./DataAnalytics.css";


// ============================================================
// API
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";



// ============================================================
// QUICK QUESTIONS
// ============================================================

const QUICK_QUESTIONS = [
  "Why did my expenses increase?",
  "What category do I spend the most on?",
  "How much did I spend recently?",
  "Which expenses should I reduce?",
  "What will be the future price of rice?",
  "Predict the price of a laptop next month",
];


// ============================================================
// MACHINE LEARNING CLASSIFICATION RESULTS
// These are the actual results produced by the existing
// ml/train_classification_models.py training run.
// Frontend only: no existing API or ML logic is changed.
// ============================================================

const CLASSIFICATION_MODELS = [
  {
    model: "Logistic Regression",
    accuracy: 20.67,
    precision: 19.94,
    recall: 20.67,
    f1_score: 19.67,
  },
  {
    model: "Random Forest",
    accuracy: 16.33,
    precision: 16.14,
    recall: 16.33,
    f1_score: 16.13,
  },
  {
    model: "Decision Tree",
    accuracy: 15.67,
    precision: 15.37,
    recall: 15.67,
    f1_score: 14.93,
  },
  {
    model: "Naive Bayes",
    accuracy: 21.33,
    precision: 17.85,
    recall: 21.33,
    f1_score: 18.25,
  },
  {
    model: "SVM",
    accuracy: 18.67,
    precision: 17.80,
    recall: 18.67,
    f1_score: 17.90,
  },
];

const classificationAverage = (key) =>
  CLASSIFICATION_MODELS.reduce(
    (sum, item) => sum + Number(item[key] || 0),
    0
  ) / CLASSIFICATION_MODELS.length;

const CLASSIFICATION_SUMMARY = {
  accuracy: classificationAverage("accuracy"),
  precision: classificationAverage("precision"),
  recall: classificationAverage("recall"),
  f1_score: classificationAverage("f1_score"),
  modelCount: CLASSIFICATION_MODELS.length,
};

const CLASSIFICATION_CHART_MAX = Math.max(
  ...CLASSIFICATION_MODELS.map((item) => item.accuracy),
  1
);



// ============================================================
// HELPER: TOKEN
// ============================================================

const getToken = () => {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("accessToken") ||
    ""
  );
};


// ============================================================
// HELPER: API REQUEST
// ============================================================

const fetchAPI = async (
  endpoint,
  options = {}
) => {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      cache: "no-store",
      headers,
    }
  );

  const text = await response.text();

  let data = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    let message =
      `${endpoint} failed with status ${response.status}`;

    if (data?.detail) {
      message =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail);
    }

    throw new Error(message);
  }

  return data;
};


// ============================================================
// HELPER: SAFE ARRAY
// ============================================================

const getArray = (response) => {
  if (Array.isArray(response)) {
    return response;
  }

  const candidates = [
    response?.data,
    response?.records,
    response?.items,
    response?.results,
    response?.expenses,
    response?.api_data,
    response?.apiData,
    response?.fused_data,
    response?.data?.data,
    response?.data?.records,
    response?.data?.items,
    response?.data?.results,
    response?.data?.expenses,
    response?.data?.api_data,
    response?.data?.apiData,
  ];

  for (const value of candidates) {
    if (Array.isArray(value)) {
      return value;
    }
  }

  return [];
};


// ============================================================
// HELPER: NUMBER
// ============================================================

const toNumber = (value) => {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : 0;
};


// ============================================================
// HELPER: CURRENCY
// ============================================================

const formatCurrency = (
  value,
  currency = "INR"
) => {
  const amount = toNumber(value);

  try {
    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency,
        maximumFractionDigits: 2,
      }
    ).format(amount);
  } catch {
    return `₹${amount.toLocaleString("en-IN")}`;
  }
};


// ============================================================
// HELPER: DATE
// ============================================================

const formatDate = (value) => {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
};


// ============================================================
// HELPER: NORMALIZE EXPENSE
// ============================================================

const normalizeExpense = (
  expense
) => {
  return {
    id:
      expense?._id ||
      expense?.id ||
      `${expense?.date}-${expense?.amount}-${Math.random()}`,

    date:
      expense?.date ||
      expense?.created_at ||
      "",

    category:
      expense?.category ||
      "Other",

    title:
      expense?.title ||
      expense?.description ||
      "Expense",

    description:
      expense?.description ||
      expense?.title ||
      "Expense",

    amount:
      toNumber(
        expense?.amount
      ),

    payment_method:
      expense?.payment_method ||
      "Other",

    notes:
      expense?.notes ||
      "",

    source:
      "User",
  };
};

// ============================================================
// HELPER: NORMALIZE API DATA
// API records are kept separate from user and historical rows,
// but use the same table structure so they can be displayed
// in the existing fused table.
// ============================================================

const normalizeApiRecord = (
  row,
  index
) => {
  const source =
    row?.source ||
    row?.provider ||
    row?.api_name ||
    row?.api ||
    row?.service ||
    row?.source_name ||
    "API Data";

  const date =
    row?.date ||
    row?.transaction_date ||
    row?.timestamp ||
    row?.created_at ||
    row?.published_at ||
    row?.updated_at ||
    "";

  const amountValue =
    row?.amount ??
    row?.value ??
    row?.price ??
    row?.expense ??
    row?.cost ??
    row?.total ??
    0;

  const description =
    row?.description ||
    row?.title ||
    row?.merchant ||
    row?.name ||
    row?.headline ||
    row?.message ||
    row?.currency_pair ||
    "API financial record";

  const category =
    row?.category ||
    row?.type ||
    row?.service_type ||
    row?.data_type ||
    "API";

  const type =
    row?.transaction_type ||
    row?.record_type ||
    row?.type ||
    "API";

  const anomaly =
    row?.anomaly_status ||
    row?.anomaly ||
    row?.status ||
    "Normal";

  return {
    id:
      row?._id ||
      row?.id ||
      `api-${index}-${date}-${amountValue}`,

    date,
    source,
    source_type: "API",
    type,
    category,
    description,
    amount: toNumber(amountValue),
    payment_method:
      row?.payment_method ||
      row?.method ||
      "API",
    anomaly,
    raw: row,
  };
};


// ============================================================
// HELPER: NORMALIZE BACKEND FUSED RECORD
// ============================================================

const normalizeBackendFusedRecord = (
  row,
  index
) => {

  const rawSourceType =
    String(
      row?.source_type ||
      row?.data_source ||
      ""
    ).toLowerCase();

  let sourceType =
    rawSourceType;

  if (
    rawSourceType === "your data" ||
    rawSourceType === "user expense" ||
    rawSourceType === "user"
  ) {
    sourceType = "user";
  } else if (
    rawSourceType === "historical" ||
    rawSourceType === "history"
  ) {
    sourceType = "historical";
  } else if (
    rawSourceType === "api" ||
    rawSourceType === "external api"
  ) {
    sourceType = "api";
  } else {
    const sourceText =
      String(
        row?.source ||
        ""
      ).toLowerCase();

    sourceType =
      sourceText.includes("api")
        ? "api"
        : sourceText.includes("user")
        ? "user"
        : "historical";
  }


  const anomalyStatus =
    row?.anomaly_status ||
    row?.anomaly ||
    row?.status ||
    "Normal";


  return {

    id:
      row?._id ||
      row?.id ||
      `fused-${index}-${row?.date || row?.timestamp || ""}-${row?.amount ?? 0}`,

    date:
      row?.date ||
      row?.transaction_date ||
      row?.Date ||
      row?.timestamp ||
      row?.created_at ||
      row?.published_at ||
      "",

    source:
      row?.source ||
      (
        sourceType === "user"
          ? "User"
          : sourceType === "api"
          ? "API Data"
          : "Historical"
      ),

    source_type:
      sourceType,

    type:
      row?.type ||
      row?.transaction_type ||
      row?.record_type ||
      "Expense",

    category:
      row?.category ||
      row?.Category ||
      row?.data_type ||
      "Other",

    description:
      row?.description ||
      row?.title ||
      row?.merchant ||
      row?.name ||
      row?.headline ||
      row?.message ||
      "Financial record",

    amount:
      toNumber(
        row?.amount ??
        row?.Amount ??
        row?.value ??
        row?.price ??
        row?.cost ??
        row?.total ??
        0
      ),

    payment_method:
      row?.payment_method ||
      row?.method ||
      "",

    anomaly:
      anomalyStatus,

    anomaly_status:
      anomalyStatus,

    anomaly_score:
      row?.anomaly_score ??
      null,

    ml_prediction:
      row?.ml_prediction ??
      null,

    status:
      row?.status ||
      anomalyStatus,

    raw:
      row,

  };
};


// ============================================================
// HELPER: DOWNLOAD CSV
// ============================================================

const downloadCSV = (
  data,
  filename
) => {
  if (
    !Array.isArray(data) ||
    data.length === 0
  ) {
    alert("No data available.");
    return;
  }

  const headers = Object.keys(
    data[0]
  );

  const rows = [];

  rows.push(
    headers.join(",")
  );

  data.forEach((row) => {
    const values =
      headers.map(
        (header) => {
          const value =
            row?.[header] ?? "";

          return `"${String(value)
            .replace(/"/g, '""')}"`;
        }
      );

    rows.push(
      values.join(",")
    );
  });

  const blob =
    new Blob(
      [rows.join("\n")],
      {
        type:
          "text/csv;charset=utf-8;",
      }
    );

  const url =
    URL.createObjectURL(
      blob
    );

  const link =
    document.createElement(
      "a"
    );

  link.href = url;
  link.download = filename;

  document.body.appendChild(
    link
  );

  link.click();

  document.body.removeChild(
    link
  );

  URL.revokeObjectURL(
    url
  );
};



// ============================================================
// EDA HELPERS
// Client-side exploratory analysis over the currently available
// fused dataset. Existing data fetching and ML logic are kept intact.
// ============================================================

const isNumericValue = (value) => {
  if (value === null || value === undefined || value === "") return false;
  const n = Number(value);
  return Number.isFinite(n);
};

const numericValues = (rows, key) =>
  rows
    .map((row) => Number(row?.[key]))
    .filter((value) => Number.isFinite(value));

// Keep missing values missing. Do not convert an unavailable
// feature into zero because zero is a real numeric value and
// would distort EDA, histograms and correlations.
const nullableNumber = (value) => {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const pairedNumericValues = (rows, firstKey, secondKey) => {
  const pairs = [];

  rows.forEach((row) => {
    const first = nullableNumber(row?.[firstKey]);
    const second = nullableNumber(row?.[secondKey]);

    if (first !== null && second !== null) {
      pairs.push([first, second]);
    }
  });

  return pairs;
};

const meanOf = (values) =>
  values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;

const medianOf = (values) => {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
};

const modeOf = (values) => {
  if (!values.length) return 0;
  const counts = new Map();
  values.forEach((value) => {
    const key = Number(value).toFixed(8);
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  let bestKey = null;
  let bestCount = 0;

  counts.forEach((count, key) => {
    if (count > bestCount) {
      bestCount = count;
      bestKey = key;
    }
  });

  return bestKey === null ? 0 : Number(bestKey);
};

const varianceOf = (values) => {
  if (values.length < 2) return 0;
  const mean = meanOf(values);
  return (
    values.reduce(
      (sum, value) => sum + Math.pow(value - mean, 2),
      0
    ) / values.length
  );
};

const standardDeviationOf = (values) =>
  Math.sqrt(varianceOf(values));

const quantileOf = (values, percentile) => {
  if (!values.length) return 0;

  const sorted = [...values].sort((a, b) => a - b);
  const index = (sorted.length - 1) * percentile;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);

  if (lower === upper) return sorted[lower];

  return (
    sorted[lower] +
    (sorted[upper] - sorted[lower]) * (index - lower)
  );
};

const pearsonCorrelation = (x, y) => {
  const pairs = [];

  for (let i = 0; i < Math.min(x.length, y.length); i += 1) {
    if (Number.isFinite(x[i]) && Number.isFinite(y[i])) {
      pairs.push([x[i], y[i]]);
    }
  }

  if (pairs.length < 2) return 0;

  const xs = pairs.map((pair) => pair[0]);
  const ys = pairs.map((pair) => pair[1]);

  const meanX = meanOf(xs);
  const meanY = meanOf(ys);

  let numerator = 0;
  let denominatorX = 0;
  let denominatorY = 0;

  for (let i = 0; i < pairs.length; i += 1) {
    const dx = xs[i] - meanX;
    const dy = ys[i] - meanY;

    numerator += dx * dy;
    denominatorX += dx * dx;
    denominatorY += dy * dy;
  }

  if (denominatorX === 0 || denominatorY === 0) return 0;

  return numerator / Math.sqrt(denominatorX * denominatorY);
};

const correlationLabel = (value) => {
  const absolute = Math.abs(value);

  if (absolute >= 0.8) return "Very strong";
  if (absolute >= 0.6) return "Strong";
  if (absolute >= 0.4) return "Moderate";
  if (absolute >= 0.2) return "Weak";
  return "Very weak";
};

const histogramBins = (values, requestedBins = 8) => {
  if (!values.length) return [];

  const min = Math.min(...values);
  const max = Math.max(...values);

  if (min === max) {
    return [{
      start: min,
      end: max,
      count: values.length,
      label: String(min),
    }];
  }

  const binCount = Math.min(
    Math.max(requestedBins, 4),
    12
  );

  const width = (max - min) / binCount;

  const bins = Array.from(
    { length: binCount },
    (_, index) => ({
      start: min + index * width,
      end: index === binCount - 1
        ? max
        : min + (index + 1) * width,
      count: 0,
    })
  );

  values.forEach((value) => {
    let index = Math.floor((value - min) / width);
    if (index >= binCount) index = binCount - 1;
    if (index < 0) index = 0;
    bins[index].count += 1;
  });

  return bins.map((bin) => ({
    ...bin,
    label: `${bin.start.toFixed(0)}-${bin.end.toFixed(0)}`,
  }));
};

const numericEdaSummary = (rows, key) => {
  const values = numericValues(rows, key);

  if (!values.length) {
    return {
      key,
      count: 0,
      mean: 0,
      median: 0,
      mode: 0,
      standardDeviation: 0,
      variance: 0,
      min: 0,
      q1: 0,
      q2: 0,
      q3: 0,
      max: 0,
      iqr: 0,
      lowerFence: 0,
      upperFence: 0,
      outlierCount: 0,
      values: [],
    };
  }

  const q1 = quantileOf(values, 0.25);
  const q2 = quantileOf(values, 0.50);
  const q3 = quantileOf(values, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;

  const outlierCount = values.filter(
    (value) => value < lowerFence || value > upperFence
  ).length;

  return {
    key,
    count: values.length,
    mean: meanOf(values),
    median: q2,
    mode: modeOf(values),
    standardDeviation: standardDeviationOf(values),
    variance: varianceOf(values),
    min: Math.min(...values),
    q1,
    q2,
    q3,
    max: Math.max(...values),
    iqr,
    lowerFence,
    upperFence,
    outlierCount,
    values,
  };
};

const escapeHtml = (value) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

// ============================================================
// MAIN COMPONENT
// ============================================================

function DataAnalytics() {

  // ==========================================================
  // USER
  // ==========================================================

  const [user, setUser] =
    useState(null);


  // ==========================================================
  // USER EXPENSES
  // ==========================================================

  const [userExpenses, setUserExpenses] =
    useState([]);


  // ==========================================================
  // ANALYTICS DATA
  // ==========================================================

  const [summary, setSummary] =
    useState([]);

  const [categories, setCategories] =
    useState([]);

  const [monthly, setMonthly] =
    useState([]);

  const [yearly, setYearly] =
    useState([]);

  const [sources, setSources] =
    useState([]);

  const [anomalies, setAnomalies] =
    useState([]);

  const [apiData, setApiData] =
    useState([]);

  const [historicalData, setHistoricalData] =
    useState([]);

  const [financialSummary, setFinancialSummary] =
    useState([]);



  // ==========================================================
  // UI
  // ==========================================================

  const [activeTab, setActiveTab] =
    useState("overview");

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [search, setSearch] =
    useState("");

  const [sourceFilter, setSourceFilter] =
    useState("all");

  // ==========================================================
  // EDA
  // ==========================================================

  const [edaFeature, setEdaFeature] =
    useState("amount");

  const [edaSecondFeature, setEdaSecondFeature] =
    useState("temperature");

  const [edaCategoryFeature, setEdaCategoryFeature] =
    useState("category");

  const [edaChartMode, setEdaChartMode] =
    useState("histogram");


  // ==========================================================
  // CHAT
  // ==========================================================

  const [chatInput, setChatInput] =
    useState("");

  const [chatMessages, setChatMessages] =
    useState([
      {
        role: "assistant",
        content:
          "Hi! I can help you understand your expenses, spending patterns, categories and unusual transactions.",
      },
    ]);

  const [chatLoading, setChatLoading] =
    useState(false);

  const [conversationId, setConversationId] =
    useState(null);

  const [savedChats, setSavedChats] =
    useState([]);

  const [showChatHistory, setShowChatHistory] =
    useState(false);

  const chatMessagesRef =
    useRef(null);


  // ==========================================================
  // LOAD USER + EXPENSES + ANALYTICS
  // ==========================================================

  const fetchAnalyticsData =
    async (
      refresh = false
    ) => {

      try {

        setError("");

        if (refresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }


        // ====================================================
        // USER
        // ====================================================

        try {

          const userResponse =
            await fetchAPI(
              "/api/auth/me"
            );

          const loggedUser =
            userResponse?.user ||
            userResponse?.data?.user ||
            userResponse ||
            null;

          setUser(
            loggedUser
          );

        } catch (userError) {

          console.error(
            "USER API ERROR:",
            userError
          );

          setUser(null);

        }


        // ====================================================
        // USER EXPENSES
        // ====================================================

        try {

          const expenseResponse =
            await fetchAPI(
              "/api/expenses/"
            );

          const expenseArray =
            getArray(
              expenseResponse
            );

          const normalizedExpenses =
            expenseArray.map(
              normalizeExpense
            );

          setUserExpenses(
            normalizedExpenses
          );

        } catch (expenseError) {

          console.error(
            "USER EXPENSE API ERROR:",
            expenseError
          );

          setUserExpenses([]);

        }


        // ====================================================
        // ANALYTICS
        //
        // IMPORTANT:
        // Your analytics router has individual endpoints such
        // as /summary, /categories, /monthly, /yearly,
        // /sources, /anomalies, /api-data, /data and
        // /financial-summary.
        //
        // There is no need to call /dashboard from the frontend.
        // Calling /dashboard was causing the "Not Found" message.
        // ====================================================

        const analyticsEndpoints = [

          {
            name: "summary",
            endpoint:
              "/api/v1/analytics/summary",
          },

          {
            name: "categories",
            endpoint:
              "/api/v1/analytics/categories",
          },

          {
            name: "monthly",
            endpoint:
              "/api/v1/analytics/monthly",
          },

          {
            name: "yearly",
            endpoint:
              "/api/v1/analytics/yearly",
          },

          {
            name: "sources",
            endpoint:
              "/api/v1/analytics/sources",
          },

          {
            name: "anomalies",
            endpoint:
              "/api/v1/analytics/anomalies",
          },

          {
            name: "apiData",
            endpoint:
              "/api/v1/analytics/api-data",
          },

          {
            name: "fusedData",
            endpoint:
              "/api/v1/analytics/data",
          },

          {
            name: "historicalData",
            endpoint:
              "/api/v1/analytics/historical-data",
          },

          {
            name: "financialSummary",
            endpoint:
              "/api/v1/analytics/financial-summary",
          },

        ];


        const settledResults =
          await Promise.all(
            analyticsEndpoints.map(
              async (
                item
              ) => {

                try {

                  const response =
                    await fetchAPI(
                      item.endpoint
                    );

                  return {

                    name:
                      item.name,

                    success:
                      true,

                    response,

                  };

                } catch (requestError) {

                  console.error(
                    `${item.name} API ERROR:`,
                    requestError
                  );

                  return {

                    name:
                      item.name,

                    success:
                      false,

                    response:
                      null,

                    error:
                      requestError,

                  };

                }

              }
            )
          );


        // ====================================================
        // GET RESPONSE BY NAME
        // ====================================================

        const getResult =
          (
            name
          ) => {

            return settledResults.find(
              (
                item
              ) =>
                item.name ===
                name
            );

          };


        // ====================================================
        // SUMMARY
        // ====================================================

        const summaryResult =
          getResult(
            "summary"
          );

        if (
          summaryResult?.success
        ) {

          setSummary(
            getArray(
              summaryResult.response
            )
          );

        } else {

          setSummary([]);

        }


        // ====================================================
        // CATEGORIES
        // ====================================================

        const categoriesResult =
          getResult(
            "categories"
          );

        if (
          categoriesResult?.success
        ) {

          setCategories(
            getArray(
              categoriesResult.response
            )
          );

        } else {

          setCategories([]);

        }


        // ====================================================
        // MONTHLY
        // ====================================================

        const monthlyResult =
          getResult(
            "monthly"
          );

        if (
          monthlyResult?.success
        ) {

          setMonthly(
            getArray(
              monthlyResult.response
            )
          );

        } else {

          setMonthly([]);

        }


        // ====================================================
        // YEARLY
        // ====================================================

        const yearlyResult =
          getResult(
            "yearly"
          );

        if (
          yearlyResult?.success
        ) {

          setYearly(
            getArray(
              yearlyResult.response
            )
          );

        } else {

          setYearly([]);

        }


        // ====================================================
        // SOURCES
        // ====================================================

        const sourcesResult =
          getResult(
            "sources"
          );

        if (
          sourcesResult?.success
        ) {

          setSources(
            getArray(
              sourcesResult.response
            )
          );

        } else {

          setSources([]);

        }


        // ====================================================
        // ANOMALIES
        // ====================================================

        const anomaliesResult =
          getResult(
            "anomalies"
          );

        if (
          anomaliesResult?.success
        ) {

          setAnomalies(
            getArray(
              anomaliesResult.response
            )
          );

        } else {

          setAnomalies([]);

        }


        // ====================================================
        // API DATA
        // ====================================================

        const apiDataResult =
          getResult(
            "apiData"
          );

        if (
          apiDataResult?.success
        ) {

          const rows =
            getArray(
              apiDataResult.response
            );

          console.log(
            "API DATA RECORD COUNT:",
            rows.length
          );

          setApiData(
            rows
          );

        } else {

          setApiData([]);

        }


        // ====================================================
        // FINANCIAL SUMMARY
        // ====================================================

        const financialSummaryResult =
          getResult(
            "financialSummary"
          );

        if (
          financialSummaryResult?.success
        ) {

          setFinancialSummary(
            getArray(
              financialSummaryResult.response
            )
          );

        } else {

          setFinancialSummary([]);

        }


        // ====================================================
        // FUSED DATA
        //
        // /data returns:
        //
        // User + Historical + API
        //
        // There is NO 27-record limit here.
        // ====================================================

        const fusedDataResult =
          getResult(
            "fusedData"
          );

        let fusedRows = [];

        if (
          fusedDataResult?.success
        ) {

          fusedRows =
            getArray(
              fusedDataResult.response
            );

        }


        console.log(
          "BACKEND FUSED RECORD COUNT:",
          fusedRows.length
        );



        // ====================================================
        // HISTORICAL DATA
        //
        // IMPORTANT:
        // Fetch the historical CSV through its own backend
        // endpoint. Do NOT depend on the fused /data response
        // to discover historical records.
        // ====================================================

        const historicalResult =
          getResult(
            "historicalData"
          );

        let extractedHistorical = [];

        if (
          historicalResult?.success
        ) {

          extractedHistorical =
            getArray(
              historicalResult.response
            );

        }

        console.log(
          "DIRECT HISTORICAL RECORD COUNT:",
          extractedHistorical.length
        );

        console.log(
          "DIRECT HISTORICAL RESPONSE:",
          historicalResult?.response
        );

        setHistoricalData(
          extractedHistorical
        );


        // ====================================================
        // DEBUG SUMMARY
        // ====================================================

        console.log(
          "================================================"
        );

        console.log(
          "DATA ANALYTICS BACKEND DATA"
        );

        console.log(
          "User expenses:",
          userExpenses.length
        );

        console.log(
          "Historical records:",
          extractedHistorical.length
        );

        console.log(
          "Historical endpoint success:",
          historicalResult?.success
        );

        console.log(
          "API records:",
          apiDataResult?.success
            ? getArray(
                apiDataResult.response
              ).length
            : 0
        );

        console.log(
          "Fused records:",
          fusedRows.length
        );

        console.log(
          "================================================"
        );


        // ====================================================
        // ERROR HANDLING
        //
        // One failed endpoint should NOT make the complete
        // dashboard show "Not Found".
        // ====================================================

        const successfulRequests =
          settledResults.filter(
            (
              item
            ) =>
              item.success
          ).length;


        const failedRequests =
          settledResults.filter(
            (
              item
            ) =>
              !item.success
          );


        if (
          successfulRequests ===
          0
        ) {

          setError(
            failedRequests[0]?.error?.message ||
            "Unable to load analytics data."
          );

        } else {

          setError("");

        }


      } catch (err) {

        console.error(
          "Data Analytics error:",
          err
        );

        setError(
          err?.message ||
          "Unable to load analytics data."
        );

      } finally {

        setLoading(false);

        setRefreshing(false);

      }

    };

  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {

    fetchAnalyticsData();

  }, []);


  // ==========================================================
  // REFRESH USER EXPENSES ONLY
  // This keeps the table in sync when a new expense is added
  // without reloading every historical analytics endpoint.
  // ==========================================================

  const refreshUserExpensesOnly =
    async () => {

      try {

        const expenseResponse =
          await fetchAPI(
            "/api/expenses/"
          );

        const expenseArray =
          getArray(
            expenseResponse
          );

        const normalizedExpenses =
          expenseArray.map(
            normalizeExpense
          );

        setUserExpenses(
          normalizedExpenses
        );

      } catch (err) {

        console.error(
          "Unable to refresh user expenses:",
          err
        );

      }

    };


  // ==========================================================
  // KEEP TABLE UPDATED
  // Handles:
  // 1. expenseAdded
  // 2. expenseUpdated
  // 3. expenseDeleted
  // 4. expensesUpdated
  // 5. page focus / visibility
  // 6. 5 second polling while this page is open
  // ==========================================================

  useEffect(() => {

    const refreshHandler =
      () => {
        refreshUserExpensesOnly();
      };


    const handleVisibility =
      () => {

        if (
          document.visibilityState ===
          "visible"
        ) {
          refreshUserExpensesOnly();
        }

      };


    const handleFocus =
      () => {
        refreshUserExpensesOnly();
      };


    window.addEventListener(
      "expenseAdded",
      refreshHandler
    );

    window.addEventListener(
      "expenseUpdated",
      refreshHandler
    );

    window.addEventListener(
      "expenseDeleted",
      refreshHandler
    );

    window.addEventListener(
      "expensesUpdated",
      refreshHandler
    );

    window.addEventListener(
      "focus",
      handleFocus
    );

    document.addEventListener(
      "visibilitychange",
      handleVisibility
    );


    // Fallback:
    // if the Add Expense page does not dispatch a custom
    // browser event, the table still gets the new entry.
    const intervalId =
      window.setInterval(
        () => {
          refreshUserExpensesOnly();
        },
        5000
      );


    return () => {

      window.removeEventListener(
        "expenseAdded",
        refreshHandler
      );

      window.removeEventListener(
        "expenseUpdated",
        refreshHandler
      );

      window.removeEventListener(
        "expenseDeleted",
        refreshHandler
      );

      window.removeEventListener(
        "expensesUpdated",
        refreshHandler
      );

      window.removeEventListener(
        "focus",
        handleFocus
      );

      document.removeEventListener(
        "visibilitychange",
        handleVisibility
      );

      window.clearInterval(
        intervalId
      );

    };

  }, []);


  // ==========================================================
  // TOTAL EXPENSE
  // ==========================================================

  const totalExpense =
    useMemo(() => {

      return userExpenses.reduce(
        (
          total,
          expense
        ) =>
          total +
          toNumber(
            expense.amount
          ),
        0
      );

    }, [
      userExpenses,
    ]);


  // ==========================================================
  // MONTHLY INCOME
  // ==========================================================

  const monthlyIncome =
    useMemo(() => {

      return toNumber(
        user?.monthly_income ??
        user?.monthlyIncome ??
        user?.income ??
        0
      );

    }, [
      user,
    ]);


  // ==========================================================
  // REMAINING
  // ==========================================================

  const remaining =
    monthlyIncome -
    totalExpense;


  // ==========================================================
  // CURRENCY
  // ==========================================================

  const currency =
    user?.preferred_currency ||
    user?.preferredCurrency ||
    "INR";


  // ==========================================================
  // USER CATEGORY DATA
  // ==========================================================

  const userCategoryData =
    useMemo(() => {

      const map = {};

      userExpenses.forEach(
        (expense) => {

          const category =
            expense.category ||
            "Other";

          if (
            !map[category]
          ) {
            map[category] = 0;
          }

          map[category] +=
            toNumber(
              expense.amount
            );

        }
      );

      return Object.entries(
        map
      )
        .map(
          ([
            category,
            amount,
          ]) => ({
            category,
            amount,
          })
        )
        .sort(
          (a, b) =>
            b.amount -
            a.amount
        );

    }, [
      userExpenses,
    ]);


  // ==========================================================
  // USER MONTHLY DATA
  // ==========================================================

  const userMonthlyData =
    useMemo(() => {

      const map = {};

      userExpenses.forEach(
        (expense) => {

          const date =
            new Date(
              expense.date
            );

          if (
            Number.isNaN(
              date.getTime()
            )
          ) {
            return;
          }

          const key =
            `${date.getFullYear()}-${String(
              date.getMonth() + 1
            ).padStart(2, "0")}`;

          if (
            !map[key]
          ) {
            map[key] = 0;
          }

          map[key] +=
            toNumber(
              expense.amount
            );

        }
      );

      return Object.entries(
        map
      )
        .sort()
        .map(
          ([
            key,
            amount,
          ]) => {

            const [
              year,
              month,
            ] =
              key.split("-");

            const date =
              new Date(
                Number(year),
                Number(month) - 1,
                1
              );

            return {
              key,

              month:
                date.toLocaleDateString(
                  "en-IN",
                  {
                    month: "short",
                  }
                ),

              amount,
            };

          }
        );

    }, [
      userExpenses,
    ]);


  // ==========================================================
  // AVERAGE EXPENSE
  // ==========================================================

  const averageExpense =
    userExpenses.length > 0
      ? totalExpense /
        userExpenses.length
      : 0;


  // ==========================================================
  // USER ANOMALIES
  // ==========================================================

  const userAnomalies =
    useMemo(() => {

      if (
        userExpenses.length ===
        0
      ) {
        return [];
      }

      return userExpenses.filter(
        (expense) =>
          toNumber(
            expense.amount
          ) >
          averageExpense * 2.5
      );

    }, [
      userExpenses,
      averageExpense,
    ]);


  // ==========================================================
  // USER FUSED DATA
  // ==========================================================

  const userFusedData =
    useMemo(() => {

      return userExpenses
        .map(
          (expense) => {

            const amount =
              toNumber(
                expense.amount
              );

            const anomaly =
              amount >
              averageExpense * 2.5;

            return {

              id:
                expense.id ||
                expense._id ||
                `${expense.date}-${expense.amount}-${expense.description}`,

              date:
                expense.date,

              source:
                "User",

              source_type:
                "User",

              type:
                "Expense",

              category:
                expense.category,

              description:
                expense.description,

              amount,

              payment_method:
                expense.payment_method,

              anomaly:
                anomaly
                  ? "Anomaly"
                  : "Normal",

            };

          }
        )
        .sort(
          (a, b) =>
            new Date(
              b.date || 0
            ).getTime() -
            new Date(
              a.date || 0
            ).getTime()
        );

    }, [
      userExpenses,
      averageExpense,
    ]);


  // ==========================================================
  // HISTORICAL FUSED DATA
  // ==========================================================

  const normalizedHistoricalData =
    useMemo(() => {

      return historicalData
        .map(
          (row, index) => {

            const amount =
              toNumber(
                row?.amount ??
                row?.Amount ??
                row?.price ??
                row?.Price ??
                row?.value ??
                row?.cost ??
                row?.total ??
                0
              );

            const product =
              row?.product ||
              row?.Product ||
              row?.name ||
              row?.Name ||
              "";

            const description =
              row?.description ||
              row?.Description ||
              row?.title ||
              row?.Title ||
              row?.merchant ||
              row?.Merchant ||
              product ||
              "Historical transaction";

            return {

              id:
                row?._id ||
                row?.id ||
                `historical-${index}-${row?.date || row?.transaction_date || row?.Date || ""}-${amount}`,

              date:
                row?.date ||
                row?.transaction_date ||
                row?.Date ||
                row?.timestamp ||
                row?.created_at ||
                row?.published_at ||
                "",

              source:
                row?.source ||
                row?.source_type ||
                "Historical",

              source_type:
                "historical",

              type:
                row?.type ||
                row?.transaction_type ||
                row?.record_type ||
                "Historical",

              category:
                row?.category ||
                row?.Category ||
                row?.data_type ||
                "Other",

              description,

              amount,

              payment_method:
                row?.payment_method ||
                row?.method ||
                "Historical",

              anomaly:
                row?.anomaly ||
                row?.anomaly_status ||
                row?.status ||
                "Normal",

              anomaly_status:
                row?.anomaly_status ||
                row?.anomaly ||
                row?.status ||
                "Normal",

              raw:
                row,

            };

          }
        )
        .sort(
          (a, b) =>
            new Date(
              b.date || 0
            ).getTime() -
            new Date(
              a.date || 0
            ).getTime()
        );

    }, [
      historicalData,
    ]);


  // ==========================================================
  // HISTORICAL EDA
  // Built directly from the historical dataset so the EDA
  // remains available even if the aggregate endpoints return
  // a different response shape.
  // ==========================================================

  const historicalEDA =
    useMemo(() => {

      const rows =
        normalizedHistoricalData.filter(
          (row) =>
            toNumber(
              row.amount
            ) >= 0
        );


      const total =
        rows.reduce(
          (
            sum,
            row
          ) =>
            sum +
            toNumber(
              row.amount
            ),
          0
        );


      const average =
        rows.length > 0
          ? total / rows.length
          : 0;


      const maximum =
        rows.reduce(
          (
            max,
            row
          ) =>
            Math.max(
              max,
              toNumber(
                row.amount
              )
            ),
          0
        );


      const categoryMap =
        {};

      rows.forEach(
        (row) => {

          const category =
            row.category ||
            "Other";

          categoryMap[
            category
          ] =
            (
              categoryMap[
                category
              ] || 0
            ) +
            toNumber(
              row.amount
            );

        }
      );


      const categoryData =
        Object.entries(
          categoryMap
        )
          .map(
            ([
              category,
              amount,
            ]) => ({
              category,
              amount,
            })
          )
          .sort(
            (a, b) =>
              b.amount -
              a.amount
          );


      const monthlyMap =
        {};

      rows.forEach(
        (row) => {

          const date =
            new Date(
              row.date
            );

          if (
            Number.isNaN(
              date.getTime()
            )
          ) {
            return;
          }


          const key =
            `${date.getFullYear()}-${String(
              date.getMonth() + 1
            ).padStart(2, "0")}`;


          if (
            !monthlyMap[
              key
            ]
          ) {

            monthlyMap[
              key
            ] = {
              key,
              label:
                date.toLocaleDateString(
                  "en-IN",
                  {
                    month:
                      "short",
                    year:
                      "2-digit",
                  }
                ),
              amount: 0,
            };

          }


          monthlyMap[
            key
          ].amount +=
            toNumber(
              row.amount
            );

        }
      );


      const monthlyData =
        Object.values(
          monthlyMap
        )
          .sort(
            (a, b) =>
              a.key.localeCompare(
                b.key
              )
          )
          .slice(-12);


      const yearlyMap =
        {};

      rows.forEach(
        (row) => {

          const date =
            new Date(
              row.date
            );

          if (
            Number.isNaN(
              date.getTime()
            )
          ) {
            return;
          }


          const year =
            String(
              date.getFullYear()
            );


          yearlyMap[
            year
          ] =
            (
              yearlyMap[
                year
              ] || 0
            ) +
            toNumber(
              row.amount
            );

        }
      );


      const yearlyData =
        Object.entries(
          yearlyMap
        )
          .map(
            ([
              year,
              amount,
            ]) => ({
              year,
              amount,
            })
          )
          .sort(
            (a, b) =>
              a.year.localeCompare(
                b.year
              )
          );


      const sourceMap =
        {};

      rows.forEach(
        (row) => {

          const source =
            row.source ||
            "Historical";

          sourceMap[
            source
          ] =
            (
              sourceMap[
                source
              ] || 0
            ) + 1;

        }
      );


      const sourceData =
        Object.entries(
          sourceMap
        )
          .map(
            ([
              source,
              count,
            ]) => ({
              source,
              count,
            })
          )
          .sort(
            (a, b) =>
              b.count -
              a.count
          );


      const anomalyRows =
        rows.filter(
          (row) =>
            String(
              row.anomaly ||
              ""
            )
              .toLowerCase()
              .includes(
                "anomaly"
              ) ||
            String(
              row.anomaly ||
              ""
            )
              .toLowerCase()
              .includes(
                "abnormal"
              ) ||
            String(
              row.anomaly ||
              ""
            )
              .toLowerCase()
              .includes(
                "outlier"
              )
        );


      const topCategory =
        categoryData.length > 0
          ? categoryData[0]
          : null;


      const highestTransaction =
        rows.reduce(
          (
            highest,
            row
          ) =>
            toNumber(
              row.amount
            ) >
            toNumber(
              highest?.amount
            )
              ? row
              : highest,
          null
        );


      return {
        rows,
        total,
        average,
        maximum,
        categoryData,
        monthlyData,
        yearlyData,
        sourceData,
        anomalyRows,
        topCategory,
        highestTransaction,
      };

    }, [
      normalizedHistoricalData,
    ]);


  // ==========================================================
  // NORMALIZED API DATA
  // ==========================================================

  const normalizedApiData =
    useMemo(() => {

      return apiData
        .map(
          (
            row,
            index
          ) => {

            const normalized =
              normalizeApiRecord(
                row,
                index
              );

            return {
              ...normalized,
              source_type: "api",
            };

          }
        )
        .sort(
          (a, b) =>
            new Date(
              b.date || 0
            ).getTime() -
            new Date(
              a.date || 0
            ).getTime()
        );

    }, [
      apiData,
    ]);


  // ==========================================================
  // FUSED DATA
  //
  // Backend fused_data is the primary source.
  // No artificial 27-record limit is applied.
  // ==========================================================

  const fusedData =
    useMemo(() => {

      /*
       * IMPORTANT:
       * The table is built from ALL three direct sources:
       *
       * 1. User expenses
       * 2. Historical dataset
       * 3. External API data
       *
       * We intentionally do NOT use backendFusedData as the
       * primary table source because an aggregate backend
       * endpoint may return only a limited sample.
       *
       * This makes the UI show every record returned by each
       * source endpoint.
       */

      const combined = [
        ...userFusedData,
        ...normalizedHistoricalData,
        ...normalizedApiData,
      ];

      return combined
        .map(
          (row, index) => ({
            ...row,

            source_type:
              String(
                row.source_type ||
                ""
              ).toLowerCase() === "user"
                ? "user"
                : String(
                    row.source_type ||
                    ""
                  ).toLowerCase() === "api"
                ? "api"
                : "historical",

            source:
              row.source ||
              (
                String(
                  row.source_type ||
                  ""
                ).toLowerCase() === "user"
                  ? "User"
                  : String(
                      row.source_type ||
                      ""
                    ).toLowerCase() === "api"
                  ? "API Data"
                  : "Historical"
              ),

            _fusion_key:
              `${row.source_type || "unknown"}-${row.id || index}`,

          })
        )
        .sort(
          (a, b) =>
            new Date(
              b.date || 0
            ).getTime() -
            new Date(
              a.date || 0
            ).getTime()
        );

    }, [
      userFusedData,
      normalizedHistoricalData,
      normalizedApiData,
    ]);


  // ==========================================================
  // FILTERED FUSED DATA
  // ==========================================================

  const filteredFusedData =
    useMemo(() => {

      let data = [
        ...fusedData,
      ];


      if (
        sourceFilter ===
        "user"
      ) {

        data =
          data.filter(
            (item) =>
              String(
                item.source_type || ""
              ).toLowerCase() ===
              "user"
          );

      }


      if (
        sourceFilter ===
        "historical"
      ) {

        data =
          data.filter(
            (item) =>
              String(
                item.source_type || ""
              ).toLowerCase() ===
              "historical"
          );

      }


      if (
        sourceFilter ===
        "api"
      ) {

        data =
          data.filter(
            (item) =>
              String(
                item.source_type || ""
              ).toLowerCase() ===
              "api"
          );

      }


      if (
        search.trim()
      ) {

        const query =
          search
            .toLowerCase()
            .trim();

        data =
          data.filter(
            (item) =>
              Object.values(
                item
              ).some(
                (value) =>
                  String(
                    value ?? ""
                  )
                    .toLowerCase()
                    .includes(
                      query
                    )
              )
          );

      }

      return data;

    }, [
      fusedData,
      search,
      sourceFilter,
    ]);


  // ==========================================================
  // TOP CATEGORY
  // ==========================================================

  const topCategory =
    userCategoryData.length > 0
      ? userCategoryData[0]
      : null;


  // ==========================================================
  // MAX MONTHLY
  // ==========================================================

  const maxMonthly =
    Math.max(
      ...userMonthlyData.map(
        (item) =>
          item.amount
      ),
      1
    );



  // ==========================================================
  // COMPLETE EDA CALCULATIONS
  // Uses all currently available fused records.
  // ==========================================================

  const edaRows = useMemo(() => {
    return fusedData.map((row) => {
      const raw = row?.raw || {};
      const sourceType = String(row?.source_type || "").toLowerCase();

      const firstNumber = (...values) => {
        for (const value of values) {
          const parsed = nullableNumber(value);
          if (parsed !== null) return parsed;
        }
        return null;
      };

      return {
        ...row,

        // Amount is the core expense variable, so existing normalized
        // amount data is retained. Missing amounts remain null.
        amount: firstNumber(
          row?.amount,
          raw?.amount,
          raw?.Amount,
          raw?.price,
          raw?.Price
        ),

        price: firstNumber(
          raw?.price,
          raw?.Price,
          raw?.unit_price,
          raw?.unitPrice
        ),

        discount: firstNumber(
          raw?.discount,
          raw?.Discount,
          raw?.discount_percentage,
          raw?.discountPercentage
        ),

        rating: firstNumber(
          raw?.rating,
          raw?.Rating
        ),

        quantity: firstNumber(
          raw?.quantity,
          raw?.Quantity
        ),

        temperature: firstNumber(
          raw?.temperature,
          raw?.temp,
          raw?.Temperature
        ),

        demand_index: firstNumber(
          raw?.demand_index,
          raw?.demandIndex,
          raw?.demand
        ),

        api_price: firstNumber(
          raw?.api_price,
          raw?.apiPrice,
          sourceType === "api" ? row?.amount : null
        ),

        api_discount: firstNumber(
          raw?.api_discount,
          raw?.apiDiscount
        ),

        price_change: firstNumber(
          raw?.price_change,
          raw?.priceChange
        ),

        price_change_percentage: firstNumber(
          raw?.price_change_percentage,
          raw?.priceChangePercentage
        ),

        rolling_avg_price: firstNumber(
          raw?.rolling_avg_price,
          raw?.rollingAvgPrice
        ),

        future_price: firstNumber(
          raw?.future_price,
          raw?.futurePrice
        ),

        monthly_income: firstNumber(
          raw?.monthly_income,
          raw?.monthlyIncome
        ),

        monthly_expense: firstNumber(
          raw?.monthly_expense,
          raw?.monthlyExpense
        ),
      };
    });
  }, [fusedData]);

  const edaNumericFeatures = useMemo(() => {
    const candidates = [
      "amount",
      "price",
      "discount",
      "rating",
      "quantity",
      "temperature",
      "demand_index",
      "api_price",
      "api_discount",
      "price_change",
      "price_change_percentage",
      "rolling_avg_price",
      "future_price",
      "monthly_income",
      "monthly_expense",
    ];

    return candidates.filter((key) =>
      edaRows.some((row) => isNumericValue(row?.[key]))
    );
  }, [edaRows]);

  useEffect(() => {
    if (!edaNumericFeatures.length) return;

    if (!edaNumericFeatures.includes(edaFeature)) {
      setEdaFeature(edaNumericFeatures[0]);
    }

    if (
      !edaNumericFeatures.includes(edaSecondFeature) ||
      edaSecondFeature === edaFeature
    ) {
      const alternative = edaNumericFeatures.find(
        (feature) => feature !== edaFeature
      );

      if (alternative) {
        setEdaSecondFeature(alternative);
      }
    }
  }, [edaNumericFeatures, edaFeature, edaSecondFeature]);

  const edaSelectedStats = useMemo(
    () => numericEdaSummary(edaRows, edaFeature),
    [edaRows, edaFeature]
  );

  const edaHistogram = useMemo(
    () => histogramBins(edaSelectedStats.values, 8),
    [edaSelectedStats.values]
  );

  const edaCategoryData = useMemo(() => {
    const map = {};

    edaRows.forEach((row) => {
      const key = String(row?.[edaCategoryFeature] ?? "Unknown").trim() || "Unknown";
      map[key] = (map[key] || 0) + toNumber(row?.amount);
    });

    return Object.entries(map)
      .map(([label, amount]) => ({ label, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 12);
  }, [edaRows, edaCategoryFeature]);

  const edaBivariate = useMemo(() => {
    const pairs = pairedNumericValues(
      edaRows,
      edaFeature,
      edaSecondFeature
    );

    const correlation = pearsonCorrelation(
      pairs.map(([x]) => x),
      pairs.map(([, y]) => y)
    );

    return {
      correlation,
      pairCount: pairs.length,
      points: pairs.slice(0, 80).map(([x, y]) => ({ x, y })),
    };
  }, [edaRows, edaFeature, edaSecondFeature]);

  const edaFeatureStats = useMemo(() => {
    return edaNumericFeatures.map((key) =>
      numericEdaSummary(edaRows, key)
    );
  }, [edaRows, edaNumericFeatures]);

  const edaCorrelationFeatures = useMemo(() => {
    return edaNumericFeatures.slice(0, 10);
  }, [edaNumericFeatures]);

  const edaCorrelationMatrix = useMemo(() => {
    return edaCorrelationFeatures.map((rowKey) => ({
      key: rowKey,
      values: edaCorrelationFeatures.map((columnKey) => {
        const pairs = pairedNumericValues(
          edaRows,
          rowKey,
          columnKey
        );

        return pearsonCorrelation(
          pairs.map(([x]) => x),
          pairs.map(([, y]) => y)
        );
      }),
    }));
  }, [edaRows, edaCorrelationFeatures]);

  const edaOutlierRows = useMemo(() => {
    const stats = numericEdaSummary(edaRows, edaFeature);

    if (!stats.count) return [];

    return edaRows
      .filter((row) => {
        const value = Number(row?.[edaFeature]);
        return (
          Number.isFinite(value) &&
          (value < stats.lowerFence || value > stats.upperFence)
        );
      })
      .slice(0, 100);
  }, [edaRows, edaFeature]);

  const edaDataQuality = useMemo(() => {
    if (!edaRows.length) {
      return {
        rows: 0,
        duplicateLikeRows: 0,
        missingDate: 0,
        missingCategory: 0,
        missingAmount: 0,
      };
    }

    const keys = new Set();
    let duplicateLikeRows = 0;
    let missingDate = 0;
    let missingCategory = 0;
    let missingAmount = 0;

    edaRows.forEach((row) => {
      const key = [
        row?.source_type,
        row?.date,
        row?.description,
        row?.amount,
      ].join("|");

      if (keys.has(key)) duplicateLikeRows += 1;
      keys.add(key);

      if (!row?.date) missingDate += 1;
      if (!row?.category) missingCategory += 1;
      if (!isNumericValue(row?.amount)) missingAmount += 1;
    });

    return {
      rows: edaRows.length,
      duplicateLikeRows,
      missingDate,
      missingCategory,
      missingAmount,
    };
  }, [edaRows]);

  const edaCorrelationColorClass = (value) => {
    const abs = Math.abs(value);
    if (abs >= 0.8) return "eda-corr-very-strong";
    if (abs >= 0.6) return "eda-corr-strong";
    if (abs >= 0.4) return "eda-corr-moderate";
    if (abs >= 0.2) return "eda-corr-weak";
    return "eda-corr-neutral";
  };

  const downloadEDAReport = () => {
    if (!edaRows.length) {
      alert("No fused data is available for EDA.");
      return;
    }

    const summaryRows = edaFeatureStats.map((item) => ({
      feature: item.key,
      count: item.count,
      mean: item.mean,
      median: item.median,
      mode: item.mode,
      standard_deviation: item.standardDeviation,
      variance: item.variance,
      min: item.min,
      q1: item.q1,
      q2: item.q2,
      q3: item.q3,
      max: item.max,
      iqr: item.iqr,
      lower_fence: item.lowerFence,
      upper_fence: item.upperFence,
      outlier_count: item.outlierCount,
    }));

    downloadCSV(
      summaryRows,
      "eda-statistical-summary.csv"
    );

    downloadCSV(
      edaOutlierRows.map((row) => ({
        date: row?.date || "",
        source: row?.source || "",
        source_type: row?.source_type || "",
        category: row?.category || "",
        description: row?.description || "",
        feature: edaFeature,
        value: row?.[edaFeature] ?? "",
      })),
      "eda-outliers.csv"
    );
  };

  // ==========================================================
  // CHATBOT PRICE PREDICTION
  //
  // Price prediction is now handled only when the user asks
  // the AI Assistant for a future price.
  //
  // The normal financial chatbot remains unchanged for
  // ordinary expense questions.
  // ==========================================================

  const isPricePredictionQuestion = (message) => {
    const text = String(message || "").toLowerCase();

    const predictionWords = [
      "predict",
      "prediction",
      "forecast",
      "future price",
      "price next month",
      "price next year",
      "will cost",
      "cost next month",
      "cost next year",
      "expected price",
      "estimated price",
      "price increase",
      "price decrease",
    ];

    const priceWords = [
      "price",
      "cost",
      "rate",
    ];

    const hasPredictionWord =
      predictionWords.some((word) => text.includes(word));

    const hasPriceWord =
      priceWords.some((word) => text.includes(word));

    return hasPredictionWord && hasPriceWord;
  };

  const detectPredictionType = (message) => {
    const text = String(message || "").toLowerCase();

    const electronicsWords = [
      "laptop",
      "mobile",
      "phone",
      "iphone",
      "samsung",
      "television",
      "tv",
      "tablet",
      "computer",
      "electronics",
      "macbook",
      "headphone",
      "watch",
    ];

    return electronicsWords.some((word) => text.includes(word))
      ? "electronics"
      : "grocery";
  };

  const extractProductFromQuestion = (message) => {
    const text = String(message || "").trim();

    const patterns = [
      /(?:price|cost|forecast|predict|prediction|future price)\s+(?:of|for)\s+(.+?)(?:\s+next\b|\s+this\b|\s+in\b|$)/i,
      /(?:of|for)\s+(.+?)(?:\s+next\b|\s+this\b|\s+in\b|$)/i,
      /(?:price|cost)\s+(?:of|for)?\s*(.+?)(?:\s+next\b|\s+this\b|\s+in\b|$)/i,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);

      if (match?.[1]) {
        return match[1]
          .replace(/[?.!,]+$/g, "")
          .trim();
      }
    }

    return "";
  };

  const getPredictionDatasetContext = (message) => {
    const productQuery =
      extractProductFromQuestion(message).toLowerCase();

    const sourceRows = fusedData.filter((row) => {
      const raw = row?.raw || {};
      const productName =
        row?.description ||
        raw?.product_name ||
        raw?.productName ||
        raw?.product ||
        raw?.name ||
        raw?.title ||
        "";

      const category =
        row?.category ||
        raw?.category ||
        "";

      if (!productQuery) {
        return true;
      }

      return (
        String(productName).toLowerCase().includes(productQuery) ||
        String(category).toLowerCase().includes(productQuery) ||
        productQuery.includes(String(productName).toLowerCase())
      );
    });

    const rows = sourceRows
      .slice(0, 100)
      .map(buildPriceFusionRow);

    return {
      columns: PRICE_FUSION_COLUMNS,
      matching_records: rows,
      total_fused_records: fusedData.length,
      historical_records: normalizedHistoricalData.length,
      api_records: normalizedApiData.length,
      user_records: userFusedData.length,
    };
  };

  const sendPricePredictionChat = async (message) => {

    /*
     * IMPORTANT:
     * Your FastAPI backend already exposes:
     *
     * POST /api/v1/ml/price-forecast/grocery
     * POST /api/v1/ml/price-forecast/electronics
     *
     * There is no /api/v1/ml/price-forecast/chat endpoint in
     * the existing backend. The previous frontend version was
     * therefore producing a 404.
     *
     * This version uses the existing ML endpoints directly.
     */

    const predictionType =
      detectPredictionType(message);

    const productQuery =
      extractProductFromQuestion(message);

    const sourceRows =
      predictionType === "electronics"
        ? normalizedHistoricalData
        : normalizedHistoricalData;

    const normalizedQuery =
      String(
        productQuery || ""
      )
        .toLowerCase()
        .trim();

    /*
     * Find the most relevant historical product.
     *
     * We prefer exact/contains matches and then select the
     * latest available row. This gives the existing ML API a
     * real current price from the historical dataset, so the
     * user does not have to type a price in the chatbot.
     */

    let matchingRows =
      sourceRows.filter(
        (row) => {

          const raw =
            row?.raw || {};

          const productName =
            row?.description ||
            raw?.Product ||
            raw?.product ||
            raw?.product_name ||
            raw?.productName ||
            raw?.Name ||
            raw?.name ||
            raw?.Title ||
            raw?.title ||
            "";

          const category =
            row?.category ||
            raw?.Category ||
            raw?.category ||
            "";

          if (!normalizedQuery) {
            return true;
          }

          const productText =
            String(
              productName
            )
              .toLowerCase()
              .trim();

          const categoryText =
            String(
              category
            )
              .toLowerCase()
              .trim();

          return (
            productText.includes(
              normalizedQuery
            ) ||
            normalizedQuery.includes(
              productText
            ) ||
            categoryText.includes(
              normalizedQuery
            )
          );

        }
      );

    /*
     * If the extracted product does not match a historical
     * product, use all historical rows as a fallback. The
     * backend ML service will still perform its own product
     * matching and return a useful error if the product truly
     * does not exist.
     */

    if (
      matchingRows.length === 0
    ) {
      matchingRows =
        sourceRows;
    }

    /*
     * Sort newest first.
     */

    matchingRows =
      [...matchingRows]
        .sort(
          (a, b) =>
            new Date(
              b.date || 0
            ).getTime() -
            new Date(
              a.date || 0
            ).getTime()
        );

    const latestRow =
      matchingRows[0];

    if (!latestRow) {

      throw new Error(
        "No historical price data is available for price prediction."
      );

    }

    const raw =
      latestRow?.raw || {};

    const product =
      productQuery ||
      raw?.Product ||
      raw?.product ||
      raw?.product_name ||
      raw?.productName ||
      latestRow?.description ||
      "";

    if (!product.trim()) {

      throw new Error(
        "Please mention the product name, for example: Predict the future price of Rice."
      );

    }

    const currentPrice =
      toNumber(
        raw?.Price ??
        raw?.price ??
        raw?.current_price ??
        latestRow?.amount
      );

    if (
      currentPrice <= 0
    ) {

      throw new Error(
        `No valid historical price was found for "${product}".`
      );

    }

    /*
     * Prediction target:
     * default to the month immediately after the latest
     * historical record.
     */

    const latestDate =
      new Date(
        latestRow?.date ||
        raw?.Date ||
        raw?.date ||
        Date.now()
      );

    let targetYear =
      latestDate.getFullYear();

    let targetMonth =
      latestDate.getMonth() + 2;

    if (
      targetMonth > 12
    ) {
      targetMonth = 1;
      targetYear += 1;
    }

    const quarter =
      Math.floor(
        (targetMonth - 1) / 3
      ) + 1;

    const endpoint =
      predictionType === "electronics"
        ? "/api/v1/ml/price-forecast/electronics"
        : "/api/v1/ml/price-forecast/grocery";

    const requestBody = {

      product:
        product.trim(),

      current_price:
        currentPrice,

      year:
        targetYear,

      month:
        targetMonth,

      quarter,

    };

    if (
      predictionType ===
      "electronics"
    ) {

      requestBody.category =
        raw?.Category ||
        raw?.category ||
        "Electronics";

      requestBody.brand =
        raw?.Brand ||
        raw?.brand ||
        "Unknown";

      requestBody.merchant =
        raw?.Merchant ||
        raw?.merchant ||
        "Unknown";

      requestBody.currency =
        raw?.Currency ||
        raw?.currency ||
        "INR";

    }

    console.log(
      "CHAT PRICE PREDICTION REQUEST:",
      endpoint,
      requestBody
    );

    const response =
      await fetchAPI(
        endpoint,
        {
          method:
            "POST",

          body:
            JSON.stringify(
              requestBody
            ),
        }
      );

    const result =
      response?.data ||
      response?.result ||
      response;

    const predicted =
      toNumber(
        result?.predicted_future_price ??
        result?.predicted_price ??
        result?.forecast_price ??
        result?.prediction ??
        result?.price ??
        result?.forecast
      );

    if (
      !Number.isFinite(predicted) ||
      predicted <= 0
    ) {

      throw new Error(
        "The ML model did not return a valid future price."
      );

    }

    const change =
      currentPrice > 0
        ? (
            (
              predicted -
              currentPrice
            ) /
            currentPrice
          ) *
          100
        : 0;

    const currencyCode =
      predictionType === "electronics"
        ? (
            raw?.Currency ||
            raw?.currency ||
            "INR"
          )
        : "INR";

    const direction =
      change > 0.01
        ? "increase"
        : change < -0.01
        ? "decrease"
        : "remain approximately stable";

    /*
     * Return a normal chatbot response string. This keeps the
     * existing Chatbot component unchanged.
     */

    return {

      success:
        true,

      response:
        `Price prediction for ${result?.matched_product || product}:\n\n` +
        `Current/latest dataset price: ${formatCurrency(currentPrice, currencyCode)}\n` +
        `Predicted price for ${targetYear}-${String(targetMonth).padStart(2, "0")}: ${formatCurrency(predicted, currencyCode)}\n` +
        `Expected change: ${change >= 0 ? "+" : ""}${change.toFixed(2)}%\n\n` +
        `The price is expected to ${direction}.\n\n` +
        `Model: ${result?.model || "ML Price Model"}\n` +
        `Dataset: ${result?.dataset || "Historical Dataset"}`,

      prediction:
        result,

      conversation_id:
        response?.conversation_id ||
        response?.data?.conversation_id ||
        conversationId,

    };

  };

  // ==========================================================
  // LOAD CHAT HISTORY
  // ==========================================================

  const loadChatHistory =
    async () => {

      try {

        const response =
          await fetchAPI(
            "/api/chat-history/conversations"
          );

        setSavedChats(
          getArray(
            response
          )
        );

      } catch (err) {

        console.log(
          "Chat history unavailable:",
          err.message
        );

      }

    };


  // ==========================================================
  // CHAT HISTORY ON LOAD
  // ==========================================================

  useEffect(() => {

    loadChatHistory();

  }, []);


  // ==========================================================
  // CHAT AUTO SCROLL
  // ==========================================================

  useEffect(() => {

    if (
      chatMessagesRef.current
    ) {

      chatMessagesRef.current.scrollTop =
        chatMessagesRef.current.scrollHeight;

    }

  }, [
    chatMessages,
    chatLoading,
  ]);


  // ==========================================================
  // NEW CHAT
  // ==========================================================

  const createNewChat =
    () => {

      setConversationId(
        null
      );

      setChatMessages([
        {
          role: "assistant",
          content:
            "Hi! I can help you understand your expenses, spending patterns, categories and unusual transactions.",
        },
      ]);

      setShowChatHistory(
        false
      );

    };


  // ==========================================================
  // OPEN CHAT
  // ==========================================================

  const openChat =
    async (
      id
    ) => {

      if (!id) {
        return;
      }

      try {

        const response =
          await fetchAPI(
            `/api/chat-history/conversations/${id}`
          );

        const conversation =
          response?.data ||
          response;

        const messages =
          Array.isArray(
            conversation?.messages
          )
            ? conversation.messages
            : [];

        setConversationId(
          id
        );

        setChatMessages(
          messages.length > 0
            ? messages
            : [
                {
                  role:
                    "assistant",
                  content:
                    "This conversation has no messages yet.",
                },
              ]
        );

        setShowChatHistory(
          false
        );

      } catch (err) {

        console.error(
          "Open chat error:",
          err
        );

      }

    };


  // ==========================================================
  // DELETE CHAT
  // ==========================================================

  const deleteChat =
    async (
      id
    ) => {

      if (!id) {
        return;
      }

      try {

        await fetchAPI(
          `/api/chat-history/conversations/${id}`,
          {
            method:
              "DELETE",
          }
        );

        setSavedChats(
          (previous) =>
            previous.filter(
              (chat) =>
                (
                  chat?.conversation_id ||
                  chat?.id ||
                  chat?._id
                ) !== id
            )
        );

        if (
          conversationId ===
          id
        ) {

          createNewChat();

        }

      } catch (err) {

        console.error(
          "Delete chat error:",
          err
        );

      }

    };


  // ==========================================================
  // SEND CHAT MESSAGE
  // ==========================================================

  const sendChatMessage =
    async () => {

      const message =
        chatInput.trim();

      if (
        !message ||
        chatLoading
      ) {
        return;
      }

      setChatMessages(
        (previous) => [
          ...previous,
          {
            role: "user",
            content: message,
          },
        ]
      );

      setChatInput("");
      setChatLoading(true);

      const priceQuestion =
        isPricePredictionQuestion(message);

      try {

        /*
         * PRICE QUESTION
         *
         * Only prediction questions go through the ML price
         * endpoint. Normal finance questions continue to use
         * the existing AI endpoint.
         */
        const response =
          priceQuestion
            ? await sendPricePredictionChat(message)
            : await fetchAPI(
                "/api/ai/chat",
                {
                  method: "POST",
                  body: JSON.stringify({
                    message,
                    conversation_id:
                      conversationId,
                  }),
                }
              );

        const newId =
          response?.conversation_id ||
          response?.data?.conversation_id ||
          response?.data?.data?.conversation_id;

        if (newId) {
          setConversationId(newId);
        }

        const answer =
          response?.response ||
          response?.answer ||
          response?.message ||
          response?.data?.response ||
          response?.data?.answer ||
          response?.data?.message ||
          (
            priceQuestion
              ? "I could not generate the price prediction. Please check that the grocery/electronics price forecasting API is running."
              : "I could not generate a response."
          );

        setChatMessages(
          (previous) => [
            ...previous,
            {
              role: "assistant",
              content: answer,
            },
          ]
        );

        loadChatHistory();

      } catch (err) {

        console.error(
          priceQuestion
            ? "ML price chat error:"
            : "AI chat error:",
          err
        );

        setChatMessages(
          (previous) => [
            ...previous,
            {
              role: "assistant",
              content:
                priceQuestion
                  ? "I could not run the price prediction. Please make sure the historical price dataset and ML price model are available."
                  : "Sorry, I could not connect to the AI assistant.",
            },
          ]
        );

      } finally {

        setChatLoading(false);

      }

    };


  // ==========================================================
  // QUICK QUESTION
  // ==========================================================

  const askQuickQuestion =
    (
      question
    ) => {

      setChatInput(
        question
      );

    };


  // ==========================================================
  // USER CSV
  // ==========================================================

  const userCSV =
    userExpenses.map(
      (expense) => ({
        date:
          expense.date,

        category:
          expense.category,

        description:
          expense.description,

        amount:
          expense.amount,

        payment_method:
          expense.payment_method,

        notes:
          expense.notes,

        source:
          "User",
      })
    );


  // ==========================================================
  // FINAL DATA-FUSION CSV
  //
  // The CSV intentionally uses many separate columns instead
  // of putting API/user/historical values into one column.
  //
  // Future price is NOT calculated here. It is a training/
  // prediction target when available in the source dataset.
  // The chatbot performs a future-price prediction only when
  // the user asks for one.
  // ==========================================================

  const PRICE_FUSION_COLUMNS = [
    "date",
    "user_id",
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "brand",
    "price",
    "discount",
    "rating",
    "quantity",
    "monthly_income",
    "monthly_expense",
    "category_expense",
    "previous_month_expense",
    "average_expense",
    "purchase_frequency",
    "budget",
    "remaining_budget",
    "savings",
    "inflation_rate",
    "exchange_rate",
    "temperature",
    "demand_index",
    "market_trend",
    "api_price",
    "api_discount",
    "month",
    "quarter",
    "day_of_week",
    "is_weekend",
    "is_festival",
    "price_change",
    "price_change_percentage",
    "rolling_avg_price",
    "future_price",
    "api_source",
    "data_source",
  ];

  const getRawValue = (row, keys, fallback = "") => {
    const raw = row?.raw || row || {};

    for (const key of keys) {
      if (
        raw?.[key] !== undefined &&
        raw?.[key] !== null &&
        raw?.[key] !== ""
      ) {
        return raw[key];
      }

      if (
        row?.[key] !== undefined &&
        row?.[key] !== null &&
        row?.[key] !== ""
      ) {
        return row[key];
      }
    }

    return fallback;
  };

  const getDateParts = (dateValue) => {
    if (!dateValue) {
      return {
        month: "",
        quarter: "",
        day_of_week: "",
        is_weekend: "",
      };
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
      return {
        month: "",
        quarter: "",
        day_of_week: "",
        is_weekend: "",
      };
    }

    const month = date.getMonth() + 1;
    const dayOfWeek = date.getDay();

    return {
      month,
      quarter: `Q${Math.floor((month - 1) / 3) + 1}`,
      day_of_week: dayOfWeek,
      is_weekend: dayOfWeek === 0 || dayOfWeek === 6,
    };
  };

  const buildPriceFusionRow = (row) => {
    const raw = row?.raw || row || {};
    const dateValue = getRawValue(
      row,
      ["date", "transaction_date", "Date", "timestamp", "created_at"],
      ""
    );

    const dateParts = getDateParts(dateValue);

    const sourceType =
      String(row?.source_type || raw?.source_type || "").toLowerCase();

    const dataSource =
      getRawValue(
        row,
        ["data_source", "source", "source_name", "provider"],
        sourceType === "user"
          ? "User"
          : sourceType === "api"
          ? "API"
          : "Historical"
      );

    const price = getRawValue(
      row,
      ["price", "Price", "current_price", "amount", "Amount", "value", "cost"],
      ""
    );

    const category = getRawValue(
      row,
      ["category", "Category", "data_type"],
      ""
    );

    const categoryExpense =
      userCategoryData.find(
        (item) => String(item.category).toLowerCase() === String(category).toLowerCase()
      )?.amount ?? "";

    const monthlyExpenseValue =
      getRawValue(
        row,
        ["monthly_expense", "monthlyExpense"],
        totalExpense
      );

    const avgExpenseValue =
      getRawValue(
        row,
        ["average_expense", "averageExpense"],
        averageExpense
      );

    const apiPrice = getRawValue(
      row,
      ["api_price", "apiPrice"],
      sourceType === "api" ? price : ""
    );

    const apiDiscount = getRawValue(
      row,
      ["api_discount", "apiDiscount"],
      ""
    );

    const apiSource = getRawValue(
      row,
      ["api_source", "apiSource", "provider", "source_name"],
      sourceType === "api" ? dataSource : ""
    );

    return {
      date: dateValue,
      user_id: getRawValue(
        row,
        ["user_id", "userId", "userid"],
        user?.id || user?._id || ""
      ),
      product_id: getRawValue(
        row,
        ["product_id", "productId", "product_code", "sku"],
        ""
      ),
      product_name: getRawValue(
        row,
        ["product_name", "productName", "product", "name", "title"],
        ""
      ),
      category,
      subcategory: getRawValue(
        row,
        ["subcategory", "sub_category", "subCategory"],
        ""
      ),
      brand: getRawValue(
        row,
        ["brand", "Brand"],
        ""
      ),
      price,
      discount: getRawValue(
        row,
        ["discount", "Discount"],
        ""
      ),
      rating: getRawValue(
        row,
        ["rating", "Rating"],
        ""
      ),
      quantity: getRawValue(
        row,
        ["quantity", "Quantity"],
        ""
      ),
      monthly_income: getRawValue(
        row,
        ["monthly_income", "monthlyIncome"],
        monthlyIncome || ""
      ),
      monthly_expense: monthlyExpenseValue,
      category_expense: getRawValue(
        row,
        ["category_expense", "categoryExpense"],
        categoryExpense
      ),
      previous_month_expense: getRawValue(
        row,
        ["previous_month_expense", "previousMonthExpense"],
        ""
      ),
      average_expense: avgExpenseValue,
      purchase_frequency: getRawValue(
        row,
        ["purchase_frequency", "purchaseFrequency"],
        ""
      ),
      budget: getRawValue(
        row,
        ["budget", "monthly_budget", "monthlyBudget"],
        ""
      ),
      remaining_budget: getRawValue(
        row,
        ["remaining_budget", "remainingBudget"],
        monthlyIncome
          ? monthlyIncome - totalExpense
          : ""
      ),
      savings: getRawValue(
        row,
        ["savings", "saving"],
        ""
      ),
      inflation_rate: getRawValue(
        row,
        ["inflation_rate", "inflationRate"],
        ""
      ),
      exchange_rate: getRawValue(
        row,
        ["exchange_rate", "exchangeRate"],
        ""
      ),
      temperature: getRawValue(
        row,
        ["temperature", "temp"],
        ""
      ),
      demand_index: getRawValue(
        row,
        ["demand_index", "demandIndex"],
        ""
      ),
      market_trend: getRawValue(
        row,
        ["market_trend", "marketTrend", "trend"],
        ""
      ),
      api_price: apiPrice,
      api_discount: apiDiscount,
      month: getRawValue(
        row,
        ["month", "Month"],
        dateParts.month
      ),
      quarter: getRawValue(
        row,
        ["quarter", "Quarter"],
        dateParts.quarter
      ),
      day_of_week: getRawValue(
        row,
        ["day_of_week", "dayOfWeek", "DayOfWeek"],
        dateParts.day_of_week
      ),
      is_weekend: getRawValue(
        row,
        ["is_weekend", "isWeekend", "IsWeekend"],
        dateParts.is_weekend
      ),
      is_festival: getRawValue(
        row,
        ["is_festival", "isFestival", "festival"],
        ""
      ),
      price_change: getRawValue(
        row,
        ["price_change", "priceChange", "PriceChange"],
        ""
      ),
      price_change_percentage: getRawValue(
        row,
        [
          "price_change_percentage",
          "priceChangePercentage",
          "PriceChangePercentage",
        ],
        ""
      ),
      rolling_avg_price: getRawValue(
        row,
        [
          "rolling_avg_price",
          "rollingAvgPrice",
          "RollingMean",
          "rolling_mean_price",
        ],
        ""
      ),
      future_price: getRawValue(
        row,
        ["future_price", "futurePrice", "FuturePrice"],
        ""
      ),
      api_source: apiSource,
      data_source: dataSource,
    };
  };

  const priceFusionCSV =
    filteredFusedData.map(buildPriceFusionRow);

  const fusedCSV = priceFusionCSV;

  // ==========================================================
  // LOADING SCREEN
  // ==========================================================

  if (
    loading
  ) {

    return (

      <div className="data-analytics-layout">

        <aside className="data-analytics-sidebar">
          <Sidebar />
        </aside>

        <main className="data-analytics-main">

          <div className="data-analytics-navbar">
            <DashboardNavbar />
          </div>

          <div className="data-analytics-content">

            <div className="analytics-loading">

              <div className="analytics-loader" />

              <p>
                Loading your financial analytics...
              </p>

            </div>

          </div>

        </main>

      </div>

    );

  }


  // ==========================================================
  // MAIN UI
  // ==========================================================

  return (

    <div className="data-analytics-layout">


      {/* ======================================================
          EXISTING SIDEBAR
      ====================================================== */}

      <aside className="data-analytics-sidebar">

        <Sidebar />

      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="data-analytics-main">


        {/* ====================================================
            EXISTING NAVBAR
        ==================================================== */}

        <div className="data-analytics-navbar">

          <DashboardNavbar />

        </div>


        {/* ====================================================
            CONTENT
        ==================================================== */}

        <div className="data-analytics-content">


          {/* ==================================================
              HEADER
          ================================================== */}

          <div className="analytics-page-header">

            <div>

              <p className="analytics-small-title">
                FINANCIAL INTELLIGENCE
              </p>

              <h1>
                Data & Analytics
              </h1>

              <p className="analytics-description">
                Explore your personal financial data,
                spending patterns, historical datasets,
                fused data and AI-powered financial analysis
                in one place.
              </p>

            </div>


            <button
              className="analytics-refresh-btn"
              onClick={() =>
                fetchAnalyticsData(
                  true
                )
              }
              disabled={
                refreshing
              }
            >

              <RefreshCw
                size={18}
                className={
                  refreshing
                    ? "analytics-spin"
                    : ""
                }
              />

              {refreshing
                ? "Refreshing..."
                : "Refresh Data"}

            </button>

          </div>


          {/* ==================================================
              ERROR
          ================================================== */}

          {error && (

            <div className="analytics-error">

              <AlertTriangle
                size={18}
              />

              {error}

            </div>

          )}


          {/* ==================================================
              SUMMARY
          ================================================== */}

          <section className="analytics-summary-grid analytics-summary-five">


            {/* INCOME */}

            <div className="analytics-stat-card">

              <div className="analytics-stat-icon blue">

                <TrendingUp
                  size={22}
                />

              </div>

              <div>

                <p>
                  Monthly Income
                </p>

                <h2>
                  {formatCurrency(
                    monthlyIncome,
                    currency
                  )}
                </h2>

                <span>
                  From your profile
                </span>

              </div>

            </div>


            {/* EXPENSE */}

            <div className="analytics-stat-card">

              <div className="analytics-stat-icon orange">

                <TrendingDown
                  size={22}
                />

              </div>

              <div>

                <p>
                  Total Expenses
                </p>

                <h2>
                  {formatCurrency(
                    totalExpense,
                    currency
                  )}
                </h2>

                <span>
                  {userExpenses.length}
                  {" "}
                  transactions
                </span>

              </div>

            </div>


            {/* REMAINING */}

            <div className="analytics-stat-card">

              <div className="analytics-stat-icon green">

                <Activity
                  size={22}
                />

              </div>

              <div>

                <p>
                  Remaining
                </p>

                <h2>
                  {formatCurrency(
                    remaining,
                    currency
                  )}
                </h2>

                <span>
                  Income minus expenses
                </span>

              </div>

            </div>


            {/* ANOMALIES */}

            <div className="analytics-stat-card">

              <div className="analytics-stat-icon red">

                <AlertTriangle
                  size={22}
                />

              </div>

              <div>

                <p>
                  Possible Anomalies
                </p>

                <h2>
                  {
                    userAnomalies.length
                  }
                </h2>

                <span>
                  Unusually high expenses
                </span>

              </div>

            </div>


            {/* FUSED */}

            <div className="analytics-stat-card">

              <div className="analytics-stat-icon purple">

                <Database
                  size={22}
                />

              </div>

              <div>

                <p>
                  Fused Records
                </p>

                <h2>
                  {
                    fusedData.length
                  }
                </h2>

                <span>
                  All backend records
                </span>

              </div>

            </div>

          </section>


          {/* ==================================================
              TABS
          ================================================== */}

          <div className="analytics-tabs">

            <button
              className={
                activeTab ===
                "overview"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "overview"
                )
              }
            >

              <BarChart3
                size={15}
              />

              Overview

            </button>


            <button
              className={
                activeTab ===
                "user"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "user"
                )
              }
            >

              <User
                size={15}
              />

              My Data

            </button>


            <button
              className={
                activeTab ===
                "historical"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "historical"
                )
              }
            >

              <History
                size={15}
              />

              Historical

            </button>


            <button
              className={
                activeTab ===
                "eda"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "eda"
                )
              }
            >

              <Sigma
                size={15}
              />

              EDA

            </button>


            <button
              className={
                activeTab ===
                "classification"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "classification"
                )
              }
            >

              <Brain
                size={15}
              />

              ML Classification

            </button>


            <button
              className={
                activeTab ===
                "fused"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "fused"
                )
              }
            >

              <Database
                size={15}
              />

              Fused Data

            </button>


            <button
              className={
                activeTab ===
                "assistant"
                  ? "active"
                  : ""
              }
              onClick={() =>
                setActiveTab(
                  "assistant"
                )
              }
            >

              <Bot
                size={15}
              />

              AI Assistant

            </button>

          </div>


          {/* ==================================================
              MACHINE LEARNING CLASSIFICATION
          ================================================== */}

          {activeTab ===
            "classification" && (

            <div className="analytics-main-grid">

              <div className="analytics-left-column">

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Machine Learning Classification Analysis
                      </h3>

                      <p>
                        Comparison of the five classification models trained on the personal finance dataset.
                      </p>

                    </div>

                  </div>


                  {/* SUMMARY CARDS */}

                  <div className="analytics-summary-grid analytics-summary-five">

                    <div className="analytics-stat-card">

                      <div className="analytics-stat-icon purple">
                        <Brain size={22} />
                      </div>

                      <div>
                        <p>Models Tested</p>
                        <h2>{CLASSIFICATION_SUMMARY.modelCount}</h2>
                        <span>Classification algorithms</span>
                      </div>

                    </div>

                    <div className="analytics-stat-card">

                      <div className="analytics-stat-icon blue">
                        <BarChart3 size={22} />
                      </div>

                      <div>
                        <p>Average Accuracy</p>
                        <h2>{CLASSIFICATION_SUMMARY.accuracy.toFixed(2)}%</h2>
                        <span>Across all five models</span>
                      </div>

                    </div>

                    <div className="analytics-stat-card">

                      <div className="analytics-stat-icon green">
                        <Activity size={22} />
                      </div>

                      <div>
                        <p>Average Precision</p>
                        <h2>{CLASSIFICATION_SUMMARY.precision.toFixed(2)}%</h2>
                        <span>Macro performance</span>
                      </div>

                    </div>

                    <div className="analytics-stat-card">

                      <div className="analytics-stat-icon orange">
                        <TrendingUp size={22} />
                      </div>

                      <div>
                        <p>Average Recall</p>
                        <h2>{CLASSIFICATION_SUMMARY.recall.toFixed(2)}%</h2>
                        <span>Across the test set</span>
                      </div>

                    </div>

                    <div className="analytics-stat-card">

                      <div className="analytics-stat-icon blue">
                        <GitBranch size={22} />
                      </div>

                      <div>
                        <p>Average F1 Score</p>
                        <h2>{CLASSIFICATION_SUMMARY.f1_score.toFixed(2)}%</h2>
                        <span>Precision-recall balance</span>
                      </div>

                    </div>

                  </div>


                  {/* ACCURACY CHART */}

                  <div
                    className="analytics-card"
                    style={{
                      marginTop: "24px",
                      boxShadow: "none",
                      border: "1px solid #e5e7eb",
                    }}
                  >

                    <div className="analytics-card-header">

                      <div>
                        <h3>Model Accuracy Comparison</h3>
                        <p>
                          Test-set accuracy from the classification training run.
                        </p>
                      </div>

                    </div>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(5, minmax(110px, 1fr))",
                        gap: "18px",
                        alignItems: "end",
                        minHeight: "300px",
                        padding: "20px 10px 10px",
                        overflowX: "auto",
                      }}
                    >

                      {CLASSIFICATION_MODELS.map((item) => {
                        const height = Math.max(
                          (item.accuracy / CLASSIFICATION_CHART_MAX) * 220,
                          8
                        );

                        return (
                          <div
                            key={item.model}
                            style={{
                              minWidth: "110px",
                              display: "flex",
                              flexDirection: "column",
                              justifyContent: "flex-end",
                              alignItems: "center",
                              gap: "8px",
                            }}
                          >

                            <strong
                              style={{
                                fontSize: "13px",
                                color: "#1f2937",
                              }}
                            >
                              {item.accuracy.toFixed(2)}%
                            </strong>

                            <div
                              title={`${item.model}: ${item.accuracy.toFixed(2)}% accuracy`}
                              style={{
                                width: "58px",
                                height: `${height}px`,
                                borderRadius: "8px 8px 3px 3px",
                                background: "linear-gradient(180deg, #2563eb 0%, #60a5fa 100%)",
                                transition: "height 0.3s ease",
                              }}
                            />

                            <span
                              style={{
                                fontSize: "12px",
                                fontWeight: 600,
                                textAlign: "center",
                                color: "#374151",
                                lineHeight: 1.3,
                              }}
                            >
                              {item.model}
                            </span>

                          </div>
                        );
                      })}

                    </div>

                  </div>


                  {/* PERFORMANCE TABLE */}

                  <div
                    className="fused-table-wrapper"
                    style={{ marginTop: "24px" }}
                  >

                    <table className="fused-table">

                      <thead>
                        <tr>
                          <th>Model</th>
                          <th>Accuracy</th>
                          <th>Precision</th>
                          <th>Recall</th>
                          <th>F1 Score</th>
                        </tr>
                      </thead>

                      <tbody>

                        {CLASSIFICATION_MODELS.map((item) => (

                          <tr key={item.model}>

                            <td>
                              <strong>{item.model}</strong>
                            </td>

                            <td>{item.accuracy.toFixed(2)}%</td>
                            <td>{item.precision.toFixed(2)}%</td>
                            <td>{item.recall.toFixed(2)}%</td>
                            <td>{item.f1_score.toFixed(2)}%</td>

                          </tr>

                        ))}

                      </tbody>

                    </table>

                  </div>

                </div>

              </div>


              <div className="analytics-right-column">

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>
                      <h3>Classification Dataset</h3>
                      <p>Training and testing configuration used for the models.</p>
                    </div>

                  </div>

                  <div className="analytics-summary-grid">

                    <div className="analytics-stat-card">
                      <div className="analytics-stat-icon blue">
                        <Database size={20} />
                      </div>
                      <div>
                        <p>Total Records</p>
                        <h2>1,500</h2>
                        <span>Personal finance dataset</span>
                      </div>
                    </div>

                    <div className="analytics-stat-card">
                      <div className="analytics-stat-icon green">
                        <Activity size={20} />
                      </div>
                      <div>
                        <p>Training Records</p>
                        <h2>1,200</h2>
                        <span>80% of dataset</span>
                      </div>
                    </div>

                    <div className="analytics-stat-card">
                      <div className="analytics-stat-icon orange">
                        <BarChart3 size={20} />
                      </div>
                      <div>
                        <p>Testing Records</p>
                        <h2>300</h2>
                        <span>20% of dataset</span>
                      </div>
                    </div>

                    <div className="analytics-stat-card">
                      <div className="analytics-stat-icon purple">
                        <Table2 size={20} />
                      </div>
                      <div>
                        <p>Target Categories</p>
                        <h2>10</h2>
                        <span>Expense categories</span>
                      </div>
                    </div>

                  </div>

                  <div style={{ marginTop: "22px" }}>

                    <h4
                      style={{
                        margin: "0 0 12px",
                        fontSize: "15px",
                        color: "#111827",
                      }}
                    >
                      Classification Features
                    </h4>

                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "8px",
                      }}
                    >

                      {[
                        "Amount",
                        "Year",
                        "Month",
                        "Day",
                        "DayOfWeek",
                        "IsWeekend",
                        "TypeEncoded",
                      ].map((feature) => (
                        <span
                          key={feature}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            padding: "7px 10px",
                            borderRadius: "999px",
                            background: "#eff6ff",
                            color: "#1d4ed8",
                            border: "1px solid #dbeafe",
                            fontSize: "12px",
                            fontWeight: 600,
                          }}
                        >
                          {feature}
                        </span>
                      ))}

                    </div>

                  </div>

                </div>


                <div className="analytics-card" style={{ marginTop: "20px" }}>

                  <div className="analytics-card-header">
                    <div>
                      <h3>Model Details</h3>
                      <p>Algorithms included in the classification experiment.</p>
                    </div>
                  </div>

                  <div style={{ display: "grid", gap: "10px" }}>

                    {CLASSIFICATION_MODELS.map((item, index) => (
                      <div
                        key={item.model}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "12px",
                          padding: "12px 14px",
                          border: "1px solid #e5e7eb",
                          borderRadius: "10px",
                          background: "#ffffff",
                        }}
                      >

                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <span
                            style={{
                              width: "26px",
                              height: "26px",
                              borderRadius: "50%",
                              display: "inline-flex",
                              alignItems: "center",
                              justifyContent: "center",
                              background: "#eff6ff",
                              color: "#1d4ed8",
                              fontSize: "12px",
                              fontWeight: 700,
                            }}
                          >
                            {index + 1}
                          </span>
                          <span style={{ fontWeight: 600, color: "#374151" }}>
                            {item.model}
                          </span>
                        </div>

                        <span style={{ fontWeight: 700, color: "#111827" }}>
                          {item.accuracy.toFixed(2)}%
                        </span>

                      </div>
                    ))}

                  </div>

                </div>

              </div>

            </div>

          )}


          {/* ==================================================
              OVERVIEW
          ================================================== */}

          {activeTab ===
            "overview" && (

            <div className="analytics-main-grid">


              {/* =================================================
                  LEFT
              ================================================= */}

              <div className="analytics-left-column">


                {/* CATEGORY */}

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Spending by Category
                      </h3>

                      <p>
                        Based on your actual
                        transactions.
                      </p>

                    </div>

                    <BarChart3
                      size={20}
                    />

                  </div>


                  {userCategoryData.length ===
                    0 ? (

                    <div className="analytics-empty">

                      No expense data available.

                    </div>

                  ) : (

                    <div className="category-chart">

                      {userCategoryData
                        .slice(
                          0,
                          8
                        )
                        .map(
                          (
                            item,
                            index
                          ) => {

                            const percentage =
                              totalExpense >
                              0
                                ? (
                                    item.amount /
                                    totalExpense
                                  ) *
                                  100
                                : 0;

                            return (

                              <div
                                className="category-row"
                                key={
                                  `${item.category}-${index}`
                                }
                              >

                                <div className="category-row-top">

                                  <span>
                                    {
                                      item.category
                                    }
                                  </span>

                                  <strong>
                                    {formatCurrency(
                                      item.amount,
                                      currency
                                    )}
                                  </strong>

                                </div>

                                <div className="category-progress">

                                  <div
                                    style={{
                                      width:
                                        `${Math.min(
                                          percentage,
                                          100
                                        )}%`,
                                    }}
                                  />

                                </div>

                              </div>

                            );

                          }
                        )}

                    </div>

                  )}

                </div>


                {/* MONTHLY */}

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Monthly Spending
                      </h3>

                      <p>
                        Your actual monthly
                        expenses.
                      </p>

                    </div>

                    <Activity
                      size={20}
                    />

                  </div>


                  {userMonthlyData.length ===
                    0 ? (

                    <div className="analytics-empty">

                      No monthly data available.

                    </div>

                  ) : (

                    <div className="monthly-chart">

                      {userMonthlyData
                        .slice(
                          -8
                        )
                        .map(
                          (
                            item,
                            index
                          ) => {

                            const height =
                              Math.max(
                                (
                                  item.amount /
                                  maxMonthly
                                ) *
                                  180,
                                8
                              );

                            return (

                              <div
                                className="monthly-column"
                                key={
                                  `${item.key}-${index}`
                                }
                              >

                                <div
                                  className="monthly-bar"
                                  style={{
                                    height:
                                      `${height}px`,
                                  }}
                                  title={
                                    formatCurrency(
                                      item.amount,
                                      currency
                                    )
                                  }
                                />

                                <span>
                                  {
                                    item.month
                                  }
                                </span>

                              </div>

                            );

                          }
                        )}

                    </div>

                  )}

                </div>


                {/* DATA SOURCES */}

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Data Sources
                      </h3>

                      <p>
                        Data used in your analytics.
                      </p>

                    </div>

                    <Database
                      size={20}
                    />

                  </div>


                  <div className="combined-source-summary">


                    <div>

                      <span>
                        My Data
                      </span>

                      <strong>
                        {
                          userExpenses.length
                        }
                      </strong>

                      <small>
                        Actual transactions
                      </small>

                    </div>


                    <div>

                      <span>
                        Historical
                      </span>

                      <strong>
                        {
                          historicalData.length
                        }
                      </strong>

                      <small>
                        Reference records
                      </small>

                    </div>


                    <div>

                      <span>
                        API Data
                      </span>

                      <strong>
                        {
                          apiData.length
                        }
                      </strong>

                      <small>
                        External API records
                      </small>

                    </div>


                    <div>

                      <span>
                        Fused
                      </span>

                      <strong>
                        {
                          fusedData.length
                        }
                      </strong>

                      <small>
                        Combined records
                      </small>

                    </div>


                    <div>

                      <span>
                        Top Category
                      </span>

                      <strong>
                        {
                          topCategory?.category ||
                          "-"
                        }
                      </strong>

                      <small>
                        Highest spending
                      </small>

                    </div>

                  </div>

                </div>


                {/* FUSED TABLE */}

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Fused Financial Dataset
                      </h3>

                      <p>
                        All available user, historical and API
                        records fused into one table.
                      </p>

                    </div>


                    <div className="fused-download-buttons">

                      <button
                        onClick={() =>
                          downloadCSV(
                            userCSV,
                            "my-expenses.csv"
                          )
                        }
                      >

                        <Download
                          size={14}
                        />

                        My Data

                      </button>


                      <button
                        onClick={() =>
                          downloadCSV(
                            priceFusionCSV,
                            "fused-price-prediction-dataset.csv"
                          )
                        }
                      >

                        <Download
                          size={14}
                        />

                        Fusion CSV

                      </button>

                    </div>

                  </div>


                  <div className="fused-actions">

                    <div>

                      Showing
                      {" "}
                      <strong>
                        {
                          filteredFusedData.length
                        }
                      </strong>
                      {" "}
                      of
                      {" "}
                      <strong>
                        {
                          fusedData.length
                        }
                      </strong>
                      {" "}
                      records

                    </div>


                    <div className="fused-download-buttons">

                      <button
                        onClick={() =>
                          setSourceFilter(
                            "all"
                          )
                        }
                      >
                        All
                      </button>

                      <button
                        onClick={() =>
                          setSourceFilter(
                            "user"
                          )
                        }
                      >
                        My Data
                      </button>

                      <button
                        onClick={() =>
                          setSourceFilter(
                            "historical"
                          )
                        }
                      >
                        Historical
                      </button>

                      <button
                        className={
                          sourceFilter ===
                          "api"
                            ? "active"
                            : ""
                        }
                        onClick={() =>
                          setSourceFilter(
                            "api"
                          )
                        }
                      >
                        API Data
                      </button>

                    </div>

                  </div>


                  <div className="table-controls">

                    <input
                      className="analytics-table-search"
                      type="text"
                      placeholder="Search fused data..."
                      value={
                        search
                      }
                      onChange={
                        (event) =>
                          setSearch(
                            event.target.value
                          )
                      }
                    />

                  </div>


                  {filteredFusedData.length ===
                    0 ? (

                    <div className="analytics-empty">

                      No fused records available.

                    </div>

                  ) : (

                    <div className="fused-table-wrapper">

                      <table className="fused-table">

                        <thead>

                          <tr>

                            <th>
                              Date
                            </th>

                            <th>
                              Source
                            </th>

                            <th>
                              Source Type
                            </th>

                            <th>
                              Type
                            </th>

                            <th>
                              Category
                            </th>

                            <th>
                              Description
                            </th>

                            <th>
                              Amount
                            </th>

                            <th>
                              Status
                            </th>

                          </tr>

                        </thead>


                        <tbody>

                          {filteredFusedData.map(
                            (
                              row,
                              index
                            ) => {

                              const isUser =
                                String(
                                  row.source_type || ""
                                ).toLowerCase() ===
                                "user";

                              const isAPI =
                                String(
                                  row.source_type || ""
                                ).toLowerCase() ===
                                "api";

                              const isAnomaly =
                                String(
                                  row.anomaly ||
                                  row.anomaly_status ||
                                  ""
                                )
                                  .toLowerCase()
                                  .includes(
                                    "anomaly"
                                  );

                              return (

                                <tr
                                  key={
                                    `${row.date}-${row.amount}-${index}`
                                  }
                                >

                                  <td>
                                    {formatDate(
                                      row.date
                                    )}
                                  </td>


                                  <td>

                                    <span
                                      className={
                                        isUser
                                          ? "source-badge user-source"
                                          : isAPI
                                          ? "source-badge api-source"
                                          : "source-badge historical-source"
                                      }
                                    >

                                      {isUser
                                        ? "Your Data"
                                        : isAPI
                                        ? row.source || "API Data"
                                        : "Historical"}

                                    </span>

                                  </td>


                                  <td>
                                    <span className="source-badge">
                                      {row.source_type || "-"}
                                    </span>
                                  </td>


                                  <td>
                                    {
                                      row.type
                                    }
                                  </td>


                                  <td>
                                    {
                                      row.category
                                    }
                                  </td>


                                  <td className="description-cell">

                                    {
                                      row.description
                                    }

                                  </td>


                                  <td className="amount-cell">

                                    {formatCurrency(
                                      row.amount,
                                      currency
                                    )}

                                  </td>


                                  <td>

                                    <span
                                      className={
                                        isAnomaly
                                          ? "anomaly-badge danger"
                                          : "anomaly-badge normal"
                                      }
                                    >

                                      {isAnomaly
                                        ? "Anomaly"
                                        : "Normal"}

                                    </span>

                                  </td>

                                </tr>

                              );

                            }
                          )}

                        </tbody>

                      </table>

                    </div>

                  )}


                  <div className="table-footer">

                    Showing all available fused records from
                    User + Historical + API sources.
                    {" "}
                    Total:
                    {" "}
                    {filteredFusedData.length}

                  </div>

                </div>

              </div>


              {/* =================================================
                  CHATBOT
              ================================================= */}

              <Chatbot
                messages={
                  chatMessages
                }

                input={
                  chatInput
                }

                setInput={
                  setChatInput
                }

                loading={
                  chatLoading
                }

                onSend={
                  sendChatMessage
                }

                savedChats={
                  savedChats
                }

                conversationId={
                  conversationId
                }

                showHistory={
                  showChatHistory
                }

                setShowHistory={
                  setShowChatHistory
                }

                newChat={
                  createNewChat
                }

                openChat={
                  openChat
                }

                deleteChat={
                  deleteChat
                }

                quickQuestion={
                  askQuickQuestion
                }

                messagesRef={
                  chatMessagesRef
                }

              />

            </div>

          )}


          {/* ==================================================
              MY DATA
          ================================================== */}

          {activeTab ===
            "user" && (

            <div className="analytics-card">

              <div className="analytics-card-header">

                <div>

                  <h3>
                    My Actual Expense Data
                  </h3>

                  <p>
                    Expenses fetched directly
                    from your account.
                  </p>

                </div>


                <button
                  className="download-button"
                  onClick={() =>
                    downloadCSV(
                      userCSV,
                      "my-expenses.csv"
                    )
                  }
                >

                  <Download
                    size={14}
                  />

                  Download CSV

                </button>

              </div>


              {userExpenses.length ===
                0 ? (

                <div className="analytics-empty">

                  You have not added
                  any expenses yet.

                </div>

              ) : (

                <div className="fused-table-wrapper">

                  <table className="fused-table">

                    <thead>

                      <tr>

                        <th>
                          Date
                        </th>

                        <th>
                          Category
                        </th>

                        <th>
                          Description
                        </th>

                        <th>
                          Payment
                        </th>

                        <th>
                          Amount
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {userExpenses.map(
                        (
                          expense,
                          index
                        ) => (

                          <tr
                            key={
                              expense.id ||
                              index
                            }
                          >

                            <td>
                              {formatDate(
                                expense.date
                              )}
                            </td>

                            <td>
                              {
                                expense.category
                              }
                            </td>

                            <td className="description-cell">
                              {
                                expense.description
                              }
                            </td>

                            <td>
                              {
                                expense.payment_method
                              }
                            </td>

                            <td className="amount-cell">

                              {formatCurrency(
                                expense.amount,
                                currency
                              )}

                            </td>

                          </tr>

                        )
                      )}

                    </tbody>

                  </table>

                </div>

              )}

            </div>

          )}


          {/* ==================================================
              HISTORICAL
          ================================================== */}

          {activeTab ===
            "historical" && (

            <div className="analytics-left-column">


              {/* ==================================================
                  HISTORICAL EDA HEADER
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <p className="analytics-small-title">
                      EXPLORATORY DATA ANALYSIS
                    </p>

                    <h3>
                      Historical Dataset EDA Dashboard
                    </h3>

                    <p>
                      This section analyses the project
                      historical dataset separately from
                      your personal expense data.
                    </p>

                  </div>

                  <History
                    size={22}
                  />

                </div>


                <div className="analytics-summary-grid analytics-summary-five">


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon purple">

                      <Database
                        size={20}
                      />

                    </div>

                    <div>

                      <p>
                        Historical Records
                      </p>

                      <h2>
                        {
                          historicalEDA.rows.length
                        }
                      </h2>

                      <span>
                        Dataset records
                      </span>

                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon orange">

                      <TrendingDown
                        size={20}
                      />

                    </div>

                    <div>

                      <p>
                        Total Historical Spend
                      </p>

                      <h2>
                        {formatCurrency(
                          historicalEDA.total,
                          currency
                        )}
                      </h2>

                      <span>
                        Historical expenses
                      </span>

                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon blue">

                      <Activity
                        size={20}
                      />

                    </div>

                    <div>

                      <p>
                        Average Transaction
                      </p>

                      <h2>
                        {formatCurrency(
                          historicalEDA.average,
                          currency
                        )}
                      </h2>

                      <span>
                        Mean transaction value
                      </span>

                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon green">

                      <BarChart3
                        size={20}
                      />

                    </div>

                    <div>

                      <p>
                        Top Category
                      </p>

                      <h2>
                        {
                          historicalEDA.topCategory?.category ||
                          "-"
                        }
                      </h2>

                      <span>
                        Highest historical spend
                      </span>

                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon red">

                      <AlertTriangle
                        size={20}
                      />

                    </div>

                    <div>

                      <p>
                        Anomalies
                      </p>

                      <h2>
                        {
                          historicalEDA.anomalyRows.length
                        }
                      </h2>

                      <span>
                        Historical outliers
                      </span>

                    </div>

                  </div>

                </div>

              </div>


              {/* ==================================================
                  CATEGORY + MONTHLY EDA
              ================================================== */}

              <div className="analytics-main-grid analytics-user-inner-grid">


                {/* CATEGORY EDA */}

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Historical Spending by Category
                      </h3>

                      <p>
                        Category distribution in the
                        historical dataset.
                      </p>

                    </div>

                    <BarChart3
                      size={20}
                    />

                  </div>


                  {historicalEDA.categoryData.length ===
                    0 ? (

                    <div className="analytics-empty">
                      No historical category data available.
                    </div>

                  ) : (

                    <div className="category-chart">

                      {historicalEDA.categoryData
                        .slice(
                          0,
                          10
                        )
                        .map(
                          (
                            item,
                            index
                          ) => {

                            const percentage =
                              historicalEDA.total >
                              0
                                ? (
                                    item.amount /
                                    historicalEDA.total
                                  ) *
                                  100
                                : 0;

                            return (

                              <div
                                className="category-row"
                                key={
                                  `${item.category}-${index}`
                                }
                              >

                                <div className="category-row-top">

                                  <span>
                                    {
                                      item.category
                                    }
                                  </span>

                                  <strong>
                                    {formatCurrency(
                                      item.amount,
                                      currency
                                    )}
                                  </strong>

                                </div>

                                <div className="category-progress">

                                  <div
                                    style={{
                                      width:
                                        `${Math.min(
                                          percentage,
                                          100
                                        )}%`,
                                    }}
                                  />

                                </div>

                                <small>
                                  {
                                    percentage.toFixed(
                                      1
                                    )
                                  }
                                  % of historical spend
                                </small>

                              </div>

                            );

                          }
                        )}

                    </div>

                  )}

                </div>


                {/* MONTHLY EDA */}

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Historical Monthly Trend
                      </h3>

                      <p>
                        Last 12 available historical
                        months.
                      </p>

                    </div>

                    <Activity
                      size={20}
                    />

                  </div>


                  {historicalEDA.monthlyData.length ===
                    0 ? (

                    <div className="analytics-empty">
                      No historical monthly data available.
                    </div>

                  ) : (

                    <div className="monthly-chart">

                      {historicalEDA.monthlyData.map(
                        (
                          item,
                          index
                        ) => {

                          const max =
                            Math.max(
                              ...historicalEDA.monthlyData.map(
                                (
                                  month
                                ) =>
                                  month.amount
                              ),
                              1
                            );

                          const height =
                            Math.max(
                              (
                                item.amount /
                                max
                              ) *
                                180,
                              8
                            );

                          return (

                            <div
                              className="monthly-column"
                              key={
                                `${item.key}-${index}`
                              }
                            >

                              <div
                                className="monthly-bar"
                                style={{
                                  height:
                                    `${height}px`,
                                }}
                                title={
                                  formatCurrency(
                                    item.amount,
                                    currency
                                  )
                                }
                              />

                              <span>
                                {
                                  item.label
                                }
                              </span>

                            </div>

                          );

                        }
                      )}

                    </div>

                  )}

                </div>

              </div>


              {/* ==================================================
                  YEARLY EDA
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <h3>
                      Yearly Expense Analysis
                    </h3>

                    <p>
                      Compare historical spending
                      across years.
                    </p>

                  </div>

                  <TrendingUp
                    size={20}
                  />

                </div>


                {historicalEDA.yearlyData.length ===
                  0 ? (

                  <div className="analytics-empty">
                    No historical yearly data available.
                  </div>

                ) : (

                  <div className="combined-source-summary">

                    {historicalEDA.yearlyData
                      .slice(
                        -8
                      )
                      .map(
                        (
                          item,
                          index
                        ) => {

                          return (

                            <div
                              key={
                                `${item.year}-${index}`
                              }
                            >

                              <span>
                                {
                                  item.year
                                }
                              </span>

                              <strong>
                                {formatCurrency(
                                  item.amount,
                                  currency
                                )}
                              </strong>

                              <small>
                                Historical expense
                              </small>

                            </div>

                          );

                        }
                      )}

                  </div>

                )}

              </div>


              {/* ==================================================
                  SOURCE DISTRIBUTION + ANOMALY EDA
              ================================================== */}

              <div className="analytics-main-grid analytics-user-inner-grid">


                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Historical Data Sources
                      </h3>

                      <p>
                        Source distribution in the
                        project dataset.
                      </p>

                    </div>

                    <Database
                      size={20}
                    />

                  </div>


                  {historicalEDA.sourceData.length ===
                    0 ? (

                    <div className="analytics-empty">
                      No source information available.
                    </div>

                  ) : (

                    <div className="category-chart">

                      {historicalEDA.sourceData
                        .slice(
                          0,
                          8
                        )
                        .map(
                          (
                            item,
                            index
                          ) => {

                            const percentage =
                              historicalEDA.rows.length >
                              0
                                ? (
                                    item.count /
                                    historicalEDA.rows.length
                                  ) *
                                  100
                                : 0;

                            return (

                              <div
                                className="category-row"
                                key={
                                  `${item.source}-${index}`
                                }
                              >

                                <div className="category-row-top">

                                  <span>
                                    {
                                      item.source
                                    }
                                  </span>

                                  <strong>
                                    {
                                      item.count
                                    }
                                  </strong>

                                </div>

                                <div className="category-progress">

                                  <div
                                    style={{
                                      width:
                                        `${Math.min(
                                          percentage,
                                          100
                                        )}%`,
                                    }}
                                  />

                                </div>

                                <small>
                                  {
                                    percentage.toFixed(
                                      1
                                    )
                                  }% of records
                                </small>

                              </div>

                            );

                          }
                        )}

                    </div>

                  )}

                </div>


                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Anomaly Analysis
                      </h3>

                      <p>
                        Potentially unusual historical
                        transactions.
                      </p>

                    </div>

                    <AlertTriangle
                      size={20}
                    />

                  </div>


                  <div className="combined-source-summary">


                    <div>

                      <span>
                        Total Records
                      </span>

                      <strong>
                        {
                          historicalEDA.rows.length
                        }
                      </strong>

                      <small>
                        Historical dataset
                      </small>

                    </div>


                    <div>

                      <span>
                        Anomalies
                      </span>

                      <strong>
                        {
                          historicalEDA.anomalyRows.length
                        }
                      </strong>

                      <small>
                        Potential outliers
                      </small>

                    </div>


                    <div>

                      <span>
                        Normal
                      </span>

                      <strong>
                        {
                          Math.max(
                            historicalEDA.rows.length -
                            historicalEDA.anomalyRows.length,
                            0
                          )
                        }
                      </strong>

                      <small>
                        Remaining records
                      </small>

                    </div>


                    <div>

                      <span>
                        Anomaly Rate
                      </span>

                      <strong>
                        {
                          historicalEDA.rows.length >
                          0
                            ? `${(
                                (
                                  historicalEDA.anomalyRows.length /
                                  historicalEDA.rows.length
                                ) *
                                100
                              ).toFixed(1)}%`
                            : "0%"
                        }
                      </strong>

                      <small>
                        Historical data
                      </small>

                    </div>

                  </div>


                  {historicalEDA.highestTransaction && (

                    <div className="analytics-empty">

                      Highest transaction:
                      {" "}
                      <strong>
                        {formatCurrency(
                          historicalEDA.highestTransaction.amount,
                          currency
                        )}
                      </strong>
                      {" "}
                      on
                      {" "}
                      {formatDate(
                        historicalEDA.highestTransaction.date
                      )}

                    </div>

                  )}

                </div>

              </div>


              {/* ==================================================
                  HISTORICAL TABLE
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <h3>
                      Historical Financial Data
                    </h3>

                    <p>
                      Historical records used for
                      EDA and model analysis.
                    </p>

                  </div>

                  <button
                    className="download-button"
                    onClick={() =>
                      downloadCSV(
                        historicalData,
                        "historical-data.csv"
                      )
                    }
                  >

                    <Download
                      size={14}
                    />

                    Download CSV

                  </button>

                </div>


                <div className="fused-actions">

                  <div>

                    Showing
                    {" "}
                    <strong>
                      {
                        normalizedHistoricalData.length
                      }
                    </strong>
                    {" "}
                    records

                  </div>

                  <span>
                    Total historical spend:
                    {" "}
                    <strong>
                      {formatCurrency(
                        historicalEDA.total,
                        currency
                      )}
                    </strong>
                  </span>

                </div>


                {normalizedHistoricalData.length ===
                  0 ? (

                  <div className="analytics-empty">

                    No historical data available.

                  </div>

                ) : (

                  <div className="fused-table-wrapper">

                    <table className="fused-table">

                      <thead>

                        <tr>

                          <th>
                            Date
                          </th>

                          <th>
                            Source
                          </th>

                          <th>
                            Category
                          </th>

                          <th>
                            Description
                          </th>

                          <th>
                            Amount
                          </th>

                          <th>
                            Status
                          </th>

                        </tr>

                      </thead>


                      <tbody>

                        {normalizedHistoricalData
                          .map(
                            (
                              row,
                              index
                            ) => {

                              const isAnomaly =
                                String(
                                  row.anomaly ||
                                  ""
                                )
                                  .toLowerCase()
                                  .includes(
                                    "anomaly"
                                  ) ||
                                String(
                                  row.anomaly ||
                                  ""
                                )
                                  .toLowerCase()
                                  .includes(
                                    "abnormal"
                                  ) ||
                                String(
                                  row.anomaly ||
                                  ""
                                )
                                  .toLowerCase()
                                  .includes(
                                    "outlier"
                                  );

                              return (

                                <tr
                                  key={
                                    `${row.date}-${row.amount}-${index}`
                                  }
                                >

                                  <td>
                                    {formatDate(
                                      row.date
                                    )}
                                  </td>

                                  <td>

                                    <span className="source-badge historical-source">

                                      {
                                        row.source ||
                                        "Historical"
                                      }

                                    </span>

                                  </td>

                                  <td>
                                    {
                                      row.category
                                    }
                                  </td>

                                  <td className="description-cell">

                                    {
                                      row.description
                                    }

                                  </td>

                                  <td className="amount-cell">

                                    {formatCurrency(
                                      row.amount,
                                      currency
                                    )}

                                  </td>

                                  <td>

                                    <span
                                      className={
                                        isAnomaly
                                          ? "anomaly-badge danger"
                                          : "anomaly-badge normal"
                                      }
                                    >

                                      {isAnomaly
                                        ? "Anomaly"
                                        : "Normal"}

                                    </span>

                                  </td>

                                </tr>

                              );

                            }
                          )}

                      </tbody>

                    </table>

                  </div>

                )}

              </div>

            </div>

          )}



          {/* ==================================================
              EDA
          ================================================== */}

          {activeTab ===
            "eda" && (

            <div className="analytics-left-column">

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <p className="analytics-small-title">
                      EXPLORATORY DATA ANALYSIS
                    </p>

                    <h3>
                      Statistical & Exploratory Analysis
                    </h3>

                    <p>
                      Univariate, bivariate and multivariate
                      analysis calculated directly from the
                      currently available fused dataset.
                    </p>

                  </div>

                  <div className="fused-download-buttons">

                    <button
                      onClick={downloadEDAReport}
                    >
                      <Download size={14} />
                      Export EDA
                    </button>

                    <button
                      onClick={() =>
                        downloadCSV(
                          priceFusionCSV,
                          "eda-fused-dataset.csv"
                        )
                      }
                    >
                      <Download size={14} />
                      Export Dataset
                    </button>

                  </div>

                </div>


                <div className="analytics-summary-grid analytics-summary-five">

                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon purple">
                      <Database size={20} />
                    </div>

                    <div>
                      <p>EDA Records</p>
                      <h2>{edaRows.length}</h2>
                      <span>User + Historical + API</span>
                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon blue">
                      <Sigma size={20} />
                    </div>

                    <div>
                      <p>Mean {edaFeature}</p>
                      <h2>
                        {formatCurrency(
                          edaSelectedStats.mean,
                          currency
                        )}
                      </h2>
                      <span>Selected numeric feature</span>
                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon green">
                      <BarChart3 size={20} />
                    </div>

                    <div>
                      <p>Median {edaFeature}</p>
                      <h2>
                        {formatCurrency(
                          edaSelectedStats.median,
                          currency
                        )}
                      </h2>
                      <span>50th percentile</span>
                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon orange">
                      <Activity size={20} />
                    </div>

                    <div>
                      <p>Std. Deviation</p>
                      <h2>
                        {formatCurrency(
                          edaSelectedStats.standardDeviation,
                          currency
                        )}
                      </h2>
                      <span>Dispersion</span>
                    </div>

                  </div>


                  <div className="analytics-stat-card">

                    <div className="analytics-stat-icon red">
                      <AlertTriangle size={20} />
                    </div>

                    <div>
                      <p>Outliers</p>
                      <h2>{edaSelectedStats.outlierCount}</h2>
                      <span>IQR method</span>
                    </div>

                  </div>

                </div>

              </div>


              {/* ==================================================
                  EDA CONTROLS
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>
                    <h3>EDA Controls</h3>
                    <p>
                      Select features to inspect their
                      distribution and relationships.
                    </p>
                  </div>

                  <Search size={20} />

                </div>


                <div className="eda-control-grid">

                  <label className="eda-control">

                    <span>Numeric Feature</span>

                    <select
                      value={edaFeature}
                      onChange={(event) =>
                        setEdaFeature(event.target.value)
                      }
                    >

                      {edaNumericFeatures.map((feature) => (
                        <option
                          key={feature}
                          value={feature}
                        >
                          {feature}
                        </option>
                      ))}

                    </select>

                  </label>


                  <label className="eda-control">

                    <span>Second Numeric Feature</span>

                    <select
                      value={edaSecondFeature}
                      onChange={(event) =>
                        setEdaSecondFeature(event.target.value)
                      }
                    >

                      {edaNumericFeatures.map((feature) => (
                        <option
                          key={feature}
                          value={feature}
                        >
                          {feature}
                        </option>
                      ))}

                    </select>

                  </label>


                  <label className="eda-control">

                    <span>Category Feature</span>

                    <select
                      value={edaCategoryFeature}
                      onChange={(event) =>
                        setEdaCategoryFeature(event.target.value)
                      }
                    >

                      <option value="category">category</option>
                      <option value="source">source</option>
                      <option value="source_type">source_type</option>
                      <option value="type">type</option>

                    </select>

                  </label>


                  <label className="eda-control">

                    <span>Distribution View</span>

                    <select
                      value={edaChartMode}
                      onChange={(event) =>
                        setEdaChartMode(event.target.value)
                      }
                    >

                      <option value="histogram">Histogram</option>
                      <option value="boxplot">Boxplot</option>

                    </select>

                  </label>

                </div>

              </div>


              {/* ==================================================
                  UNIVARIATE STATISTICS
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>
                    <h3>
                      Univariate Statistical Analysis
                    </h3>

                    <p>
                      Mean, median, mode, variance,
                      standard deviation, quartiles and IQR.
                    </p>
                  </div>

                  <Table2 size={20} />

                </div>


                <div className="fused-table-wrapper">

                  <table className="fused-table">

                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>Count</th>
                        <th>Mean</th>
                        <th>Median</th>
                        <th>Mode</th>
                        <th>Std. Dev.</th>
                        <th>Variance</th>
                        <th>Min</th>
                        <th>Q1</th>
                        <th>Q2</th>
                        <th>Q3</th>
                        <th>Max</th>
                        <th>IQR</th>
                        <th>Outliers</th>
                      </tr>
                    </thead>

                    <tbody>

                      {edaFeatureStats.map((item) => (

                        <tr key={item.key}>

                          <td>
                            <strong>{item.key}</strong>
                          </td>

                          <td>{item.count}</td>

                          <td>{item.mean.toFixed(2)}</td>
                          <td>{item.median.toFixed(2)}</td>
                          <td>{item.mode.toFixed(2)}</td>
                          <td>{item.standardDeviation.toFixed(2)}</td>
                          <td>{item.variance.toFixed(2)}</td>
                          <td>{item.min.toFixed(2)}</td>
                          <td>{item.q1.toFixed(2)}</td>
                          <td>{item.q2.toFixed(2)}</td>
                          <td>{item.q3.toFixed(2)}</td>
                          <td>{item.max.toFixed(2)}</td>
                          <td>{item.iqr.toFixed(2)}</td>
                          <td>
                            <span
                              className={
                                item.outlierCount > 0
                                  ? "anomaly-badge danger"
                                  : "anomaly-badge normal"
                              }
                            >
                              {item.outlierCount}
                            </span>
                          </td>

                        </tr>

                      ))}

                    </tbody>

                  </table>

                </div>

              </div>


              {/* ==================================================
                  DISTRIBUTION + CATEGORY
              ================================================== */}

              <div className="analytics-main-grid analytics-user-inner-grid">

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        {edaChartMode === "histogram"
                          ? "Histogram"
                          : "Boxplot"}
                      </h3>

                      <p>
                        Distribution of {edaFeature}.
                      </p>

                    </div>

                    <BarChart3 size={20} />

                  </div>


                  {edaChartMode === "histogram" ? (

                    <div className="eda-histogram">

                      {edaHistogram.length === 0 ? (

                        <div className="analytics-empty">
                          No numeric values available.
                        </div>

                      ) : (

                        edaHistogram.map((bin, index) => {

                          const maxCount = Math.max(
                            ...edaHistogram.map((item) => item.count),
                            1
                          );

                          const height = Math.max(
                            (bin.count / maxCount) * 190,
                            8
                          );

                          return (
                            <div
                              className="eda-histogram-column"
                              key={`${bin.label}-${index}`}
                            >

                              <div
                                className="eda-histogram-bar"
                                style={{
                                  height: `${height}px`,
                                }}
                                title={`${bin.count} records`}
                              />

                              <span>
                                {bin.label}
                              </span>

                              <small>
                                {bin.count}
                              </small>

                            </div>
                          );

                        })

                      )}

                    </div>

                  ) : (

                    <div className="eda-boxplot">

                      <div className="eda-boxplot-axis">

                        <span>
                          {edaSelectedStats.min.toFixed(1)}
                        </span>

                        <span>
                          {edaSelectedStats.q1.toFixed(1)}
                        </span>

                        <span>
                          {edaSelectedStats.median.toFixed(1)}
                        </span>

                        <span>
                          {edaSelectedStats.q3.toFixed(1)}
                        </span>

                        <span>
                          {edaSelectedStats.max.toFixed(1)}
                        </span>

                      </div>


                      <div className="eda-boxplot-track">

                        <div
                          className="eda-boxplot-whisker"
                          style={{
                            left: "5%",
                            width: "90%",
                          }}
                        />

                        <div
                          className="eda-boxplot-box"
                          style={{
                            left: "25%",
                            width: "50%",
                          }}
                        >

                          <span className="eda-boxplot-median" />

                        </div>

                      </div>


                      <div className="eda-boxplot-legend">

                        <span>
                          Min: {edaSelectedStats.min.toFixed(2)}
                        </span>

                        <span>
                          Q1: {edaSelectedStats.q1.toFixed(2)}
                        </span>

                        <span>
                          Median: {edaSelectedStats.median.toFixed(2)}
                        </span>

                        <span>
                          Q3: {edaSelectedStats.q3.toFixed(2)}
                        </span>

                        <span>
                          Max: {edaSelectedStats.max.toFixed(2)}
                        </span>

                      </div>

                    </div>

                  )}

                </div>


                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Category-wise Analysis
                      </h3>

                      <p>
                        Total expense by selected category
                        dimension.
                      </p>

                    </div>

                    <GitBranch size={20} />

                  </div>


                  {edaCategoryData.length === 0 ? (

                    <div className="analytics-empty">
                      No category data available.
                    </div>

                  ) : (

                    <div className="category-chart">

                      {edaCategoryData.map((item, index) => {

                        const total = edaCategoryData.reduce(
                          (sum, value) => sum + value.amount,
                          0
                        );

                        const percentage =
                          total > 0
                            ? (item.amount / total) * 100
                            : 0;

                        return (
                          <div
                            className="category-row"
                            key={`${item.label}-${index}`}
                          >

                            <div className="category-row-top">

                              <span>
                                {item.label}
                              </span>

                              <strong>
                                {formatCurrency(
                                  item.amount,
                                  currency
                                )}
                              </strong>

                            </div>

                            <div className="category-progress">

                              <div
                                style={{
                                  width:
                                    `${Math.min(
                                      percentage,
                                      100
                                    )}%`,
                                }}
                              />

                            </div>

                            <small>
                              {percentage.toFixed(1)}%
                            </small>

                          </div>
                        );

                      })}

                    </div>

                  )}

                </div>

              </div>


              {/* ==================================================
                  BIVARIATE
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <h3>
                      Bivariate Analysis
                    </h3>

                    <p>
                      Pearson correlation between
                      {` ${edaFeature}`} and
                      {` ${edaSecondFeature}`}.
                    </p>

                  </div>

                  <Activity size={20} />

                </div>


                <div className="eda-correlation-highlight">

                  <div>

                    <span>
                      Pearson Correlation
                    </span>

                    <strong>
                      {edaBivariate.correlation.toFixed(4)}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Relationship Strength
                    </span>

                    <strong>
                      {correlationLabel(
                        edaBivariate.correlation
                      )}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Direction
                    </span>

                    <strong>
                      {edaBivariate.correlation > 0.05
                        ? "Positive"
                        : edaBivariate.correlation < -0.05
                        ? "Negative"
                        : "Approximately none"}
                    </strong>

                  </div>

                </div>


                {edaBivariate.points.length === 0 ? (

                  <div className="analytics-empty">
                    Not enough numeric pairs for a scatter analysis.
                  </div>

                ) : (

                  <div className="eda-scatter">

                    {edaBivariate.points.map((point, index) => {

                      const xs = edaBivariate.points.map(
                        (item) => item.x
                      );

                      const ys = edaBivariate.points.map(
                        (item) => item.y
                      );

                      const minX = Math.min(...xs);
                      const maxX = Math.max(...xs);
                      const minY = Math.min(...ys);
                      const maxY = Math.max(...ys);

                      const left =
                        maxX === minX
                          ? 50
                          : ((point.x - minX) /
                              (maxX - minX)) *
                              88 +
                            6;

                      const bottom =
                        maxY === minY
                          ? 50
                          : ((point.y - minY) /
                              (maxY - minY)) *
                              82 +
                            8;

                      return (
                        <span
                          className="eda-scatter-point"
                          key={`${index}-${point.x}-${point.y}`}
                          title={`x: ${point.x.toFixed(2)}, y: ${point.y.toFixed(2)}`}
                          style={{
                            left: `${left}%`,
                            bottom: `${bottom}%`,
                          }}
                        />
                      );

                    })}

                    <div className="eda-scatter-axis-label x">
                      {edaFeature}
                    </div>

                    <div className="eda-scatter-axis-label y">
                      {edaSecondFeature}
                    </div>

                  </div>

                )}

              </div>


              {/* ==================================================
                  MULTIVARIATE CORRELATION MATRIX
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <h3>
                      Multivariate Correlation Matrix
                    </h3>

                    <p>
                      Pearson correlation across numeric
                      variables in the fused dataset.
                    </p>

                  </div>

                  <Table2 size={20} />

                </div>


                {edaCorrelationFeatures.length < 2 ? (

                  <div className="analytics-empty">
                    At least two numeric variables are required.
                  </div>

                ) : (

                  <div className="eda-correlation-wrapper">

                    <table className="eda-correlation-table">

                      <thead>

                        <tr>

                          <th />

                          {edaCorrelationFeatures.map(
                            (feature) => (
                              <th key={feature}>
                                {feature}
                              </th>
                            )
                          )}

                        </tr>

                      </thead>

                      <tbody>

                        {edaCorrelationMatrix.map((row) => (

                          <tr key={row.key}>

                            <th>
                              {row.key}
                            </th>

                            {row.values.map((value, index) => (

                              <td
                                key={`${row.key}-${index}`}
                                className={
                                  edaCorrelationColorClass(value)
                                }
                                title={
                                  `${row.key} vs ` +
                                  `${edaCorrelationFeatures[index]}: ` +
                                  `${value.toFixed(4)}`
                                }
                              >
                                {value.toFixed(2)}
                              </td>

                            ))}

                          </tr>

                        ))}

                      </tbody>

                    </table>

                  </div>

                )}

              </div>


              {/* ==================================================
                  OUTLIERS + DATA QUALITY
              ================================================== */}

              <div className="analytics-main-grid analytics-user-inner-grid">

                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Outlier Detection
                      </h3>

                      <p>
                        IQR rule: values below Q1 - 1.5×IQR
                        or above Q3 + 1.5×IQR.
                      </p>

                    </div>

                    <AlertTriangle size={20} />

                  </div>


                  <div className="combined-source-summary">

                    <div>
                      <span>Q1</span>
                      <strong>
                        {edaSelectedStats.q1.toFixed(2)}
                      </strong>
                      <small>25th percentile</small>
                    </div>

                    <div>
                      <span>Median</span>
                      <strong>
                        {edaSelectedStats.median.toFixed(2)}
                      </strong>
                      <small>Q2</small>
                    </div>

                    <div>
                      <span>Q3</span>
                      <strong>
                        {edaSelectedStats.q3.toFixed(2)}
                      </strong>
                      <small>75th percentile</small>
                    </div>

                    <div>
                      <span>IQR</span>
                      <strong>
                        {edaSelectedStats.iqr.toFixed(2)}
                      </strong>
                      <small>Q3 - Q1</small>
                    </div>

                    <div>
                      <span>Outliers</span>
                      <strong>
                        {edaSelectedStats.outlierCount}
                      </strong>
                      <small>
                        {edaFeature}
                      </small>
                    </div>

                  </div>


                  {edaOutlierRows.length === 0 ? (

                    <div className="analytics-empty">
                      No IQR outliers detected for {edaFeature}.
                    </div>

                  ) : (

                    <div className="fused-table-wrapper">

                      <table className="fused-table">

                        <thead>

                          <tr>
                            <th>Date</th>
                            <th>Source</th>
                            <th>Category</th>
                            <th>Description</th>
                            <th>{edaFeature}</th>
                          </tr>

                        </thead>

                        <tbody>

                          {edaOutlierRows.map((row, index) => (

                            <tr
                              key={`${row?.id || index}-outlier`}
                            >

                              <td>
                                {formatDate(row?.date)}
                              </td>

                              <td>
                                {row?.source || "-"}
                              </td>

                              <td>
                                {row?.category || "-"}
                              </td>

                              <td className="description-cell">
                                {row?.description || "-"}
                              </td>

                              <td className="amount-cell">

                                {formatCurrency(
                                  row?.[edaFeature],
                                  currency
                                )}

                              </td>

                            </tr>

                          ))}

                        </tbody>

                      </table>

                    </div>

                  )}

                </div>


                <div className="analytics-card">

                  <div className="analytics-card-header">

                    <div>

                      <h3>
                        Data Quality Check
                      </h3>

                      <p>
                        Basic completeness and duplicate-like
                        record checks.
                      </p>

                    </div>

                    <Database size={20} />

                  </div>


                  <div className="combined-source-summary">

                    <div>
                      <span>Total Rows</span>
                      <strong>
                        {edaDataQuality.rows}
                      </strong>
                      <small>Analysed</small>
                    </div>

                    <div>
                      <span>Missing Dates</span>
                      <strong>
                        {edaDataQuality.missingDate}
                      </strong>
                      <small>Rows</small>
                    </div>

                    <div>
                      <span>Missing Category</span>
                      <strong>
                        {edaDataQuality.missingCategory}
                      </strong>
                      <small>Rows</small>
                    </div>

                    <div>
                      <span>Missing Amount</span>
                      <strong>
                        {edaDataQuality.missingAmount}
                      </strong>
                      <small>Rows</small>
                    </div>

                    <div>
                      <span>Duplicate-like</span>
                      <strong>
                        {edaDataQuality.duplicateLikeRows}
                      </strong>
                      <small>Rows</small>
                    </div>

                  </div>


                  <div className="analytics-empty">

                    <strong>
                      EDA interpretation:
                    </strong>
                    {" "}
                    A high standard deviation means the selected
                    feature varies widely. The IQR identifies
                    extreme observations, while Pearson correlation
                    indicates the direction and strength of a linear
                    relationship between two numeric variables.

                  </div>

                </div>

              </div>


              {/* ==================================================
                  EDA RECORD PREVIEW
              ================================================== */}

              <div className="analytics-card">

                <div className="analytics-card-header">

                  <div>

                    <h3>
                      EDA Dataset Preview
                    </h3>

                    <p>
                      First 100 fused records available to the
                      exploratory analysis.
                    </p>

                  </div>

                  <Table2 size={20} />

                </div>


                {edaRows.length === 0 ? (

                  <div className="analytics-empty">
                    No fused data is available for EDA.
                  </div>

                ) : (

                  <div className="fused-table-wrapper">

                    <table className="fused-table">

                      <thead>

                        <tr>
                          <th>Date</th>
                          <th>Source</th>
                          <th>Category</th>
                          <th>Description</th>
                          <th>Amount</th>
                          <th>Price</th>
                          <th>Discount</th>
                          <th>Temperature</th>
                          <th>Demand</th>
                        </tr>

                      </thead>

                      <tbody>

                        {edaRows
                          .slice(0, 100)
                          .map((row, index) => (

                            <tr
                              key={`${row?.id || index}-eda`}
                            >

                              <td>
                                {formatDate(row?.date)}
                              </td>

                              <td>
                                {row?.source || "-"}
                              </td>

                              <td>
                                {row?.category || "-"}
                              </td>

                              <td className="description-cell">
                                {row?.description || "-"}
                              </td>

                              <td className="amount-cell">
                                {formatCurrency(
                                  row?.amount,
                                  currency
                                )}
                              </td>

                              <td>
                                {isNumericValue(row?.price)
                                  ? row.price.toFixed(2)
                                  : "-"}
                              </td>

                              <td>
                                {isNumericValue(row?.discount)
                                  ? row.discount.toFixed(2)
                                  : "-"}
                              </td>

                              <td>
                                {isNumericValue(row?.temperature)
                                  ? row.temperature.toFixed(2)
                                  : "-"}
                              </td>

                              <td>
                                {isNumericValue(row?.demand_index)
                                  ? row.demand_index.toFixed(2)
                                  : "-"}
                              </td>

                            </tr>

                          ))}

                      </tbody>

                    </table>

                  </div>

                )}

              </div>

            </div>

          )}


          {/* ==================================================
              FUSED
          ================================================== */}

          {activeTab ===
            "fused" && (

            <div className="analytics-card">

              <div className="analytics-card-header">

                <div>

                  <h3>
                    All Fused Financial Data
                  </h3>

                  <p>
                    Every record from your data, the historical
                    dataset and external API data. Download the
                    multi-column fusion dataset for ML analysis.
                  </p>

                </div>


                <button
                  className="download-button"
                  onClick={() =>
                    downloadCSV(
                      priceFusionCSV,
                      "fused-price-prediction-dataset.csv"
                    )
                  }
                >

                  <Download
                    size={14}
                  />

                  Download CSV

                </button>

              </div>


              <div className="fused-actions">

                <div>

                  Total Records:
                  {" "}
                  <strong>
                    {
                      fusedData.length
                    }
                  </strong>

                </div>


                <div className="fused-download-buttons">

                  <button
                    onClick={() =>
                      setSourceFilter(
                        "all"
                      )
                    }
                  >
                    All
                  </button>

                  <button
                    onClick={() =>
                      setSourceFilter(
                        "user"
                      )
                    }
                  >
                    My Data
                  </button>

                  <button
                    onClick={() =>
                      setSourceFilter(
                        "historical"
                      )
                    }
                  >
                    Historical
                  </button>

                  <button
                    className={
                      sourceFilter ===
                      "api"
                        ? "active"
                        : ""
                    }
                    onClick={() =>
                      setSourceFilter(
                        "api"
                      )
                    }
                  >
                    API Data
                  </button>

                </div>

              </div>


              <div className="table-controls">

                <input
                  className="analytics-table-search"
                  type="text"
                  placeholder="Search fused data..."
                  value={
                    search
                  }
                  onChange={
                    (event) =>
                      setSearch(
                        event.target.value
                      )
                  }
                />

              </div>


              <div className="fused-table-wrapper">

                {filteredFusedData.length ===
                  0 ? (

                  <div className="analytics-empty">

                    No fused data available.

                  </div>

                ) : (

                  <table className="fused-table">

                    <thead>

                      <tr>

                        <th>
                          Date
                        </th>

                        <th>
                          Source
                        </th>

                        <th>
                          Type
                        </th>

                        <th>
                          Category
                        </th>

                        <th>
                          Description
                        </th>

                        <th>
                          Amount
                        </th>

                        <th>
                          Status
                        </th>

                      </tr>

                    </thead>


                    <tbody>

                      {filteredFusedData.map(
                        (
                          row,
                          index
                        ) => {

                          const isUser =
                            String(
                              row.source_type || ""
                            ).toLowerCase() ===
                            "user";

                          const isAPI =
                            String(
                              row.source_type || ""
                            ).toLowerCase() ===
                            "api";

                          const isAnomaly =
                            String(
                              row.anomaly ||
                              row.anomaly_status ||
                              ""
                            )
                              .toLowerCase()
                              .includes(
                                "anomaly"
                              );

                          return (

                            <tr
                              key={
                                index
                              }
                            >

                              <td>
                                {formatDate(
                                  row.date
                                )}
                              </td>


                              <td>

                                <span
                                  className={
                                    isUser
                                      ? "source-badge user-source"
                                      : isAPI
                                      ? "source-badge api-source"
                                      : "source-badge historical-source"
                                  }
                                >

                                  {isUser
                                    ? "Your Data"
                                    : isAPI
                                    ? row.source || "API Data"
                                    : "Historical"}

                                </span>

                              </td>


                              <td>
                                {
                                  row.type
                                }
                              </td>


                              <td>
                                {
                                  row.category
                                }
                              </td>


                              <td className="description-cell">
                                {
                                  row.description
                                }
                              </td>


                              <td className="amount-cell">

                                {formatCurrency(
                                  row.amount,
                                  currency
                                )}

                              </td>


                              <td>

                                <span
                                  className={
                                    isAnomaly
                                      ? "anomaly-badge danger"
                                      : "anomaly-badge normal"
                                  }
                                >

                                  {isAnomaly
                                    ? "Anomaly"
                                    : "Normal"}

                                </span>

                              </td>

                            </tr>

                          );

                        }
                      )}

                    </tbody>

                  </table>

                )}

              </div>

            </div>

          )}


          {/* ==================================================
              AI ASSISTANT FULL PAGE
          ================================================== */}

          {activeTab ===
            "assistant" && (

            <div className="analytics-assistant-page">

              <Chatbot
                messages={
                  chatMessages
                }

                input={
                  chatInput
                }

                setInput={
                  setChatInput
                }

                loading={
                  chatLoading
                }

                onSend={
                  sendChatMessage
                }

                savedChats={
                  savedChats
                }

                conversationId={
                  conversationId
                }

                showHistory={
                  showChatHistory
                }

                setShowHistory={
                  setShowChatHistory
                }

                newChat={
                  createNewChat
                }

                openChat={
                  openChat
                }

                deleteChat={
                  deleteChat
                }

                quickQuestion={
                  askQuickQuestion
                }

                messagesRef={
                  chatMessagesRef
                }

                fullPage

              />

            </div>

          )}

        </div>

      </main>

    </div>

  );
}


// ============================================================
// CHATBOT
// ============================================================

function Chatbot({
  messages,
  input,
  setInput,
  loading,
  onSend,
  savedChats,
  conversationId,
  showHistory,
  setShowHistory,
  newChat,
  openChat,
  deleteChat,
  quickQuestion,
  messagesRef,
  fullPage = false,
}) {

  return (

    <aside
      className={
        fullPage
          ? "analytics-ai-card full"
          : "analytics-ai-card"
      }
    >


      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="analytics-ai-header">

        <div className="analytics-ai-title">

          <div className="analytics-ai-icon">

            <Bot
              size={18}
            />

          </div>

          <div>

            <h3>
              AI Financial Assistant
            </h3>

            <span>
              PERSONALIZED
            </span>

          </div>

        </div>


        <div className="analytics-ai-actions">

          <button
            title="New chat"
            onClick={
              newChat
            }
          >

            <Plus
              size={15}
            />

          </button>


          <button
            title="Chat history"
            onClick={() =>
              setShowHistory(
                (value) =>
                  !value
              )
            }
          >

            <History
              size={15}
            />

          </button>

        </div>

      </div>


      {/* ======================================================
          DESCRIPTION
      ====================================================== */}

      <div className="analytics-ai-description">

        Ask me about your expenses,
        spending patterns, categories,
        unusual transactions or future
        product prices. Price prediction
        runs only when you ask for it.

      </div>


      {/* ======================================================
          HISTORY
      ====================================================== */}

      {showHistory && (

        <div className="analytics-chat-history">

          <div className="analytics-chat-history-header">

            <div>

              <strong>
                Chat History
              </strong>

              <span>
                Previous conversations
              </span>

            </div>


            <button
              onClick={() =>
                setShowHistory(
                  false
                )
              }
            >

              ×

            </button>

          </div>


          <div className="analytics-chat-history-list">

            {savedChats.length ===
              0 ? (

              <div className="analytics-chat-empty">

                No previous conversations.

              </div>

            ) : (

              savedChats.map(
                (
                  chat,
                  index
                ) => {

                  const id =
                    chat?.conversation_id ||
                    chat?.id ||
                    chat?._id;

                  return (

                    <div
                      className={
                        conversationId ===
                        id
                          ? "analytics-chat-history-row selected"
                          : "analytics-chat-history-row"
                      }
                      key={
                        id ||
                        index
                      }
                    >

                      <button
                        onClick={() =>
                          openChat(
                            id
                          )
                        }
                      >

                        <MessageSquare
                          size={12}
                        />

                        <span>
                          {
                            chat?.title ||
                            "Conversation"
                          }
                        </span>

                      </button>


                      <button
                        className="analytics-chat-delete"
                        onClick={() =>
                          deleteChat(
                            id
                          )
                        }
                      >

                        <Trash2
                          size={12}
                        />

                      </button>

                    </div>

                  );

                }
              )

            )}

          </div>

        </div>

      )}


      {/* ======================================================
          MESSAGES
          ONLY THIS SECTION SCROLLS
      ====================================================== */}

      <div
        className="analytics-ai-messages"
        ref={
          messagesRef
        }
      >

        {messages.map(
          (
            message,
            index
          ) => {

            const isUser =
              message.role ===
              "user";

            return (

              <div
                key={
                  index
                }
                className={
                  isUser
                    ? "analytics-chat-message user"
                    : "analytics-chat-message assistant"
                }
              >

                {!isUser && (

                  <div className="analytics-message-avatar bot">

                    <Bot
                      size={13}
                    />

                  </div>

                )}


                <div className="analytics-message-bubble">

                  {
                    message.content
                  }

                </div>


                {isUser && (

                  <div className="analytics-message-avatar user">

                    <User
                      size={13}
                    />

                  </div>

                )}

              </div>

            );

          }
        )}


        {loading && (

          <div className="analytics-chat-message assistant">

            <div className="analytics-message-avatar bot">

              <Bot
                size={13}
              />

            </div>


            <div className="analytics-message-bubble typing">

              <span />
              <span />
              <span />

            </div>

          </div>

        )}

      </div>


      {/* ======================================================
          QUICK QUESTIONS
      ====================================================== */}

      <div className="analytics-quick-questions">

        {QUICK_QUESTIONS.map(
          (
            question,
            index
          ) => (

            <button
              key={
                index
              }
              onClick={() =>
                quickQuestion(
                  question
                )
              }
            >

              {question}

            </button>

          )
        )}

      </div>


      {/* ======================================================
          INPUT
      ====================================================== */}

      <div className="analytics-ai-input">

        <input
          type="text"
          value={
            input
          }
          onChange={
            (event) =>
              setInput(
                event.target.value
              )
          }
          onKeyDown={
            (event) => {

              if (
                event.key ===
                "Enter"
              ) {

                event.preventDefault();

                onSend();

              }

            }
          }
          placeholder="Ask about your finances or future prices..."
          disabled={
            loading
          }
        />


        <button
          onClick={
            onSend
          }
          disabled={
            loading ||
            !input.trim()
          }
        >

          <Send
            size={14}
          />

        </button>

      </div>

    </aside>

  );
}


export default DataAnalytics;