"use strict";


/* ============================================================
   GLOBAL STATE
   ============================================================ */

let currentSpecies = null;

let currentPrediction = null;

let currentLanguage = "en";

let currentSessionId =
    "dashboard-user";


let fishGbifChart = null;

let fishNutritionChart = null;

let fishWeatherChart = null;

let fishCountryChart = null;

let speciesDistributionChart = null;

let gbifMap = null;

let gbifMapMarkers = null;
let gbifAllRecords = [];
let exploreMap = null;
let exploreMapMarkers = null;

let generalEdaChart = null;


/* ============================================================
   HELPERS
   ============================================================ */

function $(id) {

    return document.getElementById(id);

}


function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "—";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function formatValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    if (
        typeof value === "number"
    ) {

        if (
            Number.isInteger(value)
        ) {

            return value.toLocaleString();

        }

        return value.toLocaleString(
            undefined,
            {
                maximumFractionDigits: 2
            }
        );

    }

    return String(value);

}


function formatPercent(value) {

    let n = Number(value);

    if (!Number.isFinite(n)) {
        return "—";
    }

    if (n <= 1) {
        n *= 100;
    }

    return n.toFixed(2) + "%";

}


function prettyName(name) {

    return String(name)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            c => c.toUpperCase()
        );

}


/* ============================================================
   NAVIGATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        document
            .querySelectorAll(
                ".nav-btn"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        () => {

                            const target =
                                button.dataset.section;

                            document
                                .querySelectorAll(
                                    ".nav-btn"
                                )
                                .forEach(
                                    b =>
                                        b.classList.remove(
                                            "active"
                                        )
                                );

                            button.classList.add(
                                "active"
                            );


                            document
                                .querySelectorAll(
                                    ".dashboard-section"
                                )
                                .forEach(
                                    section =>
                                        section.classList.remove(
                                            "active-section"
                                        )
                                );


                            const section =
                                $(target);

                            if (section) {

                                section.classList.add(
                                    "active-section"
                                );

                                window.scrollTo({
                                    top: 0,
                                    behavior: "smooth"
                                });

                                if (target === "gbif-distribution") {
                                    setTimeout(() => {
                                        if (Array.isArray(gbifAllRecords) && gbifAllRecords.length) {
                                            const select = $("gbifCountrySelect");
                                            const country = select?.value || "All";
                                            const filtered = country === "All"
                                                ? validMapRecords(gbifAllRecords)
                                                : validMapRecords(gbifAllRecords).filter(row => row._country === country);
                                            renderGBIFMap(filtered);
                                        } else {
                                            loadGBIFOverview();
                                        }
                                    }, 120);
                                }

                            }

                        }
                    );

                }
            );


        initializeDashboard();

    }
);


/* ============================================================
   INITIALIZATION
   ============================================================ */

async function initializeDashboard() {

    setupImagePreview();
    setupIdentifyButton();
    setupQuestionButton();
    setupExploreButtons();
    setupDatasetControls();
    setupReadAloud();
    setupGBIFCountryFilter();

    // IMPORTANT: do not let one unrelated dashboard request stop the
    // GBIF/OpenStreetMap map from initializing.  The previous sequential
    // awaits could stop execution before loadGBIFOverview().
    const jobs = [
        loadSummary,
        loadSpeciesDistribution,
        loadApiEvidence,
        loadFusionResults,
        loadGeneralEDA,
        loadGBIFOverview
    ];

    await Promise.allSettled(
        jobs.map(fn =>
            Promise.resolve()
                .then(() => fn())
                .catch(error => {
                    console.error(`Dashboard loader failed: ${fn.name}`, error);
                })
        )
    );

    // A second map pass after the page has painted fixes Leaflet's
    // hidden-container sizing problem when GBIF is not the first tab.
    setTimeout(() => {
        refreshGBIFMapAfterLayout();
    }, 250);

}


/* ============================================================
   IMAGE PREVIEW
   ============================================================ */

function setupImagePreview() {

    const input =
        $("fishImage");

    if (!input) {
        return;
    }

    input.addEventListener(
        "change",
        () => {

            const file =
                input.files[0];

            if (!file) {
                return;
            }

            const url =
                URL.createObjectURL(
                    file
                );

            $("imagePreview").innerHTML = `

                <img
                    src="${url}"
                    alt="Uploaded fish"
                >

            `;

        }
    );

}


/* ============================================================
   IDENTIFY BUTTON
   ============================================================ */

function setupIdentifyButton() {

    const button =
        $("identifyFishBtn");

    if (!button) {
        return;
    }

    button.addEventListener(
        "click",
        identifyFish
    );

}


/* ============================================================
   IDENTIFY FISH
   ============================================================ */

async function identifyFish() {

    const input =
        $("fishImage");

    const errorBox =
        $("predictionError");

    errorBox.classList.add(
        "hidden"
    );

    if (
        !input ||
        !input.files ||
        input.files.length === 0
    ) {

        showError(
            "Please choose a fish image first."
        );

        return;

    }


    const file =
        input.files[0];


    const button =
        $("identifyFishBtn");


    button.disabled = true;

    button.textContent =
        "⏳ Identifying Fish...";


    currentLanguage =
        $("outputLanguage")?.value
        || "en";


    const formData =
        new FormData();

    formData.append(
        "image",
        file
    );

    formData.append(
        "language",
        currentLanguage
    );


    try {

        /*
         * IMPORTANT:
         * This is your actual working Flask route.
         */

        const response =
            await fetch(
                "/api/main-ai/predict",
                {

                    method: "POST",

                    body: formData

                }
            );


        /*
         * Never blindly call response.json().
         *
         * This protects against the exact previous error:
         *
         * Unexpected token '<', "<!doctype..."
         *
         * which occurs when Flask returns HTML instead of JSON.
         */

        const rawText =
            await response.text();


        let data;

        try {

            data =
                JSON.parse(
                    rawText
                );

        } catch (jsonError) {

            console.error(
                "Server returned non-JSON:",
                rawText
            );

            throw new Error(
                "The prediction server returned HTML instead of JSON. Check the Flask terminal for the backend error."
            );

        }


        if (
            !response.ok
            || !data.success
        ) {

            throw new Error(
                data.error
                || "Fish prediction failed."
            );

        }


        currentPrediction = data;

        currentSpecies =
        data.species;

        displayPrediction(
        data
        );

        await loadFishEvidence(
        currentSpecies
        );

        await loadFishFeatureEDA(
        currentSpecies
        );

        await loadContextReasoning(
        currentSpecies,
        data.confidence
        );

        $("qaSpecies").textContent =
        currentSpecies;


    } catch (error) {

        console.error(
            error
        );

        showError(
            error.message
        );

    } finally {

        button.disabled = false;

        button.textContent =
            "🔎 Identify Fish";

    }

}

/* ============================================================
   CONTEXT-AWARE REASONING
   ============================================================ */

async function loadContextReasoning(
    species,
    confidence
) {

    const section =
        $("contextReasoning");

    if (!section) {
        return;
    }

    section.classList.remove(
        "hidden"
    );

    const status =
        $("contextReasoningStatus");

    const summary =
        $("contextReasoningSummary");

    const features =
        $("contextReasoningFeatures");

    const conclusion =
        $("contextReasoningConclusion");

    if (status) {

        status.textContent =
            "Analysing context...";

        status.className =
            "context-status";

    }

    if (summary) {

        summary.innerHTML = `
            <div class="loading">
                Comparing CNN evidence with
                species-associated environmental
                evidence...
            </div>
        `;

    }

    if (features) {
        features.innerHTML = "";
    }

    if (conclusion) {
        conclusion.innerHTML = "";
    }

    try {

        const response =
            await fetch(
                "/api/context-reasoning"
                +
                "?species="
                +
                encodeURIComponent(
                    species
                )
                +
                "&confidence="
                +
                encodeURIComponent(
                    confidence
                )
            );

        const data =
            await response.json();

        if (
            !response.ok
            ||
            !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Context reasoning failed."
            );

        }

        renderContextReasoning(
            data
        );

    } catch (error) {

        console.error(
            "Context reasoning error:",
            error
        );

        if (status) {

            status.textContent =
                "Unavailable";

            status.classList.add(
                "context-error"
            );

        }

        if (summary) {

            summary.innerHTML = `
                <div class="error-box">
                    Context reasoning unavailable:
                    ${escapeHtml(
                        error.message
                    )}
                </div>
            `;

        }

    }

}
/* ============================================================
   ERROR
   ============================================================ */

function showError(message) {

    const box =
        $("predictionError");

    box.textContent =
        "Prediction error: " + message;

    box.classList.remove(
        "hidden"
    );

}


/* ============================================================
   DISPLAY PREDICTION
   ============================================================ */

function displayPrediction(
    data
) {

    $("predictionEmpty")
        .classList.add(
            "hidden"
        );

    $("predictionResult")
        .classList.remove(
            "hidden"
        );


    $("predictedSpecies")
        .textContent =
        "🐟 " + data.species;


    $("cnnConfidence")
        .textContent =
        formatPercent(
            data.confidence
        );


    renderTop3(
        data.top3
    );


    renderFactSheet(
        data.fact_sheet
    );


    if (
        data.fact_sheet_error
    ) {

        $("factSheet").innerHTML += `

            <div class="warning-box">

                Gemini fact sheet could not be generated:

                ${escapeHtml(
                    data.fact_sheet_error
                )}

            </div>

        `;

    }

}


/* ============================================================
   TOP 3
   ============================================================ */

