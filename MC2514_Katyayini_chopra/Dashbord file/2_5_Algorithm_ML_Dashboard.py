
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ml_model_service import evaluate_models

st.set_page_config(
    page_title="FixAI | 5 Algorithm Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Five-Algorithm ML Dashboard")
st.caption("FixAI Maharashtra · Experimental defect-category classification")


# --------------------------------------------------
# 0. LATEST UPLOADED IMAGE PREDICTION
# --------------------------------------------------

latest_fused = st.session_state.get("fused_data") or {}
latest_ml = latest_fused.get("ml_model_analysis") or {}

st.subheader("0. Latest uploaded-image prediction")

if latest_ml.get("predictions"):

    left, right = st.columns([2, 1])

    with left:
        st.write(
            "The uploaded image was first interpreted by the "
            "image-analysis service. Its extracted text features "
            "were then passed to all five classifiers."
        )

        prediction_rows = [
            {
                "Algorithm": name,
                "Predicted defect": prediction
            }
            for name, prediction in latest_ml["predictions"].items()
        ]

        st.dataframe(
            prediction_rows,
            hide_index=True,
            use_container_width=True
        )

    with right:
        st.metric(
            "Consensus category",
            latest_ml.get("consensus", "Unavailable")
        )

        st.metric(
            "Models agreeing",
            f"{latest_ml.get('votes', 0)}/"
            f"{latest_ml.get('total_models', 5)}"
        )

        st.caption(
            "Votes represent model agreement, not a probability "
            "or diagnostic certainty."
        )

    st.caption(
        latest_ml.get(
            "warning",
            "Experimental ML output; verify with image evidence "
            "and a professional."
        )
    )

elif latest_ml.get("error"):

    st.warning(
        "The latest diagnosis could not run the five-model "
        "prediction: " + str(latest_ml["error"])
    )

else:

    st.info(
        "No uploaded-image prediction is available in this session yet. "
        "Return to the FixAI home page, upload a defect image and "
        "submit a diagnosis. Then reopen this dashboard to see "
        "the five predictions here."
    )


# --------------------------------------------------
# 1. EVALUATE FIVE ML ALGORITHMS
# --------------------------------------------------

@st.cache_resource(
    show_spinner="Training and evaluating the five ML algorithms..."
)
def get_evaluation():
    return evaluate_models()


try:
    evaluation = get_evaluation()

except Exception as exc:
    st.error(f"Could not evaluate the models: {exc}")
    st.stop()


# --------------------------------------------------
# 2. DATASET INFORMATION
# --------------------------------------------------

st.warning(
    "Research limitation: the current fused dataset contains only "
    f"{evaluation['records_total']} labelled rows. This evaluation uses "
    f"{evaluation['records_evaluated']} rows from categories with at least "
    "3 examples. It is a small experimental baseline, not proof of "
    "real-world diagnostic accuracy. Some example descriptions contain "
    "wording closely related to their defect labels, which may make "
    "the scores optimistic."
)

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Total labelled records",
    evaluation["records_total"]
)

m2.metric(
    "Records evaluated",
    evaluation["records_evaluated"]
)

m3.metric(
    "Defect classes evaluated",
    len(evaluation["labels"])
)

m4.metric(
    "Stratified CV folds",
    evaluation["folds"]
)


# --------------------------------------------------
# 3. ALGORITHMS COMPARED
# --------------------------------------------------

st.subheader("1. Algorithms compared")

st.write(
    "All five algorithms use the same text inputs "
    "(work type, building area, element and defect description) "
    "converted into TF-IDF features."
)

st.dataframe(
    pd.DataFrame({
        "Algorithm": list(evaluation["results"].keys()),
        "Method": [
            "Linear classification",
            "Rule-based tree splits",
            "Ensemble of decision trees",
            "Maximum-margin classifier",
            "Nearest-neighbour similarity",
        ],
    }),
    hide_index=True,
    use_container_width=True
)


