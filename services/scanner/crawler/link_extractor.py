from html.parser import HTMLParser
from typing import List, Optional
from services.scanner.crawler.url_utils import normalize_url

class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.raw_hrefs: List[str] = []
        self.base_href: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag_lower = tag.lower()
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}

        if tag_lower == "base" and "href" in attr_dict:
            self.base_href = attr_dict["href"].strip()
        elif tag_lower == "a" and "href" in attr_dict:
            href = attr_dict["href"].strip()
            if href:
                self.raw_hrefs.append(href)

def extract_html_links(html_content: str, page_url: str) -> List[str]:
    """
    Parses HTML content and extracts normalized candidate URLs resolved against page_url.
    """
    if not html_content or not isinstance(html_content, str):
        return []

    parser = _LinkParser()
    try:
        parser.feed(html_content)
    except Exception:
        pass

    effective_base = parser.base_href if parser.base_href else page_url
    extracted_urls = []

    for raw_href in parser.raw_hrefs:
        # Ignore Javascript / mailto / tel pseudo URIs
        if raw_href.lower().startswith(("javascript:", "mailto:", "tel:", "data:", "about:")):
            continue
        try:
            norm = normalize_url(raw_href, base_url=effective_base)
            extracted_urls.append(norm)
        except Exception:
            pass

    return extracted_urls
