# Dataset inspection

Four files were uploaded. Only `bank.csv` is used for the analysis.

| File | Rows | What it is | Used? |
|---|---|---|---|
| `bank.csv` | 4,521 | The labelled sample: 16 input columns plus `y` (subscribed yes/no). Semicolon-separated. | Yes |
| `test.csv` | 427 | Same 16 inputs plus an `Id` column, **no `y`**. Comma-separated. All 427 rows are from May. | No |
| `sample_submission_.csv` | 427 | `Id,y` with every `y` set to 0.5. A placeholder from a Kaggle-style competition. | No |
| `bank-names.txt` | - | Original UCI description of the dataset and the citation request. | Reference only |

`test.csv` and the submission file cannot be used for campaign analysis because there is no outcome to measure. `test.csv` is also all May, so it is not representative of the full year.

## Checks on bank.csv

- 4,521 rows, 17 columns (7 numeric, 10 text).
- Missing values: 0. Exact duplicate rows: 0.
- Text columns had no stray whitespace or mixed casing; values match the categories in `bank-names.txt`.
- `y`: 521 "yes" (11.52%) and 4,000 "no". The classes are imbalanced.
- Age ranges from 19 to 87. Duration is between 4 and 3,025 seconds, none are zero.
- `balance` has 366 negative values (overdrawn accounts) and a maximum of 71,188 EUR. These look like real values rather than errors, so they were kept.
- `pdays = -1` in 3,705 rows. All of these rows have `previous = 0` and `poutcome = unknown`, so -1 consistently means "not contacted in a previous campaign".
- "unknown" appears in `job` (38 rows), `education` (187), `contact` (1,324) and `poutcome` (3,705).
- 39 rows in `test.csv` have the same 16 feature values as a row in `bank.csv`. Both files appear to be drawn from the same larger UCI dataset, which is not a problem here because `test.csv` is not analysed.

## Limitations of the data

1. **It is a 10% random sample** of the full UCI file (45,211 rows). Segment sizes are small in places (for example 20 records in December, 67 under age 25).
2. **No year.** Only `day` and `month` are given. The full dataset covers May 2008 to November 2010, so a month here pools up to three years and there is no valid date to build a time series from.
3. **`duration` is known only after the call.** It is strongly related to the outcome (correlation 0.40 with the yes/no flag, the highest of any numeric column), but it cannot be used to decide who to call. The UCI authors say the same. It is described but not used as a targeting variable.
4. **`campaign` is partly a result of the process.** A client who agrees early stops being called, so clients with many contacts are, by construction, ones who had not agreed yet.
5. **`contact = unknown` is a data-recording gap**, not a channel. It is concentrated in May and June (59% and 85% of those months' records).
6. **No customer ID, no cost or revenue data.** Costs per call and deposit amounts are not in the file, so profitability cannot be measured. Results are response rates, not return on investment.
7. **Observational data.** The bank chose who to call, so differences between segments describe who responded, not what would happen if a different group were called.
