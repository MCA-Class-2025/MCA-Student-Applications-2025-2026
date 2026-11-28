import pandas as pd
from sklearn.preprocessing import StandardScaler

def run_feature_fusion():
    print("Starting Data Cleaning & Feature Fusion...")
    
    # Step 5: Load raw_fused_dataset.csv
    df = pd.read_csv("data/raw_fused_dataset.csv")
    
    # Step 6: Clean/preprocess the data
    initial_missing = df.isnull().sum().sum()
    initial_duplicates = df.duplicated().sum()
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())
        
    categorical_cols = df.select_dtypes(exclude=['number']).columns
    for col in categorical_cols:
        df[col] = df[col].fillna(df[col].mode()[0])
        
    df = df.drop_duplicates()
    
    final_missing = df.isnull().sum().sum()
    final_duplicates = df.duplicated().sum()
    
    # Optional: Save cleaned intermediate state if desired (not explicitly in pipeline but useful for app.py tab 3 display)
    df.to_csv("data/cleaned_dataset.csv", index=False)
    
    stats = {
        "missing_before": int(initial_missing),
        "missing_after": int(final_missing),
        "duplicates_before": int(initial_duplicates),
        "duplicates_after": int(final_duplicates)
    }
    
    # Step 7: Perform Feature Fusion
    # 1. Pollution Index = PM2.5 + PM10 + NO2 + O3
    df['pollution_index'] = df['pm2_5'] + df['pm10'] + df['no2'] + df['o3']
    
    # 2. GDP per capita = wb_gdp / wb_population
    df['gdp_per_capita'] = df['wb_gdp'] / df['wb_population']
    df['gdp_per_capita'] = df['gdp_per_capita'].fillna(0)
    
    # 3. Temperature-Humidity interaction
    df['temp_humidity_interaction'] = df['temperature'] * df['humidity']
    
    # Standardize numerical features
    numeric_cols = df.select_dtypes(include=['number']).columns
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    # Catch-all for any remaining NaNs (e.g., if entire column was NaN)
    df = df.fillna(0)
    
    # Step 8: Save data/feature_fusion.csv
    df.to_csv("data/feature_fusion.csv", index=False)
    print("Feature Fusion Complete. Saved to data/feature_fusion.csv")
    
    return df, stats

if __name__ == "__main__":
    df_features, stats = run_feature_fusion()
    print("Stats:", stats)
    print(df_features.head())
