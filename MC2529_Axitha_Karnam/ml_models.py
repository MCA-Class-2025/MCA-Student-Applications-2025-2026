import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

def run_ml_pipeline(csv_path="csv/stock_dataset.csv"):
    print(f"\n--- Loading Dataset from {csv_path} ---")
    try:
        df = pd.read_csv(csv_path)
        df = df.dropna()
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    if df.empty:
        print("Dataset is empty.")
        return

    print(f"Dataset loaded successfully with {len(df):,} rows.")

    # Define features (X)
    feature_cols = [c for c in ["Open", "High", "Low", "Volume", "Volatility", "SMA_10", "EMA_10"] if c in df.columns]
    if not feature_cols:
        print("No matching numerical feature columns found in dataset.")
        return

    X = df[feature_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    scaler = StandardScaler()

    # ========================================================
    # PART 1: REGRESSION MODELS (Target: Close Price)
    # ========================================================
    if "Close" in df.columns:
        print("\n========================================")
        print("   TRAINING REGRESSION MODELS (Target: Close)")
        print("========================================")
        y_reg = pd.to_numeric(df["Close"], errors='coerce').fillna(0)
        
        X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_reg, test_size=0.2, random_state=42)
        X_train_r_scaled = scaler.fit_transform(X_train_r)
        X_test_r_scaled = scaler.transform(X_test_r)

        # Model 1: Multiple Linear Regression
        from sklearn.linear_model import LinearRegression
        lin_reg = LinearRegression()
        lin_reg.fit(X_train_r_scaled, y_train_r)
        y_pred_lin = lin_reg.predict(X_test_r_scaled)
        print(f"1. Multiple Linear Regression -> R2 Score: {r2_score(y_test_r, y_pred_lin):.4f} | RMSE: {np.sqrt(mean_squared_error(y_test_r, y_pred_lin)):.4f}")

        # Model 2: Decision Tree Regressor
        from sklearn.tree import DecisionTreeRegressor
        dt_reg = DecisionTreeRegressor(random_state=42)
        dt_reg.fit(X_train_r, y_train_r)
        y_pred_dt = dt_reg.predict(X_test_r)
        print(f"2. Decision Tree Regressor    -> R2 Score: {r2_score(y_test_r, y_pred_dt):.4f} | RMSE: {np.sqrt(mean_squared_error(y_test_r, y_pred_dt)):.4f}")

        # Model 3: Random Forest Regressor
        from sklearn.ensemble import RandomForestRegressor
        rf_reg = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_reg.fit(X_train_r, y_train_r)
        y_pred_rf = rf_reg.predict(X_test_r)
        print(f"3. Random Forest Regressor    -> R2 Score: {r2_score(y_test_r, y_pred_rf):.4f} | RMSE: {np.sqrt(mean_squared_error(y_test_r, y_pred_rf)):.4f}")

    # ========================================================
    # PART 2: CLASSIFICATION MODELS (Target: Market Sentiment)
    # ========================================================
    sentiment_col = next((c for c in ["Market_Sentiment", "Sentiment"] if c in df.columns), None)
    if sentiment_col:
        print("\n========================================")
        print("   TRAINING CLASSIFICATION MODELS (Target: Sentiment)")
        print("========================================")
        y_clf = df[sentiment_col].astype(str)
        
        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_clf, test_size=0.2, random_state=42)
        X_train_c_scaled = scaler.fit_transform(X_train_c)
        X_test_c_scaled = scaler.transform(X_test_c)

        # Model 4: Logistic Regression
        from sklearn.linear_model import LogisticRegression
        log_clf = LogisticRegression(max_iter=1000)
        log_clf.fit(X_train_c_scaled, y_train_c)
        y_pred_log = log_clf.predict(X_test_c_scaled)
        print(f"4. Logistic Regression        -> Accuracy: {accuracy_score(y_test_c, y_pred_log):.4f}")

        # Model 5: Support Vector Machine (SVM)
        from sklearn.svm import SVC
        svm_clf = SVC()
        svm_clf.fit(X_train_c_scaled, y_train_c)
        y_pred_svm = svm_clf.predict(X_test_c_scaled)
        print(f"5. Support Vector Machine     -> Accuracy: {accuracy_score(y_test_c, y_pred_svm):.4f}")

        # Extra: Random Forest Classifier
        from sklearn.ensemble import RandomForestClassifier
        rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_clf.fit(X_train_c, y_train_c)
        y_pred_rfc = rf_clf.predict(X_test_c)
        print(f"6. Random Forest Classifier   -> Accuracy: {accuracy_score(y_test_c, y_pred_rfc):.4f}")

if __name__ == "__main__":
    run_ml_pipeline()