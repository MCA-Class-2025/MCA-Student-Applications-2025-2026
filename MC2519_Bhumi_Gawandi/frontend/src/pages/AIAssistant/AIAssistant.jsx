import React, {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Send,
  Plus,
  Trash2,
  MessageSquare,
  Newspaper,
  ArrowRightLeft,
  Bot,
  Sparkles,
  Search,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

import {
  sendAIMessage,
  getFinancialNews,
  convertCurrency,
  getExchangeRate,
} from "../../services/aiService";

import "./AIAssistant.css";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";


// ============================================================
// QUICK QUESTIONS
// ============================================================

const quickQuestions = [
  {
    icon: "📊",
    title: "Monthly Summary",
    question:
      "Give me a summary of my spending this month.",
  },
  {
    icon: "💰",
    title: "Budget Status",
    question:
      "Am I within my budgets? Show me which budgets are close to being exceeded.",
  },
  {
    icon: "🔥",
    title: "Top Spending",
    question:
      "Which categories and expenses are taking most of my money?",
  },
  {
    icon: "💡",
    title: "Saving Tips",
    question:
      "Analyze my spending and give me practical ways to save money.",
  },
];


// ============================================================
// AI ASSISTANT
// ============================================================

const AIAssistant = () => {

  // ==========================================================
  // CONSTANTS
  // ==========================================================

  const HISTORY_KEY =
    "spendsmart_ai_chat_history";


  // ==========================================================
  // STATES
  // ==========================================================

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "ai",
      text:
        "Hi! I'm SpendSmart AI 🤖. I can help with expenses, budgets, saving, travel plans, shopping plans and everyday financial questions. What would you like to know?",
      time: getCurrentTime(),
    },
  ]);


  const [input, setInput] = useState("");


  const [loading, setLoading] =
    useState(false);


  const [chatHistory, setChatHistory] =
    useState(() => {

      try {

        const saved =
          localStorage.getItem(
            HISTORY_KEY
          );

        return saved
          ? JSON.parse(saved)
          : [];

      } catch (error) {

        console.error(
          "Unable to load chat history:",
          error
        );

        return [];

      }

    });


  const [
    activeConversationId,
    setActiveConversationId,
  ] = useState(
    () =>
      localStorage.getItem(
        "spendsmart_ai_active_chat_id"
      ) || null
  );


  const [activeTool, setActiveTool] =
    useState("chat");


  // ==========================================================
  // NEWS
  // ==========================================================

  const [news, setNews] =
    useState([]);


  const [newsLoading, setNewsLoading] =
    useState(false);


  const [newsQuery, setNewsQuery] =
    useState(
      "personal finance India"
    );


  // ==========================================================
  // CURRENCY
  // ==========================================================

  const [baseCurrency, setBaseCurrency] =
    useState("USD");


  const [targetCurrency, setTargetCurrency] =
    useState("INR");


  const [currencyAmount, setCurrencyAmount] =
    useState(1);


  const [convertedAmount, setConvertedAmount] =
    useState(null);


  const [exchangeRate, setExchangeRate] =
    useState(null);


  const [currencyLoading, setCurrencyLoading] =
    useState(false);


  // ==========================================================
  // REF
  // ==========================================================

  const messagesEndRef =
    useRef(null);


  // ==========================================================
  // CURRENT TIME
  // ==========================================================

  function getCurrentTime() {

    return new Date().toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );

  }


  // ==========================================================
  // AUTO SCROLL
  // ==========================================================

  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [
    messages,
    loading,
  ]);


  // ==========================================================
  // SAVE CHAT HISTORY
  // ==========================================================

  const saveChatHistory = (
    updatedMessages,
    conversationId
  ) => {

    const firstUserMessage =
      updatedMessages.find(
        (message) =>
          message.sender === "user"
      );


    const title =
      firstUserMessage?.text
        ? firstUserMessage.text
            .trim()
            .slice(0, 38)
        : "New conversation";


    const conversation = {

      id: conversationId,

      title,

      messages:
        updatedMessages,

      updatedAt:
        new Date().toISOString(),

    };


    setChatHistory((previous) => {

      const filtered =
        previous.filter(
          (item) =>
            String(item.id) !==
            String(conversationId)
        );


      const updated = [
        conversation,
        ...filtered,
      ];


      localStorage.setItem(
        HISTORY_KEY,
        JSON.stringify(updated)
      );


      return updated;

    });

  };


  // ==========================================================
  // OPEN HISTORY
  // ==========================================================

  const handleOpenHistory = (
    conversation
  ) => {

    setMessages(
      Array.isArray(
        conversation.messages
      )
        ? conversation.messages
        : []
    );


    setActiveConversationId(
      String(conversation.id)
    );


    localStorage.setItem(
      "spendsmart_ai_active_chat_id",
      String(conversation.id)
    );


    setActiveTool("chat");

  };


  // ==========================================================
  // DELETE HISTORY
  // ==========================================================

  const handleDeleteHistory = (
    event,
    id
  ) => {

    event.stopPropagation();


    const updated =
      chatHistory.filter(
        (item) =>
          String(item.id) !==
          String(id)
      );


    setChatHistory(updated);


    localStorage.setItem(
      HISTORY_KEY,
      JSON.stringify(updated)
    );


    if (
      String(
        activeConversationId
      ) === String(id)
    ) {

      handleNewChat();

    }

  };


  // ==========================================================
  // NEW CHAT
  // ==========================================================

  const handleNewChat = () => {

    /*
     * This ID is only used locally for the UI/history.
     * It is NOT sent to FastAPI as conversation_id.
     */

    const localId =
      `local-${Date.now()}`;


    const newMessages = [

      {
        id:
          Date.now(),

        sender:
          "ai",

        text:
          "Hi! I'm SpendSmart AI 🤖. I can help with expenses, budgets, saving, travel plans, shopping plans and everyday financial questions. What would you like to know?",

        time:
          getCurrentTime(),

      },

    ];


    setMessages(
      newMessages
    );


    setInput("");


    setActiveConversationId(
      localId
    );


    setActiveTool(
      "chat"
    );


    localStorage.setItem(
      "spendsmart_ai_active_chat_id",
      localId
    );


    saveChatHistory(
      newMessages,
      localId
    );

  };


  // ==========================================================
  // CLEAR CHAT
  // ==========================================================

  const handleClearChat = () => {

    const localId =
      `local-${Date.now()}`;


    const newMessages = [

      {
        id:
          Date.now(),

        sender:
          "ai",

        text:
          "Chat cleared. How can I help you?",

        time:
          getCurrentTime(),

      },

    ];


    setMessages(
      newMessages
    );


    setInput("");


    setActiveConversationId(
      localId
    );


    localStorage.setItem(
      "spendsmart_ai_active_chat_id",
      localId
    );


    saveChatHistory(
      newMessages,
      localId
    );

  };


  // ==========================================================
  // SEND MESSAGE
  // ==========================================================

  const handleSendMessage = async (
    customMessage = null
  ) => {

    const message =
      customMessage ||
      input.trim();


    if (
      !message ||
      loading
    ) {

      return;

    }


    // ========================================================
    // IMPORTANT
    //
    // If activeConversationId is a local ID,
    // do NOT send it to MongoDB/FastAPI.
    //
    // Backend must create the real conversation ID.
    // ========================================================

    const isLocalConversation =
      !activeConversationId ||
      String(
        activeConversationId
      ).startsWith("local-");


    const backendConversationId =
      isLocalConversation
        ? null
        : activeConversationId;


    console.log(
      "AI MESSAGE:",
      message
    );


    console.log(
      "BACKEND CONVERSATION ID:",
      backendConversationId
    );


    // ========================================================
    // USER MESSAGE
    // ========================================================

    const userMessage = {

      id:
        Date.now(),

      sender:
        "user",

      text:
        message,

      time:
        getCurrentTime(),

    };


    // ========================================================
    // LOCAL HISTORY ID
    // ========================================================

    const localHistoryId =
      activeConversationId ||
      `local-${Date.now()}`;


    if (!activeConversationId) {

      setActiveConversationId(
        localHistoryId
      );


      localStorage.setItem(
        "spendsmart_ai_active_chat_id",
        localHistoryId
      );

    }


    // ========================================================
    // ADD USER MESSAGE
    // ========================================================

    setMessages((previous) => {

      const updatedMessages = [

        ...previous,

        userMessage,

      ];


      saveChatHistory(

        updatedMessages,

        localHistoryId

      );


      return updatedMessages;

    });


    setInput("");


    setLoading(true);


    // ========================================================
    // CALL BACKEND
    // ========================================================

    try {

      console.log(
        "Sending request to:",
        "http://127.0.0.1:8000/api/ai/chat"
      );


      const response =
        await sendAIMessage(

          message,

          backendConversationId

        );


      console.log(
        "AI BACKEND RESPONSE:",
        response
      );


      // ======================================================
      // GET REAL CONVERSATION ID
      // ======================================================

      const realConversationId =
        response?.conversation_id ||
        response?.conversationId ||
        response?.conversation?.id ||
        backendConversationId;


      console.log(
        "REAL CONVERSATION ID:",
        realConversationId
      );


      // ======================================================
      // SAVE REAL CONVERSATION ID
      // ======================================================

      if (
        realConversationId
      ) {

        setActiveConversationId(
          String(
            realConversationId
          )
        );


        localStorage.setItem(
          "spendsmart_ai_active_chat_id",
          String(
            realConversationId
          )
        );

      }


      // ======================================================
      // GET AI RESPONSE
      // ======================================================

      const aiResponseText =
        response?.message ||
        response?.response ||
        response?.answer ||
        response?.content ||
        response?.text ||
        "I couldn't generate a response.";


      // ======================================================
      // AI MESSAGE
      // ======================================================

      const aiMessage = {

        id:
          Date.now() + 1,

        sender:
          "ai",

        text:
          String(
            aiResponseText
          ),

        time:
          getCurrentTime(),

      };


      // ======================================================
      // ADD AI MESSAGE
      // ======================================================

      setMessages((previous) => {

        const updatedMessages = [

          ...previous,

          aiMessage,

        ];


        saveChatHistory(

          updatedMessages,

          realConversationId ||
            localHistoryId

        );


        return updatedMessages;

      });


    } catch (error) {

      // ======================================================
      // REAL BACKEND ERROR
      // ======================================================

      console.error(
        "========================================"
      );


      console.error(
        "AI ASSISTANT ERROR"
      );


      console.error(
        "ERROR:",
        error
      );


      console.error(
        "MESSAGE:",
        error?.message
      );


      console.error(
        "RESPONSE:",
        error?.response?.data
      );


      console.error(
        "STATUS:",
        error?.response?.status
      );


      console.error(
        "========================================"
      );


      // ======================================================
      // EXTRACT REAL ERROR
      // ======================================================

      const backendError =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Unknown AI service error.";


      // ======================================================
      // ERROR MESSAGE
      // ======================================================

      const errorMessage = {

        id:
          Date.now() + 1,

        sender:
          "ai",

        text:
          `AI service error: ${backendError}`,

        time:
          getCurrentTime(),

        error:
          true,

      };


      // ======================================================
      // DISPLAY REAL ERROR IN CHAT
      // ======================================================

      setMessages((previous) => {

        const updatedMessages = [

          ...previous,

          errorMessage,

        ];


        saveChatHistory(

          updatedMessages,

          localHistoryId

        );


        return updatedMessages;

      });


    } finally {

      setLoading(false);

    }

  };


  // ==========================================================
  // ENTER KEY
  // ==========================================================

  const handleKeyDown = (
    event
  ) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      handleSendMessage();

    }

  };


  // ==========================================================
  // LOAD NEWS
  // ==========================================================

  const handleLoadNews = async () => {

    setNewsLoading(true);


    try {

      const response =
        await getFinancialNews(
          newsQuery
        );


      setNews(
        response?.articles ||
        []
      );


    } catch (error) {

      console.error(
        "News loading failed:",
        error
      );


      setNews([]);

    } finally {

      setNewsLoading(false);

    }

  };


  // ==========================================================
  // CURRENCY CONVERSION
  // ==========================================================

  const handleConvertCurrency =
    async () => {

      if (
        !currencyAmount ||
        Number(currencyAmount) <= 0
      ) {

        return;

      }


      setCurrencyLoading(
        true
      );


      try {

        const response =
          await convertCurrency(

            baseCurrency,

            targetCurrency,

            currencyAmount

          );


        setConvertedAmount(

          response?.converted_amount ??
          response?.result ??
          response?.amount ??
          null

        );


        const rateResponse =
          await getExchangeRate(

            baseCurrency,

            targetCurrency

          );


        setExchangeRate(

          rateResponse?.rate ??
          rateResponse?.exchange_rate ??
          null

        );


      } catch (error) {

        console.error(
          "Currency conversion failed:",
          error
        );


        setConvertedAmount(
          null
        );


        setExchangeRate(
          null
        );


      } finally {

        setCurrencyLoading(
          false
        );

      }

    };


  // ==========================================================
  // SWAP CURRENCIES
  // ==========================================================

  const handleSwapCurrency = () => {

    const previousBase =
      baseCurrency;


    setBaseCurrency(
      targetCurrency
    );


    setTargetCurrency(
      previousBase
    );


    setConvertedAmount(
      null
    );


    setExchangeRate(
      null
    );

  };


  // ==========================================================
  // MAIN UI
  // ==========================================================

  return (

    <div className="dashboard-layout">


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="dashboard-sidebar">

        <Sidebar />

      </aside>


      {/* ======================================================
          MAIN AREA
      ====================================================== */}

      <div className="dashboard-main">

        <DashboardNavbar />


        <main className="dashboard-content">

          <div className="ai-page">


            {/* ==================================================
                PAGE HEADER
            ================================================== */}

            <section className="ai-page-header">

              <div>

                <div className="ai-title-row">

                  <div className="ai-title-icon">

                    <Bot size={23} />

                  </div>


                  <div>

                    <h1>
                      AI Assistant
                    </h1>


                    <p>
                      Your personal financial assistant
                    </p>

                  </div>

                </div>

              </div>


              <div className="ai-status">

                <span className="ai-status-dot" />

                AI Online

              </div>

            </section>


            {/* ==================================================
                TOOL NAVIGATION
            ================================================== */}

            <div className="ai-tool-navigation">

              <button
                className={
                  activeTool === "chat"
                    ? "ai-tool active"
                    : "ai-tool"
                }
                onClick={() =>
                  setActiveTool(
                    "chat"
                  )
                }
              >

                <MessageSquare
                  size={17}
                />

                AI Chat

              </button>


              <button
                className={
                  activeTool === "news"
                    ? "ai-tool active"
                    : "ai-tool"
                }
                onClick={() =>
                  setActiveTool(
                    "news"
                  )
                }
              >

                <Newspaper
                  size={17}
                />

                Financial News

              </button>


              <button
                className={
                  activeTool === "currency"
                    ? "ai-tool active"
                    : "ai-tool"
                }
                onClick={() =>
                  setActiveTool(
                    "currency"
                  )
                }
              >

                <ArrowRightLeft
                  size={17}
                />

                Currency

              </button>

            </div>


            {/* ==================================================
                CHAT
            ================================================== */}

            {activeTool === "chat" && (

              <div className="chat-layout">


                {/* =================================================
                    HISTORY
                ================================================= */}

                <aside className="history-card">

                  <div className="history-card-header">

                    <div>

                      <h3>
                        Conversations
                      </h3>

                      <p>
                        Your recent chats
                      </p>

                    </div>


                    <button
                      className="new-chat-button"
                      onClick={
                        handleNewChat
                      }
                      title="New conversation"
                    >

                      <Plus
                        size={17}
                      />

                    </button>

                  </div>


                  <div className="history-list">

                    {chatHistory.length === 0 ? (

                      <div className="history-empty">

                        <MessageSquare
                          size={25}
                        />

                        <p>
                          No previous conversations
                        </p>

                      </div>

                    ) : (

                      chatHistory.map(
                        (conversation) => (

                          <div
                            key={
                              conversation.id
                            }
                            className={
                              String(
                                activeConversationId
                              ) ===
                              String(
                                conversation.id
                              )
                                ? "history-item active"
                                : "history-item"
                            }
                            onClick={() =>
                              handleOpenHistory(
                                conversation
                              )
                            }
                          >

                            <div className="history-item-icon">

                              <MessageSquare
                                size={15}
                              />

                            </div>


                            <div className="history-item-content">

                              <strong>
                                {
                                  conversation.title
                                }
                              </strong>


                              <small>

                                {conversation.updatedAt
                                  ? new Date(
                                      conversation.updatedAt
                                    ).toLocaleDateString()
                                  : ""}

                              </small>

                            </div>


                            <button
                              className="history-delete"
                              onClick={(
                                event
                              ) =>
                                handleDeleteHistory(
                                  event,
                                  conversation.id
                                )
                              }
                              title="Delete conversation"
                            >

                              <Trash2
                                size={14}
                              />

                            </button>

                          </div>

                        )
                      )

                    )}

                  </div>

                </aside>


                {/* =================================================
                    CHAT CARD
                ================================================= */}

                <section className="chat-card">


                  {/* CHAT HEADER */}

                  <div className="chat-card-header">

                    <div className="chat-profile">

                      <div className="chat-ai-avatar">

                        <Bot
                          size={20}
                        />

                      </div>


                      <div>

                        <h3>
                          SpendSmart AI
                        </h3>


                        <span>
                          Personal Finance Assistant
                        </span>

                      </div>

                    </div>


                    <button
                      className="clear-chat-button"
                      onClick={
                        handleClearChat
                      }
                    >

                      Clear Chat

                    </button>

                  </div>


                  {/* MESSAGES */}

                  <div className="messages-container">

                    {messages.map(
                      (message) => (

                        <div
                          key={
                            message.id
                          }
                          className={
                            message.sender ===
                            "user"
                              ? "message-row user-row"
                              : "message-row ai-row"
                          }
                        >

                          {message.sender ===
                            "ai" && (

                            <div className="message-avatar">

                              <Bot
                                size={15}
                              />

                            </div>

                          )}


                          <div
                            className={
                              message.sender ===
                              "user"
                                ? "message-bubble user-bubble"
                                : message.error
                                ? "message-bubble ai-bubble error-bubble"
                                : "message-bubble ai-bubble"
                            }
                          >

                            <div className="message-text">

                              {
                                message.text
                              }

                            </div>


                            <div className="message-time">

                              {
                                message.time
                              }

                            </div>

                          </div>


                          {message.sender ===
                            "user" && (

                            <div className="message-avatar user-avatar">

                              👤

                            </div>

                          )}

                        </div>

                      )
                    )}


                    {/* TYPING */}

                    {loading && (

                      <div className="message-row ai-row">

                        <div className="message-avatar">

                          <Bot
                            size={15}
                          />

                        </div>


                        <div className="message-bubble ai-bubble">

                          <div className="typing-indicator">

                            <span />
                            <span />
                            <span />

                          </div>

                        </div>

                      </div>

                    )}


                    <div
                      ref={
                        messagesEndRef
                      }
                    />

                  </div>


                  {/* QUICK QUESTIONS */}

                  <div className="quick-question-section">

                    <div className="quick-question-heading">

                      <Sparkles
                        size={14}
                      />

                      <span>
                        Quick questions
                      </span>

                    </div>


                    <div className="quick-grid">

                      {quickQuestions.map(
                        (item) => (

                          <button
                            key={
                              item.title
                            }
                            className="quick-question"
                            onClick={() =>
                              handleSendMessage(
                                item.question
                              )
                            }
                          >

                            <span className="quick-question-icon">

                              {item.icon}

                            </span>


                            <span>

                              <strong>
                                {item.title}
                              </strong>


                              <small>
                                Ask AI
                              </small>

                            </span>

                          </button>

                        )
                      )}

                    </div>

                  </div>


                  {/* INPUT */}

                  <div className="chat-input-area">

                    <textarea
                      value={input}
                      onChange={(event) =>
                        setInput(
                          event.target.value
                        )
                      }
                      onKeyDown={
                        handleKeyDown
                      }
                      placeholder="Ask SpendSmart AI about your finances..."
                      rows={1}
                      disabled={loading}
                    />


                    <button
                      className="send-button"
                      onClick={() =>
                        handleSendMessage()
                      }
                      disabled={
                        loading ||
                        !input.trim()
                      }
                      title="Send message"
                    >

                      <Send
                        size={18}
                      />

                    </button>

                  </div>

                </section>

              </div>

            )}


            {/* ==================================================
                FINANCIAL NEWS
            ================================================== */}

            {activeTool === "news" && (

              <section className="tool-page">

                <div className="tool-page-header">

                  <div>

                    <div className="tool-title-icon news-icon">

                      <Newspaper
                        size={20}
                      />

                    </div>


                    <div>

                      <h2>
                        Financial News
                      </h2>


                      <p>
                        Stay updated with the latest financial news
                      </p>

                    </div>

                  </div>

                </div>


                <div className="news-search">

                  <div className="news-search-input">

                    <Search
                      size={17}
                    />


                    <input
                      type="text"
                      value={newsQuery}
                      onChange={(event) =>
                        setNewsQuery(
                          event.target.value
                        )
                      }
                      placeholder="Search financial news..."
                      onKeyDown={(event) => {

                        if (
                          event.key ===
                          "Enter"
                        ) {

                          handleLoadNews();

                        }

                      }}
                    />

                  </div>


                  <button
                    onClick={
                      handleLoadNews
                    }
                    disabled={
                      newsLoading
                    }
                  >

                    {newsLoading ? (

                      <>

                        <RefreshCw
                          size={15}
                          className="button-spin"
                        />

                        Loading...

                      </>

                    ) : (

                      <>

                        <Search
                          size={15}
                        />

                        Search News

                      </>

                    )}

                  </button>

                </div>


                {/* EMPTY */}

                {!newsLoading &&
                  news.length === 0 && (

                    <div className="empty-tool-state">

                      <div className="empty-tool-icon">

                        <Newspaper
                          size={32}
                        />

                      </div>


                      <h3>
                        Financial News
                      </h3>


                      <p>
                        Search for finance,
                        markets, business,
                        investments or
                        personal finance news.
                      </p>


                      <button
                        onClick={
                          handleLoadNews
                        }
                      >

                        Load Latest News

                      </button>

                    </div>

                  )}


                {/* LOADING */}

                {newsLoading && (

                  <div className="news-loading">

                    <div className="loading-spinner" />


                    <p>
                      Loading latest news...
                    </p>

                  </div>

                )}


                {/* NEWS */}

                {!newsLoading &&
                  news.length > 0 && (

                    <div className="news-grid">

                      {news.map(
                        (
                          article,
                          index
                        ) => (

                          <article
                            className="news-card"
                            key={
                              article.url ||
                              index
                            }
                          >

                            <div className="news-card-top">

                              <span className="news-card-icon">

                                <Newspaper
                                  size={16}
                                />

                              </span>


                              <small>

                                {article.source ||
                                  "Financial News"}

                              </small>

                            </div>


                            <h3>

                              {
                                article.title
                              }

                            </h3>


                            <p>

                              {article.description ||
                                "Read the latest financial news."}

                            </p>


                            <div className="news-card-footer">

                              <span>

                                {article.published_at
                                  ? new Date(
                                      article.published_at
                                    ).toLocaleDateString()
                                  : ""}

                              </span>


                              {article.url && (

                                <a
                                  href={
                                    article.url
                                  }
                                  target="_blank"
                                  rel="noreferrer"
                                >

                                  Read More


                                  <ExternalLink
                                    size={12}
                                  />

                                </a>

                              )}

                            </div>

                          </article>

                        )
                      )}

                    </div>

                  )}

              </section>

            )}


            {/* ==================================================
                CURRENCY
            ================================================== */}

            {activeTool ===
              "currency" && (

              <section className="tool-page">

                <div className="tool-page-header">

                  <div>

                    <div className="tool-title-icon currency-icon">

                      <ArrowRightLeft
                        size={20}
                      />

                    </div>


                    <div>

                      <h2>
                        Currency Assistant
                      </h2>


                      <p>
                        Convert currencies and check exchange rates
                      </p>

                    </div>

                  </div>

                </div>


                <div className="currency-layout">


                  {/* CONVERTER */}

                  <div className="currency-card">

                    <div className="currency-card-title">

                      <span>
                        💱
                      </span>


                      <div>

                        <h3>
                          Currency Converter
                        </h3>


                        <p>
                          Get the latest conversion value
                        </p>

                      </div>

                    </div>


                    <div className="currency-field">

                      <label>
                        Amount
                      </label>


                      <input
                        type="number"
                        min="0"
                        value={
                          currencyAmount
                        }
                        onChange={(event) =>
                          setCurrencyAmount(
                            event.target.value
                          )
                        }
                      />

                    </div>


                    <div className="currency-row">


                      <div className="currency-field">

                        <label>
                          From
                        </label>


                        <select
                          value={
                            baseCurrency
                          }
                          onChange={(event) =>
                            setBaseCurrency(
                              event.target.value
                            )
                          }
                        >

                          <option value="USD">
                            USD
                          </option>

                          <option value="INR">
                            INR
                          </option>

                          <option value="EUR">
                            EUR
                          </option>

                          <option value="GBP">
                            GBP
                          </option>

                          <option value="JPY">
                            JPY
                          </option>

                          <option value="AUD">
                            AUD
                          </option>

                          <option value="CAD">
                            CAD
                          </option>

                          <option value="SGD">
                            SGD
                          </option>

                        </select>

                      </div>


                      <button
                        className="swap-icon"
                        onClick={
                          handleSwapCurrency
                        }
                        type="button"
                        title="Swap currencies"
                      >

                        ⇄

                      </button>


                      <div className="currency-field">

                        <label>
                          To
                        </label>


                        <select
                          value={
                            targetCurrency
                          }
                          onChange={(event) =>
                            setTargetCurrency(
                              event.target.value
                            )
                          }
                        >

                          <option value="INR">
                            INR
                          </option>

                          <option value="USD">
                            USD
                          </option>

                          <option value="EUR">
                            EUR
                          </option>

                          <option value="GBP">
                            GBP
                          </option>

                          <option value="JPY">
                            JPY
                          </option>

                          <option value="AUD">
                            AUD
                          </option>

                          <option value="CAD">
                            CAD
                          </option>

                          <option value="SGD">
                            SGD
                          </option>

                        </select>

                      </div>

                    </div>


                    <button
                      className="convert-button"
                      onClick={
                        handleConvertCurrency
                      }
                      disabled={
                        currencyLoading
                      }
                    >

                      {currencyLoading ? (

                        <>

                          <RefreshCw
                            size={15}
                            className="button-spin"
                          />

                          Converting...

                        </>

                      ) : (

                        <>
                          Convert Currency
                        </>

                      )}

                    </button>


                    {convertedAmount !==
                      null && (

                      <div className="conversion-result">

                        <span>
                          Converted Amount
                        </span>


                        <strong>

                          {Number(
                            currencyAmount
                          ).toLocaleString(
                            "en-IN"
                          )}


                          {" "}


                          {baseCurrency}


                          {" = "}


                          {Number(
                            convertedAmount
                          ).toLocaleString(
                            "en-IN",
                            {
                              maximumFractionDigits:
                                2,
                            }
                          )}


                          {" "}


                          {targetCurrency}

                        </strong>

                      </div>

                    )}

                  </div>


                  {/* EXCHANGE RATE */}

                  <div className="rate-card">

                    <div className="currency-card-title">

                      <span>
                        📈
                      </span>


                      <div>

                        <h3>
                          Exchange Rate
                        </h3>


                        <p>
                          Current conversion rate
                        </p>

                      </div>

                    </div>


                    {exchangeRate !==
                    null ? (

                      <div className="rate-result">

                        <span>
                          Current Rate
                        </span>


                        <strong>

                          1{" "}
                          {baseCurrency}


                          {" = "}


                          {exchangeRate}


                          {" "}


                          {targetCurrency}

                        </strong>

                      </div>

                    ) : (

                      <div className="rate-empty">

                        <ArrowRightLeft
                          size={30}
                        />


                        <p>
                          Convert a currency to see the current exchange rate.
                        </p>

                      </div>

                    )}

                  </div>

                </div>

              </section>

            )}

          </div>

        </main>

      </div>

    </div>

  );

};


export default AIAssistant;