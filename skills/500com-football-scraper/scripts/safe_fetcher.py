#!/usr/bin/env python3
"""
500.com 反爬安全请求模块 v1.0
浏览器模拟 + Cookie 管理 + 随机延迟 + 封锁检测
"""
import urllib.request
import http.cookiejar
import random
import time
import re

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}


class SafeFetcher:
    """Safe 500.com fetcher with anti-scraping protection"""

    def __init__(self, referer_chain=None, min_delay=0.5, max_delay=2.0):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.referer_chain = referer_chain or [
            'https://www.500.com/',
            'https://trade.500.com/jczq/',
        ]
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_fetch_time = 0
        self._init_session()

    def _init_session(self):
        """Visit homepage to establish session cookie"""
        try:
            req = urllib.request.Request(
                'https://www.500.com/',
                headers={**BROWSER_HEADERS, 'Referer': 'https://www.google.com/'}
            )
            self.opener.open(req, timeout=15)
        except Exception:
            pass  # Homepage may fail, but cookie jar may still have data

    def _get_headers(self, referer=None):
        """Get headers with appropriate referer"""
        h = dict(BROWSER_HEADERS)
        if referer:
            h['Referer'] = referer
        else:
            h['Referer'] = self.referer_chain[-1] if self.referer_chain else 'https://www.500.com/'
        # Rotate User-Agent slightly to appear more natural
        # (keep same browser family, just vary patch version)
        return h

    def _detect_block(self, html, url):
        """Check if response indicates blocking"""
        indicators = []
        if len(html) < 500:
            indicators.append("Response too small")
        if '验证' in html or 'captcha' in html.lower():
            indicators.append("CAPTCHA detected")
        if '访问过于频繁' in html:
            indicators.append("Rate limited")
        if '403' in str(html[:200]):
            indicators.append("403 detected")
        if indicators:
            raise Exception(
                f"BLOCKED by 500.com at {url}: {'; '.join(indicators)}"
            )

    def fetch(self, url, referer=None, encoding='gb2312', timeout=15, delay=True):
        """Fetch a URL with anti-scraping protection"""
        if delay:
            elapsed = time.time() - self.last_fetch_time
            if elapsed < self.min_delay:
                sleep_time = random.uniform(
                    self.min_delay - elapsed,
                    self.max_delay - elapsed
                )
                if sleep_time > 0:
                    time.sleep(sleep_time)

        req = urllib.request.Request(
            url,
            headers=self._get_headers(referer)
        )
        resp = self.opener.open(req, timeout=timeout)
        raw = resp.read()
        self.last_fetch_time = time.time()

        # Try to detect and handle gzip
        try:
            import gzip
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
        except Exception:
            pass

        html = raw.decode(encoding, errors='replace')
        self._detect_block(html, url)
        return html, raw

    def batch_delay(self, batch_size=10, pause_range=(30, 60)):
        """Pause between batches to avoid rate limiting"""
        time.sleep(random.uniform(*pause_range))

    @staticmethod
    def match_delay(min_s=2.0, max_s=5.0):
        """Delay between different matches"""
        time.sleep(random.uniform(min_s, max_s))


# Usage example:
if __name__ == '__main__':
    fetcher = SafeFetcher()
    html, raw = fetcher.fetch('https://odds.500.com/fenxi/ouzhi-1033503.shtml',
                               referer='https://trade.500.com/jczq/')
    print(f"Fetched {len(html)} bytes, no block detected")
