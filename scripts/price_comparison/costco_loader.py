"""Load and match Costco warehouse CSV data by region."""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import warnings
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from .canonical_metadata import CANONICAL_PACKAGES, CanonicalPackageMeta, DEFAULT_COSTCO_DATA_ROOT
from .costco_item_mappings import all_item_numbers_for_product, resolve_item_number
from .costco_warehouse_mapping import (
    COSTCO_REGIONS,
    GROCERY_TRACKER_TO_COSTCO_REGION,
    normalize_warehouse_slug,
)
from .unit_normalize import ParsedPackage, parse_item_sign

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CACHE_OBSERVATIONS = ROOT / "data" / "processed" / "costco" / "observations.json"

FILENAME_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2})_([a-z_-]+)_.*\.csv$",
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
  match_method: str = "text"


def costco_data_root() -> Path:
  env = os.environ.get("COSTCO_DATA_ROOT")
  if env:
    return Path(env)
  primary = Path(DEFAULT_COSTCO_DATA_ROOT)
  if primary.is_dir():
    return primary
  alt = Path("/Users/kunal/Documents/costco-mvp/costco_data")
  return alt if alt.is_dir() else primary


def cache_observations_path() -> Path:
  override = os.environ.get("COSTCO_CACHE_PATH")
  return Path(override) if override else CACHE_OBSERVATIONS


def parse_costco_filename(path: Path) -> tuple[str, str] | None:
  """Return (date, normalized warehouse) from e.g. 2026-07-05_tustin_consolidated.csv."""
  match = FILENAME_PATTERN.match(path.name)
  if not match:
    return None
  file_date, filename_slug = match.group(1), match.group(2)
  warehouse = normalize_warehouse_slug(filename_slug)
  if warehouse is None:
    return None
  return file_date, warehouse


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
  warned_files: set[str] | None = None,
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
  if row_date != file_date and (warned_files is None or source_file not in warned_files):
    warnings.warn(
      f"{source_file}: CSV timestamps use {row_date} but filename date is {file_date}",
      stacklevel=2,
    )
    if warned_files is not None:
      warned_files.add(source_file)

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


def _dict_to_observation(raw: dict) -> CostcoObservation:
  return CostcoObservation(
    date=raw["date"],
    region=raw["warehouse"],
    item_number=raw["itemNumber"],
    product_name=raw["productName"],
    price=float(raw["price"]),
    size_info=raw.get("productName"),
    availability=raw.get("availability"),
    source_file=raw["sourceFile"],
    timestamp=raw["timestamp"],
  )


def load_cached_observations() -> list[CostcoObservation] | None:
  path = cache_observations_path()
  if not path.is_file():
    return None
  raw_list = json.loads(path.read_text(encoding="utf-8"))
  return [_dict_to_observation(raw) for raw in raw_list]


def load_all_observations_from_paths(
  paths: list[Path],
  data_root: Path | None = None,
) -> list[CostcoObservation]:
  observations: list[CostcoObservation] = []
  warned_files: set[str] = set()
  for path in paths:
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
          warned_files=warned_files,
        )
        if item is not None:
          observations.append(item)
  return observations


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


def _load_observations_from_csv(region: str, data_root: Path) -> list[CostcoObservation]:
  observations: list[CostcoObservation] = []
  warned_files: set[str] = set()
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
          warned_files=warned_files,
        )
        if item is not None:
          observations.append(item)
  return observations


def load_region_observations(
  region: str,
  data_root: Path | None = None,
) -> list[CostcoObservation]:
  """Load every observation for one Costco warehouse across all dated files."""
  cached = load_cached_observations()
  if cached is not None:
    filtered = [obs for obs in cached if obs.region == region]
    if not filtered and region in COSTCO_REGIONS:
      logger.warning("No cached Costco observations for warehouse '%s'", region)
    return filtered

  root = data_root or costco_data_root()
  observations = _load_observations_from_csv(region, root)
  if not observations and region in COSTCO_REGIONS:
    logger.warning("No Costco observations found for warehouse '%s'", region)
  return observations


def load_all_observations(data_root: Path | None = None) -> list[CostcoObservation]:
  """Load observations for every known Costco warehouse (including Seattle)."""
  cached = load_cached_observations()
  if cached is not None:
    return cached

  root = data_root or costco_data_root()
  observations: list[CostcoObservation] = []
  for region in COSTCO_REGIONS:
    observations.extend(_load_observations_from_csv(region, root))
  return observations