function renderTop3(
    predictions
) {

    const container =
        $("topPredictions");

    container.innerHTML =
        "";


    if (
        !Array.isArray(
            predictions
        )
    ) {

        container.textContent =
            "No top predictions returned.";

        return;

    }


    predictions
        .slice(0, 3)
        .forEach(
            prediction => {

                const percent =
                    Number(
                        prediction.confidence
                    ) <= 1
                    ?
                    Number(
                        prediction.confidence
                    ) * 100
                    :
                    Number(
                        prediction.confidence
                    );


                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "prediction-row";


                row.innerHTML = `

                    <div class="prediction-label">

                        <span>
                            ${escapeHtml(
                                prediction.species
                            )}
                        </span>

                        <strong>
                            ${formatPercent(
                                prediction.confidence
                            )}
                        </strong>

                    </div>


                    <div class="prediction-bar">

                        <div
                            style="
                                width:${Math.max(
                                    0,
                                    Math.min(
                                        100,
                                        percent
                                    )
                                )}%;
                            "
                        ></div>

                    </div>

                `;


                container.appendChild(
                    row
                );

            }
        );

}


/* ============================================================
   FACT CHECK
   ============================================================ */

async function loadFishEvidence(
    species
) {

    const container =
        $("inlineEvidence");

    container.innerHTML =
        `<div class="loading">
            Loading fused evidence...
        </div>`;


    try {

        const response =
            await fetch(
                "/api/fish-evidence?species="
                +
                encodeURIComponent(
                    species
                )
            );


        const data =
            await response.json();


        if (
            !response.ok
            || !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Evidence unavailable."
            );

        }


        renderEvidenceGroups(
            data.groups
        );


    } catch (error) {

        container.innerHTML = `

            <div class="error-box">

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;

    }

}

/* ============================================================
   CONTEXT-AWARE REASONING
   ============================================================ */

/*
 * Safely escape text before inserting it into HTML.
 * Uses the existing escapeHtml() function if your project
 * already has one.
 */
function contextEscapeHtml(value) {

    if (typeof escapeHtml === "function") {
        return escapeHtml(
            value === null || value === undefined
                ? ""
                : String(value)
        );
    }

    const div = document.createElement("div");

    div.textContent =
        value === null || value === undefined
            ? ""
            : String(value);

    return div.innerHTML;
}


/* ============================================================
   RENDER CONTEXT-AWARE REASONING
   ============================================================ */

function renderContextReasoning(data) {

    const section =
        $("contextReasoning");

    const status =
        $("contextReasoningStatus");

    const summary =
        $("contextReasoningSummary");

    const features =
        $("contextReasoningFeatures");

    const conclusion =
        $("contextReasoningConclusion");


    if (!section) {
        console.warn(
            "Context reasoning section not found."
        );
        return;
    }


    section.classList.remove(
        "hidden"
    );


    /*
     * ----------------------------------------------------------
     * STATUS
     * ----------------------------------------------------------
     */

    if (status) {

        status.textContent =
            "Available";

        status.className =
            "context-status context-success";
    }


    /*
     * ----------------------------------------------------------
     * READ API RESPONSE
     *
     * The renderer accepts the normal response structure
     * but also handles slightly different field names so
     * existing backend code does not need unnecessary changes.
     * ----------------------------------------------------------
     */

    const cnn =
        data.cnn ||
        data.cnn_evidence ||
        data.prediction ||
        {};

    const species =
        data.species ||
        cnn.species ||
        data.predicted_species ||
        "Unknown species";


    const confidence =
        data.confidence !== undefined
            ? data.confidence
            : (
                cnn.confidence !== undefined
                    ? cnn.confidence
                    : null
            );


    const apiEvidence =
        data.api_evidence ||
        data.environmental_evidence ||
        data.species_evidence ||
        data.evidence ||
        {};


    const currentConditions =
        data.current_conditions ||
        data.environment ||
        data.environmental_conditions ||
        {};


    const oceanEnvironment =
        data.ocean_environment ||
        data.noaa_environment ||
        {};


    let reasoning =
        data.reasoning ||
        data.explanation ||
        data.context_reasoning ||
        data.conclusion ||
        "";

    if (Array.isArray(reasoning)) {
        reasoning = reasoning.filter(Boolean);
    } else if (reasoning && typeof reasoning === "object") {
        reasoning =
            reasoning.reasoning ||
            reasoning.reasoning_text ||
            "";
    }


    const supported =
        data.context_supported !== undefined
            ? data.context_supported
            : (
                data.supported !== undefined
                    ? data.supported
                    : null
            );


    /*
     * ----------------------------------------------------------
     * CNN CONFIDENCE
     * ----------------------------------------------------------
     */

    let confidenceText =
        "Not available";

    if (
        confidence !== null &&
        confidence !== undefined &&
        confidence !== ""
    ) {

        let numericConfidence =
            Number(confidence);

        if (
            !Number.isNaN(
                numericConfidence
            )
        ) {

            if (
                numericConfidence <= 1
            ) {
                numericConfidence =
                    numericConfidence * 100;
            }

            confidenceText =
                numericConfidence.toFixed(2)
                + "%";
        }
        else {

            confidenceText =
                contextEscapeHtml(
                    confidence
                );
        }
    }


    /*
     * ----------------------------------------------------------
     * SUMMARY
     * ----------------------------------------------------------
     */

    if (summary) {

        summary.innerHTML = `
            <div class="context-summary-card">

                <div class="context-summary-title">
                    CNN identification
                </div>

                <div class="context-summary-main">
                    <strong>
                        ${contextEscapeHtml(
                            species
                        )}
                    </strong>

                    <span class="context-confidence">
                        ${confidenceText}
                    </span>
                </div>

                <div class="context-summary-text">
                    The image-based CNN prediction is
                    compared with external species and
                    environmental evidence to determine
                    whether the surrounding context supports
                    the predicted fish species.
                </div>

            </div>
        `;
    }


    /*
     * ----------------------------------------------------------
     * FEATURE VALUES
     * ----------------------------------------------------------
     */

    if (features) {

        features.innerHTML = "";

        let featureItems = [];


        /*
         * API / species-associated conditions
         */

        if (
            typeof apiEvidence === "object" &&
            apiEvidence !== null &&
            !Array.isArray(apiEvidence)
        ) {

            const preferredKeys = [
                "temperature",
                "temperature_range",
                "water_temperature",
                "salinity",
                "salinity_range",
                "habitat",
                "habitat_type",
                "depth",
                "depth_range",
                "pH",
                "ph",
                "oxygen",
                "dissolved_oxygen"
            ];


            preferredKeys.forEach(
                function(key) {

                    if (
                        apiEvidence[key] !== undefined &&
                        apiEvidence[key] !== null &&
                        apiEvidence[key] !== ""
                    ) {

                        featureItems.push({
                            label: formatContextLabel(
                                key
                            ),
                            value:
                                apiEvidence[key],
                            type:
                                "api"
                        });

                    }

                }
            );


            /*
             * If the API uses other fields, include them too.
             */

            Object.keys(
                apiEvidence
            ).forEach(
                function(key) {

                    const alreadyAdded =
                        featureItems.some(
                            function(item) {
                                return (
                                    item.key === key
                                );
                            }
                        );

                    if (
                        !alreadyAdded &&
                        apiEvidence[key] !== undefined &&
                        apiEvidence[key] !== null &&
                        typeof apiEvidence[key] !== "object"
                    ) {

                        featureItems.push({
                            label:
                                formatContextLabel(
                                    key
                                ),
                            value:
                                apiEvidence[key],
                            type:
                                "api",
                            key:
                                key
                        });

                    }

                }
            );

        }


        /*
         * Current environmental conditions
         */

        if (
            typeof currentConditions === "object" &&
            currentConditions !== null &&
            !Array.isArray(currentConditions)
        ) {

            Object.keys(
                currentConditions
            ).forEach(
                function(key) {

                    const value =
                        currentConditions[key];

                    if (
                        value !== undefined &&
                        value !== null &&
                        value !== "" &&
                        typeof value !== "object"
                    ) {

                        featureItems.push({
                            label:
                                formatContextLabel(
                                    key
                                ),
                            value:
                                value,
                            type:
                                "current",
                            key:
                                "current_" + key
                        });

                    }

                }
            );

        }


        /*
         * NOAA ocean environmental evidence
         */
        if (
            oceanEnvironment &&
            typeof oceanEnvironment === "object" &&
            !Array.isArray(oceanEnvironment)
        ) {
            const checked =
                Number(oceanEnvironment.checked_locations || 0);

            if (checked > 0) {
                featureItems.push({
                    label: "GBIF / NOAA locations checked",
                    value: checked.toLocaleString(),
                    type: "noaa",
                    key: "noaa_checked_locations"
                });
            }

            const temp = oceanEnvironment.temperature;
            const tr = oceanEnvironment.temperature_range;

            featureItems.push({
                label: "NOAA water temperature",
                value:
                    temp !== null && temp !== undefined
                        ? `${formatValue(temp)} °C` +
                          (tr && tr.min !== undefined && tr.max !== undefined
                              ? ` (observed ${tr.min}–${tr.max} °C)`
                              : "")
                        : "No usable value returned",
                type: "noaa",
                key: "noaa_temperature"
            });

            const sal = oceanEnvironment.salinity;
            const sr = oceanEnvironment.salinity_range;

            featureItems.push({
                label: "NOAA salinity",
                value:
                    sal !== null && sal !== undefined
                        ? `${formatValue(sal)} PSU` +
                          (sr && sr.min !== undefined && sr.max !== undefined
                              ? ` (observed ${sr.min}–${sr.max} PSU)`
                              : "")
                        : "No usable value returned",
                type: "noaa",
                key: "noaa_salinity"
            });
        }


        /*
         * Render feature cards
         */

        if (
            featureItems.length > 0
        ) {

            const uniqueItems =
                [];

            const seen =
                new Set();


            featureItems.forEach(
                function(item) {

                    const identifier =
                        (
                            item.type +
                            "_" +
                            item.label
                        ).toLowerCase();

                    if (
                        !seen.has(
                            identifier
                        )
                    ) {

                        seen.add(
                            identifier
                        );

                        uniqueItems.push(
                            item
                        );

                    }

                }
            );


            features.innerHTML = `
                <div class="context-feature-heading">
                    Environmental context comparison
                </div>

                <div class="context-feature-grid">

                    ${uniqueItems
                        .map(
                            function(item) {

                                const badge =
                                    item.type === "current"
                                        ? "Current condition"
                                        : item.type === "noaa"
                                            ? "NOAA ocean evidence"
                                            : "Species evidence";

                                return `
                                    <div class="context-feature-card">

                                        <div class="context-feature-label">
                                            ${contextEscapeHtml(
                                                item.label
                                            )}
                                        </div>

                                        <div class="context-feature-value">
                                            ${contextEscapeHtml(
                                                item.value
                                            )}
                                        </div>

                                        <div class="context-feature-badge">
                                            ${badge}
                                        </div>

                                    </div>
                                `;

                            }
                        )
                        .join("")
                    }

                </div>
            `;

        }
        else {

            features.innerHTML = `
                <div class="context-no-data">
                    No structured environmental feature
                    values were returned by the API.
                </div>
            `;
        }

    }


    /*
     * ----------------------------------------------------------
     * CONCLUSION / REASONING
     * ----------------------------------------------------------
     */

    if (conclusion) {

        let conclusionTitle =
            "Contextual interpretation";

        let conclusionClass =
            "context-neutral";


        if (
            supported === true ||
            supported === "true"
        ) {

            conclusionTitle =
                "Context supports the prediction";

            conclusionClass =
                "context-supported";

        }
        else if (
            supported === false ||
            supported === "false"
        ) {

            conclusionTitle =
                "Context does not strongly support the prediction";

            conclusionClass =
                "context-not-supported";

        }


        let reasoningItems =
            Array.isArray(reasoning)
                ? reasoning
                : (reasoning ? [String(reasoning)] : []);

        if (reasoningItems.length === 0) {
            reasoningItems = [
                "The CNN prediction is compared with external species and environmental evidence. The contextual evidence is supplementary and does not replace the image-based prediction."
            ];
        }

        const reasoningHtml = reasoningItems
            .map(item => `
                <li>${contextEscapeHtml(item)}</li>
            `)
            .join("");

        conclusion.innerHTML = `
            <div class="
                context-conclusion-card
                ${conclusionClass}
            ">

                <div class="context-conclusion-title">
                    ${contextEscapeHtml(
                        conclusionTitle
                    )}
                </div>

                <ul class="context-reasoning-list">
                    ${reasoningHtml}
                </ul>

            </div>
        `;

    }

}


/* ============================================================
   FORMAT CONTEXT FIELD LABEL
   ============================================================ */

function formatContextLabel(
    key
) {

    return String(key)
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            function(letter) {
                return letter.toUpperCase();
            }
        );
}


/* ============================================================
   LOAD CONTEXT-AWARE REASONING
   ============================================================ */

async function loadContextReasoning(
    species,
    confidence
) {

    const section =
        $("contextReasoning");

    if (!section) {
        return;
    }


    section.classList.remove(
        "hidden"
    );


    const status =
        $("contextReasoningStatus");

    const summary =
        $("contextReasoningSummary");

    const features =
        $("contextReasoningFeatures");

    const conclusion =
        $("contextReasoningConclusion");


    if (status) {

        status.textContent =
            "Analysing context...";

        status.className =
            "context-status";

    }


    if (summary) {

        summary.innerHTML = `
            <div class="loading">
                Comparing CNN evidence with
                species-associated environmental
                evidence...
            </div>
        `;

    }


    if (features) {
        features.innerHTML = "";
    }


    if (conclusion) {
        conclusion.innerHTML = "";
    }


    try {

        const response =
            await fetch(
                "/api/context-reasoning"
                +
                "?species="
                +
                encodeURIComponent(
                    species
                )
                +
                "&confidence="
                +
                encodeURIComponent(
                    confidence
                )
            );


        const data =
            await response.json();


        if (
            !response.ok
            ||
            !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Context reasoning failed."
            );

        }


        /*
         * IMPORTANT:
         *
         * This function now exists, so the
         *
         * renderContextReasoning(data)
         *
         * call will work.
         */

        renderContextReasoning(
            data
        );


    } catch (error) {

        console.error(
            "Context reasoning error:",
            error
        );


        if (status) {

            status.textContent =
                "Unavailable";

            status.className =
                "context-status context-error";

        }


        if (summary) {

            summary.innerHTML = `
                <div class="error-box">
                    Context reasoning unavailable:
                    ${contextEscapeHtml(
                        error.message
                    )}
                </div>
            `;

        }


        if (features) {
            features.innerHTML = "";
        }


        if (conclusion) {
            conclusion.innerHTML = "";
        }

    }

}
/* ============================================================
   EVIDENCE GROUPS
   ============================================================ */

function renderEvidenceGroups(
    groups
) {

    const container =
        $("inlineEvidence");

    container.innerHTML =
        "";


    const order = [
        "GBIF",
        "USDA",
        "Weather"
    ];


    order.forEach(
        groupName => {

            const group =
                groups[groupName];

            if (!group) {
                return;
            }


            Object.entries(
                group
            ).forEach(
                ([key, value]) => {

                    const card =
                        document.createElement(
                            "div"
                        );

                    card.className =
                        "feature-card";


                    card.innerHTML = `

                        <div class="feature-name">

                            ${escapeHtml(
                                prettyName(key)
                            )}

                        </div>


                        <div class="feature-value">

                            ${escapeHtml(
                                formatValue(value)
                            )}

                        </div>

                    `;


                    container.appendChild(
                        card
                    );

                }
            );

        }
    );

}


/* ============================================================
   FISH FEATURE EDA
   ============================================================ */

async function loadFishFeatureEDA(
    species
) {

    const section =
        $("fishFeatureEDA");


    section.classList.remove(
        "hidden"
    );


    $("edaSpeciesBadge")
        .textContent =
        species;


    try {

        const response =
            await fetch(
                "/api/fish-feature-eda?species="
                +
                encodeURIComponent(
                    species
                )
            );


        const data =
            await response.json();


        if (
            !response.ok
            || !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Fish Feature EDA unavailable."
            );

        }


        const scientificElement =
            $("edaScientificName");

        if (scientificElement) {
            scientificElement.textContent =
                "Scientific name: "
                +
                (
                    data.scientific_name
                    || "Not available"
                );
        }

        renderFishEdaSummary(
            data
        );


        renderFishFeatureCards(
            data
        );


        renderFishCharts(
            data
        );


        renderInterpretation(
            data.interpretation
        );


    } catch (error) {

        console.error(
            error
        );

        section.innerHTML += `

            <div class="error-box">

                Fish Feature EDA error:

                ${escapeHtml(
                    error.message
                )}

            </div>

        `;

    }

}


/* ============================================================
   FEATURE CARDS
   ============================================================ */

function renderFishFeatureCards(
    data
) {

    renderGroupCards(
        "gbifFeatures",
        data.gbif
    );

    renderGroupCards(
        "usdaFeatures",
        data.usda
    );

    renderGroupCards(
        "weatherFeatures",
        data.weather
    );

}


function renderGroupCards(
    elementId,
    group
) {

    const container =
        $(elementId);

    container.innerHTML =
        "";


    if (!group) {
        return;
    }


    group.forEach(
        item => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "feature-card";


            card.innerHTML = `

                <div class="feature-name">

                    ${escapeHtml(
                        item.label
                    )}

                </div>


                <div class="feature-value">

                    ${escapeHtml(
                        formatValue(
                            item.value
                        )
                    )}

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


/* ============================================================
   FISH CHARTS
   ============================================================ */

/* ============================================================
   FISH CHARTS — POLISHED VISUAL ANALYTICS
   ============================================================ */

const fishValueLabelPlugin = {

    id: "fishValueLabelPlugin",

    afterDatasetsDraw(chart, args, pluginOptions) {

        const dataset = chart.data.datasets?.[0];

        if (!dataset) return;

        const meta = chart.getDatasetMeta(0);
        const ctx = chart.ctx;
        const horizontal = chart.options.indexAxis === "y";
        const values = dataset.data || [];
        const suffix = pluginOptions?.suffix || "";

        ctx.save();
        ctx.font = "700 11px Arial";
        ctx.textBaseline = "middle";

        meta.data.forEach((bar, index) => {

            const raw = Number(values[index]);
            if (!Number.isFinite(raw)) return;

            const valueText =
                formatValue(raw) + suffix;

            if (horizontal) {

                const x = bar.x;
                const y = bar.y;
                const barStart = bar.base;
                const barWidth = Math.abs(x - barStart);

                if (barWidth > 70) {

                    ctx.fillStyle = "#ffffff";
                    ctx.textAlign = "right";
                    ctx.fillText(
                        valueText,
                        x - 9,
                        y
                    );

                } else {

                    ctx.fillStyle = "#173e5c";
                    ctx.textAlign = "left";
                    ctx.fillText(
                        valueText,
                        x + 9,
                        y
                    );

                }

            } else {

                ctx.fillStyle = "#173e5c";
                ctx.textAlign = "center";
                ctx.fillText(
                    valueText,
                    bar.x,
                    bar.y - 9
                );

            }

        });

        ctx.restore();
    }
};


function renderFishCharts(data) {

    destroyChart(fishGbifChart);
    destroyChart(fishNutritionChart);
    destroyChart(fishWeatherChart);
    destroyChart(fishCountryChart);

    const numeric = {};

    (data.numeric_features || []).forEach(item => {
        numeric[item.feature] = Number(item.value);
    });

    /* GBIF biodiversity footprint. These are observation records. */
    fishGbifChart = createFishChart(
        "fishGbifChart",
        "bar",
        ["Occurrences", "Countries", "Coordinates"],
        [
            numeric.gbif_occurrence_count || 0,
            numeric.gbif_country_count || 0,
            numeric.gbif_coordinate_count || 0
        ],
        "GBIF records",
        {
            indexAxis: "y",
            tooltipSuffix: " records",
            labelSuffix: "",
            color: "#147d92",
            lightColor: "#5eb8c5"
        }
    );

    /* Nutrition: all three values are grams per 100 g. */
    fishNutritionChart = createFishChart(
        "fishNutritionChart",
        "bar",
        ["Protein", "Fat", "Carbohydrate"],
        [
            numeric.usda_protein || 0,
            numeric.usda_fat || 0,
            numeric.usda_carbohydrate || 0
        ],
        "g per 100 g",
        {
            indexAxis: "y",
            tooltipSuffix: " g / 100 g",
            labelSuffix: " g",
            color: "#2b9a73",
            lightColor: "#72c7a5"
        }
    );

    /* Environmental values have different physical units. */
    fishWeatherChart = createFishChart(
        "fishWeatherChart",
        "bar",
        [
            "Temperature (°C)",
            "Humidity (%)",
            "Wind speed (m/s)"
        ],
        [
            numeric.weather_temperature || 0,
            numeric.weather_humidity || 0,
            numeric.weather_wind_speed || 0
        ],
        "Environmental reading",
        {
            indexAxis: "y",
            tooltipSuffix: "",
            labelSuffix: "",
            color: "#3979c8",
            lightColor: "#7daee8"
        }
    );

    const countries = Array.isArray(data.countries)
        ? data.countries.slice(0, 8)
        : [];

    fishCountryChart = createFishChart(
        "fishCountryChart",
        "bar",
        countries.map(item => item.country),
        countries.map(item => Number(item.records) || 0),
        "GBIF occurrence records",
        {
            indexAxis: "y",
            tooltipSuffix: " records",
            labelSuffix: "",
            color: "#7457c7",
            lightColor: "#a894df"
        }
    );

    renderFishChartExplanations(
        data,
        numeric,
        countries
    );
}


function createFishChart(
    canvasId,
    type,
    labels,
    values,
    datasetLabel,
    chartOptions = {}
) {

    const canvas = $(canvasId);
    if (!canvas) return null;

    const context = canvas.getContext("2d");
    const isHorizontal = chartOptions.indexAxis === "y";

    const primary = chartOptions.color || "#147d92";
    const secondary = chartOptions.lightColor || "#5eb8c5";

    /* Canvas gradients give each chart a cleaner, richer appearance. */
    const gradient = context.createLinearGradient(
        isHorizontal ? 0 : 0,
        isHorizontal ? 0 : canvas.height,
        isHorizontal ? canvas.width : 0,
        isHorizontal ? 0 : 0
    );

    gradient.addColorStop(0, secondary);
    gradient.addColorStop(1, primary);

    return new Chart(context, {

        type,

        data: {
            labels,
            datasets: [{
                label: datasetLabel,
                data: values,
                borderWidth: 1,
                borderRadius: 9,
                borderSkipped: false,
                backgroundColor: gradient,
                borderColor: primary,
                maxBarThickness: isHorizontal ? 28 : 38,
                categoryPercentage: 0.70,
                barPercentage: 0.78
            }]
        },

        plugins: [fishValueLabelPlugin],

        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: chartOptions.indexAxis || "x",

            layout: {
                padding: {
                    top: 16,
                    right: isHorizontal ? 32 : 16,
                    bottom: 6,
                    left: 8
                }
            },

            interaction: {
                mode: "nearest",
                intersect: true
            },

            animation: {
                duration: 750,
                easing: "easeOutQuart"
            },

            plugins: {

                legend: {
                    display: false
                },

                fishValueLabelPlugin: {
                    suffix: chartOptions.labelSuffix || ""
                },

                tooltip: {
                    backgroundColor: "rgba(18,54,83,0.96)",
                    titleColor: "#ffffff",
                    bodyColor: "#ffffff",
                    padding: 12,
                    cornerRadius: 10,
                    displayColors: false,
                    titleFont: {
                        size: 12,
                        weight: "700"
                    },
                    bodyFont: {
                        size: 12,
                        weight: "600"
                    },
                    callbacks: {
                        label: context => {
                            const value = isHorizontal
                                ? context.parsed.x
                                : context.parsed.y;

                            return (
                                datasetLabel +
                                ": " +
                                formatValue(value) +
                                (chartOptions.tooltipSuffix || "")
                            );
                        }
                    }
                }
            },

            scales: {

                x: {
                    beginAtZero: true,
                    border: {
                        display: false
                    },
                    grid: {
                        color: "rgba(99,126,149,0.11)",
                        drawTicks: false
                    },
                    ticks: {
                        color: "#71879a",
                        font: {
                            size: 10,
                            weight: "600"
                        },
                        padding: 8
                    }
                },

                y: {
                    beginAtZero: true,
                    border: {
                        display: false
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: "#365a73",
                        autoSkip: false,
                        padding: 9,
                        font: {
                            size: 11,
                            weight: "700"
                        }
                    }
                }
            }
        }
    });
}


