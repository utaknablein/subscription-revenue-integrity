import io
import math
import pandas as pd
import pytest
from model import prepare_uploaded, summary, integrity_dimensions, scenario, template_csv, make_customers


def test_minimal_two_column_upload_runs_every_screen():
    raw = pd.DataFrame({'Renewed': ['yes', 'no', 'Y', 'N'] * 10, 'Discount Pct': [0, 0.25, 0.1, 0] * 10})
    df, notes, measured = prepare_uploaded(raw, price=20, service_cost=4)
    s = summary(df)
    assert s['renewal_rate'] == 0.5
    assert s['full_price_renewal_rate'] == 0.25
    assert math.isnan(s['survey_awareness_rate'])  # not measured, never 0%
    assert measured == {'engagement': False, 'awareness': False, 'cancellation': False, 'channel': False}
    assert any('fraction' in n for n in notes)
    assert scenario(df, 20, 0.02, price=20, service_cost=4)['observed_contribution'] == s['observed_monthly_contribution']
    integrity_dimensions(df)  # must not raise


def test_full_synthetic_export_round_trips_without_notes():
    csv = make_customers(500, 3).to_csv(index=False)
    df, notes, measured = prepare_uploaded(pd.read_csv(io.StringIO(csv)))
    assert notes == []
    assert all(measured.values())
    assert summary(df)['renewal_rate'] == summary(make_customers(500, 3))['renewal_rate']


def test_custom_engagement_labels_change_engaged_share():
    raw = pd.DataFrame({'renewed': [1] * 40, 'discount_pct': [0] * 40, 'engagement': ['daily', 'weekly', 'monthly', 'none'] * 10})
    df, _, measured = prepare_uploaded(raw)
    assert measured['engagement']
    assert integrity_dimensions(df, ['daily', 'weekly'])['customer_value']['engaged_share'] == 0.5
    assert integrity_dimensions(df, ['daily'])['customer_value']['engaged_share'] == 0.25


def test_rejects_missing_required_column_and_unreadable_booleans():
    with pytest.raises(ValueError, match='Missing required'):
        prepare_uploaded(pd.DataFrame({'renewed': [1] * 30}))
    with pytest.raises(ValueError, match='not yes/no'):
        prepare_uploaded(pd.DataFrame({'renewed': ['maybe'] * 30, 'discount_pct': [0] * 30}))
    with pytest.raises(ValueError, match='at least 20'):
        prepare_uploaded(pd.DataFrame({'renewed': [1] * 5, 'discount_pct': [0] * 5}))


def test_template_is_itself_a_valid_upload():
    df, notes, measured = prepare_uploaded(pd.read_csv(io.StringIO(template_csv())))
    assert len(df) == 25
    assert all(measured.values())
    assert all('monthly_' in n for n in notes)  # only revenue and contribution are derived
