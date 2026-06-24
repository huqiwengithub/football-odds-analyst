#!/usr/bin/env python3
"""
解析 ouzhi HTML → 提取 Pinnacle + 30家公司 + 平均值/离散度
用法: python3 parse_ouzhi.py --fid 1359200 --date 2026-06-15
"""
import json, os, re, argparse
from html.parser import HTMLParser

CACHE_RAW = os.path.expanduser("/Users/tracy/WorkBuddy/2026-06-24-03-46-34/.cache/shared-football/raw/2026-06-15")
CACHE_PARSED = os.path.expanduser("/Users/tracy/WorkBuddy/2026-06-24-03-46-34/.cache/shared-football/parsed")

def parse_ouzhi_html(html):
    """
    解析 ouzhi 页面 HTML，提取：
    - Pinnacle 行（公司名含 'Pi' 或 'nacle'）
    - 全部30家公司
    - 平均值行（含'平均值'或居末）
    - 离散值行
    """
    # 用正则直接提取表格行数据（比 HTMLParser 更可靠）
    # 每行格式: 序号 公司名 初主 初平 初客 即时主 即时平 即时客 ...
    # 从 WebFetch 结果看，数据是 text 表格形式

    result = {
        "pinnacle": {},
        "bookmakers": [],
        "average": {},
        "dispersion": {}
    }

    # 方法: 按行分割，找包含赔率数字的行
    lines = html.split("\n")
    in_table = False
    pinnacle_row = None
    all_rows = []

    for i, line in enumerate(lines):
        # 检测表格开始
        if "序号" in line and "赔率公司" in line:
            in_table = True
            continue
        if in_table and ("声明" in line or "下载" in line):
            in_table = False
            continue

        if in_table:
            # 尝试提取行数据：序号 + 公司名 + 数字
            # 找包含多位小数的行（赔率特征）
            nums = re.findall(r"\d+\.\d{2}", line)
            if len(nums) >= 6:  # 至少有初盘3个+即时3个赔率
                all_rows.append(line.strip())

    # 如果上面方法没找到，用更激进的方法：直接搜 Pinnacle
    # 从 WebFetch 结果看，Pinnacle 行包含 "Pi" 和 "nacle"
    pinnacle_data = {}
    avg_data = {}
    disp_data = {}

    # 提取 Pinnacle 数据
    p_idx = html.find("Pi")
    if p_idx > 0:
        # 找 Pinnacle 所在行
        line_start = html.rfind("\n", 0, p_idx)
        line_end = html.find("\n", p_idx)
        if line_start > 0 and line_end > 0:
            p_line = html[line_start:line_end]
            nums = re.findall(r"\d+\.\d+", p_line)
            if len(nums) >= 6:
                pinnacle_data = {
                    "open": {"home": float(nums[0]), "draw": float(nums[1]), "away": float(nums[2])},
                    "current": {"home": float(nums[3]), "draw": float(nums[4]), "away": float(nums[5])}
                }

    # 提取平均值
    avg_idx = html.find("平均值")
    if avg_idx < 0:
        avg_idx = html.find("平均")
    if avg_idx > 0:
        line_start = html.rfind("\n", 0, avg_idx)
        line_end = html.find("\n", avg_idx)
        if line_start > 0 and line_end > 0:
            avg_line = html[line_start:line_end]
            nums = re.findall(r"\d+\.\d+", avg_line)
            if len(nums) >= 6:
                avg_data = {
                    "open": {"home": float(nums[0]), "draw": float(nums[1]), "away": float(nums[2])},
                    "current": {"home": float(nums[3]), "draw": float(nums[4]), "away": float(nums[5])}
                }

    # 提取离散值
    disp_idx = html.find("离散")
    if disp_idx > 0:
        line_start = html.rfind("\n", 0, disp_idx)
        line_end = html.find("\n", disp_idx)
        if line_start > 0 and line_end > 0:
            disp_line = html[line_start:line_end]
            nums = re.findall(r"\d+\.\d+", disp_line)
            if len(nums) >= 6:
                disp_data = {
                    "open": {"home": float(nums[0]), "draw": float(nums[1]), "away": float(nums[2])},
                    "current": {"home": float(nums[3]), "draw": float(nums[4]), "away": float(nums[5])}
                }

    result["pinnacle"] = pinnacle_data
    result["average"] = avg_data
    result["dispersion"] = disp_data

    return result

def parse_all_fids(fids, date_str):
    """解析多个 fid 的 ouzhi 页面"""
    all_data = {}
    for fid in fids:
        html_file = os.path.join(CACHE_RAW, f"ouzhi_{fid}.html")
        if not os.path.exists(html_file):
            print(f"  ⚠️  文件不存在: {html_file}")
            continue

        with open(html_file, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        parsed = parse_ouzhi_html(html)

        # 保存到 parsed 目录
        out_file = os.path.join(CACHE_PARSED, f"{date_str}_{fid}_ouzhi.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)

        all_data[str(fid)] = parsed
        print(f"  ✅ fid={fid}: Pinnacle={parsed['pinnacle']}, avg={parsed['average']}")

    # 保存汇总
    summary_file = os.path.join(CACHE_PARSED, f"{date_str}_ouzhi_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\n📊 汇总已保存: {summary_file}")
    return all_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fid", help="单个 fid")
    parser.add_argument("--fids", help="逗号分隔的 fid 列表")
    parser.add_argument("--date", default="2026-06-15")
    args = parser.parse_args()

    if args.fid:
        fids = [args.fid]
    elif args.fids:
        fids = [f.strip() for f in args.fids.split(",")]
    else:
        fids = ["1359200", "1359203", "1359236", "1359239"]

    print(f"🔍 解析 {len(fids)} 个 ouzhi 页面...")
    parse_all_fids(fids, args.date)

if __name__ == "__main__":
    main()