function renderFishEdaSummary(
    data
) {

    const container =
        $("fishEdaSummary");

    if (!container) {
        return;
    }


    const numeric =
        {};


    (data.numeric_features || [])
        .forEach(
            item => {

                numeric[
                    item.feature
                ] = Number(
                    item.value
                );

            }
        );


    const cards = [

        {
            label:
                "Species records",

            value:
                formatValue(
                    data.records
                ),

            icon:
                "🐟"
        },

        {
            label:
                "GBIF occurrences",

            value:
                formatValue(
                    numeric.gbif_occurrence_count
                    || 0
                ),

            icon:
                "🧬"
        },

        {
            label:
                "Recorded countries",

            value:
                formatValue(
                    numeric.gbif_country_count
                    || 0
                ),

            icon:
                "🌍"
        },

        {
            label:
                "Calories / 100 g",

            value:
                numeric.usda_calories
                != null
                ?
                formatValue(
                    numeric.usda_calories
                )
                :
                "—",

            icon:
                "🥗"
        }

    ];


    container.innerHTML =
        cards
            .map(
                card => `

                    <div
                        class="eda-summary-card"
                    >

                        <span
                            class="eda-summary-icon"
                        >
                            ${card.icon}
                        </span>

                        <div>

                            <span
                                class="eda-summary-label"
                            >
                                ${escapeHtml(
                                    card.label
                                )}
                            </span>

                            <strong>
                                ${escapeHtml(
                                    card.value
                                )}
                            </strong>

                        </div>

                    </div>

                `
            )
            .join("");

}


