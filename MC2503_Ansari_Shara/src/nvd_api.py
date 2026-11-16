import os
import requests
from dotenv import load_dotenv


load_dotenv()


class NVD:

    API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self):

        self.api_key = os.getenv("NVD_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NVD_API_KEY not found in .env"
            )

    def search_cve(self, keyword):

        headers = {
            "apiKey": self.api_key
        }

        params = {
            "keywordSearch": keyword,
            "resultsPerPage": 5
        }

        try:

            response = requests.get(
                self.API_URL,
                headers=headers,
                params=params,
                timeout=15
            )

            print("HTTP Status:", response.status_code)

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:

            return {
                "error": str(e)
            }


if __name__ == "__main__":

    nvd = NVD()

    print("=" * 60)
    print("NVD API TEST")
    print("=" * 60)

    result = nvd.search_cve("Microsoft Windows")

    if "error" in result:

        print("\nERROR:")
        print(result["error"])

    else:

        print("\nTotal Results:")
        print(result.get("totalResults"))

        print("\nCVE Results")
        print("-" * 40)

        for item in result.get("vulnerabilities", []):

            cve = item.get("cve", {})

            print(
                "\nCVE ID:",
                cve.get("id")
            )

            descriptions = cve.get(
                "descriptions",
                []
            )

            if descriptions:

                print(
                    "Description:",
                    descriptions[0].get("value")
                )