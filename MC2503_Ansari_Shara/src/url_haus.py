import requests


class URLHaus:

    API_URL = "https://urlhaus-api.abuse.ch/v1/url/"

    def __init__(self, auth_key):

        self.auth_key = auth_key

    def check_url(self, url):

        headers = {
            "Auth-Key": self.auth_key
        }

        data = {
            "url": url
        }

        try:

            response = requests.post(
                self.API_URL,
                headers=headers,
                data=data,
                timeout=15
            )

            response.raise_for_status()

            result = response.json()

            return result

        except requests.exceptions.RequestException as e:

            return {
                "query_status": "error",
                "error": str(e)
            }