function renderFishChartExplanations(
    data,
    numeric,
    countries
) {

    const occurrence =
        numeric.gbif_occurrence_count
        || 0;

    const countryCount =
        numeric.gbif_country_count
        || 0;

    const coordinateCount =
        numeric.gbif_coordinate_count
        || 0;

    const protein =
        numeric.usda_protein;

    const fat =
        numeric.usda_fat;

    const carbohydrate =
        numeric.usda_carbohydrate;

    const temperature =
        numeric.weather_temperature;

    const humidity =
        numeric.weather_humidity;

    const wind =
        numeric.weather_wind_speed;


    const gbifExplanation =
        $("fishGbifExplanation");

    if (gbifExplanation) {

        gbifExplanation.innerHTML = `
            <strong>What this means:</strong>
            The chart summarizes the biodiversity footprint of
            <b>${escapeHtml(
                data.species
            )}</b> in the linked GBIF data.
            It contains ${formatValue(
                occurrence
            )} occurrence records,
            ${formatValue(
                countryCount
            )} recorded countries and
            ${formatValue(
                coordinateCount
            )} coordinate records.
            These are observation records, not a direct estimate
            of the fish population.
        `;

    }


    const nutritionExplanation =
        $("fishNutritionExplanation");

    if (nutritionExplanation) {

        nutritionExplanation.innerHTML = `
            <strong>What this means:</strong>
            The USDA-linked record reports the macronutrient
            profile per 100 g: ${formatValue(
                protein
            )} g protein,
            ${formatValue(
                fat
            )} g fat and
            ${formatValue(
                carbohydrate
            )} g carbohydrate.
            Calories are shown separately in the fish summary above.
        `;

    }


    const weatherExplanation =
        $("fishWeatherExplanation");

    if (weatherExplanation) {

        weatherExplanation.innerHTML = `
            <strong>What this means:</strong>
            The retrieved environmental context reports
            temperature ${formatValue(
                temperature
            )}, humidity ${formatValue(
                humidity
            )}% and wind speed ${formatValue(
                wind
            )}. These measurements describe the associated
            environmental record; they do not by themselves prove
            habitat suitability.
        `;

    }


    const countryExplanation =
        $("fishCountryExplanation");

    if (countryExplanation) {

        const topCountry =
            countries.length > 0
            ?
            countries[0]
            :
            null;

        countryExplanation.innerHTML =
            topCountry
            ?
            `
                <strong>What this means:</strong>
                ${escapeHtml(
                    topCountry.country
                )}
                has the largest number of recorded GBIF occurrences
                among the countries shown, with
                ${formatValue(
                    topCountry.records
                )} records.
                This reflects the available occurrence data rather
                than fish abundance in that country.
            `
            :
            `
                <strong>What this means:</strong>
                No country-level occurrence records were returned
                for this species.
            `;

    }

}


