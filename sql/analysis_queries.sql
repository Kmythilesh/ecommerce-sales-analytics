-- 1. Monthly revenue and growth
-- Checking how revenue changes from one month to the next.

WITH monthly AS (
    SELECT month, SUM(net_revenue) AS revenue
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 0) AS revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1
    ) AS mom_growth_pct
FROM monthly
ORDER BY month;


-- 2. Category performance
-- Comparing revenue and return rates across categories.

SELECT
    category,
    ROUND(SUM(net_revenue), 0) AS revenue,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    ) AS return_rate_pct,
    RANK() OVER (ORDER BY SUM(net_revenue) DESC) AS revenue_rank
FROM orders
GROUP BY category
ORDER BY revenue DESC;


-- 3. Top 10 customers by lifetime value
-- Finding the customers who bring in the most revenue.

SELECT
    customer_id,
    COUNT(*) AS orders,
    ROUND(SUM(net_revenue), 0) AS ltv
FROM orders
WHERE status = 'Delivered'
GROUP BY customer_id
ORDER BY ltv DESC
LIMIT 10;


-- 4. Repeat-purchase rate
-- Finding the percentage of customers who ordered more than once.

SELECT
    ROUND(
        100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END)
        / COUNT(*), 1
    ) AS repeat_customer_pct
FROM (
    SELECT customer_id, COUNT(*) AS n
    FROM orders
    GROUP BY customer_id
) t;


-- 5. Best sales channel in each city
-- Checking which channel generates the most revenue in each city.

SELECT city, channel, revenue
FROM (
    SELECT
        city,
        channel,
        ROUND(SUM(net_revenue), 0) AS revenue,
        ROW_NUMBER() OVER (
            PARTITION BY city
            ORDER BY SUM(net_revenue) DESC, channel
        ) AS rn
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY city, channel
) ranked
WHERE rn = 1
ORDER BY city;