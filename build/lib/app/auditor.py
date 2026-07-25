from __future__ import annotations

from bs4 import BeautifulSoup

from app.models import ParseResult


def parse_html(html: str) -> ParseResult:
    soup = BeautifulSoup(html or "", "lxml")

    title_tag = soup.title
    title = title_tag.get_text(strip=True) if title_tag else None
    title = title or None

    description = None
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = meta["content"].strip() or None

    h1_count = len(soup.find_all("h1"))

    images = soup.find_all("img")
    images_total = len(images)
    images_missing_alt = sum(
        1 for img in images if not (img.get("alt") or "").strip()
    )

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    word_count = len(text.split())

    return ParseResult(
        title=title,
        meta_description=description,
        h1_count=h1_count,
        images_total=images_total,
        images_missing_alt=images_missing_alt,
        word_count=word_count,
    )
