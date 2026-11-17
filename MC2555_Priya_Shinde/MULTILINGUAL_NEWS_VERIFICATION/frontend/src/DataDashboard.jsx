const dashboardImages = {
  // ============================================================
  // PART A — ORIGINAL DATASET
  // ============================================================

  fakeReal: "/eda/01_fake_real_distribution.png",
  subject: "/eda/02_subject_distribution.png",
  fakeRealSubject: "/eda/03_fake_real_by_subject.png",
  titleLength: "/eda/04_title_length_distribution.png",
  textLength: "/eda/05_text_length_distribution.png",
  textBoxplot: "/eda/06_fake_real_text_length_boxplot.png",
  year: "/eda/07_articles_by_year.png",

  // ============================================================
  // PART B / PART E — API + FUSED DATASET
  // ============================================================

  apiSource: "/eda/01_api_source_distribution.png",
  query: "/eda/02_query_distribution.png",
  newsSources: "/eda/03_top_news_sources.png",

  apiTitleLength: "/eda/04_api_title_length_distribution.png",
  apiDescriptionDistribution:
    "/eda/05_description_length_distribution.png",

  titleDescription: "/eda/06_title_vs_description.png",

  apiDescription:
    "/eda/07_api_vs_description_length.png",

  queryApi:
    "/eda/08_query_vs_api_source.png",

  apiTitle:
    "/eda/09_api_vs_title_length.png",

  publication:
    "/eda/10_publication_year.png",

  correlation:
    "/eda/11_correlation_heatmap.png",

  // ============================================================
  // PART C — DATA FUSION
  // ============================================================

  fusionMatch:
    "/eda/01_fusion_matched_vs_unmatched.png",

  fusionSimilarity:
    "/eda/02_fusion_similarity_distribution.png",

  fusionApi:
    "/eda/03_fusion_api_source_distribution.png",

  fusionStatus:
    "/eda/04_fusion_api_source_vs_match_status.png",
};

