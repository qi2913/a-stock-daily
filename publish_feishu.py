#!/usr/bin/env python3
"""Publish reports to Feishu documents."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from analysis.engine import analyze_market


def generate_feishu_content() -> str:
    """Generate Feishu-friendly Markdown content for today's report."""
    analysis = analyze_market()
    date = datetime.now().strftime("%Y-%m-%d")
    
    content = f"""# 📊 A股每日复盘 ({date})
    
## 大盘概况
{analysis.get("market_summary", "数据加载中...")}

## 资金面
{analysis.get("capital_flow", "数据加载中...")}

## 明日关注
{analysis.get("watch_list", "")}

---

## 💰 基金估值速览
{analysis.get("fund_ranking", "数据加载中...")}

---
> 🤖 由 AI Agent 自动生成 | 仅供参考
> 💎 付费订阅获取完整技术分析报告

"""
    return content


if __name__ == "__main__":
    content = generate_feishu_content()
    # Save to file for Feishu doc creation
    out_path = os.path.join(
        os.path.dirname(__file__), "output", "feishu",
        f"{datetime.now().strftime('%Y-%m-%d')}-feishu.md"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Feishu content saved: {out_path}")
    print(f"\n{content}")
