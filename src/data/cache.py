"""File-based JSON cache for fetched market data."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


LOGGER = logging.getLogger(__name__)
CHINA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = REPO_ROOT / "output" / "cache"


class FileCache:
    """Small JSON cache for pandas DataFrames.

    The default expiry is the current trading day's close (15:30 China time).
    If data is fetched after the close, it expires at the end of that calendar
    day so repeated post-close runs do not call the same API again.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = Path(cache_dir or DEFAULT_CACHE_DIR)

    def get_dataframe(self, key: str, allow_expired: bool = False) -> Optional["pd.DataFrame"]:
        """Return a cached DataFrame, or None when missing/expired/unreadable."""

        path = self._path_for_key(key)
        if not path.exists():
            return None

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            expires_at = datetime.fromisoformat(payload["expires_at"])
            expired = self._now() > expires_at
            if expired and not allow_expired:
                return None

            pd = self._require_pandas()
            df = pd.DataFrame(payload.get("data", []), columns=payload.get("columns"))
            df.attrs["cache_key"] = key
            df.attrs["cache_path"] = str(path)
            df.attrs["cache_created_at"] = payload.get("created_at")
            df.attrs["cache_expires_at"] = payload.get("expires_at")
            df.attrs["cache_stale"] = expired
            return df
        except Exception as exc:
            LOGGER.warning("Failed to read cache %s: %s", path, exc)
            return None

    def set_dataframe(
        self,
        key: str,
        df: "pd.DataFrame",
        *,
        ttl_seconds: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Store a DataFrame as a JSON file."""

        now = self._now()
        expires_at = expires_at or self._expiry_from_ttl(now, ttl_seconds)
        path = self._path_for_key(key)
        payload = {
            "key": key,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "columns": list(df.columns),
            "data": json.loads(df.to_json(orient="records", date_format="iso", force_ascii=False)),
        }

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + ".tmp")
            tmp_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_path.replace(path)
        except Exception as exc:
            LOGGER.warning("Failed to write cache %s: %s", path, exc)

    def clear_expired(self) -> int:
        """Delete expired cache files and return the number removed."""

        removed = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if self._now() > datetime.fromisoformat(payload["expires_at"]):
                    path.unlink()
                    removed += 1
            except Exception as exc:
                LOGGER.warning("Failed to inspect cache %s: %s", path, exc)
        return removed

    def _expiry_from_ttl(self, now: datetime, ttl_seconds: Optional[int]) -> datetime:
        if ttl_seconds is not None:
            return now + timedelta(seconds=ttl_seconds)
        return self._end_of_trading_day(now)

    def _path_for_key(self, key: str) -> Path:
        safe_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", key).strip("_.-") or "cache"
        digest = sha256(key.encode("utf-8")).hexdigest()[:12]
        return self.cache_dir / f"{safe_key}-{digest}.json"

    @staticmethod
    def _end_of_trading_day(now: datetime) -> datetime:
        trading_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if now <= trading_close:
            return trading_close
        return datetime.combine(now.date(), time.max, tzinfo=now.tzinfo)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(CHINA_TZ)

    @staticmethod
    def _require_pandas() -> Any:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependency 'pandas'. Install dependencies with: "
                "pip install -r requirements.txt"
            ) from exc
        return pd
