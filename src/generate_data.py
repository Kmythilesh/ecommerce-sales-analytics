"""Create a sample e-commerce dataset with some messy data to clean."""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 12_000

CATEGORIES = {
    "Electronics": (3000, 60000),
    "Fashion": (400, 6000),
    "Home & Kitchen": (500, 15000),
    "Beauty": (200, 3000),
    "Books": (150, 1200),
    "Sports": (500, 9000),
}
CITIES = ["Hyderabad", "Bengaluru", "Mumbai", "Delhi", "Chennai", "Pune", "Kolkata", "Jaipur"]
CHANNELS = ["Organic", "Paid Ads", "Email", "Social", "Referral"]
PAYMENTS = ["UPI", "Credit Card", "Debit Card", "COD", "Net Banking"]
STATUS = ["Delivered", "Delivered", "Delivered", "Delivered", "Returned", "Cancelled"]

# Generate order dates across one year, with more orders during sale periods.
dates = pd.to_datetime("2025-10-01") + pd.to_timedelta(
    rng.integers(0, 365, N), unit="D"
)
month_weight = dates.month.map({10: 1.0, 11: 1.0, 1: 0.8}).fillna(0.35).to_numpy()
keep = rng.random(N) < month_weight
dates = dates[keep]
n = len(dates)

# Pick random product details for each order.
cat = rng.choice(list(CATEGORIES), n, p=[0.18, 0.28, 0.17, 0.14, 0.10, 0.13])
price = np.array([rng.integers(*CATEGORIES[c]) for c in cat], dtype=float)
qty = rng.choice([1, 2, 3, 4], n, p=[0.7, 0.18, 0.08, 0.04])
discount = rng.choice([0, 5, 10, 20, 30], n, p=[0.35, 0.2, 0.2, 0.15, 0.10])

df = pd.DataFrame({
    "order_id": [f"ORD{100000 + i}" for i in range(n)],
    "order_date": dates,
    "customer_id": [f"C{rng.integers(1, 3500):05d}" for _ in range(n)],
    "city": rng.choice(CITIES, n),
    "category": cat,
    "unit_price": price,
    "quantity": qty,
    "discount_pct": discount,
    "channel": rng.choice(CHANNELS, n, p=[0.3, 0.25, 0.15, 0.2, 0.1]),
    "payment_method": rng.choice(PAYMENTS, n, p=[0.4, 0.2, 0.15, 0.15, 0.1]),
    "status": rng.choice(STATUS, n),
})


# Add a few common data issues so the cleaning script has something to fix.
df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

mixed = rng.random(n) < 0.05
df.loc[mixed, "order_date"] = (
    pd.to_datetime(df.loc[mixed, "order_date"]).dt.strftime("%d/%m/%Y")
)

df.loc[rng.random(n) < 0.04, "city"] = None
df.loc[rng.random(n) < 0.03, "discount_pct"] = np.nan
df.loc[rng.random(n) < 0.02, "quantity"] = -1

# Some text values have extra spaces or inconsistent capitalisation.
df["city"] = df["city"].apply(
    lambda x: x if not isinstance(x, str) or rng.random() > 0.08
    else str(rng.choice([x.upper(), x.lower(), f" {x} "]))
)
df["status"] = df["status"].apply(
    lambda x: x if rng.random() > 0.05 else x.lower()
)

# Add duplicate rows and shuffle the data before saving it.
df = pd.concat(
    [df, df.sample(frac=0.02, random_state=1)],
    ignore_index=True
)

out = Path(__file__).resolve().parents[1] / "data" / "raw_orders.csv"
out.parent.mkdir(exist_ok=True)

df.sample(frac=1, random_state=7).to_csv(out, index=False)
print(f"Wrote {len(df):,} raw rows -> {out}")