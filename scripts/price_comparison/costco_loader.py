"""Load and match Costco warehouse CSV data by region."""

from __future__ import annotations

import csv
import logging
import os
import re
import warnings
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path

from .canonical_metadata import CANONICAL_PACKAGES, CanonicalPackageMeta, DEFAULT_COSTCO_DATA_ROOT
from .unit_normalize import ParsedPackage, parse_item_sign

logger = logging.getLogger(__name__)

COSTCO_REGIONS = ("san-francisco", "tustin", "seattle")
GROCERY_TRACKER_TO_COSTCO_REGION = {
    "safeway": "san-francisco",
    "vons-albertsons": "tustin",
}

FILENAME_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2})_([a-z-]+)_.*\.csv$",
)


@dataclass(frozen=True)
class CostcoObservation:
  """One Costco warehouse price observation from a regional CSV."""

  date: str
  region: str
  item_number: str
  product_name: str
  price: float
  size_info: str | None
  availability: str | None
  source_file: str
  timestamp: str
  parsed: ParsedPackage | None = None


@dataclass(frozen=True)
class CostcoItem:
  """Latest Costco catalog row for a single item number within one region."""

  item_number: str
  item_sign: str
  sell_price: float
  timestamp: str
  source_file: str
  region: str
  date: str
  availability: str | None
  parsed: ParsedPackage | None


def costco_data_root() -> Path:
  return Path(os.environ.get("COSTCO_DATA_ROOT", DEFAULT_COSTCO_DATA_ROOT))


def parse_costco_filename(path: Path) -> tuple[str, str] | None:
  """Return (date, region) from e.g. 2026-06-18_san-francisco_consolidated.csv."""
  match = FILENAME_PATTERN.match(path.name)
  if not match:
    return None
  file_date, region = match.group(1), match.group(2)
  return file_date, region


def _timestamp_date(timestamp: str) -> str | None:
  try:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date().isoformat()
  except ValueError:
    return None


def _ts_key(ts: str) -> datetime:
  try:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
  except ValueError:
    return datetime.min


def _row_to_observation(
  row: dict[str, str],
  *,
  file_date: str,
  region: str,
  source_file: str,
) -> CostcoObservation | None:
  item_number = (row.get("itemNumber") or "").strip()
  if not item_number:
    return None
  try:
    price = float(row.get("sellPrice") or 0)
  except ValueError:
    return None
  if price <= 0:
    return None

  timestamp = (row.get("timestamp") or "").strip() or f"{file_date}T00:00:00"
  row_date = _timestamp_date(timestamp) or file_date
  if row_date != file_date:
    warnings.warn(
      f"{source_file}: CSV date {row_date} differs from filename date {file_date} "
      f"for item {item_number}",
      stacklevel=2,
    )

  product_name = (row.get("itemSign") or "").strip()
  availability = (row.get("inventoryStatus") or "").strip() or None

  return CostcoObservation(
    date=row_date,
    region=region,
    item_number=item_number,
    product_name=product_name,
    price=price,
    size_info=product_name or None,
    availability=availability,
    source_file=source_file,
    timestamp=timestamp,
  )


def iter_costco_csv_files(
  data_root: Path | None = None,
  *,
  region: str | None = None,
) -> list[Path]:
  root = data_root or costco_data_root()
  if not root.is_dir():
    raise FileNotFoundError(f"Costco data directory not found: {root}")

  files: list[Path] = []
  for path in sorted(root.iterdir()):
    if not path.is_file():
      continue
    parsed = parse_costco_filename(path)
    if parsed is None:
      continue
    _, file_region = parsed
    if region is not None and file_region != region:
      continue
    files.append(path)
  return files


def load_region_observations(
  region: str,
  data_root: Path | None = None,
) -> list[CostcoObservation]:
  """Load every observation for one Costco region across all dated CSV files."""
  observations: list[CostcoObservation] = []
  for path in iter_costco_csv_files(data_root, region=region):
    parsed = parse_costco_filename(path)
    if parsed is None:
      continue
    file_date, file_region = parsed
    with path.open(newline="", encoding="utf-8") as handle:
      reader = csv.DictReader(handle)
      for row in reader:
        item = _row_to_observation(
          row,
          file_date=file_date,
          region=file_region,
          source_file=path.name,
        )
        if item is not None:
          observations.append(item)
  if not observations and region in COSTCO_REGIONS:
    logger.warning("No Costco observations found for region '%s'", region)
  return observations


