import pytest
from model import make_customers, summary, scenario, group_summary, integrity_dimensions

def test_reproducible():
    a,b=make_customers(1000,7),make_customers(1000,7)
    assert a.equals(b)

def test_internal_consistency():
    df=make_customers(2000)
    s=summary(df)
    assert 0<=s['full_price_renewal_rate']<=s['renewal_rate']<=1
    assert not df.loc[~df.cancellation_attempt,'cancellation_friction_observed'].any()
    assert (df.monthly_contribution<=df.monthly_revenue).all()

def test_zero_change():
    df=make_customers(1000)
    assert abs(scenario(df,0,0)['scenario_delta'])<1e-6

def test_group_counts():
    df=make_customers(1000)
    assert group_summary(df,'engagement').customers.sum()==1000

def test_invalid():
    with pytest.raises(ValueError): make_customers(5)
    with pytest.raises(ValueError): scenario(make_customers(100),120,0)


def test_three_dimensions_and_bounds():
    dims=integrity_dimensions(make_customers(1000))
    assert set(dims)=={'customer_value','economic_quality','choice_integrity'}
    assert 0<=dims['customer_value']['engaged_share']<=1
    assert 0<=dims['economic_quality']['full_price_share_of_renewers']<=1
    assert 0<=dims['choice_integrity']['friction_per_attempt']<=1
