# Power BI dashboard specification

No `.pbix` file is included. Power BI Desktop was not available in the environment where this project was built, and a hand-written .pbix would not be a real file. The finished static version of the dashboard is `outputs/charts/dashboard.png`. This document describes how to build the same report in Power BI Desktop. The DAX below has **not** been run in Power BI; the logic mirrors the SQL and Python results, which were verified, so use those as your check figures.

## 1. Load the data

1. Get Data > Text/CSV > `data/processed/bank_clean.csv`. Name the table `bank_clean`.
2. Check the types: `subscribed_flag`, `previously_contacted`, `month_num` as whole numbers; `days_since_prev_contact` as decimal (it has blanks).
3. Sorting: select `month` > Column tools > Sort by column > `month_num`.
4. Add an age-group sort column (Modeling > New column):

```DAX
Age Group Order =
SWITCH ( bank_clean[age_group],
    "<25", 1, "25-34", 2, "35-44", 3, "45-54", 4, "55-64", 5, "65+", 6 )
```
Then sort `age_group` by `Age Group Order`. Do the same for `balance_band` and `campaign_band` if the default alphabetical order looks wrong.

## 2. Measures

```DAX
Total Records = COUNTROWS ( bank_clean )

Subscribers = CALCULATE ( COUNTROWS ( bank_clean ), bank_clean[subscribed] = "yes" )

Response Rate = DIVIDE ( [Subscribers], [Total Records] )

Total Contacts = SUM ( bank_clean[campaign] )

Contacts per Subscription = DIVIDE ( [Total Contacts], [Subscribers] )

Avg Age = AVERAGE ( bank_clean[age] )

Overall Response Rate = CALCULATE ( [Response Rate], ALL ( bank_clean ) )

Pts vs Overall = ( [Response Rate] - [Overall Response Rate] ) * 100

Share of Contacts =
DIVIDE ( [Total Contacts], CALCULATE ( [Total Contacts], ALL ( bank_clean[campaign_band] ) ) )

Share of Subscriptions =
DIVIDE ( [Subscribers], CALCULATE ( [Subscribers], ALL ( bank_clean[campaign_band] ) ) )

Sample Flag = IF ( [Total Records] < 100, "Small sample (n<100)", "OK" )
```

Format `Response Rate` and the two share measures as percentages with one decimal.

## 3. Check figures (full, unfiltered report)

Total Records 4,521 | Subscribers 521 | Response Rate 11.5% | Total Contacts 12,630 | Contacts per Subscription 24.2 | Avg Age 41.2

If your cards show different numbers, the data load or types are wrong.

## 4. Page layout (16:9)

| Area | Visual | Fields |
|---|---|---|
| Top row | 6 cards | Total Records, Subscribers, Response Rate, Total Contacts, Avg Age, Contacts per Subscription |
| Row 1 left | Donut | Legend `subscribed`, Values `Total Records` |
| Row 1 middle | Clustered column | Axis `age_group`, Values `Response Rate` |
| Row 1 right | Clustered bar | Axis `job`, Values `Response Rate`, sorted descending |
| Row 2 | Clustered column | Axis `contact`, Values `Response Rate` |
| Row 2 | Clustered column | Axis `month` (sorted by month_num), Values `Response Rate` |
| Row 2 | Clustered column | Axis `poutcome`, Values `Response Rate` |
| Row 2 | Clustered column | Axis `campaign_band`, Values `Share of Contacts` and `Share of Subscriptions` |
| Side | Slicers | `education`, `marital`, `housing`, `loan` |

Add a constant line at `Overall Response Rate` in each rate chart (Analytics pane > Constant line, or a line series using the measure). In the tooltip for each chart, add `Total Records` so small groups are visible.

## 5. Design notes

- Palette: navy `#0B2545`, teal `#1B7F8C`, gold `#C9A227`, grey `#8A94A6` (a ready-made theme is in `docs/powerbi_theme.json`; View > Themes > Browse for themes).
- Add a text box stating that the month field has no year and that results are descriptive.
- Keep `duration` out of any "who to target" visual because it is only known after the call.
