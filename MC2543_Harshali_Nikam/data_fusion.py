import pandas as pd
from api_clients import collect_all_apis
import os

def run_raw_data_fusion():
    print("Starting Raw Data Fusion...")
    cities_df = pd.read_csv("data/cities.csv")
    
    # Collect all API data and fuse based on City
    fused_data = collect_all_apis(cities_df)
    
    df_fused = pd.DataFrame(fused_data)
    df_fused.to_csv("data/raw_fused_dataset.csv", index=False)
    print("Raw Data Fusion Complete. Saved to data/raw_fused_dataset.csv")
    return df_fused

if __name__ == "__main__":
    df_fused = run_raw_data_fusion()
