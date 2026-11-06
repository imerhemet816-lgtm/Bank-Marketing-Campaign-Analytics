# Data dictionary

## Original columns (bank.csv)

| Column | Type | Description |
|---|---|---|
| age | integer | Client age in years (19-87). |
| job | text | Job type, 12 categories including `unknown` (38 rows). |
| marital | text | `married`, `single`, `divorced` (divorced includes widowed, per the source). |
| education | text | `primary`, `secondary`, `tertiary`, `unknown` (187 rows). |
| default | text | Has credit in default? yes/no. |
| balance | integer | Average yearly balance in euros. Can be negative. |
| housing | text | Has a housing loan? yes/no. |
| loan | text | Has a personal loan? yes/no. |
| contact | text | Contact channel: `cellular`, `telephone`, `unknown`. |
| day | integer | Day of month of the last contact. |
| month | text | Month of the last contact (jan-dec). No year is provided. |
| duration | integer | Last call length in seconds. Known only after the call. |
| campaign | integer | Contacts made to this client during this campaign, including the last one. |
| pdays | integer | Days since the client was last contacted in a previous campaign. -1 = never contacted. |
| previous | integer | Contacts made before this campaign. |
| poutcome | text | Outcome of the previous campaign: `success`, `failure`, `other`, `unknown`. |
| y | text | Target: did the client subscribe to a term deposit? yes/no. |

## Columns changed or added by `src/01_clean_data.py`

| Column | Description |
|---|---|
| record_id | Row number (1-4,521), added as a key. The source has no client ID. |
| credit_default | Renamed from `default`, which is a reserved word in SQL. |
| subscribed | Renamed from `y`. |
| subscribed_flag | 1 if subscribed = yes, else 0. Averaging it gives the response rate. |
| previously_contacted | 1 if pdays is not -1. |
| days_since_prev_contact | pdays with -1 replaced by empty (NULL), so averages are not distorted. |
| age_group | `<25`, `25-34`, `35-44`, `45-54`, `55-64`, `65+`. |
| balance_band | `Negative`, `Zero`, `1-500`, `501-1,500`, `1,501-5,000`, `5,000+` (EUR). |
| campaign_band | Contacts in this campaign: `1`, `2`, `3`, `4-5`, `6+`. |
| month_num | Month as a number 1-12, for sorting. |

The original `pdays` and `y`-derived values are kept, so nothing from the source file was dropped.
