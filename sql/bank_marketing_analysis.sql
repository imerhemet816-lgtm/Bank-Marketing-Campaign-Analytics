/* =====================================================================
   Bank Marketing Campaign Performance Analysis - MySQL 8.0
   Source table: data/processed/bank_clean.csv (4,521 rows, produced by
   src/01_clean_data.py).

   How to run (from the repository root):
     mysql --local-infile=1 -u <user> -p < sql/bank_marketing_analysis.sql
   The script only creates objects and never drops anything. If the table
   already exists the run stops at the CREATE TABLE statement (see below).
   LOAD DATA LOCAL INFILE resolves the CSV path relative to the folder you
   start the mysql client from, and the server must allow local_infile
   (SET GLOBAL local_infile = 1; as an admin user).

   Note: the dataset has a month and day but no year (2008-2010 combined),
   so no query here builds a time series by date.
   ===================================================================== */

-- Nothing is dropped. If bank_marketing.campaign_contacts already exists, the
-- CREATE TABLE below fails on purpose so existing data is never overwritten.
-- To rerun from scratch, run this yourself first (it deletes only this table):
--   DROP TABLE bank_marketing.campaign_contacts;
CREATE DATABASE IF NOT EXISTS bank_marketing CHARACTER SET utf8mb4;
USE bank_marketing;

CREATE TABLE campaign_contacts (
    record_id               INT          PRIMARY KEY,
    age                     TINYINT UNSIGNED NOT NULL,
    job                     VARCHAR(20)  NOT NULL,
    marital                 VARCHAR(10)  NOT NULL,
    education               VARCHAR(10)  NOT NULL,
    credit_default          ENUM('yes','no') NOT NULL,
    balance                 INT          NOT NULL,      -- average yearly balance, EUR
    housing                 ENUM('yes','no') NOT NULL,
    loan                    ENUM('yes','no') NOT NULL,
    contact                 VARCHAR(10)  NOT NULL,
    day                     TINYINT UNSIGNED NOT NULL,
    month                   CHAR(3)      NOT NULL,
    duration                SMALLINT UNSIGNED NOT NULL, -- seconds, known only after the call
    campaign                TINYINT UNSIGNED NOT NULL,  -- contacts in this campaign, incl. last
    pdays                   SMALLINT     NOT NULL,      -- -1 = not previously contacted
    previous                TINYINT UNSIGNED NOT NULL,
    poutcome                VARCHAR(10)  NOT NULL,
    subscribed              ENUM('yes','no') NOT NULL,
    subscribed_flag         TINYINT(1)   NOT NULL,
    previously_contacted    TINYINT(1)   NOT NULL,
    days_since_prev_contact SMALLINT     NULL,
    age_group               VARCHAR(5)   NOT NULL,
    balance_band            VARCHAR(12)  NOT NULL,
    campaign_band           VARCHAR(3)   NOT NULL,
    month_num               TINYINT UNSIGNED NOT NULL,
    INDEX idx_job (job),
    INDEX idx_month (month_num)
);

LOAD DATA LOCAL INFILE 'data/processed/bank_clean.csv'
INTO TABLE campaign_contacts
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(record_id, age, job, marital, education, credit_default, balance, housing, loan,
 contact, day, month, duration, campaign, pdays, previous, poutcome, subscribed,
 subscribed_flag, previously_contacted, @days_prev, age_group, balance_band,
 campaign_band, month_num)
SET days_since_prev_contact = NULLIF(TRIM(TRAILING '\r' FROM @days_prev), '');

-- Sanity check after loading: should return 4521 rows and 521 subscribers
SELECT COUNT(*) AS row_count, SUM(subscribed_flag) AS subscribers FROM campaign_contacts;


/* ---------------------------------------------------------------------
   Q1. Headline numbers: how many clients were contacted, how many said
       yes, and what did it cost in contact attempts?
   --------------------------------------------------------------------- */
SELECT COUNT(*)                                        AS clients,
       SUM(subscribed_flag)                            AS subscribers,
       ROUND(100 * AVG(subscribed_flag), 2)            AS response_rate_pct,
       SUM(campaign)                                   AS total_contacts,
       ROUND(SUM(campaign) / SUM(subscribed_flag), 1)  AS contacts_per_subscription,
       ROUND(AVG(age), 1)                              AS avg_age
