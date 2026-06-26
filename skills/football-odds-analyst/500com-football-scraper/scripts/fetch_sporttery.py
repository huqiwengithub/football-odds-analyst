#!/usr/bin/env python3
"""
竞彩官网 (sporttery.cn) 赔率抓取器 v1.1

抓取策略: webapi REST API → 快速失败
- 🥇 主源: webapi.sporttery.cn REST API (SPA页面实际使用的数据接口)
- 失败时直接报告, 由上层调用方降级到 500.com 后备 ("竞*官*" 行)

修复记录:
  v1.1 (2026-06-26): 原脚本抓取 m.sporttery.cn 的 HTML 空壳页面,
    该页面是 SPA, 数据通过 AJAX 从 webapi REST API 加载。
    删除全部 HTML DOM 解析函数 (extract_matches_from_html 等),
    改为直接调用 REST API 获取 JSON 数据。
  
输出: JSON 到 .cache/sporttery/{date}_jingcai.json
缓存: 1 小时

用法:
  python3 fetch_sporttery.py --date 2026-06-25 [--no-cache]
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# ── 配置 ──────────────────────────────────────────
SPORTTERY_API = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=tycp"
CACHE_DIR = Path.home() / ".cache" / "workbuddy" / "sporttery"
CACHE_TTL_HOURS = 1
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

# ── 工具函数 ──────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}][{level}] {msg}", file=sys.stderr)


def fetch_json(url: str, retries: int = 3) -> dict | None:
    """抓取 JSON API，带重试"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Referer": "https://m.sporttery.cn/",
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            log(f"HTTP {e.code} attempt {attempt+1}/{retries}", "WARN")
        except Exception as e:
            log(f"Fetch error attempt {attempt+1}/{retries}: {e}", "WARN")
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    return None


def parse_api_matches(match_info_list: list) -> list[dict]:
    """解析 webapi.sporttery.cn REST API 返回的比赛数据
    
    API 返回结构:
    matchInfoList[].subMatchList[].had = {h:主胜赔率, d:平赔, a:客胜赔率}
    matchInfoList[].subMatchList[].hhad = {goalLine:让球数, h:让球主胜, d:让球平, a:让球客胜}
    """
    parsed = []
    for day_block in match_info_list:
        business_date = day_block.get("businessDate", "")
        for sub in day_block.get("subMatchList", []):
            match = {
                "matchId": str(sub.get("matchId", "")),
                "matchNum": sub.get("matchNumStr", ""),
                "homeTeam": sub.get("homeTeamAbbName", sub.get("homeTeamAllName", "")),
                "awayTeam": sub.get("awayTeamAbbName", sub.get("awayTeamAllName", "")),
                "league": sub.get("leagueAbbName", ""),
                "businessDate": business_date,
                "matchDate": sub.get("matchDate", ""),
                "matchTime": sub.get("matchTime", ""),
                "spf": None,
                "rqspf": None,
            }
            
            # SPF 赔率 (had 池): h=主胜, d=平局, a=客胜
            had = sub.get("had", {})
            if had:
                h, d, a = had.get("h"), had.get("d"), had.get("a")
                if h and d and a and h != "?" and d != "?" and a != "?":
                    match["spf"] = {
                        "home": float(h),
                        "draw": float(d),
                        "away": float(a),
                    }
            
            # 让球胜平负 (hhad 池)
            hhad = sub.get("hhad", {})
            if hhad:
                gl = hhad.get("goalLine", "0")
                hh_h, hh_d, hh_a = hhad.get("h"), hhad.get("d"), hhad.get("a")
                if hh_h and hh_d and hh_a and hh_h != "?" and hh_d != "?" and hh_a != "?":
                    try:
                        handicap = int(float(gl)) if gl else 0
                    except (ValueError, TypeError):
                        handicap = 0
                    match["rqspf"] = {
                        "handicap": handicap,
                        "home": float(hh_h),
                        "draw": float(hh_d),
                        "away": float(hh_a),
                    }
            
            parsed.append(match)
    return parsed


# ── 主流程 ─────────────────────────────────────────
def fetch_jingcai_odds(date: str, no_cache: bool = False) -> dict:
    """抓取竞彩赔率，返回标准化 JSON"""
    
    # 检查缓存
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{date}_jingcai.json"
    
    if not no_cache and cache_file.exists():
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=CACHE_TTL_HOURS):
            log(f"Cache hit: {cache_file}", "INFO")
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    
    log(f"Fetching sporttery.cn API for {date}...", "INFO")
    
    result: dict = {
        "source": "sporttery.cn",
        "url": SPORTTERY_API,
        "fetch_time": datetime.now().isoformat(),
        "date": date,
        "success": False,
        "matches": [],
        "status": "UNKNOWN",
    }
    
    # 🥇 主源: 调用 webapi REST API (SPA 页面实际使用的数据接口)
    api_data = fetch_json(SPORTTERY_API)
    
    if api_data and api_data.get("success") and api_data.get("value", {}).get("matchInfoList"):
        matches = parse_api_matches(api_data["value"]["matchInfoList"])
        if any(m.get("spf") for m in matches):  # 至少有一场有 SPF 赔率
            result["success"] = True
            result["status"] = "OK_API"
            result["matches"] = matches
            result["url"] = SPORTTERY_API
            log(f"Extracted {len(matches)} matches from sporttery.cn API, {sum(1 for m in matches if m.get('spf'))} with SPF odds", "INFO")
            
            # 写入缓存并返回
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return result
    
    # 🥈 API 未返回有效数据
    log("sporttery.cn API returned no valid data", "WARN")
    result["status"] = "API_FAILED"
    return result


# ── CLI ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="竞彩官网赔率抓取器")
    parser.add_argument("--date", required=True, help="日期 YYYY-MM-DD")
    parser.add_argument("--no-cache", action="store_true", help="跳过缓存")
    parser.add_argument("--json", action="store_true", help="JSON 输出到 stdout")
    args = parser.parse_args()
    
    result = fetch_jingcai_odds(args.date, args.no_cache)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "✅" if result["success"] else "❌"
        print(f"{status} sporttery.cn: {result['status']} ({len(result['matches'])} matches)")
        if result["status"] in ("FETCH_FAILED", "API_FAILED"):
            print("⚠️  降级到 500.com 后备源")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