# --------------------------------------------------
# 4. PERFORMANCE COMPARISON
# --------------------------------------------------

st.subheader("2. Performance comparison")

rows = []

for name, item in evaluation["results"].items():

    rows.append({
        "Algorithm": name,
        **{
            k: round(v, 3)
            for k, v in item["metrics"].items()
        }
    })

metrics_df = pd.DataFrame(rows).set_index("Algorithm")

st.dataframe(
    metrics_df.style.format("{:.3f}").highlight_max(
        subset=["F1 (macro)"],
        axis=0
    ),
    use_container_width=True
)

st.markdown("**Metric comparison (0 to 1; higher is better)**")

chart_df = metrics_df[
    [
        "Accuracy",
        "Precision (macro)",
        "Recall (macro)",
        "F1 (macro)"
    ]
]

st.bar_chart(
    chart_df,
    y=list(chart_df.columns),
    use_container_width=True
)


# --------------------------------------------------
# 5. BEST PERFORMING MODEL
# --------------------------------------------------

best = evaluation["best_model"]

best_score = evaluation["results"][best]["metrics"]["F1 (macro)"]

st.success(
    f"Best model on this small cross-validation run: "
    f"**{best}** (Macro F1 = {best_score:.3f})."
)

st.caption(
    "The winner is based on macro F1 so each evaluated defect "
    "class contributes equally. Small dataset results can change "
    "substantially when new records are added."
)


# --------------------------------------------------
# 6. CONFUSION MATRICES
# --------------------------------------------------

st.subheader("3. Confusion matrices")

selected = st.selectbox(
    "Choose an algorithm",
    list(evaluation["results"].keys())
)

fig, ax = plt.subplots(figsize=(7, 5))

# Convert nested list into NumPy array.
# This fixes the confusion matrix plotting error.

cm = np.asarray(
    evaluation["results"][selected]["confusion_matrix"],
    dtype=int
)

ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=evaluation["labels"]
).plot(
    ax=ax,
    cmap="Blues",
    colorbar=False,
    xticks_rotation=35
)

ax.set_title(
    f"{selected} — out-of-fold predictions"
)

fig.tight_layout()

st.pyplot(fig)

plt.close(fig)


# --------------------------------------------------
# 7. DATASET CLASS DISTRIBUTION
# --------------------------------------------------

st.subheader("4. Dataset class distribution")

class_df = pd.DataFrame(
    [
        {
            "Defect category": k,
            "Records": v,
            "Evaluation status": (
                "Included"
                if k in evaluation["labels"]
                else "Excluded: fewer than 3 records"
            )
        }
        for k, v in evaluation["class_counts"].items()
    ]
).sort_values(
    "Records",
    ascending=False
)

st.bar_chart(
    class_df.set_index("Defect category")["Records"]
)

st.dataframe(
    class_df,
    hide_index=True,
    use_container_width=True
)


# --------------------------------------------------
# 8. EXCLUDED CLASSES
# --------------------------------------------------

if evaluation["excluded_classes"]:

    st.info(
        "Not evaluated: " + ", ".join(
            f"{label} ({count})"
            for label, count
            in evaluation["excluded_classes"].items()
        ) +
        ". These classes need more labelled examples "
        "before a fair test is possible."
    )


# --------------------------------------------------
# 9. CLASSIFICATION REPORT
# --------------------------------------------------

with st.expander("View cross-validation classification report"):

    report = evaluation["results"][selected]["classification_report"]

    report_df = pd.DataFrame(report).T

    st.dataframe(
        report_df.round(3),
        use_container_width=True
    )


# --------------------------------------------------
# 10. FOOTER
# --------------------------------------------------

st.caption(
    "Evaluation method: stratified 3-fold cross-validation "
    "(or fewer folds if required by the smallest included class). "
    "Metrics are computed from out-of-fold predictions."
)
