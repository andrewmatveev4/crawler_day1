import aiohttp
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger("crawler")


class SitemapParser:
    def __init__(self, user_agent: str = "MyBot/1.0"):
        self.user_agent = user_agent

    async def _download(self, sitemap_url: str, session=None) -> str:
        headers = {"User-Agent": self.user_agent}
        if session is not None:
            async with session.get(sitemap_url, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        else:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as own:
                async with own.get(sitemap_url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.text()

    async def fetch_sitemap(self, sitemap_url: str, session=None) -> list:
        try:
            xml_text = await self._download(sitemap_url, session=session)
        except Exception as e:
            logger.warning(f"Не удалось загрузить sitemap {sitemap_url}: {e}")
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning(f"Битый XML в sitemap {sitemap_url}: {e}")
            return []

        tag = root.tag.lower()

        def local_name(element_tag: str) -> str:
            return element_tag.split("}")[-1].lower()

        if tag.endswith("sitemapindex"):
            all_urls = []
            for child in root:
                if local_name(child.tag) != "sitemap":
                    continue
                for sub in child:
                    if local_name(sub.tag) == "loc" and sub.text:
                        child_urls = await self.fetch_sitemap(sub.text.strip(), session=session)
                        all_urls.extend(child_urls)
            return all_urls
        else:
            urls = []
            for child in root:
                if local_name(child.tag) != "url":
                    continue
                for sub in child:
                    if local_name(sub.tag) == "loc" and sub.text:
                        urls.append(sub.text.strip())
            return urls