import os
import requests

API_KEY = os.getenv("DATA_GOV_API_KEY")

print("=" * 80)
print("CPCB / DATA.GOV.IN API TEST")
print("=" * 80)

if not API_KEY:
    print("\nERROR: DATA_GOV_API_KEY is not loaded.")
    print('Run:')
    print('$env:DATA_GOV_API_KEY="YOUR_API_KEY"')
    raise SystemExit(1)

print("\nAPI key detected.")

url = "https://api.data.gov.in/resource"

print("\nTesting connection to:")
print(url)

try:
    response = requests.get(
        url,
        params={
            "api-key": API_KEY,
            "format": "json",
            "limit": 1
        },
        timeout=60
    )

    print("\nHTTP Status:", response.status_code)

    print("\nResponse:")
    print(response.text[:1000])

except requests.exceptions.Timeout:
    print("\nERROR: Connection timed out.")

except requests.exceptions.SSLError as e:
    print("\nERROR: SSL connection failed.")
    print(e)

except requests.exceptions.ConnectionError as e:
    print("\nERROR: Could not connect to data.gov.in.")
    print(e)

except Exception as e:
    print("\nERROR:")
    print(e)

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)