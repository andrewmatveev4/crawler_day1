from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from errors import ParseError


class HTMLParser:
    def __init__(self):
        self.logger = logging.getLogger("parser")

    async def parse_html(self, html: str, url: str) -> dict:
            try:
                soup = BeautifulSoup(html, "lxml")
                metadata = self.extract_metadata(soup)

                return {
                    "url": url,
                    "metadata": metadata,
                    "title": metadata.get("title", ""),
                    "text": self.extract_text(soup),
                    "links": self.extract_links(soup, url),
                    "images": self.extract_images(soup),
                    "headings": self.extract_headings(soup),
                    "lists": self.extract_lists(soup),
                    "tables": self.extract_tables(soup),
                }
            except Exception as e:
                self.logger.warning(f"Ошибка парсинга {url}: {e}")
                raise ParseError(f"Не удалось распарсить {url}: {e}")

    def extract_links(self, soup, base_url):
        links = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if not href:
                continue
            full_url = urljoin(base_url, href)
            if full_url.startswith(("http://", "https://")):
                links.append(full_url)
        return links

    def extract_images(self, soup):
        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            alt = img.get("alt", "")
            if src:
                images.append({"src": src, "alt": alt})
        return images

    def extract_headings(self, soup):
        headings = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            headings.append({"tag": h.name, "text": h.text})
        return headings

    def extract_metadata(self, soup):
        metadata = {}

        # title — обычный тег, как раньше
        if soup.title:
            metadata["title"] = soup.title.text
        else:
            metadata["title"] = ""

        # description — ищем meta с name="description"
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            metadata["description"] = desc.get("content", "")
        else:
            metadata["description"] = ""

        # keywords — тот же приём
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords:
            metadata["keywords"] = keywords.get("content", "")
        else:
            metadata["keywords"] = ""

        return metadata

    def extract_text(self, soup, selector: str = None):
        for tag in soup(["script", "style"]):
            tag.decompose()
        if selector:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator=" ", strip=True)
            return ""
        return soup.get_text(separator=" ", strip=True)

    def extract_lists(self, soup):
        lists = []
        for ul in soup.find_all(["ul", "ol"]):
            items = []
            for li in ul.find_all("li"):
                items.append(li.get_text(strip=True))
            lists.append(items)
        return lists

    def extract_tables(self, soup):
        tables = []
        for table in soup.find_all("table"):
            table_data = []
            for row in table.find_all("tr"):
                row_data = []
                for cell in row.find_all(["td", "th"]):
                    row_data.append(cell.get_text(strip=True))
                table_data.append(row_data)
            tables.append(table_data)
        return tables
