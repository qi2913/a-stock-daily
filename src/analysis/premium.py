"""Premium Analysis - Technical indicators, sentiment, key levels.

Requires: pip install ta (technical analysis library)
If ta is not available, falls back to manual calculations.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
import json

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.fetcher import fetch_market_overview, DataFetchError

# Try to import ta, fall back to manual
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False


def fetch_index_history(symbol: str, days: int = 120) -> Optional[pd.DataFrame]:
    """Fetch historical daily data for an index using cached approach.
    
    Tries multiple akshare endpoints in order.
    """
    try:
        import akshare as ak
    except ImportError:
        return None
    
    # Symbol mapping
    symbol_map = {
        "000001": "sh000001",  # 上证指数
        "399001": "sz399001",  # 深证成指
        "399006": "sz399006",  # 创业板指
    }
    
    akshare_symbol = symbol_map.get(symbol, symbol)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days + 10)).strftime("%Y%m%d")
    
    # Try eastmoney endpoint
    try:
        df = ak.stock_zh_index_daily_em(
            symbol=akshare_symbol,
            start_date=start_date,
            end_date=end_date,
        )
        if df is not None and not df.empty:
            df = df.rename(columns={
                "date": "date", "open": "open", "close": "close",
                "high": "high", "low": "low", "volume": "volume",
            })
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date").sort_index()
            return df.tail(days)
    except Exception:
        pass
    
    # Try sina endpoint (simpler, less likely to be throttled)
    try:
        df = ak.stock_zh_index_daily(symbol=akshare_symbol)
        if df is not None and not df.empty:
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date").sort_index()
            return df.tail(days)
    except Exception:
        pass
    
    return None


def calc_ma(series: pd.Series, period: int) -> pd.Series:
    """Calculate moving average."""
    return series.rolling(window=period).mean()


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI manually."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
              ) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD manually."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def detect_cross(series1: pd.Series, series2: pd.Series) -> str:
    """Detect golden cross (金叉) or death cross (死叉)."""
    if len(series1) < 3 or len(series2) < 3:
        return "数据不足"
    prev_diff = series1.iloc[-2] - series2.iloc[-2]
    curr_diff = series1.iloc[-1] - series2.iloc[-1]
    if prev_diff <= 0 and curr_diff > 0:
        return "🟢 金叉（看涨信号）"
    elif prev_diff >= 0 and curr_diff < 0:
        return "🔴 死叉（看跌信号）"
    else:
        return "➡️ 无交叉"


def find_support_resistance(series: pd.Series) -> Dict[str, float]:
    """Find simple support and resistance levels."""
    recent = series.tail(60)
    high = recent.max()
    low = recent.min()
    avg = recent.mean()
    
    resistance = round(float(high), 2)
    support = round(float(low), 2)
    pivot = round(float(avg), 2)
    
    return {
        "resistance": resistance,
        "support": support,
        "pivot": pivot,
    }


def calc_sentiment(index_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Calculate market sentiment score (0-100). 0 = extreme fear, 100 = extreme greed."""
    score = 50  # Default neutral
    
    if index_data is None:
        return {"score": 50, "label": "中性", "emoji": "😐", "detail": "数据不足"}
    
    # Check price vs moving averages
    if "close" in index_data.columns and len(index_data) >= 20:
        close = index_data["close"]
        ma5 = calc_ma(close, 5)
        ma20 = calc_ma(close, 20)
        
        if ma5.iloc[-1] > ma20.iloc[-1]:
            score += 10
        else:
            score -= 10
    
    # Check RSI
    if "close" in index_data.columns and len(index_data) >= 14:
        rsi = calc_rsi(index_data["close"])
        if len(rsi) > 0:
            last_rsi = rsi.iloc[-1]
            if last_rsi > 70:
                score += 15
            elif last_rsi < 30:
                score -= 15
            elif last_rsi > 60:
                score += 5
            elif last_rsi < 40:
                score -= 5
    
    # Clamp
    score = max(0, min(100, int(score)))
    
    # Label
    if score >= 70:
        label, emoji = "极度贪婪", "🤩"
    elif score >= 55:
        label, emoji = "偏多", "😊"
    elif score >= 45:
        label, emoji = "中性", "😐"
    elif score >= 25:
        label, emoji = "偏空", "😟"
    else:
        label, emoji = "极度恐惧", "😱"
    
    return {"score": score, "label": label, "emoji": emoji, "detail": f"市场情绪{label}"}


