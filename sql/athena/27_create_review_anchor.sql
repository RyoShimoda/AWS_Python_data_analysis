WITH valid_reviews AS (
    SELECT
        order_id,
        review_id,
        TRY_CAST(review_score AS INTEGER) AS review_score,
        TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_timestamp

    FROM reviews

    WHERE TRY_CAST(review_answer_timestamp AS TIMESTAMP) IS NOT NULL
      AND TRY_CAST(review_score AS INTEGER) BETWEEN 1 AND 5
),

ranked_reviews AS (
    SELECT
        order_id,
        review_id,
        review_score,
        review_timestamp,

        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY review_timestamp ASC, review_id ASC
        ) AS review_rank

    FROM valid_reviews
)

SELECT
    order_id,
    review_score,
    review_timestamp,

    CASE
        WHEN review_score <= 2 THEN 1
        ELSE 0
    END AS low_review

FROM ranked_reviews

WHERE review_rank = 1

ORDER BY order_id;
