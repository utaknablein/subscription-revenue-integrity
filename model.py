"""Synthetic subscription data + descriptive quality analysis. No real user records."""
import numpy as np
import pandas as pd


def make_customers(n=12000, seed=42):
    if n < 100: raise ValueError('n must be >= 100')
    r = np.random.default_rng(seed)
    cohort = r.choice(['Organic acquisition','Promotional acquisition','Partner acquisition'], n, p=[.4,.42,.18])
    tenure = r.integers(1, 37, n)
    engagement = r.choice(['High','Moderate','Low','No recent activity'],n,p=[.25,.3,.29,.16])
    discount = np.where(cohort=='Promotional acquisition',r.choice([0,10,25,40],n,p=[.1,.22,.38,.3]),r.choice([0,10,25,40],n,p=[.63,.24,.1,.03]))
    awareness = r.random(n) < np.clip(.84 - .16*(engagement=='No recent activity')-.10*(tenure>18),.2,.98)
    # 'Awareness' stands for an explicit synthetic survey answer; it is not derived from inactivity.
    cancellation_attempt = r.random(n)<(.035+.11*(engagement=='No recent activity')+.05*(discount>=25))
    # Friction is generated only for people who tried to cancel and describes a synthetic process outcome.
    cancellation_friction = cancellation_attempt & (r.random(n)<.24)
    renewal_p = np.clip(.88 + .055*(engagement=='High')-.13*(engagement=='Low')-.31*(engagement=='No recent activity')+.06*(discount>=25)-.11*cancellation_attempt+.06*cancellation_friction,.02,.98)
    renewed = r.random(n)<renewal_p
    price = 30.0
    service_cost=6.0
    revenue = renewed*(price*(1-discount/100))
    margin = revenue-renewed*service_cost
    data=pd.DataFrame({'customer_id':np.arange(1,n+1),'acquisition_source':cohort,'tenure_months':tenure,'engagement':engagement,'discount_pct':discount,'survey_aware_of_renewal':awareness,'cancellation_attempt':cancellation_attempt,'cancellation_friction_observed':cancellation_friction,'renewed':renewed,'monthly_revenue':revenue,'monthly_contribution':margin})
    return data


ENGAGED_DEFAULT = ('High', 'Moderate')
PRICE_DEFAULT = 30.0
SERVICE_COST_DEFAULT = 6.0


def summary(df, engaged_labels=ENGAGED_DEFAULT):
    if df.empty: raise ValueError('No records in selected population')
    engaged_labels = list(engaged_labels)
    renewers=df[df.renewed]
    attempters=df[df.cancellation_attempt]
    return {
        'customers':len(df), 'renewal_rate':float(df.renewed.mean()),
        'full_price_renewal_rate':float((df.renewed & df.discount_pct.eq(0)).mean()),
        'discounted_share_of_renewers':float(renewers.discount_pct.gt(0).mean()) if len(renewers) else 0.,
        'active_full_price_share_of_renewers':float(((renewers.engagement.isin(engaged_labels)) & renewers.discount_pct.eq(0)).mean()) if len(renewers) else 0.,
        'survey_awareness_rate':float(df.survey_aware_of_renewal.mean()),
        'cancellation_friction_rate_among_attempts':float(attempters.cancellation_friction_observed.mean()) if len(attempters) else 0.,
        'contribution_per_eligible_customer':float(df.monthly_contribution.mean()),
        'observed_monthly_contribution':float(df.monthly_contribution.sum())
    }


def group_summary(df, field, engaged_labels=ENGAGED_DEFAULT):
    return pd.DataFrame([{'group':str(k), **summary(part, engaged_labels)} for k,part in df.groupby(field,dropna=False)])