function createChart(
    canvasId,
    type,
    labels,
    values,
    datasetLabel
) {

    const canvas =
        $(canvasId);

    if (!canvas) {
        return null;
    }


    return new Chart(
        canvas,
        {

            type:
                type,

            data: {

                labels:
                    labels,

                datasets: [

                    {

                        label:
                            datasetLabel,

                        data:
                            values,

                    }

                ]

            },

            options: {

                responsive:
                    true,

                maintainAspectRatio:
                    false,

                plugins: {

                    legend: {

                        display:
                            true

                    }

                },

                scales:
                    type === "doughnut"
                    ?
                    {}
                    :
                    {

                        y: {

                            beginAtZero:
                                true

                        }

                    }

            }

        }
    );

}


function destroyChart(
    chart
) {

    if (chart) {

        chart.destroy();

    }

}


function renderFishCountries(
    countries
) {

    const container =
        $("fishCountries");

    container.innerHTML =
        "";


    if (
        !countries ||
        countries.length === 0
    ) {

        container.innerHTML =
            "<p>No country records available.</p>";

        return;

    }


    const max =
        Math.max(
            ...countries.map(
                x =>
                    Number(
                        x.records
                    )
            )
        );


    countries
        .slice(0, 10)
        .forEach(
            item => {

                const percent =
                    max > 0
                    ?
                    (
                        Number(
                            item.records
                        )
                        /
                        max
                    ) * 100
                    :
                    0;


                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "country-row";


                row.innerHTML = `

                    <div class="country-label">

                        <span>
                            ${escapeHtml(
                                item.country
                            )}
                        </span>

                        <strong>
                            ${formatValue(
                                item.records
                            )}
                        </strong>

                    </div>


                    <div class="prediction-bar">

                        <div
                            style="
                                width:${percent}%;
                            "
                        ></div>

                    </div>

                `;


                container.appendChild(
                    row
                );

            }
        );

}


/* ============================================================
   INTERPRETATION
   ============================================================ */

function renderInterpretation(
    items
) {

    const list =
        $("fishInterpretation");

    list.innerHTML =
        "";


    if (
        !items ||
        items.length === 0
    ) {

        list.innerHTML =
            "<li>No interpretation available.</li>";

        return;

    }


    items.forEach(
        text => {

            const li =
                document.createElement(
                    "li"
                );

            li.textContent =
                text;

            list.appendChild(
                li
            );

        }
    );

}


/* ============================================================
   FACT SHEET
   ============================================================ */

function renderFactSheet(
    text
) {

    const container =
        $("factSheet");


    if (!text) {

        container.innerHTML = `

            <p>
                Gemini fact sheet was not returned.
            </p>

        `;

        return;

    }


    container.innerHTML =
        formatFactSheet(
            text
        );

}


function formatFactSheet(
    text
) {

    const labels = [

        "Fish Name",
        "Scientific Name",
        "Habitat",
        "Nutrition",
        "Average Weight",
        "Cooking Uses",
        "Health Benefits"

    ];


    let html =
        "";


    labels.forEach(
        label => {

            const regex =
                new RegExp(
                    label +
                    "\\s*:\\s*([\\s\\S]*?)(?=\\n(?:"
                    +
                    labels.join("|")
                    +
                    ")\\s*:|$)",
                    "i"
                );


            const match =
                text.match(
                    regex
                );


            if (!match) {
                return;
            }


            html += `

                <div class="fact-card">

                    <div class="fact-label">

                        ${escapeHtml(
                            label
                        )}

                    </div>

                    <div class="fact-value">

                        ${escapeHtml(
                            match[1].trim()
                        )}

                    </div>

                </div>

            `;

        }
    );


    if (!html) {

        return `
            <div class="fact-card">
                ${escapeHtml(text)}
            </div>
        `;

    }


    return `
        <div class="fact-grid">
            ${html}
        </div>
    `;

}


/* ============================================================
   READ ALOUD
   ============================================================ */

function setupReadAloud() {

    const button =
        $("readFactSheetBtn");

    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        () => {

            const text =
                $("factSheet")
                    .innerText
                    .trim();


            if (!text) {
                return;
            }


            if (
                "speechSynthesis"
                in window
            ) {

                window.speechSynthesis.cancel();


                const utterance =
                    new SpeechSynthesisUtterance(
                        text
                    );


                utterance.lang =
                    currentLanguage === "hi"
                    ?
                    "hi-IN"
                    :
                    currentLanguage === "mr"
                    ?
                    "mr-IN"
                    :
                    "en-IN";


                window.speechSynthesis.speak(
                    utterance
                );

            }

        }
    );

}


/* ============================================================
   Q&A
   ============================================================ */

function setupQuestionButton() {

    const button =
        $("askQuestionBtn");

    const input =
        $("questionInput");


    if (!button || !input) {
        return;
    }


    button.addEventListener(
        "click",
        askQuestion
    );


    input.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
            ) {

                askQuestion();

            }

        }
    );

}


async function askQuestion() {

    const input =
        $("questionInput");

    const answerBox =
        $("qaAnswer");


    const question =
        input.value.trim();


    if (!currentSpecies) {

        answerBox.textContent =
            "Please identify a fish first.";

        return;

    }


    if (!question) {
        return;
    }


    answerBox.textContent =
        "🤔 Thinking...";


    try {

        const response =
            await fetch(
                "/api/main-ai/ask",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            question:
                                question,

                            species:
                                currentSpecies,

                            language:
                                currentLanguage,

                            session_id:
                                currentSessionId

                        })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok
            || !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Question failed."
            );

        }


        answerBox.innerHTML = `

            <div class="qa-question">

                🧑 ${escapeHtml(
                    question
                )}

            </div>


            <div class="qa-response">

                🤖 ${escapeHtml(
                    data.answer
                )}

            </div>

        `;


        input.value =
            "";


        await loadSummary();

    } catch (error) {

        answerBox.textContent =
            "Q&A error: "
            + error.message;

    }

}


/* ============================================================
   EXPLORE MORE
   ============================================================ */

function setupExploreButtons() {

    document
        .querySelectorAll(
            "[data-explore]"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const type =
                            button.dataset.explore;

                        handleExplore(
                            type
                        );

                    }
                );

            }
        );

}


async function handleExplore(
    type
) {

    const container =
        $("exploreContent");


    if (!currentSpecies) {

        container.innerHTML = `

            <div class="warning-box">

                Identify a fish first.

            </div>

        `;

        return;

    }


    if (
        type === "distribution"
    ) {

        await renderDistributionExplore();

        return;

    }


    if (
        type === "fishing"
    ) {

        await renderFishingExplore();

        return;

    }


    if (
        type === "taxonomy"
    ) {

        await renderTaxonomyExplore();

        return;

    }


    if (
        type === "nutrition"
    ) {

        await renderNutritionExplore();

        return;

    }


    if (
        type === "weather"
    ) {

        renderWeatherExplore();

        return;

    }


    if (
        type === "markets"
    ) {

        renderMarketsExplore();

        return;

    }

}


/* ============================================================
   TAXONOMY
   ============================================================ */

async function renderTaxonomyExplore() {

    const container =
        $("exploreContent");


    container.innerHTML =
        "<div class='loading'>Verifying with GBIF...</div>";


    try {

        const response =
            await fetch(
                "/api/explore/taxonomy?species="
                +
                encodeURIComponent(
                    currentSpecies
                )
            );


        const data =
            await response.json();


        if (
            !data.success
        ) {

            throw new Error(
                data.error
                ||
                "GBIF unavailable."
            );

        }


        const taxonomy =
            data.taxonomy;


        if (!taxonomy) {

            container.innerHTML =
                "<p>No GBIF taxonomy match found.</p>";

            return;

        }


        container.innerHTML = `

            <div class="evidence-box">

                <h3>
                    🧬 GBIF Taxonomy
                </h3>

                <p>

                    <strong>
                        Canonical Name:
                    </strong>

                    ${escapeHtml(
                        taxonomy.canonical_name
                    )}

                </p>

                <p>

                    <strong>
                        Family:
                    </strong>

                    ${escapeHtml(
                        taxonomy.family
                    )}

                </p>

                <p>

                    <strong>
                        Order:
                    </strong>

                    ${escapeHtml(
                        taxonomy.order
                    )}

                </p>

                <p>

                    <strong>
                        Class:
                    </strong>

                    ${escapeHtml(
                        taxonomy.class
                    )}

                </p>

                <p>

                    <strong>
                        Confidence:
                    </strong>

                    ${escapeHtml(
                        taxonomy.confidence
                    )}

                </p>

            </div>

        `;

    } catch (error) {

        container.innerHTML =
            `<div class="error-box">
                ${escapeHtml(error.message)}
            </div>`;

    }

}


/* ============================================================
   NUTRITION
   ============================================================ */

async function renderNutritionExplore() {

    const container =
        $("exploreContent");


    container.innerHTML =
        "<div class='loading'>Fetching USDA nutrition...</div>";


    try {

        const response =
            await fetch(
                "/api/explore/nutrition?species="
                +
                encodeURIComponent(
                    currentSpecies
                )
            );


        const data =
            await response.json();


        if (
            !data.success
        ) {

            throw new Error(
                data.error
                ||
                "Nutrition unavailable."
            );

        }


        const nutrition =
            data.nutrition;


        if (!nutrition) {

            container.innerHTML =
                "<p>No USDA nutrition match found.</p>";

            return;

        }


        let html =
            `<div class="evidence-box">

                <h3>
                    🥗 USDA FoodData Central
                </h3>`;


        if (
            nutrition.matched_food_name
        ) {

            html += `
                <p>
                    <strong>
                        Matched food:
                    </strong>
                    ${escapeHtml(
                        nutrition.matched_food_name
                    )}
                </p>
            `;

        }


        const values =
            nutrition.nutrients_per_100g
            || {};


        html += `
            <div class="feature-grid">
        `;


        Object.entries(
            values
        ).forEach(
            ([key, value]) => {

                html += `

                    <div class="feature-card">

                        <div class="feature-name">

                            ${escapeHtml(
                                key
                            )}

                        </div>

                        <div class="feature-value">

                            ${escapeHtml(
                                formatValue(
                                    value
                                )
                            )}

                        </div>

                    </div>

                `;

            }
        );


        html += `
            </div>
            </div>
        `;


        container.innerHTML =
            html;

    } catch (error) {

        container.innerHTML =
            `<div class="error-box">
                ${escapeHtml(error.message)}
            </div>`;

    }

}


