from urllib.parse import urlparse


def validate_url(url):

    errors = []

    if not url:
        errors.append("URL не может быть пустым")
        return errors

    if len(url) > 255:
        errors.append("URL не может превышать 255 символов")

    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        errors.append("Некорректный URL")

    return errors
