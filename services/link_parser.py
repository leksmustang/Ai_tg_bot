import aiohttp
from bs4 import BeautifulSoup

async def fetch_and_parse_url(session: aiohttp.ClientSession, url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with session.get(url, timeout=10, headers=headers) as resp:
            if resp.status != 200:
                return ""
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = ' '.join(tag.get_text(strip=True) for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'article']))
            if len(text) > 3000:
                text = text[:3000] + "..."
            return text if len(text) > 50 else ""
    except:
        return ""