import re


class URLExtractor:

    def extract_urls(self, text):

        pattern = (
            r'(?:https?://|www\.)'
            r'[^\s<>"\'\]\)]+'
        )

        urls = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        cleaned_urls = []

        for url in urls:

            url = url.rstrip(
                ".,!?;:'\"()[]{}<>"
            )

            # Add https to www URLs
            if url.lower().startswith("www."):

                url = "https://" + url

            if url not in cleaned_urls:

                cleaned_urls.append(url)

        return cleaned_urls