function renderExploreMap(records, containerId = "exploreMap", title = "Fish distribution") {
    const container = $(containerId);
    if (!container) return;

    if (!ensureLeafletLoaded()) {
        container.innerHTML = `<div class="error-box map-error-message">OpenStreetMap could not be loaded. Check the internet connection.</div>`;
        return;
    }

    const validRecords = validMapRecords(records);

    try {
        if (!exploreMap) {
            exploreMap = L.map(container, {
                center: [20, 0],
                zoom: 2,
                scrollWheelZoom: true,
                worldCopyJump: true,
                preferCanvas: true
            });

            L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {
                    maxZoom: 19,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
                }
            ).addTo(exploreMap);

            exploreMapMarkers = L.layerGroup().addTo(exploreMap);
        }

        exploreMap.invalidateSize(true);
        exploreMapMarkers.clearLayers();

        if (!validRecords.length) {
            exploreMap.setView([20, 0], 2);
            return;
        }

        const bounds = [];
        validRecords.forEach(row => {
            const lat = row._latitude;
            const lon = row._longitude;
            bounds.push([lat, lon]);

            L.circleMarker([lat, lon], {
                radius: 6,
                color: "#1464d2",
                weight: 1.5,
                fillColor: "#2f7cf6",
                fillOpacity: 0.78
            }).bindPopup(`
                <div class="fish-map-popup">
                    <strong>🐟 ${escapeHtml(row.species || currentSpecies || "Fish occurrence")}</strong><br>
                    🌍 ${escapeHtml(row._country)}<br>
                    📍 ${lat.toFixed(4)}, ${lon.toFixed(4)}
                </div>
            `).addTo(exploreMapMarkers);
        });

        if (bounds.length === 1) {
            exploreMap.setView(bounds[0], 8);
        } else {
            exploreMap.fitBounds(bounds, { padding: [30, 30], maxZoom: 7 });
        }

        [100, 300].forEach(delay => {
            setTimeout(() => {
                if (exploreMap) exploreMap.invalidateSize(true);
            }, delay);
        });
    } catch (error) {
        console.error(`${title} map failed:`, error);
        container.innerHTML = `<div class="error-box map-error-message">${escapeHtml(error.message)}</div>`;
    }
}

/* ============================================================
   DISTRIBUTION
   ============================================================ */

async function renderDistributionExplore() {
    const container = $("exploreContent");
    container.innerHTML = "<div class='loading'>Loading GBIF distribution...</div>";

    try {
        const response = await fetch("/api/gbif-distribution?species=" + encodeURIComponent(currentSpecies), {cache:"no-store"});
        if (!response.ok) throw new Error(`GBIF endpoint returned HTTP ${response.status}`);
        const data = await response.json();
        if (!Array.isArray(data)) throw new Error("GBIF distribution unavailable.");

        const countries = {};
        data.forEach(item => {
            const country = getRecordCountry(item);
            countries[country] = (countries[country] || 0) + 1;
        });

        let cards = "";
        Object.entries(countries).sort((a,b)=>b[1]-a[1]).slice(0,12).forEach(([country,count])=>{
            cards += `<div class="feature-card"><div class="feature-name">${escapeHtml(country)}</div><div class="feature-value">${count.toLocaleString()}</div></div>`;
        });

        container.innerHTML = `
            <div class="evidence-box">
                <h3>🌍 GBIF Distribution</h3>
                <p>${data.length.toLocaleString()} documented occurrence records are available for <strong>${escapeHtml(currentSpecies)}</strong>.</p>
                <div class="feature-grid">${cards}</div>
            </div>
            <div class="map-panel">
                <div class="chart-heading"><div><span class="chart-kicker">OPENSTREETMAP</span><h3>🐟 Distribution of ${escapeHtml(currentSpecies)}</h3></div><span class="chart-icon">📍</span></div>
                <div id="exploreMap" class="explore-map"></div>
                <div class="chart-explanation"><strong>What this means:</strong> These markers show documented geographic occurrence locations for the predicted fish from GBIF. They describe recorded distribution, not population density or fishing suitability.</div>
            </div>`;

        exploreMap = null;
        exploreMapMarkers = null;
        renderExploreMap(data, "exploreMap", "Distribution");
    } catch (error) {
        container.innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
    }
}


/* ============================================================
   FISHING
   ============================================================ */

async function renderFishingExplore() {
    const container = $("exploreContent");
    container.innerHTML = `
        <div class="evidence-box">
            <h3>🎣 Fishing Grounds</h3>
            <p>Select a country from the GBIF occurrence records.</p>
            <select id="fishingCountrySelect"><option value="">Loading countries...</option></select>
            <div id="fishingResults"></div>
        </div>
        <div class="map-panel">
            <div class="chart-heading"><div><span class="chart-kicker">OPENSTREETMAP</span><h3>🎣 Recorded Fishing-Ground Locations</h3></div><span class="chart-icon">📍</span></div>
            <div id="fishingMap" class="explore-map"></div>
            <div class="chart-explanation"><strong>What this means:</strong> The selected country's points are GBIF-recorded locations for the identified fish. They are geographic observations and do not by themselves prove that every point is an active fishing ground.</div>
        </div>`;

    try {
        const response = await fetch("/api/gbif-distribution?species=" + encodeURIComponent(currentSpecies), {cache:"no-store"});
        if (!response.ok) throw new Error(`GBIF endpoint returned HTTP ${response.status}`);
        const points = await response.json();
        if (!Array.isArray(points)) throw new Error("GBIF distribution unavailable.");

        const mapped = validMapRecords(points);
        const countries = {};
        mapped.forEach(point => {
            countries[point._country] = (countries[point._country] || 0) + 1;
        });

        const select = $("fishingCountrySelect");
        select.innerHTML = "";
        const entries = Object.entries(countries).sort((a,b)=>b[1]-a[1] || a[0].localeCompare(b[0]));

        if (!entries.length) {
            select.innerHTML = `<option value="">No mapped countries</option>`;
            $("fishingResults").innerHTML = "<p>No georeferenced GBIF records are available.</p>";
            exploreMap = null; exploreMapMarkers = null;
            renderExploreMap([], "fishingMap", "Fishing grounds");
            return;
        }

        entries.forEach(([country,count])=>{
            const option = document.createElement("option");
            option.value = country;
            option.textContent = `${country} (${count})`;
            select.appendChild(option);
        });

        const updateFishingMap = () => {
            const country = select.value;
            const selected = mapped.filter(point => point._country === country);
            $("fishingResults").innerHTML = `<p><strong>${selected.length.toLocaleString()}</strong> georeferenced GBIF records found for <strong>${escapeHtml(country)}</strong>.</p>`;
            exploreMap = null; exploreMapMarkers = null;
            renderExploreMap(selected, "fishingMap", "Fishing grounds");
        };

        select.addEventListener("change", updateFishingMap);
        updateFishingMap();
    } catch (error) {
        $("fishingResults").innerHTML = `<div class="error-box">${escapeHtml(error.message)}</div>`;
    }
}


/* ============================================================
   WEATHER
   ============================================================ */

function renderWeatherExplore() {

    const container =
        $("exploreContent");


    container.innerHTML = `

        <div class="evidence-box">

            <h3>
                ☁️ Weather
            </h3>

            <input
                id="weatherCity"
                placeholder="Enter city e.g. Mumbai"
            >

            <button
                id="weatherButton"
            >
                Get Weather
            </button>

            <div
                id="weatherResult"
            ></div>

        </div>

    `;


    $("weatherButton")
        .addEventListener(
            "click",
            async () => {

                const city =
                    $("weatherCity")
                        .value
                        .trim();


                if (!city) {
                    return;
                }


                $("weatherResult")
                    .textContent =
                    "Loading...";


                try {

                    const response =
                        await fetch(
                            "/api/explore/weather?city="
                            +
                            encodeURIComponent(
                                city
                            )
                        );


                    const data =
                        await response.json();


                    if (
                        !data.success
                    ) {

                        throw new Error(
                            data.error
                        );

                    }


                    const weather =
                        data.weather;


                    $("weatherResult")
                        .innerHTML = `

                            <div class="feature-grid">

                                <div class="feature-card">

                                    <div class="feature-name">
                                        Temperature
                                    </div>

                                    <div class="feature-value">
                                        ${escapeHtml(
                                            weather.temperature_c
                                        )}°C
                                    </div>

                                </div>

                                <div class="feature-card">

                                    <div class="feature-name">
                                        Humidity
                                    </div>

                                    <div class="feature-value">
                                        ${escapeHtml(
                                            weather.humidity_pct
                                        )}%
                                    </div>

                                </div>

                                <div class="feature-card">

                                    <div class="feature-name">
                                        Condition
                                    </div>

                                    <div class="feature-value">
                                        ${escapeHtml(
                                            weather.description
                                        )}
                                    </div>

                                </div>

                            </div>

                        `;

                } catch (error) {

                    $("weatherResult")
                        .innerHTML =
                        `<div class="error-box">
                            ${escapeHtml(error.message)}
                        </div>`;

                }

            }
        );

}


/* ============================================================
   MARKETS
   ============================================================ */

