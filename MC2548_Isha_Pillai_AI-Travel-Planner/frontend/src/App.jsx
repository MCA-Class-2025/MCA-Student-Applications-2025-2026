import { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./App.css";

function App() {
  const [destination, setDestination] = useState("");
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState(80000);

  const [travelPlan, setTravelPlan] = useState("");
  const [travelContext, setTravelContext] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ========================================
  // GENERATE TRAVEL PLAN
  // ========================================

  const generatePlan = async () => {
    if (!destination.trim()) {
      setError("Please enter a destination.");
      return;
    }

    setLoading(true);
    setError("");
    setTravelPlan("");
    setTravelContext(null);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/plan",
        {
          destination: destination,
          days: Number(days),
          budget: Number(budget),
        }
      );

      setTravelPlan(response.data.travel_plan);
      setTravelContext(response.data.context || null);

    } catch (err) {
      console.error(err);

      setError(
        "Unable to generate travel plan. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ========================================
  // GENERAL NUMBER FORMAT
  // ========================================

  const formatNumber = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "Not Available";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return value;
    }

    return number.toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    });
  };

  // ========================================
  // CURRENCY RATE FORMAT
  // Keep full project-data precision
  // ========================================

  const formatExchangeRate = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "Not Available";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return value;
    }

    return number.toFixed(5);
  };

  // ========================================
  // FLIGHT NUMBER FORMAT
  // ========================================

  const formatFlightNumber = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "Not Available";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return value;
    }

    return Number.isInteger(number)
      ? String(number)
      : String(number);
  };

  // ========================================
  // CLEAN PROJECT PLACES
  // ========================================

  const excludedPlaces = [
    "boat model",
    "victory hand",
    "pen",
    "seawings airplane counter",
  ];

  const displayPlaces = (
    travelContext?.places || []
  ).filter((place) => {
    const name = String(place)
      .toLowerCase()
      .trim();

    return !excludedPlaces.includes(name);
  });

  // ========================================
  // PAGE
  // ========================================

  return (
    <div className="app">

      {/* ====================================
          HERO
      ==================================== */}

      <header className="hero">
        <div className="hero-content">

          <div className="hero-icon">
            ✈️
          </div>

          <h1>
            AI Travel Planner
          </h1>

          <p>
            Create personalized travel plans
            using AI and real project data.
          </p>

        </div>
      </header>


      <main className="container">

        {/* ====================================
            INPUT CARD
        ==================================== */}

        <section className="planner-card">

          <h2>
            Plan Your Trip
          </h2>

          <p className="planner-subtitle">
            Enter your destination, trip duration
            and budget to generate your AI-powered
            travel plan.
          </p>


          <div className="form-group">

            <label>
              Destination
            </label>

            <input
              type="text"
              placeholder="e.g. Dubai, London"
              value={destination}
              onChange={(e) =>
                setDestination(e.target.value)
              }
            />

          </div>


          <div className="form-row">

            <div className="form-group">

              <label>
                Number of Days
              </label>

              <input
                type="number"
                min="1"
                max="30"
                value={days}
                onChange={(e) =>
                  setDays(e.target.value)
                }
              />

            </div>


            <div className="form-group">

              <label>
                Budget (₹)
              </label>

              <input
                type="number"
                min="1"
                value={budget}
                onChange={(e) =>
                  setBudget(e.target.value)
                }
              />

            </div>

          </div>


          <button
            onClick={generatePlan}
            disabled={loading}
          >
            {loading
              ? "Generating Your Plan..."
              : "Generate Travel Plan"}
          </button>


          {error && (
            <div className="error">
              {error}
            </div>
          )}

        </section>


        {/* ====================================
            TRAVEL RESULT
        ==================================== */}

        {travelContext && (
          <>

            {/* ==================================
                DESTINATION HEADER
            ================================== */}

            <section className="destination-card">

              <div>

                <span className="small-label">
                  YOUR DESTINATION
                </span>

                <h2>
                  📍 {travelContext.destination}
                </h2>

              </div>


              <div className="trip-summary">

                <div>
                  <strong>
                    {days}
                  </strong>

                  <span>
                    Days
                  </span>
                </div>


                <div>
                  <strong>
                    ₹{formatNumber(budget)}
                  </strong>

                  <span>
                    Budget
                  </span>
                </div>

              </div>

            </section>


            {/* ==================================
                INFORMATION GRID
            ================================== */}

            <section className="info-grid">

              {/* ==================================
                  WEATHER
              ================================== */}

              <div className="info-card">

                <div className="card-icon">
                  🌤️
                </div>

                <div className="card-content">

                  <h3>
                    Weather
                  </h3>

                  <div className="main-value">
                    {formatNumber(
                      travelContext.weather?.temperature_c
                    )}°C
                  </div>

                  <p>
                    Feels like{" "}
                    {formatNumber(
                      travelContext.weather?.feels_like_c
                    )}°C
                  </p>

                  <p>
                    ☁️{" "}
                    {travelContext.weather?.condition ||
                      "Not Available"}
                  </p>

                  <p>
                    💧{" "}
                    {formatNumber(
                      travelContext.weather?.humidity
                    )}% humidity
                  </p>

                  <p>
                    💨{" "}
                    {formatNumber(
                      travelContext.weather?.wind_speed
                    )} m/s
                  </p>

                </div>

              </div>


              {/* ==================================
                  CURRENCY
              ================================== */}

              <div className="info-card">

                <div className="card-icon">
                  💱
                </div>

                <div className="card-content">

                  <h3>
                    Currency
                  </h3>

                  <div className="main-value">
                    {travelContext.currency?.from}
                    {" → "}
                    {travelContext.currency?.to}
                  </div>

                  <p>
                    1{" "}
                    {travelContext.currency?.from}
                    {" = "}
                    {formatExchangeRate(
                      travelContext.currency?.exchange_rate
                    )}{" "}
                    {travelContext.currency?.to}
                  </p>

                  <p>
                    ₹
                    {formatNumber(
                      travelContext.currency?.amount_inr
                    )}
                    {" ≈ "}
                    {formatNumber(
                      travelContext.currency?.converted_amount
                    )}{" "}
                    {travelContext.currency?.to}
                  </p>

                  <span className="badge">
                    Project reference rate
                  </span>

                </div>

              </div>


              {/* ==================================
                  FLIGHT
              ================================== */}

              <div className="info-card">

                <div className="card-icon">
                  ✈️
                </div>

                <div className="card-content">

                  <h3>
                    Flight
                  </h3>

                  <div className="main-value">
                    {travelContext.flight?.airline ||
                      "Not Available"}
                  </div>

                  <p>
                    Flight{" "}
                    {formatFlightNumber(
                      travelContext.flight?.flight_number
                    )}
                  </p>

                  <p>
                    Status:{" "}
                    <strong>
                      {travelContext.flight?.status ||
                        "Not Available"}
                    </strong>
                  </p>

                  <p>
                    Date:{" "}
                    {travelContext.flight?.date ||
                      "Not Available"}
                  </p>

                </div>

              </div>


              {/* ==================================
                  ACCOMMODATION
              ================================== */}

              <div className="info-card">

                <div className="card-icon">
                  🏨
                </div>

                <div className="card-content">

                  <h3>
                    Accommodation
                  </h3>

                  <div className="main-value">
                    {travelContext.accommodation?.type ||
                      "Not Available"}
                  </div>

                  <p>
                    Historical / Reference cost
                  </p>

                  <div className="cost">
                    {formatNumber(
                      travelContext.accommodation?.cost
                    )}{" "}
                    {travelContext.currency?.to}
                  </div>

                  <span className="badge">
                    Reference data
                  </span>

                </div>

              </div>


              {/* ==================================
                  TRANSPORTATION
              ================================== */}

              <div className="info-card">

                <div className="card-icon">
                  🚇
                </div>

                <div className="card-content">

                  <h3>
                    Transportation
                  </h3>

                  <div className="main-value">
                    {travelContext.transportation?.type ||
                      "Not Available"}
                  </div>

                  <p>
                    Historical / Reference cost
                  </p>

                  <div className="cost">
                    {formatNumber(
                      travelContext.transportation?.cost
                    )}{" "}
                    {travelContext.currency?.to}
                  </div>

                  <span className="badge">
                    Reference data
                  </span>

                </div>

              </div>

            </section>


            {/* ==================================
                DESTINATION IMAGE
            ================================== */}

            {travelContext.image?.image_url && (
              <section className="image-card">

                <img
                  src={
                    travelContext.image.image_url
                  }
                  alt={
                    travelContext.destination
                  }
                />

                <div className="image-caption">

                  <strong>
                    {travelContext.destination}
                  </strong>

                  <span>
                    Photo by{" "}
                    {travelContext.image.photographer}
                  </span>

                </div>

              </section>
            )}


            {/* ==================================
                PLACES TO VISIT
            ================================== */}

            {displayPlaces.length > 0 && (
              <section className="places-section">

                <div className="section-heading">

                  <span>
                    📍
                  </span>

                  <div>

                    <h2>
                      Places to Visit
                    </h2>

                    <p>
                      Places available in the
                      project data.
                    </p>

                  </div>

                </div>


                <div className="places-grid">

                  {displayPlaces.map(
                    (place, index) => (

                      <div
                        className="place-card"
                        key={`${place}-${index}`}
                      >

                        <div className="place-number">
                          {index + 1}
                        </div>

                        <div>

                          <h3>
                            {place}
                          </h3>

                          <span>
                            Project data place
                          </span>

                        </div>

                      </div>

                    )
                  )}

                </div>

              </section>
            )}


            {/* ==================================
                BUDGET
            ================================== */}

            <section className="budget-card">

              <div className="section-heading">

                <span>
                  💰
                </span>

                <div>

                  <h2>
                    Budget Summary
                  </h2>

                  <p>
                    Based on project reference
                    values.
                  </p>

                </div>

              </div>


              <div className="budget-grid">

                <div className="budget-item">

                  <span>
                    Your Budget
                  </span>

                  <strong>
                    ₹{formatNumber(budget)}
                  </strong>

                </div>


                <div className="budget-item">

                  <span>
                    Project Conversion
                  </span>

                  <strong>
                    {formatNumber(
                      travelContext.currency
                        ?.converted_amount
                    )}{" "}
                    {travelContext.currency?.to}
                  </strong>

                </div>


                <div className="budget-item">

                  <span>
                    Accommodation
                  </span>

                  <strong>
                    {formatNumber(
                      travelContext.accommodation?.cost
                    )}{" "}
                    {travelContext.currency?.to}
                  </strong>

                </div>


                <div className="budget-item">

                  <span>
                    Transportation
                  </span>

                  <strong>
                    {formatNumber(
                      travelContext.transportation?.cost
                    )}{" "}
                    {travelContext.currency?.to}
                  </strong>

                </div>

              </div>


              <div className="budget-note">
                ⚠️ Accommodation and transportation
                values are historical/reference data
                from the project dataset and may not
                represent current prices.
              </div>

            </section>


            {/* ==================================
                AI TRAVEL PLAN
            ================================== */}

            {travelPlan && (
              <section className="result-card">

                <div className="ai-heading">

                  <span>
                    🤖
                  </span>

                  <div>

                    <h2>
                      Your AI Travel Plan
                    </h2>

                    <p>
                      Personalized using your
                      project data.
                    </p>

                  </div>

                </div>


                <div className="travel-plan">

                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ children }) => (
                        <h1 className="plan-main-heading">
                          {children}
                        </h1>
                      ),

                      h2: ({ children }) => (
                        <h2 className="plan-section-heading">
                          {children}
                        </h2>
                      ),

                      h3: ({ children }) => (
                        <h3 className="plan-day-heading">
                          {children}
                        </h3>
                      ),

                      p: ({ children }) => (
                        <p className="plan-paragraph">
                          {children}
                        </p>
                      ),

                      ul: ({ children }) => (
                        <ul className="plan-list">
                          {children}
                        </ul>
                      ),

                      ol: ({ children }) => (
                        <ol className="plan-list">
                          {children}
                        </ol>
                      ),

                      li: ({ children }) => (
                        <li className="plan-list-item">
                          {children}
                        </li>
                      ),

                      table: ({ children }) => (
                        <div className="plan-table-wrap">
                          <table>{children}</table>
                        </div>
                      )
                    }}
                  >
                    {travelPlan}
                  </ReactMarkdown>

                </div>

              </section>
            )}

          </>
        )}

      </main>


      {/* ====================================
          FOOTER
      ==================================== */}

      <footer>

        <p>
          AI Travel Planner • Powered by
          FastAPI + Groq + React
        </p>

      </footer>

    </div>
  );
}

export default App;