def scenario(df, discount_reduction_pct=10., elasticity=0., price=PRICE_DEFAULT, service_cost=SERVICE_COST_DEFAULT):
    """Non-causal sensitivity analysis. elasticity: renewal probability point loss per 10% discount decrease.
    price and service_cost are the per-customer monthly list price and cost to serve used to value the scenario."""
    if not 0<=discount_reduction_pct<=100 or not 0<=elasticity<=.5: raise ValueError('Invalid assumptions')
    discounted=df.discount_pct.gt(0)
    new_discounts=df.discount_pct * (1-discount_reduction_pct/100)
    new_renew_rate=np.where(discounted, np.clip(df.renewed.astype(float)-elasticity*discount_reduction_pct/10,0,1),df.renewed.astype(float))
    # Historical binary renewed values don't identify the counterfactual; this is a deliberately simplistic sensitivity illustration.
    new_contribution=(price*(1-new_discounts/100)-service_cost)*new_renew_rate
    return {'observed_contribution':float(df.monthly_contribution.sum()), 'scenario_contribution':float(new_contribution.sum()), 'scenario_delta':float(new_contribution.sum()-df.monthly_contribution.sum())}


def integrity_dimensions(df, engaged_labels=ENGAGED_DEFAULT):
    """Descriptive indicators, not a causal or psychometric loyalty score."""
    if df.empty:
        raise ValueError('No records in selected population')
    engaged_labels = list(engaged_labels)
    renewers = df.loc[df.renewed]
    attempts = df.loc[df.cancellation_attempt]
    return {
        'customer_value': {
            'engaged_share': float(df.engagement.isin(engaged_labels).mean()),
            'engaged_renewers_share': float(renewers.engagement.isin(engaged_labels).mean()) if len(renewers) else 0.,
        },
        'economic_quality': {
            'full_price_share_of_renewers': float(renewers.discount_pct.eq(0).mean()) if len(renewers) else 0.,
            'contribution_per_eligible_customer': float(df.monthly_contribution.mean()),
            'renewal_rate': float(df.renewed.mean()),
        },
        'choice_integrity': {
            'survey_awareness_rate': float(df.survey_aware_of_renewal.mean()),
            'friction_per_attempt': float(attempts.cancellation_friction_observed.mean()) if len(attempts) else 0.,
            'attempts_observed': int(len(attempts)),
        },
    }


# ---------------------------------------------------------------------------
# Running the analysis on your own data
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ('renewed', 'discount_pct')
OPTIONAL_COLUMNS = ('customer_id', 'acquisition_source', 'tenure_months', 'engagement',
                    'survey_aware_of_renewal', 'cancellation_attempt', 'cancellation_friction_observed',
                    'monthly_revenue', 'monthly_contribution')

_TRUE = {'1', 'true', 't', 'yes', 'y', 'renewed', 'active'}
_FALSE = {'0', 'false', 'f', 'no', 'n', 'churned', 'cancelled', 'canceled', 'lapsed', ''}


def _to_bool(series, name):
    """Coerce 1/0, true/false, yes/no, renewed/churned to booleans. Unrecognised values raise."""
    if series.dtype == bool:
        return series
    text = series.astype(str).str.strip().str.lower()
    unknown = sorted(set(text[~text.isin(_TRUE | _FALSE | {'nan', 'none'})]))
    if unknown:
        raise ValueError(f"Column '{name}' has values that are not yes/no: {unknown[:5]}")
    out = text.isin(_TRUE)
    out[text.isin({'nan', 'none'})] = False
    return out


