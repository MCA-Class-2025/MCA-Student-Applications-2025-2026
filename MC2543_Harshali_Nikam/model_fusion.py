import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def run_model_fusion():
    print("Starting Machine Learning & Model Fusion...")
    df = pd.read_csv("data/feature_fusion.csv")
    
    target_col = "pm2_5"
    
    # Select features (exclude non-numeric and the target)
    # PM10, NO2, O3, pollution_index are highly correlated with PM2.5, but for demonstration, we exclude pm2_5
    X = df.select_dtypes(include=[np.number]).drop(columns=[target_col], errors="ignore")
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 1. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    
    # 2. Random Forest Regressor
    rf = RandomForestRegressor(random_state=42)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    
    # 3. Support Vector Regression (SVR)
    svr = SVR()
    svr.fit(X_train, y_train)
    svr_pred = svr.predict(X_test)
    
    # Model Fusion (30% LR, 40% RF, 30% SVR)
    fused_pred = (0.30 * lr_pred) + (0.40 * rf_pred) + (0.30 * svr_pred)
    
    def calculate_metrics(y_true, y_pred):
        return {
            "R²": r2_score(y_true, y_pred),
            "MSE": mean_squared_error(y_true, y_pred),
            "MAE": mean_absolute_error(y_true, y_pred)
        }
        
    metrics = {
        "Linear Regression": calculate_metrics(y_test, lr_pred),
        "Random Forest": calculate_metrics(y_test, rf_pred),
        "SVR": calculate_metrics(y_test, svr_pred),
        "Fused Model": calculate_metrics(y_test, fused_pred)
    }
    
    # Compile a dataframe of predictions for the UI
    predictions_df = pd.DataFrame({
        "Actual PM2.5 (Scaled)": y_test.values,
        "Linear Regression": lr_pred,
        "Random Forest": rf_pred,
        "SVR": svr_pred,
        "Final Fused Prediction": fused_pred
    })
    
    print("Model Fusion Complete.")
    return metrics, predictions_df

if __name__ == "__main__":
    metrics, preds = run_model_fusion()
    print("Metrics:")
    for m, vals in metrics.items():
        print(f"{m}: {vals}")
    print("\nPredictions sample:")
    print(preds.head())
