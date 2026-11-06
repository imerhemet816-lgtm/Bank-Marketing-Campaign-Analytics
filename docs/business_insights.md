# Business insights

All figures come from `bank.csv` (4,521 records, 10% random sample) and can be reproduced with `src/02_eda.py` or `sql/bank_marketing_analysis.sql`. These are historical observations about who responded. They are not forecasts, and the bank chose who to call, so none of them show that a change in targeting would cause a change in results.

**Baseline:** 521 of 4,521 clients subscribed (11.52%, 95% interval roughly 10.6% to 12.5%). The campaign used 12,630 contacts, or about 24 contacts per subscription.

---

## 1. Clients with a successful previous campaign are by far the most likely to say yes

**Evidence.** 83 of 129 clients whose previous outcome was "success" subscribed again (64.3%). Clients never contacted before converted at 9.1% (337 of 3,705). Those 129 clients are 2.9% of the records but 15.9% of all subscriptions. Clients with any previous contact (success, failure or other) responded at 22.5% (184 of 816), compared with 9.1% for new clients.

**Interpretation.** Existing relationships are the cheapest source of subscriptions in this data. Even previous "failure" clients (12.9%) did better than first-time contacts.

**Recommendation.** Call previous-success and other previously contacted clients first, before working through cold lists. In a banking CRM that means a simple priority flag on the call list.

**Limitations.** Only 129 records are in the success group (interval roughly 56% to 72%). These clients were already customers who engaged before, so the gap reflects who they are as well as the earlier contact.

## 2. A third of the contact attempts went to clients who were contacted six or more times, and they produced 6.5% of subscriptions

**Evidence.** Clients with 6+ contacts in this campaign are 473 records (10.5%). They used 4,559 of the 12,630 contacts (36.1%) and delivered 34 of the 521 subscriptions (6.5%). Their response rate is 7.2%, against 13.8% for clients contacted once. The 4-5 contact group converted at 10.6%.

**Interpretation.** Returns drop as attempts pile up. Pushing past five attempts consumed a large share of call capacity for few extra subscriptions.

**Recommendation.** Test a cap of around five attempts per client in the next campaign and move the saved call time to higher-response segments (insights 1 and 5).

**Limitations.** This is partly built into the variable: someone who agrees on the first call is never called six times. The data cannot tell us whether a sixth call changes anyone's mind. A capped pilot would be the way to find out.

## 3. Records with an unrecorded contact channel convert at a third of the rate of the others

**Evidence.** Contact = "unknown" (1,324 records): 4.6% response. Cellular: 14.4% (2,896). Telephone: 14.6% (301). The gap holds inside the busiest months. In May, unknown is 3.9% (32 of 820) against 10.6% (61 of 578) for known channels. In June, unknown is 4.7% (21 of 450) against 42.0% (34 of 81).

**Interpretation.** Cellular and telephone perform about the same, so the choice between those two does not explain much. The weak group is the unrecorded one, which suggests a different calling process or list, or a record-keeping problem.

**Recommendation.** Find out what "unknown" represents (a particular list, dialler or team) and make the channel a required field. Until then, treat these records as a separate segment when judging campaign performance.

**Limitations.** I cannot tell from the file what "unknown" means. 59% of May records and 85% of June records are unknown, so channel and month are tangled together.

## 4. May carries the most volume and has the lowest response rate

**Evidence.** May has 1,398 records (30.9% of the sample) and a 6.7% response rate, contributing 93 subscriptions (17.9% of the total). March, September, October and December together have only 201 records but 84 subscriptions (41.8%). July is also low at 8.6% (706 records).

**Interpretation.** The campaign was heavily weighted to May, and that is where it converted worst.

**Recommendation.** Before drawing a seasonal conclusion, compare the client lists used in May against the quieter months. If the lists were similar, shifting some volume away from May is worth testing.

**Limitations.** The data has no year, so months from 2008 to 2010 are pooled. The high-rate months are small (20 to 80 records each) and may reflect a targeted list rather than a seasonal effect. May also overlaps with the unknown-channel problem in insight 3.

## 5. Clients with no housing loan and no personal loan respond about twice as often

**Evidence.** No housing loan and no personal loan: 16.9% (1,677 clients). Housing loan only: 9.1% (2,153). Personal loan only: 6.3% (285). Both: 6.2% (406). A segment of "no loans and a positive balance" has a response rate of 18.2% (264 of 1,453) against 8.4% for everyone else. The housing-loan gap does not disappear when age is held roughly constant: among clients aged 35-54, 12.7% without a housing loan subscribed versus 8.4% with one. Response also rises with balance up to the 1,501-5,000 EUR band (16.9%), then falls to 11.0% above 5,000 EUR (309 clients).

**Interpretation.** Clients who are not already committed to loan repayments are more receptive to a term deposit. The drop at the highest balances suggests balance alone is not the driver.

**Recommendation.** Use loan status and a positive balance as a first filter when building call lists, and test it against a random control group.

**Limitations.** The reason is not in the data; "less cash tied up in loans" is a hypothesis. The segment definition was chosen after looking at the data, so the 18.2% will likely look a bit weaker on a fresh sample.

## 6. The oldest and youngest clients respond most, but the groups are small

**Evidence.** Age 65+: 36.0% (32 of 89). Under 25: 19.4% (13 of 67). Ages 35-44 are lowest at 9.4% (1,456 clients). By job, retired clients respond at 23.5% (230) and students at 22.6% (84), while blue-collar clients are at 7.3% (946). Retired clients under 65 still convert at 15.4% (156). Tertiary-educated clients respond at 14.3% against 9.4% for primary education, and blue-collar clients with primary education are lowest at 4.3% (369).

**Interpretation.** Retirees are the clearest high-response group with a usable sample size. The age pattern is U-shaped rather than a steady rise.

**Recommendation.** Try a retiree-focused offer or script as a pilot, and review whether blue-collar clients with primary education need a different product or message than a term deposit pitch.

**Limitations.** The 65+ interval is wide (about 27% to 46%) and the under-25 group has 67 clients. Job, age and education overlap, so these are not independent effects.

## 7. Call length is the strongest signal in the data, but it cannot be used for targeting

**Evidence.** Subscribers averaged 553 seconds per call against 226 seconds for non-subscribers. Duration has the highest correlation with the outcome of any numeric column (0.40).

**Interpretation.** Longer conversations go with a yes, but duration is only known after the call ends and a call tends to be long because the client is interested.

**Recommendation.** Do not use duration in any call-prioritisation rule. It is more useful for call-quality review, for example listening to short calls from segments that normally convert well.

**Limitations.** Direction of cause cannot be determined from this data.

---

### What this analysis cannot say

There is no cost, revenue or deposit-size data, so no insight here measures profit. The sample is 10% of the full file. Segment differences are descriptive, and none were tested in a controlled experiment.
