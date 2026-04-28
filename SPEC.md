# Auto Income Engine - 项目规格书

## 目标
构建一个全自动的财经内容生成与发布系统，通过程序化 SEO 和内容变现产生被动收入。

## 架构

```
auto-income-engine/
├── src/
│   ├── data/          # 数据采集层
│   ├── analysis/      # 分析引擎
│   ├── content/       # 内容生成
│   └── publish/       # 发布管道
├── configs/           # 配置文件
├── templates/         # 内容模板
├── output/            # 生成的内容输出
├── main.py            # 主入口
└── scheduler.py       # 定时任务调度
```

## 模块说明

### 1. 数据采集层 (src/data/)
- 使用 akshare 获取 A 股每日行情数据
- 获取板块资金流向
- 获取 ETF 估值数据
- 获取基金净值排名
- 获取北向资金数据
- 缓存机制避免重复请求

### 2. 分析引擎 (src/analysis/)
- 市场概况分析（涨跌比、成交量、热点板块）
- 技术指标计算（均线、MACD、RSI）
- 资金面分析（北向资金、主力资金）
- 估值分析（PE/PB 历史分位）
- 生成结构化分析数据

### 3. 内容生成器 (src/content/)
- 每日市场复盘文章
- 板块热点分析
- 个股/ETF 估值报告
- 基金配置建议
- 生成 Markdown 格式内容
- 支持多模板切换

### 4. 发布管道 (src/publish/)
- 生成静态 HTML 博客页面
- 支持 GitHub Pages 发布
- 飞书文档自动推送
- RSS Feed 生成
- SEO 元数据优化

## 技术栈
- Python 3.8+
- akshare (股票数据)
- jinja2 (模板引擎)
- schedule/cron (定时任务)
- markdown (内容格式)

## 变现策略
1. 每日免费内容 → SEO 流量 → 广告收入
2. 飞书付费订阅群 → 深度分析报告
3. 基金/股票数据工具 → 付费功能
