import os
import requests
from dotenv import load_dotenv

load_dotenv()


class IPInfo:

    API_URL = "https://ipinfo.io"

    def __init__(self):

        self.api_token = os.getenv(
            "IPINFO_API_TOKEN"
        )

        if not self.api_token:
            raise ValueError(
                "IPINFO_API_TOKEN not found in .env"
            )

    def lookup_ip(self, ip_address):

        url = f"{self.API_URL}/{ip_address}/json"

        params = {
            "token": self.api_token
        }

        try:

            response = requests.get(
                url,
                params=params,
                timeout=15
            )

            print(
                "IPinfo HTTP Status:",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()

            return {
                "ip_address": data.get(
                    "ip",
                    ip_address
                ),

                "hostname": data.get(
                    "hostname"
                ),

                "city": data.get(
                    "city"
                ),

                "region": data.get(
                    "region"
                ),

                "country": data.get(
                    "country"
                ),

                "location": data.get(
                    "loc"
                ),

                "organization": data.get(
                    "org"
                ),

                "postal": data.get(
                    "postal"
                ),

                "timezone": data.get(
                    "timezone"
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

    ipinfo = IPInfo()

    test_ip = "218.149.142.253"

    print("=" * 60)
    print("IPINFO API TEST")
    print("=" * 60)

    result = ipinfo.lookup_ip(
        test_ip
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )