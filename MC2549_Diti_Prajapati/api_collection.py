import requests
import pandas as pd
import os


# ==========================================
# API 1: DUMMYJSON PRODUCTS API
# ==========================================

API_URL = "https://dummyjson.com/products?limit=0"


def collect_dummyjson_products():

    print("\n==========================================")
    print("API 1: DummyJSON Products API")
    print("==========================================")

    print("Request URL:", API_URL)

    try:

        # ----------------------------------
        # 1. API REQUEST
        # ----------------------------------

        response = requests.get(
            API_URL,
            timeout=20
        )

        print("HTTP Status Code:", response.status_code)

        # Check whether request was successful
        response.raise_for_status()

        # ----------------------------------
        # 2. PARSE JSON RESPONSE
        # ----------------------------------

        data = response.json()

        products = data.get("products", [])

        print("Products received:", len(products))

        # ----------------------------------
        # 3. CONVERT TO DATAFRAME
        # ----------------------------------

        api_df = pd.DataFrame(products)

        print("Original API columns:")
        print(api_df.columns.tolist())

        # ----------------------------------
        # 4. SELECT RELEVANT ATTRIBUTES
        # ----------------------------------

        selected_columns = [
            "id",
            "title",
            "description",
            "category",
            "price",
            "rating",
            "stock",
            "brand",
            "availabilityStatus",
            "shippingInformation",
            "warrantyInformation"
        ]

        api_df = api_df[
            [column for column in selected_columns
             if column in api_df.columns]
        ]

        # ----------------------------------
        # 5. RENAME COLUMNS
        # ----------------------------------

        api_df.rename(
            columns={
                "id": "api_product_id",
                "title": "api_product_name",
                "availabilityStatus": "api_availability",
                "shippingInformation": "api_shipping",
                "warrantyInformation": "api_warranty"
            },
            inplace=True
        )

        # ----------------------------------
        # 6. DATA VALIDATION
        # ----------------------------------

        print("\n========== API DATA VALIDATION ==========")

        print(
            "Number of API records:",
            len(api_df)
        )

        print(
            "Number of API attributes:",
            len(api_df.columns)
        )

        print("\nMissing values:")

        print(
            api_df.isnull().sum()
        )

        print(
            "\nDuplicate API product IDs:",
            api_df["api_product_id"].duplicated().sum()
        )

        print(
            "\nDuplicate complete rows:",
            api_df.duplicated().sum()
        )

        # ----------------------------------
        # 7. SAVE API DATASET
        # ----------------------------------

        os.makedirs("data", exist_ok=True)

        output_file = "data/api1_dummyjson.csv"

        api_df.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "\nAPI dataset saved to:",
            output_file
        )

        # ----------------------------------
        # 8. DISPLAY SAMPLE
        # ----------------------------------

        print("\n========== SAMPLE API DATA ==========")

        print(
            api_df.head().to_string(index=False)
        )

        return api_df

    except requests.exceptions.RequestException as error:

        print("\nAPI REQUEST ERROR:")
        print(error)

        return pd.DataFrame()

    except Exception as error:

        print("\nPROCESSING ERROR:")
        print(error)

        return pd.DataFrame()


# ==========================================
# RUN API COLLECTION
# ==========================================

if __name__ == "__main__":

    dummyjson_df = collect_dummyjson_products()

    if not dummyjson_df.empty:

        print("\n==========================================")
        print("API 1 COLLECTION COMPLETED SUCCESSFULLY")
        print("==========================================")

    else:

        print("\nAPI 1 collection failed.")