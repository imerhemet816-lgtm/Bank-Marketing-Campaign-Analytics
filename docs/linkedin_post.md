I put together a small analytics project on a bank's phone marketing campaign for term deposits, using the UCI Bank Marketing data (a 4,521-record sample).

The question was simple: where did the calling effort go, and where did it pay off? I cleaned the data and analysed it in Python, wrote 19 queries in MySQL to cross-check the numbers, and built an Excel workbook and an interactive dashboard in Streamlit.

Three things stood out:

- Overall, 11.5% of clients subscribed, which took about 24 contacts per subscription.
- Clients contacted six or more times used 36% of all contact attempts but produced 6.5% of the subscriptions.
- Clients with a previous successful campaign subscribed again 64% of the time, against 9% for clients never contacted before. That group is only 129 records, so I would treat the exact figure with caution.

A few limits worth saying: it's observational data with no year, cost or revenue information, so it shows who responded, not what would work if the bank changed its approach. Part of the drop at high contact counts is built in too, since people who agree early stop being called.

I used AI assistance for the code and drafts and checked the results against the raw data. The dashboard runs locally; I haven't deployed it.

Code, SQL and write-up: [GitHub repository link]

#DataAnalytics #SQL #Python #Excel
