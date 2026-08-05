# Build from repository root:
#   docker build -f services/aislecheck_api/Dockerfile -t aislecheck-api .
FROM python:3.11-slim

WORKDIR /app

COPY services/aislecheck_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Matcher + shopper_query + deal_assessment need scripts/, data/, config/, and
# generated weekly unit-price series on disk (same files the price tracker uses).
COPY scripts /app/scripts
COPY data/canonical_tracker_families.yaml /app/data/canonical_tracker_families.yaml
COPY config/canonical_match_rules.yaml /app/config/canonical_match_rules.yaml
COPY config/price_benchmark_thresholds.json /app/config/price_benchmark_thresholds.json
COPY src/data/weeklyAdPrices.generated.ts /app/src/data/weeklyAdPrices.generated.ts
COPY src/data/vonsWeeklyAdPrices.generated.ts /app/src/data/vonsWeeklyAdPrices.generated.ts
COPY src/data/familyWeeklyAdPrices.generated.ts /app/src/data/familyWeeklyAdPrices.generated.ts
COPY src/data/canonicalTrackerFamilies.generated.ts /app/src/data/canonicalTrackerFamilies.generated.ts
COPY services/__init__.py /app/services/__init__.py
COPY services/aislecheck_api /app/services/aislecheck_api

ENV PYTHONPATH=/app/scripts
ENV PYTHONUNBUFFERED=1
ENV AISLECHECK_CORS_ORIGINS=https://scrollingtheaisle.com,http://127.0.0.1:8000,http://localhost:8000
ENV AISLECHECK_DEBUG_LOG=0

EXPOSE 8080
CMD ["uvicorn", "services.aislecheck_api.app:app", "--host", "0.0.0.0", "--port", "8080"]
