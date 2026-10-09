"""Clean the raw orders data and save the changes made."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
raw = pd.read_csv(ROOT / "data" / "raw_orders.csv")
log = [("raw rows", len(raw))]


# Remove duplicate rows
raw = raw.drop_duplicates()
log.append(("after removing exact duplicates", len(raw)))


# Convert dates to one format, since the raw file has mixed formats
iso = pd.to_datetime(raw["order_date"], format="%Y-%m-%d", errors="coerce")
dmy = pd.to_datetime(raw["order_date"], format="%d/%m/%Y", errors="coerce")
raw["order_date"] = iso.fillna(dmy)

log.append(("unparseable dates dropped", int(raw["order_date"].isna().sum())))
raw = raw.dropna(subset=["order_date"])


# Clean up city and status names and fill missing cities
raw["city"] = raw["city"].str.strip().str.title()
raw["status"] = raw["status"].str.strip().str.title()

log.append(("missing city -> 'Unknown'", int(raw["city"].isna().sum())))
raw["city"] = raw["city"].fillna("Unknown")


# Remove invalid quantities and use 0 for missing discounts
bad_qty = int((raw["quantity"] <= 0).sum())
raw = raw[raw["quantity"] > 0]
log.append(("rows with quantity <= 0 dropped", bad_qty))

log.append(("missing discount -> 0", int(raw["discount_pct"].isna().sum())))
raw["discount_pct"] = raw["discount_pct"].fillna(0)


# Calculate revenue after applying the discount
raw["gross_revenue"] = raw["unit_price"] * raw["quantity"]
raw["net_revenue"] = (
    raw["gross_revenue"] * (1 - raw["discount_pct"] / 100)
).round(2)

raw["month"] = raw["order_date"].dt.to_period("M").astype(str)
raw["is_completed"] = (raw["status"] == "Delivered").astype(int)


# Save the cleaned data and a log of the changes
log.append(("clean rows", len(raw)))

raw.to_csv(ROOT / "data" / "clean_orders.csv", index=False)

pd.DataFrame(log, columns=["step", "rows"]).to_csv(
    ROOT / "outputs" / "cleaning_log.csv", index=False
)

for step, n in log:
    print(f"{step:<40}{n:>8,}")