function ChartCard({
  title,
  description,
  image,
  large = false,
}) {
  return (
    <div className={`analytics-chart-card ${large ? "analytics-chart-large" : ""}`}>
      <div className="analytics-chart-heading">
        <div>
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </div>
      </div>

      {image ? (
        <img
          src={image}
          alt={title}
          className="analytics-chart-image"
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
        />
      ) : (
        <div className="analytics-no-chart">
          Chart unavailable
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, subtext }) {
  return (
    <div className="analytics-metric-card">
      <span className="analytics-metric-label">{label}</span>
      <strong>{value}</strong>
      {subtext && <small>{subtext}</small>}
    </div>
  );
}

export default function DataDashboard({ onBack }) {
  return (
    <section className="analytics-page">

      {/* =====================================================
          DASHBOARD HEADER
      ===================================================== */}

      <div className="analytics-header">

        <div>
          <div className="analytics-kicker">
            PHASE 1 • DATA ANALYTICS
          </div>

          <h1>
            EDA & Data Analytics Dashboard
          </h1>

          <p>
            Exploratory analysis of the original dataset, API
            collection, data fusion and fused dataset.
          </p>
        </div>

        <button
          className="analytics-back-button"
          onClick={onBack}
        >
          ← Verify News
        </button>

      </div>


      {/* =====================================================
          OVERVIEW METRICS
      ===================================================== */}

      <div className="analytics-section">

        <div className="analytics-section-header">
          <div>
            <span>DATASET OVERVIEW</span>
            <h2>Phase 1 summary</h2>
          </div>
        </div>

        <div className="analytics-metrics-grid">

          <MetricCard
            label="Original Articles"
            value="44,898"
            subtext="ISOT dataset"
          />

          <MetricCard
            label="Fake Articles"
            value="23,481"
            subtext="52.3%"
          />

          <MetricCard
            label="Real Articles"
            value="21,417"
            subtext="47.7%"
          />

          <MetricCard
            label="API Articles"
            value="173"
            subtext="6 API providers"
          />

          <MetricCard
            label="Fused Records"
            value="44,862"
            subtext="18 original attributes"
          />

          <MetricCard
            label="News Sources"
            value="129"
            subtext="API dataset"
          />

        </div>

      </div>


      {/* =====================================================
          PART A — ORIGINAL DATASET
      ===================================================== */}

      <div className="analytics-section">

        <div className="analytics-section-header">
          <div>
            <span>PART A</span>
            <h2>Original Dataset EDA</h2>
            <p>
              Analysis of the original ISOT Fake/Real news dataset.
            </p>
          </div>
        </div>


        <div className="analytics-chart-grid">

          <ChartCard
            title="Fake vs Real News"
            description="Distribution of fake and real articles."
            image={dashboardImages.fakeReal}
          />

          <ChartCard
            title="News Articles by Subject"
            description="Distribution across news categories."
            image={dashboardImages.subject}
          />

          <ChartCard
            title="Fake vs Real by Subject"
            description="Relationship between subject and news label."
            image={dashboardImages.fakeRealSubject}
            large
          />

          <ChartCard
            title="Title Length Distribution"
            description="Distribution of article title lengths."
            image={dashboardImages.titleLength}
          />

          <ChartCard
            title="Text Length Distribution"
            description="Distribution of article text lengths."
            image={dashboardImages.textLength}
          />

          <ChartCard
            title="Fake vs Real Text Length"
            description="Comparison of article text length."
            image={dashboardImages.textBoxplot}
          />

          <ChartCard
            title="Articles by Publication Year"
            description="Distribution of available publication years."
            image={dashboardImages.year}
          />

        </div>

      </div>


      {/* =====================================================
          PART B — API ANALYTICS
      ===================================================== */}

      <div className="analytics-section">

        <div className="analytics-section-header">
          <div>
            <span>PART B</span>
            <h2>API Data Analytics</h2>
            <p>
              Analysis of the additional news data collected through
              external APIs.
            </p>
          </div>
        </div>


        <div className="analytics-metrics-grid analytics-metrics-small">

          <MetricCard
            label="GNews"
            value="35"
            subtext="articles"
          />

          <MetricCard
            label="Currents"
            value="37"
            subtext="articles"
          />

          <MetricCard
            label="NewsAPI"
            value="34"
            subtext="articles"
          />

          <MetricCard
            label="NewsData.io"
            value="33"
            subtext="articles"
          />

          <MetricCard
            label="Google News RSS"
            value="28"
            subtext="articles"
          />

          <MetricCard
            label="TheNewsAPI"
            value="6"
            subtext="articles"
          />

        </div>


        <div className="analytics-chart-grid">

          <ChartCard
            title="API Source Distribution"
            description="Number of records collected from each API."
            image={dashboardImages.apiSource}
          />

          <ChartCard
            title="Search Query Distribution"
            description="Articles retrieved for each search query."
            image={dashboardImages.query}
          />

          <ChartCard
            title="Top News Sources"
            description="Most frequent news sources in the API dataset."
            image={dashboardImages.newsSources}
            large
          />

          <ChartCard
            title="Title Length Distribution"
            description="Distribution of API article title lengths."
            image={dashboardImages.titleLength}
          />

          <ChartCard
            title="Description Length Distribution"
            description="Distribution of API article descriptions."
            image={dashboardImages.apiDescription}
          />

          <ChartCard
            title="Publication Year"
            description="Available API article publication years."
            image={dashboardImages.publication}
          />

        </div>

      </div>


      {/* =====================================================
          PART C — FUSION
      ===================================================== */}

      <div className="analytics-section">

        <div className="analytics-section-header">
          <div>
            <span>PART C</span>
            <h2>Data Fusion Analysis</h2>
            <p>
              Content-based matching between the original and API
              datasets.
            </p>
          </div>
        </div>


        <div className="analytics-fusion-note">

          <div className="analytics-note-icon">
            i
          </div>

          <div>
            <strong>Fusion methodology</strong>

            <p>
              The original and API datasets did not share a common
              unique identifier. Content-based matching was therefore
              attempted using normalized article content and
              TF-IDF cosine similarity. API records that did not
              satisfy the matching threshold were retained as
              API-only records.
            </p>
          </div>

        </div>


        <div className="analytics-metrics-grid">

          <MetricCard
            label="Original Records"
            value="44,689"
            subtext="after duplicate removal"
          />

          <MetricCard
            label="API Records"
            value="173"
            subtext="collected records"
          />

          <MetricCard
            label="Matched"
            value="0"
            subtext="above similarity threshold"
          />

          <MetricCard
            label="API Only"
            value="173"
            subtext="retained as enrichment"
          />

          <MetricCard
            label="Final Fused Records"
            value="44,862"
            subtext="final dataset"
          />

        </div>


        <div className="analytics-chart-grid">

          <ChartCard
            title="Matched vs Unmatched"
            description="API records crossing the fusion threshold."
            image={dashboardImages.fusionMatch}
          />

          <ChartCard
            title="Similarity Distribution"
            description="TF-IDF cosine similarity across API records."
            image={dashboardImages.fusionSimilarity}
          />

          <ChartCard
            title="API Source Distribution"
            description="API contribution to the fusion dataset."
            image={dashboardImages.fusionApi}
          />

          <ChartCard
            title="API Source vs Match Status"
            description="Fusion status across API sources."
            image={dashboardImages.fusionStatus}
            large
          />

        </div>

      </div>


     {/* =====================================================
    PART D — DATA QUALITY
===================================================== */}

<div className="analytics-section">

  <div className="analytics-section-header">

    <div>

      <span>PART D</span>

      <h2>
        Data Quality Assessment
      </h2>

      <p>
        Structural, missing-data, consistency and outlier checks.
      </p>

    </div>

  </div>


  {/* =====================================================
      QUALITY SUMMARY CARDS
  ===================================================== */}

  <div className="analytics-quality-grid">

    <div className="analytics-quality-card">

      <span>
        Duplicate Records
      </span>

      <strong>
        0
      </strong>

      <p>
        No exact duplicate rows remain in the fused dataset.
      </p>

    </div>


    <div className="analytics-quality-card">

      <span>
        Duplicate Fused IDs
      </span>

      <strong>
        0
      </strong>

      <p>
        All fused identifiers are unique.
      </p>

    </div>


    <div className="analytics-quality-card">

      <span>
        Duplicate API URLs
      </span>

      <strong>
        0
      </strong>

      <p>
        All API URLs are unique.
      </p>

    </div>


    <div className="analytics-quality-card">

      <span>
        API Duplicate Titles
      </span>

      <strong>
        4
      </strong>

      <p>
        Four repeated API titles were observed.
      </p>

    </div>


    <div className="analytics-quality-card">

      <span>
        API Images Missing
      </span>

      <strong>
        35
      </strong>

      <p>
        20.23% of API records have no image.
      </p>

    </div>


    <div className="analytics-quality-card">

      <span>
        Valid Original Dates
      </span>

      <strong>
        11,868
      </strong>

      <p>
        Valid publication dates in the original dataset.
      </p>

    </div>

  </div>


  {/* =====================================================
      DATA QUALITY OBSERVATIONS
  ===================================================== */}

  <div className="analytics-quality-text">

    <h3>
      Data quality observations
    </h3>

    <p>
      The fused dataset contains structurally valid unique
      identifiers and no exact duplicate rows. Missing values
      primarily occur because original records do not contain
      API-specific fields, while API-only records do not contain
      original-dataset fields.
    </p>

    <p>
      Date consistency checks identified unavailable or invalid
      publication dates in a large portion of the API data.
      Outlier analysis was performed using the IQR method on
      available numerical attributes.
    </p>

  </div>


  {/* =====================================================
      OUTLIER ANALYSIS
  ===================================================== */}

  <div className="analytics-section-header analytics-subsection-header">

    <div>

      <span>
        OUTLIER ANALYSIS
      </span>

      <h2>
        IQR-Based Outlier Detection
      </h2>

      <p>
        Numerical attributes were checked using the
        Interquartile Range (IQR) method.
      </p>

    </div>

  </div>


  <div className="analytics-chart-grid">

    <ChartCard
      title="Original ID Outlier Analysis"
      description="IQR-based analysis of original dataset identifiers."
      image="/eda/outlier_original_id.png"
    />


    <ChartCard
      title="Similarity Score Outlier Analysis"
      description="IQR-based analysis of API similarity scores."
      image="/eda/outlier_similarity_score.png"
    />

  </div>


  {/* =====================================================
      QUALITY INTERPRETATION
  ===================================================== */}

  <div className="analytics-fusion-note">

    <div className="analytics-note-icon">
      ✓
    </div>

    <div>

      <strong>
        Quality interpretation
      </strong>

      <p>
        No outliers were identified for the original identifier
        field or similarity score under the IQR calculation.
        The high number of missing API-specific fields is mainly
        structural because those attributes are not applicable
        to the original records in the fused dataset.
      </p>

    </div>

  </div>

</div>


      {/* =====================================================
          PART E — FUSED DATA EDA
      ===================================================== */}

      <div className="analytics-section">

        <div className="analytics-section-header">
          <div>
            <span>PART E</span>
            <h2>Fused Dataset EDA</h2>
            <p>
              Analysis focused on variables introduced by the API
              collection and fusion process.
            </p>
          </div>
        </div>


        <div className="analytics-insight-grid">

          <div className="analytics-insight-card">

            <span>API PROVIDERS</span>

            <strong>6</strong>

            <p>
              The API dataset contains records from six external
              sources.
            </p>

          </div>


          <div className="analytics-insight-card">

            <span>NEWS SOURCES</span>

            <strong>129</strong>

            <p>
              The API collection introduced substantial source
              diversity.
            </p>

          </div>


          <div className="analytics-insight-card">

            <span>TITLE/DESCRIPTION CORRELATION</span>

            <strong>0.23</strong>

            <p>
              A weak positive relationship exists between title and
              description length.
            </p>

          </div>


          <div className="analytics-insight-card">

            <span>API DESCRIPTION RANGE</span>

            <strong>25–4,113</strong>

            <p>
              Description lengths vary substantially across sources.
            </p>

          </div>

        </div>


        <div className="analytics-chart-grid">

          <ChartCard
            title="Title Length vs Description Length"
            description="Bivariate relationship between article title and description size."
            image={dashboardImages.titleDescription}
            large
          />

          <ChartCard
            title="Average Description Length by API"
            description="Comparison of API-generated description lengths."
            image={dashboardImages.apiDescription}
          />

          <ChartCard
            title="Average Title Length by API"
            description="Comparison of API-generated title lengths."
            image={dashboardImages.apiTitle}
          />

          <ChartCard
            title="Search Query vs API Source"
            description="Group-wise distribution of search queries across API providers."
            image={dashboardImages.queryApi}
            large
          />

          <ChartCard
            title="Correlation Heatmap"
            description="Multivariate relationship between numerical API variables."
            image={dashboardImages.correlation}
            large
          />

        </div>

      </div>


      {/* =====================================================
          FINAL INSIGHT
      ===================================================== */}

      <div className="analytics-conclusion">

        <div className="analytics-conclusion-icon">
          ✓
        </div>

        <div>
          <span>PHASE 1 CONCLUSION</span>

          <h2>
            Data collection, fusion, quality assessment and EDA completed
          </h2>

          <p>
            The Phase 1 pipeline combines the historical news dataset
            with real-time API information, performs data-quality
            assessment, and provides analytical insights into the
            resulting data.
          </p>
        </div>

      </div>

    </section>
  );
}