FROM campaign_contacts;


/* Q2. Which age groups respond best? Group sizes are shown because the
       youngest and oldest groups are small. */
SELECT age_group,
       COUNT(*)                             AS clients,
       SUM(subscribed_flag)                 AS subscribers,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY age_group
ORDER BY MIN(age);


/* Q3. Which job categories respond best, ignoring categories with fewer
       than 100 clients (HAVING removes unreliable small groups)? */
SELECT job,
       COUNT(*)                             AS clients,
       SUM(subscribed_flag)                 AS subscribers,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY job
HAVING COUNT(*) >= 100
ORDER BY response_rate_pct DESC;


/* Q4. Does education level change the response rate? */
SELECT education,
       COUNT(*)                             AS clients,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct,
       ROUND(AVG(balance), 0)               AS avg_balance_eur
FROM campaign_contacts
GROUP BY education
ORDER BY response_rate_pct DESC;


/* Q5. Which contact channel performs best, and how many attempts does each
       need on average? 'unknown' means the channel was not recorded. */
SELECT contact,
       COUNT(*)                             AS clients,
       ROUND(AVG(campaign), 2)              AS avg_contacts,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY contact
ORDER BY response_rate_pct DESC;


/* Q6. How does response change with the number of contact attempts in this
       campaign? CASE WHEN builds the frequency bands. */
SELECT CASE WHEN campaign = 1 THEN '1 contact'
            WHEN campaign = 2 THEN '2 contacts'
            WHEN campaign = 3 THEN '3 contacts'
            WHEN campaign BETWEEN 4 AND 5 THEN '4-5 contacts'
            ELSE '6+ contacts' END           AS contact_band,
       COUNT(*)                              AS clients,
       ROUND(100 * AVG(subscribed_flag), 2)  AS response_rate_pct
FROM campaign_contacts
GROUP BY contact_band
ORDER BY MIN(campaign);


/* Q7. Where did the contact effort go compared with where the
       subscriptions came from? (CTE + window function for the shares.) */
WITH by_band AS (
    SELECT campaign_band,
           SUM(campaign)        AS contacts,
           SUM(subscribed_flag) AS subscribers
    FROM campaign_contacts
    GROUP BY campaign_band
)
SELECT campaign_band,
       contacts,
       subscribers,
       ROUND(100 * contacts    / SUM(contacts)    OVER (), 1) AS pct_of_contacts,
       ROUND(100 * subscribers / SUM(subscribers) OVER (), 1) AS pct_of_subscriptions
FROM by_band
ORDER BY FIELD(campaign_band, '1', '2', '3', '4-5', '6+');


/* Q8. How did clients with a past campaign outcome respond this time? */
SELECT poutcome,
       COUNT(*)                             AS clients,
       SUM(subscribed_flag)                 AS subscribers,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY poutcome
ORDER BY response_rate_pct DESC;


/* Q9. Response by calendar month, with a rank. Months with few records
       (March, September, October, December) have very high rates but
       cannot be compared fairly with May. */
SELECT month,
       COUNT(*)                                              AS clients,
       ROUND(100 * AVG(subscribed_flag), 2)                  AS response_rate_pct,
       RANK() OVER (ORDER BY AVG(subscribed_flag) DESC)      AS rate_rank
FROM campaign_contacts
GROUP BY month, month_num
ORDER BY month_num;


/* Q10. Is the account balance related to response? */
SELECT balance_band,
       COUNT(*)                             AS clients,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY balance_band
ORDER BY MIN(balance);


/* Q11. Do clients who already carry a housing or personal loan respond
        differently? */
SELECT housing, loan,
       COUNT(*)                             AS clients,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY housing, loan
ORDER BY response_rate_pct DESC;


/* Q12. Within each education level, which jobs rank highest? (RANK with
        PARTITION BY; groups under 30 clients excluded.) */
