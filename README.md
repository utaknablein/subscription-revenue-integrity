# Subscription Revenue Integrity

**Are we building customer loyalty, or merely recording renewals?**

Subscription businesses often report renewal rates as evidence of healthy customer relationships. But identical renewal rates can hide fundamentally different economics: full-price demand, incentive-supported renewals, customer engagement, and the ability to make informed subscription decisions.

This interactive research prototype examines those differences through three complementary dimensions.

## The framework

| Dimension | What to examine | Executive decision |
|---|---|---|
| **Customer value** | Engagement, customer-defined outcomes, satisfaction | Are we earning the relationship through delivered value? |
| **Economic quality** | Full-price renewal, discount recurrence, contribution margin | Are renewals financially sustainable? |
| **Choice integrity** | Customer-reported awareness, renewal disclosures, cancellation completion | Can customers make an informed choice? |

These measures are intentionally separate. A single blended score could conceal important differences between a valuable low-frequency subscription and a heavily discounted, high-engagement one.

## What the prototype demonstrates

1. **Renewal economics:** Compare reported renewal rates, full-price renewals, discounts, and contribution per eligible subscriber.
2. **Customer evidence:** Inspect simulated awareness responses and observed cancellation-path friction alongside engagement data.
3. **Cohort analysis:** Compare acquisition channels and engagement segments.
4. **Financial sensitivity:** Explore the trade-off between reducing discounts and potentially losing renewals.
5. **VALUE methodology:** Verify the customer problem, Assess economics, Launch a fair experiment, Understand evidence, and Expand or exit.

## The argument

**Problem:** Revenue dashboards can make very different customer relationships look equally healthy.

**Hypothesis:** Looking at customer outcomes, sustainable contribution, and informed choice together can improve management's assessment of recurring-revenue durability.

**Method:** Compare independently defined measures and test financial sensitivities. Use controlled experiments to learn which pricing or communication changes cause incremental improvements.

**Demonstration:** The interactive dashboard illustrates how cohorts with similar renewal rates can differ in profitability and customer experience. In the default simulation an 82% reported renewal rate sits alongside a 33% full-price renewal rate, and the best-renewing cohort contributes the least per customer.

**Next question:** Which indicators, independently or together, best predict sustained contribution over subsequent renewal cycles?

## Run it on your own data

Switch the sidebar from *Simulated cohort* to *My own CSV* and upload a customer-level export: one row per customer who was eligible to renew. Two columns are required, `renewed` (yes/no) and `discount_pct` (0 to 100). Every other column is optional and unlocks a view when present: `acquisition_source`, `engagement` (any labels; you choose which count as engaged), `survey_aware_of_renewal`, `cancellation_attempt`, `cancellation_friction_observed`, `monthly_revenue`, `monthly_contribution`. A template CSV is downloadable from the sidebar. Indicators the file does not contain show as *not measured* rather than as zero, and every assumption the app makes about your file (a missing column, a fraction converted to percent) is listed above the results.

Run the app locally and the file never leaves your machine. On a hosted instance it is processed in memory for the session and not stored. The measures are descriptive summaries of the cohort you uploaded; the sensitivity screen still depends on an assumed renewal response, as it does for simulated data.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run automated checks:

```bash
pytest -q
```

## What this is and is not

In its default mode this is a synthetic-data decision demonstration, not a validated predictor, a causal estimate, or a finding about any real company. With your own data uploaded it is a descriptive view of that cohort, still not a causal estimate. Every record is generated locally by `model.make_customers()` from a fixed random seed; the repository contains no customer exports, and prices, discounts, channel mixes and renewal probabilities are invented illustrative parameters. Customer inattention cannot be inferred from non-use, and changes in renewal outcomes require appropriate measurement. All proposed tests preserve required disclosure and cancellation protections.

## Next research steps

- Conduct customer interviews to define realized value and renewal awareness.
- Study actual, appropriately authorized renewal cohorts and incentive histories.
- Estimate the uncertainty of cohort differences and longer-term contribution.
- Test pricing and communication policies with compliant randomized experiments.
- Compare forecasts against real subsequent renewal outcomes.

## Research context

See [RESEARCH_CONTEXT.md](RESEARCH_CONTEXT.md) for foundational scholarship and the validation questions it raises. This framework is an independent synthesis, with room to challenge and improve its assumptions.

## Rights and attribution

Copyright © 2026 Uta Knablein. All rights reserved. See [COPYRIGHT.md](COPYRIGHT.md). Third-party libraries retain their own licensing terms.

## Project files

- `app.py`: interactive Streamlit dashboard
- `model.py`: reproducible customer simulation and calculations
- `tests/test_model.py`: model tests
- `tests/test_upload.py`: tests for running the analysis on uploaded data
- `requirements.txt`: dependencies
- `RESEARCH_CONTEXT.md`: literature and methodological context
- `COPYRIGHT.md`: rights notice
