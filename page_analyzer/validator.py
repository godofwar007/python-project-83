from urllib.parse import urlparse


def validate_url(url):
    error = ["Некорректный URL"]

    if not url or len(url) > 255:
        return error

    parsed_url = urlparse(url)

    if not parsed_url.scheme or not parsed_url.netloc:
        return error

    if parsed_url.scheme not in {"http", "https"}:
        return error

    return []


def normalize_url(url):
    parsed = urlparse(url, scheme="http")
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if not netloc:
        netloc = parsed.path.lower()
    return f"{scheme}://{netloc}"
