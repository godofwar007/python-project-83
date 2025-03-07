from bs4 import BeautifulSoup


def parse_url(response):
    status_code = response.status_code
    soup = BeautifulSoup(response.text, "html.parser")
    h1 = soup.find("h1")
    title = soup.find("title")
    meta = soup.find("meta", attrs={"name": "description"})

    h1_value = h1.get_text(strip=True) if h1 else None
    title_value = title.get_text(strip=True) if title else ""
    description_value = meta.get("content", "").strip() if meta else None

    return status_code, h1_value, title_value, description_value
