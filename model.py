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


def summary(df):
    if df.empty: raise ValueError('No records in selected population')
    renewers=df[df.renewed]
    attempters=df[df.cancellation_attempt]
    return {
        'customers':len(df), 'renewal_rate':float(df.renewed.mean()),
        'full_price_renewal_rate':float((df.renewed & df.discount_pct.eq(0)).mean()),
        'discounted_share_of_renewers':float(renewers.discount_pct.gt(0).mean()) if len(renewers) else 0.,
        'active_full_price_share_of_renewers':float(((renewers.engagement.isin(['High','Moderate'])) & renewers.discount_pct.eq(0)).mean()) if len(renewers) else 0.,
        'survey_awareness_rate':float(df.survey_aware_of_renewal.mean()),
        'cancellation_friction_rate_among_attempts':float(attempters.cancellation_friction_observed.mean()) if len(attempters) else 0.,
        'contribution_per_eligible_customer':float(df.monthly_contribution.mean()),
        'observed_monthly_contribution':float(df.monthly_contribution.sum())
    }


def group_summary(df, field):
    return pd.DataFrame([{'group':str(k), **summary(part)} for k,part in df.groupby(field,dropna=False)])


def scenario(df, discount_reduction_pct=10., elasticity=0.):
    """Non-causal sensitivity analysis. elasticity: renewal probability point loss per 10% discount decrease."""
    if not 0<=discount_reduction_pct<=100 or not 0<=elasticity<=.5: raise ValueError('Invalid assumptions')
    discounted=df.discount_pct.gt(0)
    new_discounts=df.discount_pct * (1-discount_reduction_pct/100)
    new_renew_rate=np.where(discounted, np.clip(df.renewed.astype(float)-elasticity*discount_reduction_pct/10,0,1),df.renewed.astype(float))
    # Historical binary renewed values don't identify the counterfactual; this is a deliberately simplistic sensitivity illustration.
    new_contribution=(30*(1-new_discounts/100)-6)*new_renew_rate
    return {'observed_contribution':float(df.monthly_contribution.sum()), 'scenario_contribution':float(new_contribution.sum()), 'scenario_delta':float(new_contribution.sum()-df.monthly_contribution.sum())}


def integrity_dimensions(df):
    """Descriptive indicators, not a causal or psychometric loyalty score."""
    if df.empty:
        raise ValueError('No records in selected population')
    renewers = df.loc[df.renewed]
    attempts = df.loc[df.cancellation_attempt]
    return {
        'customer_value': {
            'engaged_share': float(df.engagement.isin(['High', 'Moderate']).mean()),
            'engaged_renewers_share': float(renewers.engagement.isin(['High', 'Moderate']).mean()) if len(renewers) else 0.,
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
