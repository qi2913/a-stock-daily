"""Analysis Engine - Transform raw market data into structured analysis."""

from __future__ import annotations

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd

# Add parent to path for data module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.fetcher import (
    fetch_market_overview,
    fetch_north_flow,
    fetch_top_funds,
    fetch_sector_flow,
)


def analyze_market(date_str: Optional[str] = None) -> Dict[str, Any]:
    """Run full market analysis and return structured results.
    
    Returns dict with keys: market_summary, sector_hotspots, capital_flow, 
    north_flow, watch_list, fund_ranking, valuation_summary
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    result = {
        "date": date_str,
        "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # 1. Market overview
    try:
        market_df = fetch_market_overview()
        result["market_summary"] = _analyze_indexes(market_df)
        result["market_data"] = market_df
    except Exception as e:
        result["market_summary"] = f"数据获取失败: {e}"
        result["market_data"] = None
    
    # 2. Sector flow (try, but don't fail)
    try:
        sector_df = fetch_sector_flow()
        result["sector_hotspots"] = _analyze_sectors(sector_df)
        result["sector_data"] = sector_df
    except Exception:
        result["sector_hotspots"] = "板块数据暂不可用（API限流）。请关注日内成交量变化和资金异动。"
        result["sector_data"] = None
    
    # 3. North flow
    try:
        north_df = fetch_north_flow()
        result["north_flow"] = _analyze_north_flow(north_df)
        result["north_data"] = north_df
    except Exception:
        result["north_flow"] = "北向资金数据暂不可用。"
        result["north_data"] = None
    
    # 4. Fund ranking
    try:
        fund_df = fetch_top_funds(sort_by="one_year_return", limit=10)
        result["fund_ranking"] = _analyze_funds(fund_df)
        result["fund_data"] = fund_df
    except Exception:
        result["fund_ranking"] = "基金排名数据暂不可用。"
        result["fund_data"] = None
    
    # 5. Capital flow summary
    result["capital_flow"] = _capital_flow_summary(result)
    
    # 6. Watch list
    result["watch_list"] = _generate_watch_list(result)
    
    return result


def _analyze_indexes(df: pd.DataFrame) -> str:
    """Generate natural language analysis of market indexes."""
    if df is None or df.empty:
        return "市场数据暂不可用。"
    
    lines = []
    
    for _, row in df.iterrows():
        name = row.get("name", "未知")
        latest = row.get("latest", "N/A")
        change = row.get("change", 0)
        pct = row.get("pct_change", 0)
        
        direction = "上涨" if pct > 0 else "下跌" if pct < 0 else "平盘"
        arrow = "📈" if pct > 0 else "📉" if pct < 0 else "➡️"
        
        lines.append(
            f"- {arrow} **{name}**：{latest}，{direction} {abs(pct):.2f}%"
        )
    
    # Determine overall trend
    up_count = sum(1 for _, row in df.iterrows() if row.get("pct_change", 0) > 0)
    
    if up_count >= 2:
        overall = "今日市场整体偏强，三大指数多数收涨。市场情绪较为积极。"
    elif up_count == 0:
        overall = "今日市场整体偏弱，三大指数全线收跌。市场情绪偏谨慎。"
    else:
        overall = "今日市场分化，指数涨跌互现。结构性行情特征明显。"
    
    lines.insert(0, f"**{overall}**\n")
    
    # Add volume info if available
    if "turnover" in df.columns:
        total_turnover = df["turnover"].sum()
        if total_turnover > 0:
            turnover_billion = total_turnover / 1e8
            lines.append(f"\n两市成交额约 {turnover_billion:.0f} 亿元。")
    
    return "\n".join(lines)


def _analyze_sectors(df: pd.DataFrame) -> str:
    """Analyze sector flow data."""
    if df is None or df.empty:
        return "暂无板块数据。"
    
    lines = ["**今日板块资金流向：**\n"]
    
    # Top gainers by net inflow
    if "main_net_inflow" in df.columns and "sector_name" in df.columns:
        top_inflow = df.nlargest(5, "main_net_inflow")
        lines.append("**资金净流入前5：**")
        for _, row in top_inflow.iterrows():
            name = row.get("sector_name", "")
            inflow = row.get("main_net_inflow", 0)
            pct = row.get("pct_change", 0)
            lines.append(f"- {name}：净流入 {inflow/1e8:.2f}亿，涨跌幅 {pct:.2f}%")
    
    return "\n".join(lines)


def _analyze_north_flow(df: pd.DataFrame) -> str:
    """Analyze north-bound capital flow."""
    if df is None or df.empty:
        return "北向资金数据暂不可用。"
    
    lines = ["**北向资金动态：**\n"]
    
    for _, row in df.iterrows():
        date = row.get("trade_date", "")
        net = row.get("net_flow", 0)
        direction = "净流入" if net > 0 else "净流出"
        lines.append(f"- {date}：北向资金{direction} {abs(net/1e8):.2f}亿元")
    
    return "\n".join(lines)


def _analyze_funds(df: pd.DataFrame) -> str:
    """Generate fund ranking analysis."""
    if df is None or df.empty:
        return "暂无基金排名数据。"
    
    lines = ["**近一年表现最优基金（前5）：**\n"]
    
    top5 = df.head(5)
    for i, (_, row) in enumerate(top5.iterrows()):
        name = row.get("name", row.get("fund_name", ""))
        ytd = row.get("one_year_return", row.get("daily_return", "N/A"))
        lines.append(f"{i+1}. {name} - 近1年收益: {ytd:.2f}%" if isinstance(ytd, (int, float)) else f"{i+1}. {name}")
    
    return "\n".join(lines)


def _capital_flow_summary(result: Dict[str, Any]) -> str:
    """Generate capital flow summary."""
    parts = []
    
    market_df = result.get("market_data")
    if market_df is not None and not market_df.empty:
        total_pct = market_df["pct_change"].mean()
        if total_pct > 0.5:
            parts.append("市场整体资金面偏暖，指数普遍收红。")
        elif total_pct < -0.5:
            parts.append("市场整体资金面偏冷，空方力量较强。")
        else:
            parts.append("市场整体资金面中性，多空力量均衡。")
    
    if not parts:
        parts.append("资金面数据暂不可用，请关注后续更新。")
    
    parts.append("\n建议关注：成交量变化、北向资金动向、主力资金流向。")
    return "\n".join(parts)


def _generate_watch_list(result: Dict[str, Any]) -> str:
    """Generate watch list for next trading day."""
    items = [
        "关注政策面是否有新的利好消息",
        "关注北向资金是否持续流入",
        "关注成交量是否有效放大",
        "关注外围市场（美股、港股）走势",
    ]
    
    market_df = result.get("market_data")
    if market_df is not None and not market_df.empty:
        # Check if any index dropped more than 2%
        big_drops = market_df[market_df["pct_change"] < -2]
        if not big_drops.empty:
            names = ", ".join(big_drops["name"].tolist())
            items.append(f"⚠️ {names} 跌幅超2%，关注是否有进一步下探风险")
    
    return "\n".join(f"- {item}" for item in items)
