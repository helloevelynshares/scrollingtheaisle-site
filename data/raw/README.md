# TikTok transcript input

Place **`bulk_transcripts.csv`** here (or at the repo root).

## Expected columns

The extractor auto-detects common header names:

| Purpose | Accepted column names |
|--------|------------------------|
| Title | `video_title`, `title`, `name` |
| URL | `video_url`, `url`, `link`, `video_link` |
| Views | `views`, `view_count`, `play_count`, `plays` |
| Text | `transcript`, `text`, `caption`, `description`, `content` |

Views drive priority:

- **≥ 20,000** → priority 3.0 (highest)
- **≥ 10,000** → priority 2.0 (high)
- **< 10,000** → priority 1.0 (secondary)

## Run extraction

```bash
python scripts/extract_tiktok_food_mentions.py
```

Output: `data/processed/tiktok_item_mentions.csv`

Non-food categories (household, pet, baby, personal care) are excluded automatically.