def prepare_uploaded(raw, price=PRICE_DEFAULT, service_cost=SERVICE_COST_DEFAULT):
    """Normalise a customer-level export so every screen can run on it.

    Needs: renewed (yes/no), discount_pct (0 to 100, the discount applied to the renewal).
    Optional: acquisition_source, engagement, tenure_months, survey_aware_of_renewal,
    cancellation_attempt, cancellation_friction_observed, monthly_revenue, monthly_contribution.
    Missing optional columns are filled so the analysis runs, and each fill is reported in `notes`
    so the user knows which indicators are their data and which are placeholders.
    Returns (dataframe, notes, measured) where measured says which optional dimensions the data contains.
    """
    df = raw.copy()
    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    raw_cols = set(df.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}. Needed: {list(REQUIRED_COLUMNS)}")
    if len(df) < 20:
        raise ValueError('Upload at least 20 customer rows')
    notes = []

    df['renewed'] = _to_bool(df['renewed'], 'renewed')
    df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce')
    if df['discount_pct'].isna().any():
        notes.append(f"{int(df['discount_pct'].isna().sum())} rows had a non-numeric discount and were treated as 0% discount")
        df['discount_pct'] = df['discount_pct'].fillna(0)
    if df['discount_pct'].between(0, 1).all() and df['discount_pct'].gt(0).any():
        df['discount_pct'] = df['discount_pct'] * 100
        notes.append('discount_pct looked like a fraction (0 to 1) and was converted to percent')
    df['discount_pct'] = df['discount_pct'].clip(0, 100)

    if 'customer_id' not in df.columns:
        df['customer_id'] = np.arange(1, len(df) + 1)
    if 'acquisition_source' not in df.columns:
        df['acquisition_source'] = 'All customers'
        notes.append('No acquisition_source column: the channel view shows one group')
    if 'engagement' not in df.columns:
        df['engagement'] = 'Not provided'
        notes.append('No engagement column: customer value indicators are not available')
    if 'tenure_months' not in df.columns:
        df['tenure_months'] = np.nan
    df['acquisition_source'] = df['acquisition_source'].fillna('Unknown').astype(str)
    df['engagement'] = df['engagement'].fillna('Unknown').astype(str)

    measured = {'engagement': 'engagement' in raw_cols, 'awareness': 'survey_aware_of_renewal' in df.columns,
                'cancellation': 'cancellation_attempt' in df.columns, 'channel': 'acquisition_source' in raw_cols}
    if measured['awareness']:
        df['survey_aware_of_renewal'] = _to_bool(df['survey_aware_of_renewal'], 'survey_aware_of_renewal')
    else:
        df['survey_aware_of_renewal'] = np.nan  # "not measured", never 0%
        notes.append('No survey_aware_of_renewal column: renewal awareness is not measured in this data')
    for col, label in (('cancellation_attempt', 'cancellation attempts are'),
                       ('cancellation_friction_observed', 'cancellation friction is')):
        if col in df.columns:
            df[col] = _to_bool(df[col], col)
        else:
            df[col] = False
            notes.append(f'No {col} column: {label} not measured in this data')

    if 'monthly_revenue' not in df.columns:
        df['monthly_revenue'] = df['renewed'] * (price * (1 - df['discount_pct'] / 100))
        notes.append(f'No monthly_revenue column: revenue valued at a ${price:.2f} list price less the discount')
    else:
        df['monthly_revenue'] = pd.to_numeric(df['monthly_revenue'], errors='coerce').fillna(0)
    if 'monthly_contribution' not in df.columns:
        df['monthly_contribution'] = df['monthly_revenue'] - df['renewed'] * service_cost
        notes.append(f'No monthly_contribution column: contribution is revenue less ${service_cost:.2f} cost to serve per renewal')
    else:
        df['monthly_contribution'] = pd.to_numeric(df['monthly_contribution'], errors='coerce').fillna(0)

    cols = ['customer_id', 'acquisition_source', 'tenure_months', 'engagement', 'discount_pct',
            'survey_aware_of_renewal', 'cancellation_attempt', 'cancellation_friction_observed',
            'renewed', 'monthly_revenue', 'monthly_contribution']
    return df[cols], notes, measured


def template_csv():
    """A small CSV in the expected shape, for download."""
    return make_customers(200, 7).drop(columns=['monthly_revenue', 'monthly_contribution']).head(25).to_csv(index=False)