def _observation_to_item(obs: CostcoObservation, *, match_method: str = "text") -> CostcoItem:
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
    match_method=match_method,
  )


def load_location_catalog(location_slug: str, data_root: Path | None = None) -> list[CostcoItem]:
  """Latest observation per item number for one Costco warehouse."""
  observations = load_region_observations(location_slug, data_root)
  if not observations and location_slug in COSTCO_REGIONS:
    raise FileNotFoundError(
      f"No Costco data for warehouse '{location_slug}' "
      f"(cache: {cache_observations_path()}, root: {data_root or costco_data_root()})",
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


def _match_by_item_number(
  canonical_id: str,
  catalog: list[CostcoItem],
  warehouse: str,
  meta: CanonicalPackageMeta,
) -> tuple[CostcoItem | None, str | None]:
  item_numbers = all_item_numbers_for_product(canonical_id, warehouse)
  if not item_numbers:
    return None, None

  by_number = {item.item_number: item for item in catalog}
  candidates: list[CostcoItem] = []
  for item_number in item_numbers:
    item = by_number.get(item_number)
    if item is not None:
      candidates.append(item)

  if not candidates:
    return None, f"Mapped item(s) {item_numbers} not in {warehouse} catalog"

  item = max(candidates, key=lambda i: _ts_key(i.timestamp))
  parsed = parse_item_sign(item.item_sign, meta.comparable_unit)
  enriched = replace(item, parsed=parsed, match_method="item_number")
  if parsed is None:
    return enriched, f"Item #{item.item_number} matched but package size unclear: {item.item_sign}"
  return enriched, None


def match_costco_item(
  canonical_id: str,
  catalog: list[CostcoItem],
  *,
  warehouse: str | None = None,
) -> tuple[CostcoItem | None, str | None]:
  meta = CANONICAL_PACKAGES.get(canonical_id)
  if meta is None:
    return None, "Unknown canonical product"

  wh = warehouse or (catalog[0].region if catalog else None)
  if wh:
    by_number, note = _match_by_item_number(canonical_id, catalog, wh, meta)
    if by_number is not None:
      return by_number, note
    if note and "not in" in note:
      return None, note

  candidates: list[tuple[int, CostcoItem]] = []
  for item in catalog:
    score = _score_match(item.item_sign, meta)
    if score > 0:
      parsed = parse_item_sign(item.item_sign, meta.comparable_unit)
      enriched = replace(item, parsed=parsed, match_method="text")
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
  return best, "Text match, verify size/flavor" if best.match_method == "text" else None


def match_costco_history(
  canonical_id: str,
  observations: list[CostcoObservation],
  *,
  warehouse: str | None = None,
) -> list[CostcoObservation]:
  """Return warehouse-scoped historical matches for one canonical product."""
  meta = CANONICAL_PACKAGES.get(canonical_id)
  if meta is None:
    return []

  wh = warehouse or (observations[0].region if observations else None)
  item_numbers = all_item_numbers_for_product(canonical_id, wh) if wh else []
  if item_numbers:
    number_set = set(item_numbers)
    matched = [
      replace(obs, parsed=parse_item_sign(obs.product_name, meta.comparable_unit))
      for obs in observations
      if obs.item_number in number_set
    ]
    if matched:
      return matched

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
    warehouse=region,
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
        "itemNumber": obs.item_number,
      },
    )
  return points


def list_unmatched_products(data_root: Path | None = None) -> list[str]:
  """Products with no Costco match in their paired warehouse (for manual review)."""
  from .canonical_metadata import GROCERY_FEEDS

  root = data_root or costco_data_root()
  unmatched: list[str] = []
  for canonical_id in CANONICAL_PACKAGES:
    for feed_id, feed_cfg in GROCERY_FEEDS.items():
      warehouse = feed_cfg["costco_location_slug"]
      catalog = load_location_catalog(warehouse, root)
      item, _ = match_costco_item(canonical_id, catalog, warehouse=warehouse)
      if item is None:
        unmatched.append(f"{canonical_id} @ {feed_id} ({warehouse})")
  return unmatched
