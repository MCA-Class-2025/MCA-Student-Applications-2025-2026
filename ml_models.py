"""Train/evaluate the requested eight classical ML models on the fused interior dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, PolynomialFeatures
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.base import clone

CLASSIFICATION_MODELS = ["Naive Bayes", "Support Vector Machine (SVM)", "Decision Tree", "Random Forest", "Logistic Regression"]
REGRESSION_MODELS = ["Linear Regression", "Multiple Linear Regression", "Polynomial Regression"]


def _feature_columns(df: pd.DataFrame, target: str):
    excluded = {target, "interior_image_id", "material_image_id", "product_url", "color_palette", "Image_id", "image_id", "design_description", "user_preference", "product_name"}
    candidates = [c for c in df.columns if c not in excluded]
    # Avoid near-unique identifiers/free-form fields while retaining fused design and product metadata.
    return [c for c in candidates if df[c].nunique(dropna=True) <= min(100, max(20, int(len(df) * .25)))]


def _preprocessor(X: pd.DataFrame, scale=True):
    numeric = X.select_dtypes(include=np.number).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler() if scale else "passthrough")])
    categorical_pipe = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("num", numeric_pipe, numeric), ("cat", categorical_pipe, categorical)], remainder="drop")


def train_evaluate(fused_path: str, decor_path: str | None = None):
    """Returns result rows, fitted model summaries and dataset metadata."""
    df = pd.read_csv(fused_path)
    if decor_path:
        try:
            decor = pd.read_csv(decor_path)
            # Use fused product/design records as the primary training table; append decor rows only
            # when their schema overlaps and the records are not already present.
            shared = [c for c in df.columns if c in decor.columns]
            if shared:
                df = pd.concat([df, decor[shared]], ignore_index=True).drop_duplicates().reset_index(drop=True)
        except Exception:
            pass

    results = []
    fitted = {}
    # Five classification algorithms predict the interior style from fused product/design features.
    if "style_tags" in df.columns:
        cdf = df.dropna(subset=["style_tags"]).copy()
        cols = _feature_columns(cdf, "style_tags")
        X, y = cdf[cols], cdf["style_tags"].astype(str)
        if len(y) >= 20 and y.nunique() >= 2:
            stratify = y if y.value_counts().min() >= 2 else None
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42, stratify=stratify)
            prep = _preprocessor(X_train)
            classifiers = {
                "Naive Bayes": GaussianNB(),
                "Support Vector Machine (SVM)": SVC(kernel="rbf", C=2.0, class_weight="balanced"),
                "Decision Tree": DecisionTreeClassifier(max_depth=12, random_state=42, class_weight="balanced"),
                "Random Forest": RandomForestClassifier(n_estimators=160, random_state=42, class_weight="balanced", n_jobs=-1),
                "Logistic Regression": LogisticRegression(max_iter=1500, class_weight="balanced"),
            }
            for name, estimator in classifiers.items():
                model = Pipeline([("features", clone(prep)), ("model", estimator)])
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                results.append({"Model": name, "Task": "Classification · style prediction", "Accuracy": accuracy_score(y_test, pred), "Precision": precision_score(y_test, pred, average="weighted", zero_division=0), "Recall": recall_score(y_test, pred, average="weighted", zero_division=0), "F1": f1_score(y_test, pred, average="weighted", zero_division=0), "MAE": np.nan, "RMSE": np.nan, "R²": np.nan})
                fitted[name] = model

    # Three regression analyses predict match_score from multiple fused attributes.
    if "match_score" in df.columns:
        rdf = df.dropna(subset=["match_score"]).copy()
        cols = _feature_columns(rdf, "match_score")
        X, y = rdf[cols], pd.to_numeric(rdf["match_score"], errors="coerce")
        valid = y.notna(); X, y = X.loc[valid], y.loc[valid]
        if len(y) >= 20 and len(cols):
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42)
            prep = _preprocessor(X_train)
            # Single-variable linear regression: price is the explanatory variable when available.
            price_col = "price" if "price" in X_train.columns else X_train.select_dtypes(include=np.number).columns[0]
            simple = Pipeline([("features", _preprocessor(X_train[[price_col]])), ("model", LinearRegression())])
            multi = Pipeline([("features", clone(prep)), ("model", LinearRegression())])
            # Polynomial regression applies degree-2 expansion to the numeric feature matrix.
            numeric_cols = X_train.select_dtypes(include=np.number).columns.tolist()
            if not numeric_cols:
                numeric_cols = [price_col]
            poly_prep = ColumnTransformer([
                ("poly_num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("poly", PolynomialFeatures(degree=2, include_bias=False)), ("scale", StandardScaler())]), numeric_cols),
                ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), [c for c in X_train.columns if c not in numeric_cols])
            ], remainder="drop")
            poly = Pipeline([("features", poly_prep), ("model", LinearRegression())])
            for name, model, train_x, test_x in [
                ("Linear Regression", simple, X_train[[price_col]], X_test[[price_col]]),
                ("Multiple Linear Regression", multi, X_train, X_test),
                ("Polynomial Regression", poly, X_train, X_test),
            ]:
                model.fit(train_x, y_train)
                pred = model.predict(test_x)
                results.append({"Model": name, "Task": "Regression · match-score estimation", "Accuracy": np.nan, "Precision": np.nan, "Recall": np.nan, "F1": np.nan, "MAE": mean_absolute_error(y_test, pred), "RMSE": mean_squared_error(y_test, pred) ** .5, "R²": r2_score(y_test, pred)})
                fitted[name] = model

    return pd.DataFrame(results), fitted, {"rows": len(df), "columns": len(df.columns), "source": fused_path}
