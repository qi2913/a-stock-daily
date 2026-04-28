# Auto Income Engine - Content Templates

# ============================================================
# Template 1: Daily Market Recap
# ============================================================
DAILY_RECAP = """
# {date} A股市场复盘

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
*数据来源：沪深交易所 | 自动生成于 {generate_time}*
*免责声明：本文为AI自动生成，仅供参考，不构成投资建议。*
"""

# ============================================================
# Template 2: Sector Analysis
# ============================================================
SECTOR_ANALYSIS = """
# {sector_name}板块深度分析 ({date})

## 一、板块概况
{overview}

## 二、龙头个股表现
{leading_stocks}

## 三、资金流向
{fund_flow}

## 四、技术面分析
{technical_analysis}

## 五、后市展望
{outlook}

---
*数据来源：东方财富 | 自动生成于 {generate_time}*
"""

# ============================================================
# Template 3: ETF/Fund Valuation Report
# ============================================================
FUND_VALUATION = """
# 基金估值日报 ({date})

## 🔍 估值概览
{valuation_summary}

## 📉 低估区间机会
{undervalued}

## 📈 高估区间风险
{overvalued}

## 💡 定投策略建议
{dca_advice}

---
*数据来源：天天基金 | 自动生成于 {generate_time}*
"""

# ============================================================
# Template 4: Weekly Market Outlook
# ============================================================
WEEKLY_OUTLOOK = """
# A股周度展望 ({week_range})

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
