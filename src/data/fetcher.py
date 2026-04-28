"""AkShare-backed financial data fetchers."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, TYPE_CHECKING

from .cache import FileCache

if TYPE_CHECKING:
    import pandas as pd


LOGGER = logging.getLogger(__name__)
CHINA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.5
CACHE = FileCache()


class DataFetchError(RuntimeError):
    """Raised when an upstream data fetch fails after retries."""


MARKET_INDEX_NAMES = ("上证指数", "深证成指", "创业板指")

MARKET_INDEX_COLUMNS: Dict[str, str] = {
    "序号": "rank",
    "代码": "code",
    "名称": "name",
    "最新价": "latest",
    "涨跌额": "change",
    "涨跌幅": "pct_change",
    "成交量": "volume",
    "成交额": "turnover",
    "振幅": "amplitude",
    "最高": "high",
    "最低": "low",
    "今开": "open",
    "昨收": "prev_close",
    "量比": "volume_ratio",
}

SECTOR_FLOW_COLUMNS: Dict[str, str] = {
    "序号": "rank",
    "名称": "sector_name",
    "板块名称": "sector_name",
    "今日涨跌幅": "pct_change",
    "涨跌幅": "pct_change",
    "今日主力净流入-净额": "main_net_inflow",
    "主力净流入-净额": "main_net_inflow",
    "今日主力净流入-净占比": "main_net_inflow_pct",
    "主力净流入-净占比": "main_net_inflow_pct",
    "今日超大单净流入-净额": "super_large_net_inflow",
    "超大单净流入-净额": "super_large_net_inflow",
    "今日超大单净流入-净占比": "super_large_net_inflow_pct",
    "超大单净流入-净占比": "super_large_net_inflow_pct",
    "今日大单净流入-净额": "large_net_inflow",
    "大单净流入-净额": "large_net_inflow",
    "今日大单净流入-净占比": "large_net_inflow_pct",
    "大单净流入-净占比": "large_net_inflow_pct",
    "今日中单净流入-净额": "medium_net_inflow",
    "中单净流入-净额": "medium_net_inflow",
    "今日中单净流入-净占比": "medium_net_inflow_pct",
    "中单净流入-净占比": "medium_net_inflow_pct",
    "今日小单净流入-净额": "small_net_inflow",
    "小单净流入-净额": "small_net_inflow",
    "今日小单净流入-净占比": "small_net_inflow_pct",
    "小单净流入-净占比": "small_net_inflow_pct",
    "今日主力净流入最大股": "top_net_inflow_stock",
    "主力净流入最大股": "top_net_inflow_stock",
}

NORTH_FLOW_COLUMNS: Dict[str, str] = {
    "序号": "rank",
    "交易日": "trade_date",
    "类型": "connect_type",
    "板块": "board",
    "资金方向": "direction",
    "交易状态": "trade_status",
    "成交净买额": "net_buy_amount",
    "资金净流入": "net_inflow",
    "资金余额": "balance",
    "上涨数": "rising_count",
    "持平数": "flat_count",
    "下跌数": "falling_count",
    "相关指数": "related_index",
    "指数涨跌幅": "index_pct_change",
}

ETF_VALUATION_COLUMNS: Dict[str, str] = {
    "序号": "rank",
    "基金代码": "fund_code",
    "代码": "fund_code",
    "基金简称": "fund_name",
    "名称": "fund_name",
    "类型": "fund_type",
    "最新价": "latest",
    "涨跌额": "change",
    "涨跌幅": "pct_change",
    "成交量": "volume",
    "成交额": "turnover",
    "开盘价": "open",
    "今开": "open",
    "最高价": "high",
    "最高": "high",
    "最低价": "low",
    "最低": "low",
    "昨收": "prev_close",
    "换手率": "turnover_rate",
    "量比": "volume_ratio",
    "外盘": "buy_volume",
    "内盘": "sell_volume",
    "最新份额": "latest_share",
    "流通市值": "float_market_cap",
    "总市值": "total_market_cap",
    "数据日期": "data_date",
    "更新时间": "updated_at",
    "IOPV实时估值": "iopv",
    "基金折价率": "discount_rate",
    "折价率": "discount_rate",
    "主力净流入-净额": "main_net_inflow",
    "主力净流入-净占比": "main_net_inflow_pct",
    "超大单净流入-净额": "super_large_net_inflow",
    "超大单净流入-净占比": "super_large_net_inflow_pct",
    "大单净流入-净额": "large_net_inflow",
    "大单净流入-净占比": "large_net_inflow_pct",
    "中单净流入-净额": "medium_net_inflow",
    "中单净流入-净占比": "medium_net_inflow_pct",
    "小单净流入-净额": "small_net_inflow",
    "小单净流入-净占比": "small_net_inflow_pct",
}

FUND_RANK_COLUMNS: Dict[str, str] = {
    "序号": "rank",
    "基金代码": "fund_code",
    "基金简称": "fund_name",
    "日期": "date",
    "单位净值": "unit_nav",
    "累计净值": "accumulated_nav",
    "日增长率": "daily_return",
    "近1周": "one_week_return",
    "近1月": "one_month_return",
    "近3月": "three_month_return",
    "近6月": "six_month_return",
    "近1年": "one_year_return",
    "近2年": "two_year_return",
    "近3年": "three_year_return",
    "今年来": "year_to_date_return",
    "成立来": "since_inception_return",
    "自定义": "custom_return",
    "手续费": "fee",
}

NUMERIC_COLUMNS = {
    "rank",
    "latest",
    "change",
    "pct_change",
    "volume",
    "turnover",
    "amplitude",
    "high",
    "low",
    "open",
    "prev_close",
    "volume_ratio",
    "main_net_inflow",
    "main_net_inflow_pct",
    "super_large_net_inflow",
    "super_large_net_inflow_pct",
    "large_net_inflow",
    "large_net_inflow_pct",
    "medium_net_inflow",
    "medium_net_inflow_pct",
    "small_net_inflow",
    "small_net_inflow_pct",
    "net_buy_amount",
    "net_inflow",
    "balance",
    "rising_count",
    "flat_count",
    "falling_count",
    "index_pct_change",
    "iopv",
    "discount_rate",
    "turnover_rate",
    "buy_volume",
    "sell_volume",
    "latest_share",
    "float_market_cap",
    "total_market_cap",
    "unit_nav",
    "accumulated_nav",
    "daily_return",
    "one_week_return",
    "one_month_return",
    "three_month_return",
    "six_month_return",
    "one_year_return",
    "two_year_return",
    "three_year_return",
    "year_to_date_return",
    "since_inception_return",
    "custom_return",
}

FUND_SORT_COLUMNS = {
    "daily_return": "daily_return",
    "日增长率": "daily_return",
    "one_week_return": "one_week_return",
    "近1周": "one_week_return",
    "one_month_return": "one_month_return",
    "近1月": "one_month_return",
    "three_month_return": "three_month_return",
    "近3月": "three_month_return",
    "six_month_return": "six_month_return",
    "近6月": "six_month_return",
    "one_year_return": "one_year_return",
    "近1年": "one_year_return",
    "two_year_return": "two_year_return",
    "近2年": "two_year_return",
    "three_year_return": "three_year_return",
    "近3年": "three_year_return",
    "year_to_date_return": "year_to_date_return",
    "今年来": "year_to_date_return",
    "since_inception_return": "since_inception_return",
    "成立来": "since_inception_return",
}


def fetch_market_overview(retries: int = DEFAULT_RETRIES, use_cache: bool = True) -> "pd.DataFrame":
    """Fetch 上证指数, 深证成指, and 创业板指 market index data."""

    return _fetch_with_cache(
        cache_key="market_overview",
        fetch_fn=_fetch_market_overview_from_api,
        retries=retries,
        use_cache=use_cache,
    )


def fetch_sector_flow(
    indicator: str = "今日",
    sector_type: str = "行业资金流",
    retries: int = DEFAULT_RETRIES,
    use_cache: bool = True,
) -> "pd.DataFrame":
    """Fetch sector capital-flow rankings."""

    cache_key = f"sector_flow_{indicator}_{sector_type}"
    return _fetch_with_cache(
        cache_key=cache_key,
        fetch_fn=lambda: _fetch_sector_flow_from_api(indicator, sector_type),
        retries=retries,
        use_cache=use_cache,
    )


def fetch_north_flow(retries: int = DEFAULT_RETRIES, use_cache: bool = True) -> "pd.DataFrame":
    """Fetch north-bound Stock Connect capital-flow data."""

    return _fetch_with_cache(
        cache_key="north_flow",
        fetch_fn=_fetch_north_flow_from_api,
        retries=retries,
        use_cache=use_cache,
    )


def fetch_etf_valuation(retries: int = DEFAULT_RETRIES, use_cache: bool = True) -> "pd.DataFrame":
    """Fetch ETF market data including IOPV valuation and discount rate."""

    return _fetch_with_cache(
        cache_key="etf_valuation",
        fetch_fn=_fetch_etf_valuation_from_api,
        retries=retries,
        use_cache=use_cache,
    )


def fetch_top_funds(
    symbol: str = "全部",
    sort_by: str = "one_year_return",
    limit: int = 50,
    retries: int = DEFAULT_RETRIES,
    use_cache: bool = True,
) -> "pd.DataFrame":
    """Fetch top performing open funds sorted by a return metric."""

    sort_column = FUND_SORT_COLUMNS.get(sort_by, sort_by)
    cache_key = f"top_funds_{symbol}_{sort_column}_{limit}"
    return _fetch_with_cache(
        cache_key=cache_key,
        fetch_fn=lambda: _fetch_top_funds_from_api(symbol, sort_column, limit),
        retries=retries,
        use_cache=use_cache,
    )


def _fetch_market_overview_from_api() -> "pd.DataFrame":
    pd = _require_pandas()
    ak = _require_akshare()

    try:
        raw = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    except Exception as exc:
        raise DataFetchError(
            "AkShare call stock_zh_index_spot_em(symbol='沪深重要指数') failed: "
            f"{exc}"
        ) from exc

    if not _has_index_names(raw, MARKET_INDEX_NAMES):
        fallback_frames = [raw]
        for symbol in ("上证系列指数", "深证系列指数"):
            try:
                fallback_frames.append(ak.stock_zh_index_spot_em(symbol=symbol))
            except Exception as exc:
                LOGGER.warning(
                    "AkShare fallback call stock_zh_index_spot_em(symbol=%r) failed: %s",
                    symbol,
                    exc,
                )
        raw = pd.concat(fallback_frames, ignore_index=True)

    name_column = "名称" if "名称" in raw.columns else "name"
    df = raw[raw[name_column].isin(MARKET_INDEX_NAMES)].copy()
    if df.empty:
        raise DataFetchError("AkShare returned no target A-share index rows.")

    df = _standardize_dataframe(
        df,
        MARKET_INDEX_COLUMNS,
        ordered_columns=[
            "market",
            "code",
            "name",
            "latest",
            "change",
            "pct_change",
            "volume",
            "turnover",
            "amplitude",
            "high",
            "low",
            "open",
            "prev_close",
            "volume_ratio",
            "fetched_at",
        ],
        static_columns={"market": "A-share"},
    )
    order = {name: index for index, name in enumerate(MARKET_INDEX_NAMES)}
    df["_sort_order"] = df["name"].map(order)
    df = df.sort_values("_sort_order").drop(columns=["_sort_order"])
    return df.reset_index(drop=True)


def _fetch_sector_flow_from_api(indicator: str, sector_type: str) -> "pd.DataFrame":
    ak = _require_akshare()

    try:
        raw = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type=sector_type)
    except Exception as exc:
        raise DataFetchError(
            "AkShare call stock_sector_fund_flow_rank("
            f"indicator={indicator!r}, sector_type={sector_type!r}) failed: {exc}"
        ) from exc

    df = _standardize_dataframe(
        raw,
        SECTOR_FLOW_COLUMNS,
        ordered_columns=[
            "rank",
            "sector_name",
            "indicator",
            "sector_type",
            "pct_change",
            "main_net_inflow",
            "main_net_inflow_pct",
            "super_large_net_inflow",
            "super_large_net_inflow_pct",
            "large_net_inflow",
            "large_net_inflow_pct",
            "medium_net_inflow",
            "medium_net_inflow_pct",
            "small_net_inflow",
            "small_net_inflow_pct",
            "top_net_inflow_stock",
            "fetched_at",
        ],
        static_columns={"indicator": indicator, "sector_type": sector_type},
    )
    return df


def _fetch_north_flow_from_api() -> "pd.DataFrame":
    ak = _require_akshare()

    try:
        raw = ak.stock_hsgt_fund_flow_summary_em()
    except Exception as exc:
        raise DataFetchError(
            "AkShare call stock_hsgt_fund_flow_summary_em() failed: "
            f"{exc}"
        ) from exc

    df = raw.copy()
    direction_column = "资金方向" if "资金方向" in df.columns else "direction"
    if direction_column in df.columns:
        df = df[df[direction_column].astype(str).str.contains("北向", na=False)].copy()
    if df.empty:
        raise DataFetchError("AkShare returned no north-bound capital-flow rows.")

    return _standardize_dataframe(
        df,
        NORTH_FLOW_COLUMNS,
        ordered_columns=[
            "rank",
            "trade_date",
            "connect_type",
            "board",
            "direction",
            "trade_status",
            "net_buy_amount",
            "net_inflow",
            "balance",
            "rising_count",
            "flat_count",
            "falling_count",
            "related_index",
            "index_pct_change",
            "fetched_at",
        ],
    )


def _fetch_etf_valuation_from_api() -> "pd.DataFrame":
    ak = _require_akshare()

    try:
        raw = ak.fund_etf_spot_em()
    except Exception as exc:
        raise DataFetchError(f"AkShare call fund_etf_spot_em() failed: {exc}") from exc

    return _standardize_dataframe(
        raw,
        ETF_VALUATION_COLUMNS,
        ordered_columns=[
            "rank",
            "fund_code",
            "fund_name",
            "fund_type",
            "latest",
            "iopv",
            "discount_rate",
            "change",
            "pct_change",
            "volume",
            "turnover",
            "open",
            "high",
            "low",
            "prev_close",
            "turnover_rate",
            "volume_ratio",
            "latest_share",
            "float_market_cap",
            "total_market_cap",
            "data_date",
            "updated_at",
            "fetched_at",
        ],
    )


def _fetch_top_funds_from_api(symbol: str, sort_column: str, limit: int) -> "pd.DataFrame":
    ak = _require_akshare()

    try:
        raw = ak.fund_open_fund_rank_em(symbol=symbol)
    except Exception as exc:
        raise DataFetchError(
            f"AkShare call fund_open_fund_rank_em(symbol={symbol!r}) failed: {exc}"
        ) from exc

    df = _standardize_dataframe(
        raw,
        FUND_RANK_COLUMNS,
        ordered_columns=[
            "rank",
            "fund_code",
            "fund_name",
            "date",
            "unit_nav",
            "accumulated_nav",
            "daily_return",
            "one_week_return",
            "one_month_return",
            "three_month_return",
            "six_month_return",
            "one_year_return",
            "two_year_return",
            "three_year_return",
            "year_to_date_return",
            "since_inception_return",
            "custom_return",
            "fee",
            "fetched_at",
        ],
    )

    if sort_column not in df.columns:
        raise DataFetchError(
            f"Cannot sort top funds by {sort_column!r}; available columns: "
            f"{', '.join(df.columns)}"
        )

    df = df.sort_values(sort_column, ascending=False, na_position="last")
    if limit > 0:
        df = df.head(limit)
    return df.reset_index(drop=True)


def _fetch_with_cache(
    *,
    cache_key: str,
    fetch_fn: Callable[[], "pd.DataFrame"],
    retries: int,
    use_cache: bool,
) -> "pd.DataFrame":
    if use_cache:
        cached = CACHE.get_dataframe(cache_key)
        if cached is not None:
            return cached

    last_error: Optional[Exception] = None
    attempts = max(1, retries)
    for attempt in range(1, attempts + 1):
        try:
            df = fetch_fn()
            if df.empty:
                raise DataFetchError(f"{cache_key} fetch returned an empty DataFrame.")
            if use_cache:
                CACHE.set_dataframe(cache_key, df)
            return df
        except Exception as exc:
            last_error = exc
            LOGGER.warning(
                "Failed to fetch %s (attempt %s/%s): %s",
                cache_key,
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(DEFAULT_BACKOFF_SECONDS * attempt)

    if use_cache:
        stale = CACHE.get_dataframe(cache_key, allow_expired=True)
        if stale is not None:
            LOGGER.warning("Returning expired cache for %s after API failures.", cache_key)
            return stale

    raise DataFetchError(
        f"Failed to fetch {cache_key} after {attempts} attempt(s): {last_error}"
    ) from last_error


def _standardize_dataframe(
    df: "pd.DataFrame",
    column_map: Dict[str, str],
    *,
    ordered_columns: Sequence[str],
    static_columns: Optional[Dict[str, Any]] = None,
) -> "pd.DataFrame":
    pd = _require_pandas()
    if not isinstance(df, pd.DataFrame):
        raise DataFetchError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    normalized = df.copy()
    normalized = normalized.rename(columns=column_map)
    normalized = normalized.loc[:, ~normalized.columns.duplicated()]

    for column, value in (static_columns or {}).items():
        normalized[column] = value

    normalized["fetched_at"] = _now_iso()
    normalized = _coerce_numeric_columns(normalized, NUMERIC_COLUMNS)
    return _order_columns(normalized, ordered_columns)


def _coerce_numeric_columns(df: "pd.DataFrame", columns: Iterable[str]) -> "pd.DataFrame":
    pd = _require_pandas()
    for column in columns:
        if column in df.columns:
            cleaned = (
                df[column]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.replace("--", "", regex=False)
                .str.strip()
            )
            df[column] = pd.to_numeric(cleaned, errors="coerce")
    return df


def _order_columns(df: "pd.DataFrame", ordered_columns: Sequence[str]) -> "pd.DataFrame":
    present = [column for column in ordered_columns if column in df.columns]
    extras = [column for column in df.columns if column not in present]
    return df[present + extras]


def _has_index_names(df: "pd.DataFrame", names: Sequence[str]) -> bool:
    if df is None or "名称" not in df.columns:
        return False
    found = set(df["名称"].dropna().astype(str))
    return set(names).issubset(found)


def _require_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise DataFetchError(
            "Missing dependency 'pandas'. Install dependencies with: "
            "pip install -r requirements.txt"
        ) from exc
    return pd


def _require_akshare() -> Any:
    try:
        import akshare as ak
    except ImportError as exc:
        raise DataFetchError(
            "Missing dependency 'akshare'. Install dependencies with: "
            "pip install -r requirements.txt"
        ) from exc
    return ak


def _now_iso() -> str:
    return datetime.now(CHINA_TZ).isoformat(timespec="seconds")


__all__ = [
    "DataFetchError",
    "fetch_market_overview",
    "fetch_sector_flow",
    "fetch_north_flow",
    "fetch_etf_valuation",
    "fetch_top_funds",
]
