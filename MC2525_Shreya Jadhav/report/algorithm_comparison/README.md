# Seven-algorithm comparison on the fused FemCare dataset

This is a reproducible **academic analysis**, not a clinical decision system. Run it from the project root with:

```powershell
python scripts/compare_seven_algorithms.py
```

If `python` is not on PATH on this computer, use `C:\Users\SHREYA\anaconda3\python.exe` in its place. The script reads `data/api_fusion/final/femcare_final_cleaned.csv` and regenerates the score CSV, metadata JSON, and two charts in this folder. It needs `pandas`, `numpy`, `matplotlib`, and `scikit-learn` (listed in the root `requirements.txt`).

## What was predicted

The seven algorithms do not all solve the same type of problem, so they are reported in two groups:

| Group | Algorithms | Target | Main measures |
| --- | --- | --- | --- |
| Classification | Naive Bayes, Random Forest, Decision Tree, Logistic Regression | Is `pain_level` **7 or higher**? | Precision, recall, F1; also accuracy and ROC-AUC |
| Regression | Simple Linear, Multiple Linear, Polynomial (degree 2) | Exact `pain_level` score | Mean absolute error (MAE), root mean squared error (RMSE), R² |

The original pain scores in this file range from 1 to 10. The high-pain cutoff of 7 is an **analysis choice**, not a clinical threshold. Classification and regression scores must not be ranked against one another.

## Data and fair test

The cleaned fused file has **17,976 rows and 56 columns**. A fixed 80/20 split by `user_id` put **1,600 users / 14,400 rows** in training and **400 different users / 3,576 rows** in testing. No user appears in both sets. The high-pain rate was **23.94%** in training and **23.46%** in testing. The script uses random seed 42. Missing-value filling, category encoding, and scaling are learned from training rows only.

All four classifiers and multiple linear regression use the same 21 selected input columns: age, BMI, usual sleep, caffeine, water intake, birth control, PCOS diagnosis, baseline stress, Census median household income, four CDC PLACES prevalence measures, four historical weather measures, diet quality, exercise frequency, alcohol consumption, and smoking status. Simple linear regression and polynomial regression both use only **baseline stress**; the polynomial adds the squared term. This makes the two one-variable regression models directly comparable, while multiple regression deliberately tests whether additional information helps.

We excluded `pain_level` from inputs because it is the answer; user and state identifiers to avoid memorization; same-cycle symptoms and outcomes such as mood, work hours lost, and overall health score because they could leak information about the answer; and redundant population/coordinate fields. The full selected/excluded list is in `comparison_metadata.json`. Census and CDC values are state-level context, not individual measurements. Weather is attached by historical date and a representative state location, so these are **retrospective associations**, not evidence of causality or a ready-to-use future forecast.

## Results on the held-out users

### Classification: high pain (7–10)

| Algorithm | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naive Bayes | 0.764 | 0.494 | 0.262 | 0.343 | 0.729 |
| Random Forest | 0.775 | 0.596 | 0.122 | 0.202 | 0.737 |
| Decision Tree | 0.755 | 0.466 | **0.297** | **0.363** | 0.686 |
| Logistic Regression | **0.778** | 0.566 | 0.236 | 0.333 | **0.753** |

The positive class is only 23.46% of test rows. A model that always predicts “not high pain” would get about **76.54% accuracy**, but identify **zero** high-pain cases. Thus, accuracy alone is misleading. Decision Tree had the best F1 and recall among these four; Logistic Regression had the best accuracy and ROC-AUC. All four have low recall at the default 0.5 probability threshold, so **none should be described as reliable high-pain detection**.

### Regression: exact pain score

| Algorithm | MAE (points; lower is better) | RMSE (points) | R² |
| --- | ---: | ---: | ---: |
| Simple Linear Regression | 1.584 | 1.942 | 0.223 |
| Multiple Linear Regression | **1.524** | **1.871** | **0.279** |
| Polynomial Regression, degree 2 | 1.585 | 1.942 | 0.223 |

Multiple Linear Regression gave the lowest average error on this split, but its predictions were still off by about **1.52 pain-score points** on average. Adding a squared baseline-stress term did not improve the one-variable model. These are observed test results, not proof that one algorithm is universally best.

## Files to show the professor

| File | Purpose |
| --- | --- |
| `scripts/compare_seven_algorithms.py` | Executable code: inputs, 80/20 user split, preprocessing, seven model fits, scoring, and output generation |
| `report/algorithm_comparison/seven_algorithm_scores.csv` | Exact numeric results for all seven models |
| `report/algorithm_comparison/comparison_metadata.json` | Dataset shape, target definitions, split counts, selected/excluded fields, and limitations |
| `report/algorithm_comparison/classification_f1.png` | Classification comparison chart |
| `report/algorithm_comparison/regression_mae.png` | Regression comparison chart |
| `data/api_fusion/final/femcare_final_cleaned.csv` | The fused input dataset |

This is one fixed hold-out split without hyperparameter search, confidence intervals, or external validation. For a research-grade result, add repeated user-group cross-validation, a genuinely prospective test set, calibration/threshold analysis, and a clear data-origin assessment before claiming generalization.