def generate_premium_report() -> Dict[str, Any]:
    """Generate premium technical analysis report.
    
    Returns dict with: technical_indicators, sentiment, key_levels, signals
    """
    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "technical_indicators": "",
        "sentiment": "",
        "key_levels": "",
        "signals": "",
    }
    
    # Fetch history for 上证指数
    hist = fetch_index_history("000001", days=120)
    
    if hist is None or hist.empty:
        result["technical_indicators"] = "⚠️ 历史数据获取失败，技术指标暂不可用。"
        result["sentiment"] = "⚠️ 无法计算情绪指标。"
        return result
    
    close = hist.get("close", pd.Series())
    if close.empty:
        result["technical_indicators"] = "⚠️ 数据格式异常。"
        return result
    
    # Moving Averages
    ma5 = calc_ma(close, 5)
    ma10 = calc_ma(close, 10)
    ma20 = calc_ma(close, 20)
    ma60 = calc_ma(close, 60)
    
    # RSI
    rsi_series = calc_rsi(close, 14)
    
    # MACD
    macd_line, signal_line, hist_line = calc_macd(close)
    
    # Cross detection
    ma_cross = detect_cross(ma5, ma20)
    macd_cross = detect_cross(macd_line, signal_line)
    
    # Support/Resistance
    levels = find_support_resistance(close)
    
    # Current values
    current_price = float(close.iloc[-1])
    last_ma5 = float(ma5.iloc[-1]) if not pd.isna(ma5.iloc[-1]) else 0
    last_ma20 = float(ma20.iloc[-1]) if not pd.isna(ma20.iloc[-1]) else 0
    last_rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
    
    # Price vs MA
    price_vs_ma5 = "上方" if current_price > last_ma5 else "下方"
    price_vs_ma20 = "上方" if current_price > last_ma20 else "下方"
    
    # Technical indicators report
    tech_lines = [
        f"**📈 技术指标速览（上证指数 @ {current_price}）**\n",
        f"- **MA5**: {last_ma5:.0f} | 价格在MA5{price_vs_ma5}",
        f"- **MA20**: {last_ma20:.0f} | 价格在MA20{price_vs_ma20}",
        f"- **RSI(14)**: {last_rsi:.1f} | {'超买区' if last_rsi > 70 else '超卖区' if last_rsi < 30 else '中性区'}",
        f"- **均线交叉**: {ma_cross}",
        f"- **MACD**: {macd_cross}",
    ]
    result["technical_indicators"] = "\n".join(tech_lines)
    
    # Sentiment
    sentiment = calc_sentiment(hist)
    result["sentiment"] = (
        f"{sentiment['emoji']} **情绪指数**: {sentiment['score']}/100 — {sentiment['label']}"
    )
    
    # Key levels
    result["key_levels"] = (
        f"- **压力位**: {levels['resistance']}\n"
        f"- **支撑位**: {levels['support']}\n"
        f"- **中枢位**: {levels['pivot']}"
    )
    
    # Signals
    signals = []
    if ma_cross.startswith("🟢"):
        signals.append("✅ MA金叉出现，短期看多")
    elif ma_cross.startswith("🔴"):
        signals.append("⚠️ MA死叉出现，短期看空")
    
    if last_rsi > 70:
        signals.append("⚠️ RSI进入超买区，注意回调风险")
    elif last_rsi < 30:
        signals.append("💡 RSI进入超卖区，关注反弹机会")
    
    if current_price < levels["support"]:
        signals.append("🔴 价格跌破支撑位，关注进一步下行风险")
    elif current_price > levels["resistance"]:
        signals.append("🟢 价格突破压力位，关注能否站稳")
    
    if not signals:
        signals.append("➡️ 暂无明确交易信号，建议观望")
    
    result["signals"] = "\n".join(signals)
    
    # Price action summary
    weekly_change = float((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) >= 5 else 0
    monthly_change = float((close.iloc[-1] / close.iloc[-20] - 1) * 100) if len(close) >= 20 else 0
    
    result["price_summary"] = (
        f"近5日: {'+' if weekly_change >= 0 else ''}{weekly_change:.2f}% | "
        f"近20日: {'+' if monthly_change >= 0 else ''}{monthly_change:.2f}%"
    )
    
    return result


def generate_premium_markdown() -> str:
    """Generate premium report as Markdown string for Feishu/blog."""
    report = generate_premium_report()
    
    md = f"""# 📊 A股技术分析报告（付费版）
*生成时间: {report['generated_at']}*

---

## 技术指标
{report['technical_indicators']}

## 情绪指数
{report['sentiment']}

## 关键价位
{report['key_levels']}

## 交易信号
{report['signals']}

---

> ⚠️ 以上为AI自动生成的技术分析，仅供参考，不构成投资建议。
> 💎 本报告为付费订阅内容，每日自动更新。
"""
    return md


if __name__ == "__main__":
    print("📊 生成增值技术分析报告...")
    report = generate_premium_report()
    print(f"\n技术指标:\n{report['technical_indicators']}")
    print(f"\n情绪指数:\n{report['sentiment']}")
    print(f"\n关键价位:\n{report['key_levels']}")
    print(f"\n交易信号:\n{report['signals']}")
