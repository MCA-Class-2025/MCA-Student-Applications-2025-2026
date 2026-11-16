import os
import requests
from dotenv import load_dotenv

load_dotenv()


class AbuseIPDB:

    API_URL = "https://api.abuseipdb.com/api/v2/check"

    def __init__(self):

        self.api_key = os.getenv(
            "ABUSEIPDB_API_KEY"
        )

        if not self.api_key:
            raise ValueError(
                "ABUSEIPDB_API_KEY not found in .env"
            )

    def check_ip(self, ip_address):

        headers = {
            "Accept": "application/json",
            "Key": self.api_key
        }

        params = {
            "ipAddress": ip_address,
            "maxAgeInDays": 90
        }

        try:

            response = requests.get(
                self.API_URL,
                headers=headers,
                params=params,
                timeout=15
            )

            print(
                "AbuseIPDB HTTP Status:",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

            result = data.get(
                "data",
                {}
            )

            return {
                "ip_address": result.get(
                    "ipAddress",
                    ip_address
                ),

                "abuse_confidence_score":
                    result.get(
                        "abuseConfidenceScore"
                    ),

                "total_reports":
                    result.get(
                        "totalReports"
                    ),

                "country_code":
                    result.get(
                        "countryCode"
                    ),

                "usage_type":
                    result.get(
                        "usageType"
                    ),

                "isp":
                    result.get(
                        "isp"
                    ),

                "domain":
                    result.get(
                        "domain"
                    ),

                "is_whitelisted":
                    result.get(
                        "isWhitelisted"
                    ),

                "last_reported_at":
                    result.get(
                        "lastReportedAt"
                    )
            }

        except requests.exceptions.RequestException as e:

            return {
                "ip_address": ip_address,
                "error": str(e)
            }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    abuse = AbuseIPDB()

    test_ip = "218.149.142.253"

    print("=" * 60)
    print("ABUSEIPDB API TEST")
    print("=" * 60)

    result = abuse.check_ip(
        test_ip
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )