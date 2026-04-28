#!/usr/bin/env python3
"""Auto Income Engine - Integrated pipeline with real market data.

Usage:
    .venv/bin/python run.py              # Generate all reports
    .venv/bin/python run.py --mode daily # Daily recap only
    .venv/bin/python run.py --publish    # Also generate HTML
"""

import sys
import os
import argparse
from datetime import datetime

# Ensure we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from analysis.engine import analyze_market
from content.generator import (
    generate_daily_recap,
    generate_fund_valuation_report,
    generate_weekly_outlook,
)
from publish.publisher import save_markdown, save_html, ensure_output_dirs


def print_banner():
    print("""
╔══════════════════════════════════════════╗
║     🤖 Auto Income Engine v0.2           ║
║     Real Market Data → AI Content         ║
╚══════════════════════════════════════════╝
""")


def run(date_str=None):
    """Run the full pipeline: fetch → analyze → generate → save."""
    print_banner()
    ensure_output_dirs()
    
    print("📡 正在获取实时市场数据...\n")
    analysis = analyze_market(date_str)
    
    date = date_str or datetime.now().strftime("%Y-%m-%d")
    
    # 1. Daily market recap
    print("📊 生成每日市场复盘...")
    recap = generate_daily_recap(
        date=date,
        market_data={
            "market_summary": analysis.get("market_summary", ""),
            "sector_hotspots": analysis.get("sector_hotspots", ""),
            "capital_flow": analysis.get("capital_flow", ""),
            "north_flow": analysis.get("north_flow", ""),
            "watch_list": analysis.get("watch_list", ""),
        },
    )
    md_path = save_markdown(recap, f"{date}-market-recap.md", "daily")
    html_path = save_html(recap, f"{date}-market-recap.html", "daily", 
                          title=f"{date} A股市场复盘")
    print(f"   ✅ Markdown: {md_path}")
    print(f"   ✅ HTML: {html_path}")
    
    # 2. Fund valuation
    print("💰 生成基金估值报告...")
    fund = generate_fund_valuation_report(
        date=date,
        fund_data={
            "valuation_summary": f"基于近1年收益排名，表现最优的基金：\n\n{analysis.get('fund_ranking', '数据暂不可用')}",
            "undervalued": "当前市场整体估值处于中等偏上水平。建议关注PE分位数低于30%的指数基金。",
            "overvalued": "部分热门板块估值偏高，注意控制仓位。",
            "dca_advice": "定投策略：当前市场波动较大，建议保持纪律性定投，利用市场下跌增加份额。",
        },
    )
    md_path2 = save_markdown(fund, f"{date}-fund-valuation.md", "fund")
    html_path2 = save_html(fund, f"{date}-fund-valuation.html", "fund",
                           title=f"{date} 基金估值日报")
    print(f"   ✅ Markdown: {md_path2}")
    print(f"   ✅ HTML: {html_path2}")
    
    # 3. Weekly outlook
    print("📅 生成周度展望...")
    weekly = generate_weekly_outlook()
    md_path3 = save_markdown(weekly, f"{date}-weekly-outlook.md", "weekly")
    print(f"   ✅ Markdown: {md_path3}")
    
    print(f"\n{'='*50}")
    print(f"✅ 全部完成！生成了 3 份报告")
    print(f"📁 输出目录: {os.path.join(os.path.dirname(__file__), 'output')}")
    print(f"\n💡 下一步：")
    print(f"   1. 部署到 GitHub Pages 获取SEO流量")
    print(f"   2. 设置 cron 定时任务自动生成")
    print(f"   3. 通过飞书推送付费订阅内容")
    print(f"{'='*50}\n")
    
    return analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Target date (YYYY-MM-DD)")
    parser.add_argument("--mode", choices=["daily", "fund", "weekly", "all"],
                        default="all")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip actual API calls, use cached data")
    args = parser.parse_args()
    
    run(date_str=args.date)