WITH job_edu AS (
    SELECT education, job,
           COUNT(*)                             AS clients,
           ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
    FROM campaign_contacts
    GROUP BY education, job
    HAVING COUNT(*) >= 30
)
SELECT education, job, clients, response_rate_pct, rate_rank
FROM (
    SELECT job_edu.*,
           RANK() OVER (PARTITION BY education ORDER BY response_rate_pct DESC) AS rate_rank
    FROM job_edu
) ranked
WHERE rate_rank <= 3
ORDER BY education, rate_rank;


/* Q13. How far above or below the overall rate is each job (percentage
        points)? Useful for a quick segment ranking. */
WITH overall AS (
    SELECT AVG(subscribed_flag) AS overall_rate FROM campaign_contacts
)
SELECT c.job,
       COUNT(*)                                                        AS clients,
       ROUND(100 * AVG(c.subscribed_flag), 2)                          AS response_rate_pct,
       ROUND(100 * (AVG(c.subscribed_flag) - o.overall_rate), 2)       AS pts_vs_overall
FROM campaign_contacts c
CROSS JOIN overall o
GROUP BY c.job, o.overall_rate
HAVING COUNT(*) >= 100
ORDER BY pts_vs_overall DESC;


/* Q14. New vs previously contacted clients, split by contact channel. */
SELECT CASE WHEN previously_contacted = 1 THEN 'Previously contacted'
            ELSE 'New to campaigns' END      AS client_type,
       contact,
       COUNT(*)                              AS clients,
       ROUND(100 * AVG(subscribed_flag), 2)  AS response_rate_pct
FROM campaign_contacts
GROUP BY client_type, contact
ORDER BY client_type, response_rate_pct DESC;


/* Q15. Is the weak 'unknown' contact channel just a May/June effect? Shows
        the share of unknown-channel records and the response rate by month. */
SELECT month,
       COUNT(*)                                                    AS clients,
       ROUND(100 * AVG(contact = 'unknown'), 1)                    AS pct_channel_unknown,
       ROUND(100 * AVG(CASE WHEN contact = 'unknown' THEN subscribed_flag END), 2) AS rate_unknown_pct,
       ROUND(100 * AVG(CASE WHEN contact <> 'unknown' THEN subscribed_flag END), 2) AS rate_known_pct
FROM campaign_contacts
GROUP BY month, month_num
ORDER BY month_num;


/* Q16. Cumulative share of subscriptions through the calendar year
        (running total window function). Months are pooled across years. */
WITH monthly AS (
    SELECT month, month_num, SUM(subscribed_flag) AS subscribers
    FROM campaign_contacts
    GROUP BY month, month_num
)
SELECT month,
       subscribers,
       ROUND(100 * SUM(subscribers) OVER (ORDER BY month_num)
             / SUM(subscribers) OVER (), 1) AS cumulative_pct_of_subscriptions
FROM monthly
ORDER BY month_num;


/* Q17. Call length (seconds) for subscribers and non-subscribers. Duration
        is only known after the call, so this describes the calls rather
        than a way to pick who to call. */
SELECT subscribed,
       COUNT(*)                  AS clients,
       ROUND(AVG(duration), 1)   AS avg_duration_sec,
       MIN(duration)             AS min_sec,
       MAX(duration)             AS max_sec
FROM campaign_contacts
GROUP BY subscribed;


/* Q18. Best job x education combinations with at least 100 clients. */
SELECT job, education,
       COUNT(*)                             AS clients,
       SUM(subscribed_flag)                 AS subscribers,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY job, education
HAVING COUNT(*) >= 100
ORDER BY response_rate_pct DESC
LIMIT 10;


/* Q19. A simple 'no loans, positive balance' profile versus everyone else.
        This is a descriptive segment, not a fitted model. */
SELECT CASE WHEN housing = 'no' AND loan = 'no' AND balance > 0
            THEN 'No loans, balance > 0' ELSE 'All other clients' END AS segment,
       COUNT(*)                             AS clients,
       SUM(subscribed_flag)                 AS subscribers,
       ROUND(100 * AVG(subscribed_flag), 2) AS response_rate_pct
FROM campaign_contacts
GROUP BY segment;

