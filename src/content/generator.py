"""Content Generator - Generate publishable financial content."""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(os.path.dirname(HERE), "templates")


def generate_daily_recap(
    date: Optional[str] = None,
    market_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate daily market recap article.
    
    Args:
        date: Date string YYYY-MM-DD, defaults to today
        market_data: Dict with market_summary, sector_hotspots, capital_flow, 
                     north_flow, watch_list keys
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    if market_data is None:
        market_data = _get_default_market_data()
    
    template = """# {date} A股市场复盘

## 📊 大盘概况
{market_summary}

## 🔥 今日热点板块
{sector_hotspots}

## 💰 资金面分析
{capital_flow}

## 📈 北向资金
{north_flow}

## 🎯 明日关注
{watch_list}

---
*数据来源：沪深交易所 & AkShare | 自动生成于 {generate_time}*
*免责声明：本文为AI自动生成，仅供学习参考，不构成投资建议。投资有风险，入市需谨慎。*
"""
    return template.format(
        date=date,
        generate_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        **market_data,
    )


def generate_fund_valuation_report(
    date: Optional[str] = None,
    fund_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate fund/ETF valuation report."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    if fund_data is None:
        fund_data = _get_default_fund_data()
    
    template = """# 基金估值日报 ({date})

## 🔍 估值概览
{valuation_summary}

## 📉 低估区间机会
{undervalued}

## 📈 高估区间风险
{overvalued}

## 💡 定投策略建议
{dca_advice}

---
*数据来源：天天基金 & AkShare | 自动生成于 {generate_time}*
*免责声明：本文为AI自动生成，仅供学习参考，不构成投资建议。*
"""
    return template.format(
        date=date,
        generate_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        **fund_data,
    )


def generate_sector_analysis(
    sector_name: str = "热门板块",
    date: Optional[str] = None,
    sector_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate sector analysis article."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    if sector_data is None:
        sector_data = _get_default_sector_data()
    
    template = """# {sector_name}板块深度分析 ({date})

## 一、板块概况
{overview}

## 二、资金流向
{fund_flow}

## 三、后市展望
{outlook}

---
*数据来源：东方财富 & AkShare | 自动生成于 {generate_time}*
"""
    return template.format(
        sector_name=sector_name,
        date=date,
        generate_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        **sector_data,
    )


def generate_weekly_outlook(
    week_range: Optional[str] = None,
    weekly_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate weekly market outlook."""
    today = datetime.now()
    if week_range is None:
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        next_monday = sunday + timedelta(days=1)
        next_friday = next_monday + timedelta(days=4)
        week_range = f"{monday.strftime('%m/%d')}-{sunday.strftime('%m/%d')}"
    
    if weekly_data is None:
        weekly_data = _get_default_weekly_data()
    
    template = """# A股周度展望 ({week_range})

## 本周回顾
{weekly_review}

## 下周展望
{next_week_outlook}

## 配置策略
{allocation_strategy}

## 风险提示
{risk_warning}

---
*自动生成于 {generate_time}*
"""
    return template.format(
        week_range=week_range,
        generate_time=today.strftime("%Y-%m-%d %H:%M"),
        **weekly_data,
    )


def _get_default_market_data() -> Dict[str, str]:
    return {
        "market_summary": "数据采集中... 请确保已配置 akshare 并运行数据获取。",
        "sector_hotspots": "数据采集中...",
        "capital_flow": "数据采集中...",
        "north_flow": "数据采集中...",
        "watch_list": "关注政策面变化和成交量异动。",
    }


def _get_default_fund_data() -> Dict[str, str]:
    return {
        "valuation_summary": "数据采集中...",
        "undervalued": "数据采集中...",
        "overvalued": "数据采集中...",
        "dca_advice": "定投建议：关注低估值指数基金，保持纪律性定投。",
    }


def _get_default_sector_data() -> Dict[str, str]:
    return {
        "overview": "数据采集中...",
        "fund_flow": "数据采集中...",
        "outlook": "关注政策支持和资金持续流入的板块。",
    }


def _get_default_weekly_data() -> Dict[str, str]:
    return {
        "weekly_review": "数据采集中...",
        "next_week_outlook": "关注宏观数据和政策动向。",
        "allocation_strategy": "建议保持股债平衡，控制仓位风险。",
        "risk_warning": "市场有风险，投资需谨慎。本文不构成投资建议。",
    }