def load_all_observations(data_root: Path | None = None) -> list[CostcoObservation]:
  """Load observations for every known Costco region (including Seattle)."""
  root = data_root or costco_data_root()
  observations: list[CostcoObservation] = []
  for region in COSTCO_REGIONS:
    observations.extend(load_region_observations(region, root))
  return observations


def _observation_to_item(obs: CostcoObservation) -> CostcoItem:
  return CostcoItem(
    item_number=obs.item_number,
    item_sign=obs.product_name,
    sell_price=obs.price,
    timestamp=obs.timestamp,
    source_file=obs.source_file,
    region=obs.region,
    date=obs.date,
    availability=obs.availability,
    parsed=obs.parsed,
  )


def load_location_catalog(location_slug: str, data_root: Path | None = None) -> list[CostcoItem]:
  """Latest observation per item number for one Costco region."""
  observations = load_region_observations(location_slug, data_root)
  if not observations and location_slug in COSTCO_REGIONS:
    raise FileNotFoundError(
      f"No Costco CSV files for location '{location_slug}' in {data_root or costco_data_root()}",
    )

  by_item: dict[str, CostcoObservation] = {}
  for obs in observations:
    existing = by_item.get(obs.item_number)
    if existing is None or _ts_key(obs.timestamp) >= _ts_key(existing.timestamp):
      by_item[obs.item_number] = obs

  return [_observation_to_item(obs) for obs in by_item.values()]


def _score_match(text: str, meta: CanonicalPackageMeta) -> int:
  lower = text.lower()
  if any(re.search(p, lower) for p in meta.costco_exclude):
    return -1
  if not any(re.search(p, lower) for p in meta.costco_include):
    return 0
  score = 10
  for idx, pref in enumerate(meta.costco_prefer):
    if re.search(pref, lower):
      score += (len(meta.costco_prefer) - idx) * 5
  return score


def match_costco_item(
  canonical_id: str,
  catalog: list[CostcoItem],
) -> tuple[CostcoItem | None, str | None]:
  meta = CANONICAL_PACKAGES.get(canonical_id)
  if meta is None:
    return None, "Unknown canonical product"

  candidates: list[tuple[int, CostcoItem]] = []
  for item in catalog:
    score = _score_match(item.item_sign, meta)
    if score > 0:
      parsed = parse_item_sign(item.item_sign, meta.comparable_unit)
      enriched = replace(item, parsed=parsed)
      candidates.append((score, enriched))

  if not candidates:
    return None, None

  candidates.sort(key=lambda pair: pair[0], reverse=True)
  best_score, best = candidates[0]
  if best_score < 10:
    return None, f"Low-confidence Costco match: {best.item_sign}"
  if best.parsed is None:
    best = replace(
      best,
      parsed=parse_item_sign(best.item_sign, meta.comparable_unit),
    )
  return best, None


def match_costco_history(
  canonical_id: str,
  observations: list[CostcoObservation],
) -> list[CostcoObservation]:
  """Return region-scoped historical matches for one canonical product."""
  meta = CANONICAL_PACKAGES.get(canonical_id)
  if meta is None:
    return []

  matched: list[CostcoObservation] = []
  for obs in observations:
    score = _score_match(obs.product_name, meta)
    if score < 10:
      continue
    parsed = parse_item_sign(obs.product_name, meta.comparable_unit)
    matched.append(replace(obs, parsed=parsed))
  return matched


def history_points_for_region(
  canonical_id: str,
  region: str,
  data_root: Path | None = None,
) -> list[dict[str, object]]:
  """Serialize dated Costco prices for one canonical product in one region."""
  from .unit_normalize import unit_price

  observations = match_costco_history(
    canonical_id,
    load_region_observations(region, data_root),
  )
  by_date: dict[str, CostcoObservation] = {}
  for obs in observations:
    existing = by_date.get(obs.date)
    if existing is None or _ts_key(obs.timestamp) >= _ts_key(existing.timestamp):
      by_date[obs.date] = obs

  points: list[dict[str, object]] = []
  for obs_date in sorted(by_date):
    obs = by_date[obs_date]
    unit_up = unit_price(obs.price, obs.parsed) if obs.parsed else None
    points.append(
      {
        "date": obs_date,
        "region": obs.region,
        "price": obs.price,
        "unitPrice": unit_up,
        "packageDescription": obs.product_name,
        "availability": obs.availability,
        "sourceFile": obs.source_file,
      },
    )
  return points