function renderMarketsExplore() {

    const container =
        $("exploreContent");


    container.innerHTML = `

        <div class="evidence-box">

            <h3>
                📍 Nearby Seafood Markets
            </h3>

            <input
                id="marketCity"
                placeholder="Enter city e.g. Mumbai"
            >

            <button
                id="marketButton"
            >
                Find Markets
            </button>

            <div
                id="marketResults"
            ></div>

        </div>

    `;


    $("marketButton")
        .addEventListener(
            "click",
            async () => {

                const city =
                    $("marketCity")
                        .value
                        .trim();


                if (!city) {
                    return;
                }


                $("marketResults")
                    .textContent =
                    "Searching...";


                try {

                    const response =
                        await fetch(
                            "/api/explore/markets?city="
                            +
                            encodeURIComponent(
                                city
                            )
                        );


                    const data =
                        await response.json();


                    if (
                        !data.success
                    ) {

                        throw new Error(
                            data.error
                        );

                    }


                    const places =
                        data.places
                        || [];


                    if (
                        places.length === 0
                    ) {

                        $("marketResults")
                            .textContent =
                            "No nearby seafood markets found.";

                        return;

                    }


                    $("marketResults")
                        .innerHTML = `

                            <div class="market-list">

                                ${
                                    places
                                    .map(
                                        place => `

                                            <div class="market-item">

                                                <strong>
                                                    ${escapeHtml(
                                                        place.name
                                                    )}
                                                </strong>

                                                <span>
                                                    ${escapeHtml(
                                                        place.type
                                                    )}
                                                </span>

                                            </div>

                                        `
                                    )
                                    .join("")
                                }

                            </div>

                        `;

                } catch (error) {

                    $("marketResults")
                        .innerHTML =
                        `<div class="error-box">
                            ${escapeHtml(error.message)}
                        </div>`;

                }

            }
        );

}


/* ============================================================
   SUMMARY
   ============================================================ */

async function loadSummary() {

    try {

        const response =
            await fetch(
                "/api/summary"
            );


        const data =
            await response.json();


        $("summaryImages")
            .textContent =
            Number(
                data.dataset_images
                || 0
            ).toLocaleString();


        $("summarySpecies")
            .textContent =
            data.species
            || 0;


        $("summaryFeatures")
            .textContent =
            data.api_feature_count
            || 0;


        $("predictionCount")
            .textContent =
            data.prediction_count
            || 0;


        $("qaCount")
            .textContent =
            data.qa_count
            || 0;


    } catch (error) {

        console.error(
            "Summary error:",
            error
        );

    }

}


/* ============================================================
   SPECIES DISTRIBUTION
   ============================================================ */

async function loadSpeciesDistribution() {

    try {

        const response =
            await fetch(
                "/api/species-distribution"
            );


        const data =
            await response.json();


        const labels =
            data.map(
                x => x.species
            );


        const values =
            data.map(
                x => x.images
            );


        destroyChart(
            speciesDistributionChart
        );


        speciesDistributionChart =
            createChart(
                "speciesDistributionChart",
                "bar",
                labels,
                values,
                "Images"
            );


        const select =
            $("datasetSpeciesFilter");


        if (select) {

            data.forEach(
                item => {

                    const option =
                        document.createElement(
                            "option"
                        );

                    option.value =
                        item.species;

                    option.textContent =
                        item.species;

                    select.appendChild(
                        option
                    );

                }
            );

        }

    } catch (error) {

        console.error(
            error
        );

    }

}


/* ============================================================
   API EVIDENCE
   ============================================================ */

async function loadApiEvidence() {

    try {

        const response =
            await fetch(
                "/api/api-evidence"
            );


        const data =
            await response.json();


        const container =
            $("apiEvidenceCards");


        container.innerHTML =
            "";


        (
            data.apis
            || []
        ).forEach(
            api => {

                const card =
                    document.createElement(
                        "div"
                    );

                card.className =
                    "api-card";


                card.innerHTML = `

                    <h3>
                        ${escapeHtml(
                            api.name
                        )}
                    </h3>

                    <strong>
                        ${escapeHtml(
                            api.category
                        )}
                    </strong>

                    <p>
                        ${escapeHtml(
                            api.description
                        )}
                    </p>

                `;


                container.appendChild(
                    card
                );

            }
        );

    } catch (error) {

        console.error(
            error
        );

    }

}


/* ============================================================
   FUSION RESULTS
   ============================================================ */

async function loadFusionResults() {

    try {

        const response =
            await fetch(
                "/api/fusion-results"
            );


        const data =
            await response.json();


        const container =
            $("fusionResults");


        if (
            !Array.isArray(data)
            || data.length === 0
        ) {

            container.innerHTML =
                "<p>No fusion results available.</p>";

            return;

        }


        const columns =
            Object.keys(
                data[0]
            );


        let html =
            "<div class='table-wrapper'><table><thead><tr>";


        columns.forEach(
            column => {

                html +=
                    `<th>${escapeHtml(
                        prettyName(column)
                    )}</th>`;

            }
        );


        html +=
            "</tr></thead><tbody>";


        data.forEach(
            row => {

                html += "<tr>";


                columns.forEach(
                    column => {

                        html +=
                            `<td>${escapeHtml(
                                formatValue(
                                    row[column]
                                )
                            )}</td>`;

                    }
                );


                html +=
                    "</tr>";

            }
        );


        html +=
            "</tbody></table></div>";


        container.innerHTML =
            html;

    } catch (error) {

        console.error(
            error
        );

    }

}


/* ============================================================
   GENERAL EDA
   ============================================================ */

async function loadGeneralEDA() {

    try {

        const response =
            await fetch(
                "/api/eda?species=All"
            );


        const data =
            await response.json();


        const features =
            data.numeric
            || [];


        const selected =
            features.slice(
                0,
                15
            );


        destroyChart(
            generalEdaChart
        );


        generalEdaChart =
            createChart(
                "generalEdaChart",
                "bar",
                selected.map(
                    x =>
                        prettyName(
                            x.feature
                        )
                ),
                selected.map(
                    x =>
                        x.mean
                ),
                "Mean"
            );

        const explanation =
            $("generalEdaExplanation");

        if (explanation) {

            explanation.innerHTML = `
                <strong>What this means:</strong>
                The chart summarizes the mean of the selected numeric
                features in the fused fish dataset. It helps compare
                dataset-level fish attributes; the displayed features
                are not all measured in the same unit.
            `;

        }

    } catch (error) {

        console.error(
            error
        );

    }

}


/* ============================================================
   OPENSTREETMAP / LEAFLET MAP
   ============================================================ */

function getRecordLatitude(row) {
    const value = row?.latitude ?? row?.lat ?? row?.decimalLatitude;
    const n = Number(value);
    return Number.isFinite(n) && n >= -90 && n <= 90 ? n : null;
}

function getRecordLongitude(row) {
    const value = row?.longitude ?? row?.lon ?? row?.lng ?? row?.decimalLongitude;
    const n = Number(value);
    return Number.isFinite(n) && n >= -180 && n <= 180 ? n : null;
}

function getRecordCountry(row) {
    return String(
        row?.country
        ?? row?.gbif_top_country
        ?? row?.gbif_country
        ?? "Unknown"
    ).trim() || "Unknown";
}

function validMapRecords(records) {
    if (!Array.isArray(records)) return [];

    return records
        .map(row => ({
            ...row,
            _latitude: getRecordLatitude(row),
            _longitude: getRecordLongitude(row),
            _country: getRecordCountry(row)
        }))
        .filter(row =>
            row._latitude !== null &&
            row._longitude !== null
        );
}

function updateMapStatus(message, warning = false) {
    const status = $("gbifMapStatus");
    if (!status) return;

    status.textContent = message;
    status.classList.toggle("map-warning", warning);
}

function ensureLeafletLoaded() {
    return typeof window.L !== "undefined";
}

