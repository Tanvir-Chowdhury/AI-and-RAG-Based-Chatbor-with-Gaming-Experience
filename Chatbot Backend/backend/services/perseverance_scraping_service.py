

import logging
import requests
from bs4 import BeautifulSoup
import asyncio
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import time
import re

logger = logging.getLogger(__name__)

class NASAPerseveranceScrapingService:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    async def scrape_perseverance_page(self, url: str) -> Dict[str, Any]:

        try:
            logger.info(f" Scraping NASA Perseverance page: {url}")

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(url, timeout=30)
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                page_data = {
                    'url': url,
                    'title': self._extract_title(soup),
                    'main_content': self._extract_main_content(soup),
                    'sections': self._extract_sections(soup),
                    'images': self._extract_images(soup, url),
                    'links': self._extract_related_links(soup, url),
                    'metadata': self._extract_metadata(soup),
                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }

                logger.info(f" Successfully scraped Perseverance page")
                logger.info(f"    Title: {page_data['title']}")
                logger.info(f"    Sections: {len(page_data['sections'])}")
                logger.info(f"     Images: {len(page_data['images'])}")
                logger.info(f"    Links: {len(page_data['links'])}")

                return page_data

            else:
                logger.error(f"Failed to scrape {url}: Status {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error scraping Perseverance page: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:

        title_selectors = ['title', 'h1', '.page-title', '.hero-title', '.main-title']

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 5:
                    return title

        return "NASA Perseverance Rover Information"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:

        content_parts = []

        content_selectors = [
            '.content-area',
            '.main-content',
            '.page-content',
            '.article-content',
            '.body-content',
            'main',
            '.container .row'
        ]

        main_content = None
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                main_content = elem
                break

        if not main_content:
            main_content = soup.find('body')

        if main_content:

            for elem in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'div'], recursive=True):
                text = elem.get_text().strip()

                if self._is_content_text(text):
                    content_parts.append(text)

        return '\n\n'.join(content_parts)

    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:

        sections = []

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])

        for heading in headings:
            heading_text = heading.get_text().strip()
            if not heading_text or len(heading_text) < 3:
                continue

            content_parts = []
            current = heading.next_sibling

            while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if self._is_content_text(text):
                        content_parts.append(text)
                current = current.next_sibling

                if len(content_parts) > 10:
                    break

            if content_parts:
                sections.append({
                    'heading': heading_text,
                    'content': '\n'.join(content_parts[:5])
                })

        return sections

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:

        images = []

        for img in soup.find_all('img'):
            src = img.get('src')
            if src:

                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)

                alt_text = img.get('alt', '')
                title = img.get('title', '')

                images.append({
                    'src': src,
                    'alt': alt_text,
                    'title': title,
                    'description': alt_text or title
                })

        return images[:20]

    def _extract_related_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:

        links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()

            if href and text and len(text) > 3:

                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = urljoin(base_url, href)

                if self._is_relevant_link(href, text):
                    links.append({
                        'url': href,
                        'text': text,
                        'title': link.get('title', '')
                    })

        return links[:30]

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:

        metadata = {}

        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')

            if name and content:
                if name in ['description', 'keywords', 'author', 'og:description', 'og:title']:
                    metadata[name] = content

        return metadata

    def _is_content_text(self, text: str) -> bool:

        if not text or len(text) < 10:
            return False

        skip_patterns = [
            'cookie', 'privacy', 'terms', 'navigation', 'menu', 'footer',
            'skip to', 'back to top', 'share this', 'social media',
            'follow us', 'subscribe', 'newsletter', 'advertisement'
        ]

        text_lower = text.lower()
        for pattern in skip_patterns:
            if pattern in text_lower:
                return False

        word_ratio = len(re.findall(r'\b[a-zA-Z]{3,}\b', text)) / max(len(text.split()), 1)
        return word_ratio > 0.3

    def _is_relevant_link(self, href: str, text: str) -> bool:

        if not href or not text:
            return False

        relevant_domains = ['nasa.gov', 'jpl.nasa.gov', 'mars.nasa.gov']
        relevant_keywords = [
            'mars', 'perseverance', 'rover', 'mission', 'sample', 'rock',
            'science', 'exploration', 'discovery', 'research', 'experiment'
        ]

        href_lower = href.lower()
        text_lower = text.lower()

        for domain in relevant_domains:
            if domain in href_lower:
                return True

        for keyword in relevant_keywords:
            if keyword in href_lower or keyword in text_lower:
                return True

        return False

    async def create_knowledge_entry(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:

        if not scraped_data:
            return {}

        content_parts = []

        if scraped_data.get('title'):
            content_parts.append(f"Title: {scraped_data['title']}")

        if scraped_data.get('main_content'):
            content_parts.append(f"Content: {scraped_data['main_content'][:2000]}")

        for section in scraped_data.get('sections', [])[:10]:
            content_parts.append(f"Section - {section['heading']}: {section['content'][:500]}")

        metadata = scraped_data.get('metadata', {})
        if metadata.get('description'):
            content_parts.append(f"Description: {metadata['description']}")

        knowledge_entry = {
            'source_file': 'NASA_Perseverance_Web_Scrape',
            'content': '\n\n'.join(content_parts),
            'chunk_id': 'perseverance_web_001',
            'metadata': {
                'source_type': 'web_scrape',
                'url': scraped_data.get('url', ''),
                'title': scraped_data.get('title', ''),
                'scraped_at': scraped_data.get('scraped_at', ''),
                'images_json': json.dumps(scraped_data.get('images', [])[:10]),
                'related_links_json': json.dumps(scraped_data.get('links', [])[:15]),
                'section_count': len(scraped_data.get('sections', [])),
                'topic': 'Mars Perseverance Rover',
                'mission': 'Mars 2020 Perseverance',
                'image_urls': ','.join([img['src'] for img in scraped_data.get('images', [])[:5]])
            }
        }

        return knowledge_entry