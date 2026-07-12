"""
HTML parser for product enrichment.

Extracts page title, paragraphs, likely product-page links, and cleaned text.
No LLM — rule-based parsing with BeautifulSoup only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from utils.logger import get_logger

logger = get_logger(__name__)

REMOVED_TAGS: frozenset[str] = frozenset(
    {"script", "style", "noscript", "svg", "iframe"}
)

PRODUCT_PATH_KEYWORDS: tuple[str, ...] = (
    "/product",
    "/products",
    "/shop",
    "/store",
    "/item",
    "/catalog",
    "/collection",
    "/collections",
    "/p/",
    "/dp/",
    "/sku/",
)

PRODUCT_LINK_TEXT_KEYWORDS: tuple[str, ...] = (
    "product",
    "products",
    "shop",
    "catalog",
    "buy",
    "collection",
)


@dataclass
class ParsedPage:
    """Structured content extracted from a single HTML page."""

    title: str = ""
    paragraphs: list[str] = field(default_factory=list)
    product_page_urls: list[str] = field(default_factory=list)

    @property
    def clean_text(self) -> str:
        """All extracted text combined into one cleaned string."""
        parts: list[str] = []
        if self.title:
            parts.append(self.title)
        parts.extend(self.paragraphs)
        return "\n\n".join(parts)


def clean_text(text: str) -> str:
    """
    Normalize whitespace and strip a text fragment.

    Args:
        text: Raw text from HTML.

    Returns:
        Cleaned single-line or short text.
    """
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


class HtmlParser:
    """
    Parse HTML and extract enrichment-ready content.

    Example:
        parser = HtmlParser()
        page = parser.parse(html, base_url="https://example.com")
        print(page.title)
        print(page.paragraphs)
        print(page.product_page_urls)
    """

    def parse(self, html: str, *, base_url: str | None = None) -> ParsedPage:
        """
        Extract title, paragraphs, and product-page URLs from HTML.

        Args:
            html: Raw HTML string.
            base_url: Optional page URL used to resolve relative links.

        Returns:
            ParsedPage with cleaned fields.
        """
        if not html or not html.strip():
            logger.warning("Empty HTML received for parsing")
            return ParsedPage()

        soup = BeautifulSoup(html, "html.parser")
        self._remove_noise(soup)

        title = self._extract_title(soup)
        paragraphs = self._extract_paragraphs(soup)
        product_page_urls = self._extract_product_page_urls(soup, base_url)

        logger.debug(
            "Parsed page: title=%r, paragraphs=%d, product_links=%d",
            title,
            len(paragraphs),
            len(product_page_urls),
        )

        return ParsedPage(
            title=title,
            paragraphs=paragraphs,
            product_page_urls=product_page_urls,
        )

    def _remove_noise(self, soup: BeautifulSoup) -> None:
        for tag_name in REMOVED_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if isinstance(og_title, Tag):
            content = og_title.get("content")
            if isinstance(content, str) and content.strip():
                return clean_text(content)

        if soup.title and soup.title.string:
            return clean_text(soup.title.string)

        h1 = soup.find("h1")
        if h1:
            return clean_text(h1.get_text(" ", strip=True))

        return ""

    def _extract_paragraphs(self, soup: BeautifulSoup) -> list[str]:
        paragraphs: list[str] = []
        seen: set[str] = set()

        for p_tag in soup.find_all("p"):
            text = clean_text(p_tag.get_text(" ", strip=True))
            if len(text) < 20:
                continue
            if text in seen:
                continue
            seen.add(text)
            paragraphs.append(text)

        return paragraphs

    def _extract_product_page_urls(
        self,
        soup: BeautifulSoup,
        base_url: str | None,
    ) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            if not isinstance(anchor, Tag):
                continue

            href = anchor.get("href")
            if not isinstance(href, str) or not href.strip():
                continue

            href = href.strip()
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue

            absolute_url = urljoin(base_url, href) if base_url else href
            absolute_url = absolute_url.split("#", 1)[0].rstrip("/")

            if not self._looks_like_product_page(absolute_url, anchor):
                continue

            if base_url and not self._same_domain(base_url, absolute_url):
                continue

            if absolute_url in seen:
                continue

            seen.add(absolute_url)
            urls.append(absolute_url)

        return urls

    def _looks_like_product_page(self, url: str, anchor: Tag) -> bool:
        lowered_url = url.lower()
        if any(keyword in lowered_url for keyword in PRODUCT_PATH_KEYWORDS):
            return True

        link_text = clean_text(anchor.get_text(" ", strip=True)).lower()
        return any(keyword in link_text for keyword in PRODUCT_LINK_TEXT_KEYWORDS)

    def _same_domain(self, base_url: str, candidate_url: str) -> bool:
        base_host = urlparse(base_url).netloc.lower()
        candidate_host = urlparse(candidate_url).netloc.lower()
        return bool(base_host) and base_host == candidate_host


def parse_html(html: str, *, base_url: str | None = None) -> ParsedPage:
    """
    Convenience function to parse HTML content.

    Args:
        html: Raw HTML string.
        base_url: Optional page URL used to resolve relative links.

    Returns:
        ParsedPage with cleaned fields.
    """
    return HtmlParser().parse(html, base_url=base_url)