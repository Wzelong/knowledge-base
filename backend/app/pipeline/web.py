import re
from dataclasses import dataclass

import httpx
from agents import function_tool
from bs4 import BeautifulSoup

FETCH_TIMEOUT = 20.0
MAX_PAGE_CHARS = 80000
MAX_TOOL_RESULT_CHARS = 20000
USER_AGENT = "Mozilla/5.0 (compatible; knowledge-base-ingest/0.1)"

STRIPPED_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]


@dataclass
class WebPage:
    title: str | None
    text: str


async def fetch_page(url: str) -> WebPage | None:
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(STRIPPED_TAGS):
        tag.decompose()

    text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n\n", strip=True))
    if not text:
        return None
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    return WebPage(title=title, text=text[:MAX_PAGE_CHARS])


@function_tool
async def fetch_url(url: str) -> str:
    """Fetch a web page and return its readable text content."""
    page = await fetch_page(url)
    if page is None:
        return "Could not fetch this URL."
    header = f"Title: {page.title}\n\n" if page.title else ""
    return f"{header}{page.text}"[:MAX_TOOL_RESULT_CHARS]