function renderGBIFMap(records) {

    const mapContainer = $("gbifMap");
    if (!mapContainer) return;

    // The CSS must give Leaflet a real height before L.map() is called.
    mapContainer.style.width = "100%";
    mapContainer.style.height = "460px";
    mapContainer.style.minHeight = "460px";

    if (!ensureLeafletLoaded()) {
        updateMapStatus(
            "OpenStreetMap/Leaflet did not load. Check the internet connection and refresh.",
            true
        );
        mapContainer.innerHTML = `
            <div class="error-box map-error-message">
                OpenStreetMap could not be initialized because Leaflet is unavailable.
            </div>
        `;
        return;
    }

    const validRecords = validMapRecords(records);

    try {
        if (!gbifMap) {
            gbifMap = L.map(mapContainer, {
                center: [20, 0],
                zoom: 2,
                scrollWheelZoom: true,
                zoomControl: true,
                worldCopyJump: true,
                preferCanvas: true
            });

            L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {
                    maxZoom: 19,
                    minZoom: 1,
                    attribution:
                        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
                    crossOrigin: true
                }
            ).addTo(gbifMap);

            gbifMapMarkers = L.layerGroup().addTo(gbifMap);
        }

        if (!gbifMapMarkers) {
            gbifMapMarkers = L.layerGroup().addTo(gbifMap);
        }

        gbifMap.invalidateSize(true);
        gbifMapMarkers.clearLayers();

        if (validRecords.length === 0) {
            gbifMap.setView([20, 0], 2);
            updateMapStatus(
                "No GBIF occurrence records with valid latitude/longitude are available.",
                true
            );

            const explanation = $("gbifMapExplanation");
            if (explanation) {
                explanation.innerHTML = `
                    <strong>What this means:</strong>
                    The selected fish has no usable georeferenced GBIF records for this view.
                `;
            }
            return;
        }

        const bounds = [];

        validRecords.forEach(row => {
            const latitude = row._latitude;
            const longitude = row._longitude;
            bounds.push([latitude, longitude]);

            const species =
                row.species ||
                row.gbif_canonical_name ||
                currentSpecies ||
                "Fish occurrence";

            const country = row._country;

            L.circleMarker(
                [latitude, longitude],
                {
                    radius: 6,
                    color: "#1464d2",
                    weight: 1.5,
                    fillColor: "#2f7cf6",
                    fillOpacity: 0.78
                }
            )
                .bindPopup(`
                    <div class="fish-map-popup">
                        <strong>🐟 ${escapeHtml(species)}</strong><br>
                        🌍 ${escapeHtml(country)}<br>
                        📍 ${latitude.toFixed(4)}, ${longitude.toFixed(4)}
                    </div>
                `)
                .addTo(gbifMapMarkers);
        });

        if (bounds.length === 1) {
            gbifMap.setView(bounds[0], 8);
        } else {
            gbifMap.fitBounds(bounds, {
                padding: [35, 35],
                maxZoom: 7
            });
        }

        updateMapStatus(
            `${validRecords.length.toLocaleString()} georeferenced fish occurrence records loaded.`
        );

        const explanation = $("gbifMapExplanation");
        if (explanation) {
            explanation.innerHTML = `
                <strong>What this means:</strong>
                The map displays ${validRecords.length.toLocaleString()} documented GBIF occurrence
                locations for the selected fish records. Each marker represents a recorded
                observation location; it is not a population-density or habitat-suitability map.
            `;
        }

        // Leaflet must recalculate dimensions after the section becomes visible.
        [100, 300, 700].forEach(delay => {
            setTimeout(() => {
                if (gbifMap) {
                    gbifMap.invalidateSize(true);
                }
            }, delay);
        });

    } catch (error) {
        console.error("GBIF map initialization failed:", error);
        updateMapStatus(
            `Map initialization failed: ${error.message}`,
            true
        );
    }
}

function refreshGBIFMapAfterLayout() {
    if (!gbifMap) {
        if (Array.isArray(gbifAllRecords) && gbifAllRecords.length) {
            renderGBIFMap(gbifAllRecords);
        }
        return;
    }

    gbifMap.invalidateSize(true);

    const mapSection = $("gbif-distribution");
    if (mapSection && mapSection.classList.contains("active-section")) {
        setTimeout(() => {
            gbifMap.invalidateSize(true);
        }, 150);
    }
}


/* ============================================================
   GBIF OVERVIEW
   ============================================================ */



function populateGBIFCountryFilter(records) {
    const select = $("gbifCountrySelect");
    if (!select) return;

    const counts = {};
    validMapRecords(records).forEach(row => {
        const country = row._country;
        counts[country] = (counts[country] || 0) + 1;
    });

    const current = select.value || "All";

    select.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "All";
    allOption.textContent = `All Countries (${validMapRecords(records).length})`;
    select.appendChild(allOption);

    Object.entries(counts)
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .forEach(([country, count]) => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = `${country} (${count})`;
            select.appendChild(option);
        });

    if ([...select.options].some(option => option.value === current)) {
        select.value = current;
    } else {
        select.value = "All";
    }

    updateGBIFCountryCount(select.value);
}

function updateGBIFCountryCount(country) {
    const countEl = $("gbifCountryCount");
    const selectedEl = $("gbifSelectedRecords");
    const records = validMapRecords(gbifAllRecords);

    const filtered = country && country !== "All"
        ? records.filter(row => row._country === country)
        : records;

    if (countEl) {
        const countries = new Set(records.map(row => row._country)).size;
        countEl.textContent = `${countries.toLocaleString()} countries`;
    }

    if (selectedEl) {
        selectedEl.textContent = `${filtered.length.toLocaleString()} mapped records`;
    }
}

function setupGBIFCountryFilter() {
    const select = $("gbifCountrySelect");
    if (!select || select.dataset.bound === "1") return;

    select.dataset.bound = "1";

    select.addEventListener("change", () => {
        const country = select.value || "All";
        const records = validMapRecords(gbifAllRecords);

        const filtered = country === "All"
            ? records
            : records.filter(row => row._country === country);

        updateGBIFCountryCount(country);
        renderGBIFMap(filtered);
        renderGBIFTable(filtered);
    });
}

function renderGBIFTable(data) {
    const table = $("gbifTable");
    if (!table) return;

    if (!Array.isArray(data) || data.length === 0) {
        table.innerHTML = `
            <tbody>
                <tr><td>No records for the selected country.</td></tr>
            </tbody>
        `;
        return;
    }

    const columns = Object.keys(data[0]).filter(
        column => !column.startsWith("_")
    );

    let html = "<thead><tr>";
    columns.slice(0, 8).forEach(column => {
        html += `<th>${escapeHtml(prettyName(column))}</th>`;
    });
    html += "</tr></thead><tbody>";

    data.slice(0, 100).forEach(row => {
        html += "<tr>";
        columns.slice(0, 8).forEach(column => {
            html += `<td>${escapeHtml(formatValue(row[column]))}</td>`;
        });
        html += "</tr>";
    });

    html += "</tbody>";
    table.innerHTML = html;
}

async function loadGBIFOverview() {
    try {
        const response = await fetch(
            "/api/gbif-distribution?species=All",
            { cache: "no-store" }
        );

        if (!response.ok) {
            throw new Error(`GBIF endpoint returned HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data)) {
            throw new Error("GBIF distribution endpoint did not return an array.");
        }

        gbifAllRecords = data;

        setupGBIFCountryFilter();
        populateGBIFCountryFilter(data);

        const select = $("gbifCountrySelect");
        const country = select?.value || "All";

        const filtered = country === "All"
            ? validMapRecords(data)
            : validMapRecords(data).filter(row => row._country === country);

        renderGBIFMap(filtered);
        renderGBIFTable(filtered);
        updateGBIFCountryCount(country);

        const container = $("gbifDistributionSummary");
        if (container) {
            const mapped = validMapRecords(data).length;
            const countries = new Set(
                validMapRecords(data).map(row => row._country)
            ).size;

            container.innerHTML = `
                <div class="metric-grid">
                    <div class="metric-card">
                        <span>Available Records</span>
                        <strong>${data.length.toLocaleString()}</strong>
                    </div>
                    <div class="metric-card">
                        <span>Mapped Occurrences</span>
                        <strong>${mapped.toLocaleString()}</strong>
                    </div>
                    <div class="metric-card">
                        <span>Recorded Countries</span>
                        <strong>${countries.toLocaleString()}</strong>
                    </div>
                </div>
            `;
        }

    } catch (error) {
        console.error("GBIF overview failed:", error);

        updateMapStatus(
            `Could not load GBIF distribution: ${error.message}`,
            true
        );

        const container = $("gbifDistributionSummary");
        if (container) {
            container.innerHTML = `
                <div class="error-box">
                    ${escapeHtml(error.message)}
                </div>
            `;
        }
    }
}


/* ============================================================
   DATASET CONTROLS
   ============================================================ */

function setupDatasetControls() {

    const button =
        $("datasetSearchBtn");


    if (button) {

        button.addEventListener(
            "click",
            () => {

                loadFusedDataset(
                    1
                );

            }
        );

    }


    const select =
        $("datasetSpeciesFilter");


    if (select) {

        select.addEventListener(
            "change",
            () => {

                loadFusedDataset(
                    1
                );

            }
        );

    }


    loadFusedDataset(
        1
    );

}


async function loadFusedDataset(
    page
) {

    const species =
        $("datasetSpeciesFilter")
            ?.value
        || "All";


    const search =
        $("datasetSearch")
            ?.value
            .trim()
        || "";


    try {

        const url =
            "/api/fused-data"
            +
            "?page="
            +
            page
            +
            "&page_size=25"
            +
            "&species="
            +
            encodeURIComponent(
                species
            )
            +
            "&search="
            +
            encodeURIComponent(
                search
            );


        const response =
            await fetch(
                url
            );


        const data =
            await response.json();


        renderDatasetTable(
            data
        );


        renderPagination(
            data
        );


    } catch (error) {

        console.error(
            error
        );

    }

}


function renderDatasetTable(
    data
) {

    const table =
        $("fusedTable");


    if (
        !data.rows
        ||
        data.rows.length === 0
    ) {

        table.innerHTML =
            "<tr><td>No records found.</td></tr>";

        return;

    }


    const columns =
        data.columns;


    let html =
        "<thead><tr>";


    columns.forEach(
        column => {

            html +=
                `<th>${escapeHtml(
                    prettyName(column)
                )}</th>`;

        }
    );


    html +=
        "</tr></thead><tbody>";


    data.rows.forEach(
        row => {

            html += "<tr>";


            columns.forEach(
                column => {

                    html +=
                        `<td>${escapeHtml(
                            formatValue(
                                row[column]
                            )
                        )}</td>`;

                }
            );


            html +=
                "</tr>";

        }
    );


    html +=
        "</tbody>";


    table.innerHTML =
        html;

}


function renderPagination(
    data
) {

    const container =
        $("datasetPagination");


    const totalPages =
        Math.ceil(
            data.total
            /
            data.page_size
        );


    container.innerHTML =
        "";


    if (
        totalPages <= 1
    ) {

        return;

    }


    for (
        let page = 1;
        page <= totalPages;
        page++
    ) {

        if (
            page > 10
            &&
            page !== data.page
        ) {

            continue;

        }


        const button =
            document.createElement(
                "button"
            );


        button.textContent =
            page;


        if (
            page === data.page
        ) {

            button.classList.add(
                "current-page"
            );

        }


        button.addEventListener(
            "click",
            () =>
                loadFusedDataset(
                    page
                )
        );


        container.appendChild(
            button
        );

    }

}