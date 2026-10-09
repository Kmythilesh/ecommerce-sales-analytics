"""Business analysis: revenue, customer retention and RFM."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
df = pd.read_csv(ROOT / "data" / "clean_orders.csv", parse_dates=["order_date"])
done = df[df["status"] == "Delivered"].copy()

plt.rcParams.update({
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 130
})
BLUE, GREY = "#2563eb", "#9ca3af"

# Overall numbers for a quick look at the business
kpi = {
    "Net revenue (delivered)": f"Rs {done['net_revenue'].sum():,.0f}",
    "Orders": f"{len(df):,}",
    "Avg order value": f"Rs {done['net_revenue'].mean():,.0f}",
    "Return rate": f"{(df['status'] == 'Returned').mean():.1%}",
    "Cancel rate": f"{(df['status'] == 'Cancelled').mean():.1%}",
    "Repeat customers": f"{(df.groupby('customer_id').size() > 1).mean():.1%}",
}
pd.Series(kpi).to_csv(OUT / "kpis.csv", header=["value"])
print(pd.Series(kpi).to_string())


# 1. Monthly revenue
# Checking how revenue changes over the year.
m = done.groupby("month")["net_revenue"].sum() / 1e6

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(
    m.index, m.values,
    color=[BLUE if v == m.max() else GREY for v in m.values]
)
ax.set_title("Monthly net revenue (Rs million)", loc="left")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
fig.savefig(OUT / "01_monthly_revenue.png")
plt.close(fig)


# 2. Category performance
# Comparing category revenue with the percentage of orders returned.
cat = df.groupby("category").agg(
    revenue=("net_revenue", "sum"),
    return_rate=("status", lambda s: (s == "Returned").mean()),
).sort_values("revenue")

fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(cat.index, cat["revenue"] / 1e6, color=BLUE)

for i, (rev, rr) in enumerate(
    zip(cat["revenue"] / 1e6, cat["return_rate"])
):
    ax.text(rev, i, f"  {rr:.0%} returned", va="center", fontsize=8)

ax.set_title("Revenue by category (Rs million)", loc="left")
fig.tight_layout()
fig.savefig(OUT / "02_category.png")
plt.close(fig)
cat.to_csv(OUT / "category_summary.csv")


# 3. Channel performance
# Looking at order volume and average order value for each channel.
ch = done.groupby("channel").agg(
    orders=("order_id", "count"),
    aov=("net_revenue", "mean")
).round(0)

ch.to_csv(OUT / "channel_summary.csv")


# 4. Discounts and order value
# Checking whether higher discounts are linked to a higher average order value.
disc = done.groupby("discount_pct").agg(
    orders=("order_id", "count"),
    aov=("net_revenue", "mean")
)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(disc.index, disc["aov"], marker="o", color=BLUE)
ax.set_xlabel("Discount %")
ax.set_ylabel("Avg net order value (Rs)")
ax.set_title("Discounts vs average order value", loc="left")
fig.tight_layout()
fig.savefig(OUT / "03_discount.png")
plt.close(fig)


# 5. Cohort retention
# Grouping customers by their first order month to see who comes back.
df["cohort"] = (
    df.groupby("customer_id")["order_date"]
    .transform("min")
    .dt.to_period("M")
)
df["period"] = df["order_date"].dt.to_period("M")
df["age"] = (df["period"] - df["cohort"]).apply(lambda x: x.n)

coh = df.groupby(["cohort", "age"])["customer_id"].nunique().unstack(fill_value=0)
ret = coh.div(coh[0], axis=0)

fig, ax = plt.subplots(figsize=(8, 5))
r = ret.iloc[:, 1:9]  # Leaving out the first month, when retention is 100%

im = ax.imshow(
    r, cmap="Blues", vmin=0, vmax=r.max().max(), aspect="auto"
)
ax.set_yticks(range(len(r)))
ax.set_yticklabels(r.index.astype(str))
ax.set_xticks(range(r.shape[1]))
ax.set_xticklabels(r.columns)
ax.set_xlabel("Months since first order")
ax.set_title("Customer retention by cohort", loc="left")

cb = fig.colorbar(im, ax=ax)
cb.ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
fig.tight_layout()
fig.savefig(OUT / "04_cohort_retention.png")
plt.close(fig)


# 6. RFM segmentation
# Grouping customers by how recently and how often they order, and how much they spend.
snap = done["order_date"].max() + pd.Timedelta(days=1)

rfm = done.groupby("customer_id").agg(
    recency=("order_date", lambda s: (snap - s.max()).days),
    frequency=("order_id", "count"),
    monetary=("net_revenue", "sum"),
)

# Higher scores mean better recent activity, more orders and higher spending.
rfm["R"] = pd.qcut(
    rfm["recency"], 4, labels=[4, 3, 2, 1]
).astype(int)
rfm["F"] = pd.qcut(
    rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]
).astype(int)
rfm["M"] = pd.qcut(
    rfm["monetary"], 4, labels=[1, 2, 3, 4]
).astype(int)

rfm["score"] = rfm[["R", "F", "M"]].sum(axis=1)
rfm["segment"] = pd.cut(
    rfm["score"],
    [0, 5, 8, 10, 12],
    labels=["At risk", "Casual", "Loyal", "Champions"]
)

seg = rfm.groupby("segment", observed=True).agg(
    customers=("monetary", "size"),
    revenue=("monetary", "sum")
)
seg["revenue_share"] = (
    seg["revenue"] / seg["revenue"].sum()
).round(3)

seg.to_csv(OUT / "rfm_segments.csv")
print("\n", seg)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(seg.index.astype(str), seg["revenue_share"] * 100, color=BLUE)
ax.set_ylabel("% of revenue")
ax.set_title("Revenue share by customer segment", loc="left")
fig.tight_layout()
fig.savefig(OUT / "05_rfm.png")
plt.close(fig)

print("\nCharts and tables saved to outputs/")