#!/usr/bin/env python3
"""
按 shuju_id 逐场抓取 500.com 6页深数据 → 写入共享缓存
用法: python3 fetch_deep_data.py --fids 1359200,1359203,1359236,1359239 --date 2026-06-15
"""
import json, os, sys, time, argparse, re
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser

CACHE_DIR = os.path.expanduser("/Users/tracy/WorkBuddy/2026-06-24-23-14-33/.cache/shared-football")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT, "Referer": "https://odds.500.com/"}

PAGE_TEMPLATES = {
    "ouzhi":   "https://odds.500.com/fenxi/ouzhi-{fid}.shtml",
    "yazhi":   "https://odds.500.com/fenxi/yazhi-{fid}.shtml",
    "rangqiu": "https://odds.500.com/fenxi/rangqiu-{fid}.shtml",
    "daxiao":   "https://odds.500.com/fenxi/daxiao-{fid}.shtml",
    "shuju":    "https://odds.500.com/fenxi/shuju-{fid}.shtml",
    "touzhu":   "https://odds.500.com/fenxi/touzhu-{fid}.shtml",
}

def fetch_url(url, timeout=20):
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type","")
            if "gb" in ct.lower() or "gb2312" in ct.lower():
                return raw.decode("gb2312","replace")
            return raw.decode("utf-8","replace")
    except Exception as e:
        print(f"  ⚠️  抓取失败 {url}: {e}", file=sys.stderr)
        return ""

def parse_ouzhi_html(html, fid):
    """解析欧赔页面 - 提取30家公司+平均+Pinnacle"""
    data = {"pinnacle": {}, "average": {}, "bookmakers": []}
    # 提取表格行 - 简化版：提取Pinnacle行和平均行
    # 实际解析需要完整的HTML解析，这里先做框架
    return data

def fetch_all_pages(fid, date_str, cache_dir):
    """抓取一场比赛的6页，存raw，返回解析后的JSON"""
    raw_dir = os.path.join(cache_dir, "raw", date_str)
    parsed_dir = os.path.join(cache_dir, "parsed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(parsed_dir, exist_ok=True)

    parsed = {
        "match_id": fid,
        "date": date_str,
        "pages": {}
    }

    for page_name, url_template in PAGE_TEMPLATES.items():
        url = url_template.format(fid=fid)
        raw_file = os.path.join(raw_dir, f"{page_name}_{fid}.html")

        # 检查raw缓存
        if os.path.exists(raw_file):
            print(f"  ✅ [{page_name}] raw缓存命中 fid={fid}")
            with open(raw_file, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
        else:
            print(f"  🌐 [{page_name}] 抓取 {url}")
            html = fetch_url(url)
            if html:
                with open(raw_file, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"  💾 [{page_name}] 已缓存 fid={fid}")
            time.sleep(1)  # 礼貌延迟

        parsed["pages"][page_name] = {"html_len": len(html), "url": url}

    # 写入解析后的JSON（简化版，实际需要进一步解析）
    out_file = os.path.join(parsed_dir, f"{date_str}_{fid}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    print(f"  📝 已写入 {out_file}")
    return out_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fids", required=True, help="逗号分隔的shuju_id列表")
    parser.add_argument("--date", default="2026-06-15", help="比赛日期 YYYY-MM-DD")
    args = parser.parse_args()

    fids = [f.strip() for f in args.fids.split(",")]
    print(f"📦 开始抓取 {len(fids)} 场比赛的 deep 数据...")
    print(f"   date={args.date}, fids={fids}")

    for fid in fids:
        print(f"\n🔍 处理 fid={fid}...")
        out = fetch_all_pages(fid, args.date, CACHE_DIR)
        print(f"✅ fid={fid} 完成 → {out}")

if __name__ == "__main__":
    main()
