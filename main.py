#!/usr/bin/env python3
"""Auto Income Engine - Main entry point for daily automated financial content generation.

Usage:
    python3 main.py                    # Generate all reports for today
    python3 main.py --mode daily       # Daily recap only
    python3 main.py --mode fund        # Fund valuation only
    python3 main.py --mode all         # All reports + publish
    python3 main.py --date 2026-04-27  # Specific date
"""

import sys
import os
import argparse
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from content.generator import (
    generate_daily_recap,
    generate_fund_valuation_report,
    generate_sector_analysis,
    generate_weekly_outlook,
)
from publish.publisher import save_markdown, save_html, ensure_output_dirs


def print_banner():
    print("""
╔══════════════════════════════════════════╗
║     🤖 Auto Income Engine v0.1           ║
║     AI-Powered Financial Content Gen      ║
╚══════════════════════════════════════════╝
""")


def run_daily(date_str=None):
    """Generate daily market recap."""
    print(f"\n📊 生成每日市场复盘... ({date_str or 'today'})")
    content = generate_daily_recap(date=date_str)
    
    filename = f"{date_str or datetime.now().strftime('%Y-%m-%d')}-market-recap.md"
    path = save_markdown(content, filename, "daily")
    print(f"   ✅ 已保存: {path}")
    
    html_filename = filename.replace(".md", ".html")
    save_html(content, html_filename, "daily", title="A股每日市场复盘")
    return content


def run_fund(date_str=None):
    """Generate fund valuation report."""
    print(f"\n💰 生成基金估值报告... ({date_str or 'today'})")
    content = generate_fund_valuation_report(date=date_str)
    
    filename = f"{date_str or datetime.now().strftime('%Y-%m-%d')}-fund-valuation.md"
    path = save_markdown(content, filename, "fund")
    print(f"   ✅ 已保存: {path}")
    
    html_filename = filename.replace(".md", ".html")
    save_html(content, html_filename, "fund", title="基金估值日报")
    return content


def run_sector(date_str=None):
    """Generate sector analysis."""
    print(f"\n🔥 生成板块分析... ({date_str or 'today'})")
    content = generate_sector_analysis(date=date_str)
    
    filename = f"{date_str or datetime.now().strftime('%Y-%m-%d')}-sector-analysis.md"
    path = save_markdown(content, filename, "sector")
    print(f"   ✅ 已保存: {path}")
    return content


def run_weekly():
    """Generate weekly outlook."""
    print(f"\n📅 生成周度展望...")
    content = generate_weekly_outlook()
    
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}-weekly-outlook.md"
    path = save_markdown(content, filename, "weekly")
    print(f"   ✅ 已保存: {path}")
    return content


def build_parser():
    parser = argparse.ArgumentParser(description="Auto Income Engine")
    parser.add_argument("--mode", choices=["daily", "fund", "sector", "weekly", "all"],
                        default="all", help="Report mode")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD)")
    parser.add_argument("--publish", action="store_true", help="Also generate HTML site")
    return parser


def main():
    print_banner()
    ensure_output_dirs()
    
    args = build_parser().parse_args()
    date_str = args.date
    
    results = {}
    
    if args.mode in ("daily", "all"):
        results["daily"] = run_daily(date_str)
    
    if args.mode in ("fund", "all"):
        results["fund"] = run_fund(date_str)
    
    if args.mode in ("sector", "all"):
        results["sector"] = run_sector(date_str)
    
    if args.mode in ("weekly", "all"):
        results["weekly"] = run_weekly()
    
    if args.publish:
        from publish.publisher import save_html
        for category, content in results.items():
            filename = f"{date_str or datetime.now().strftime('%Y-%m-%d')}-{category}.html"
            save_html(content, filename, category, title=f"A股{category}分析")
    
    print(f"\n{'='*50}")
    print(f"✅ 完成! 共生成 {len(results)} 份报告")
    print(f"📁 输出目录: {os.path.join(os.path.dirname(__file__), 'output')}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
