"""Subscription Revenue Integrity: interactive research prototype."""
import math
import streamlit as st
import pandas as pd
from model import (make_customers, summary, group_summary, scenario, integrity_dimensions,
                   prepare_uploaded, template_csv, ENGAGED_DEFAULT, PRICE_DEFAULT, SERVICE_COST_DEFAULT)

st.set_page_config(page_title='Subscription Revenue Integrity',page_icon='◈',layout='wide')
st.title('Subscription Revenue Integrity')
st.caption('Are we building customer loyalty or merely recording renewals?')

with st.sidebar:
    mode=st.radio('Data',['Simulated cohort','My own CSV'],help='Simulated data illustrates the framework. Upload a customer-level export to run every screen on your own cohort.')
    if mode=='Simulated cohort':
        st.header('Simulation controls')
        n=st.slider('Synthetic customers',1000,30000,12000,1000)
        seed=st.number_input('Reproducible random seed',min_value=0,max_value=99999,value=42)
    else:
        st.header('Your data')
        up=st.file_uploader('Customer-level CSV',type=['csv'],help='One row per customer eligible to renew. Required: renewed, discount_pct. Everything else is optional.')
        st.download_button('Download a template CSV',template_csv(),'subscription_template.csv','text/csv')
        with st.expander('Columns'):
            st.markdown("""**Required**
- `renewed`: yes/no, 1/0 or true/false
- `discount_pct`: discount on the renewal, 0 to 100 (0 to 1 is accepted and converted)

**Optional** (each one unlocks a view)
- `acquisition_source`: channel or cohort label
- `engagement`: any labels; choose below which ones count as engaged
- `survey_aware_of_renewal`: yes/no, from a survey, not inferred
- `cancellation_attempt`, `cancellation_friction_observed`: yes/no
- `monthly_revenue`, `monthly_contribution`: if absent, valued from the price and cost below""")
        price=st.number_input('Monthly list price',min_value=0.0,value=PRICE_DEFAULT,step=1.0)
        service_cost=st.number_input('Cost to serve per renewing customer, per month',min_value=0.0,value=SERVICE_COST_DEFAULT,step=0.5)
        st.caption('Processed in memory for this session and not stored. Run the app locally and the file never leaves your machine.')

@st.cache_data
def data(n, seed):return make_customers(n,seed)

engaged_labels=list(ENGAGED_DEFAULT)
measured={'engagement':True,'awareness':True,'cancellation':True,'channel':True}
if mode=='Simulated cohort':
    df=data(n,seed)
    st.warning('Research demonstration using simulated customer data. Figures illustrate decisions and assumptions rather than findings about a real business.')
else:
    if up is None:
        st.info('Upload a CSV in the sidebar, or download the template to see the expected shape. Required columns: renewed and discount_pct.'); st.stop()
    try:
        df,notes,measured=prepare_uploaded(pd.read_csv(up),price,service_cost)
    except Exception as err:
        st.error(f'Could not read this file: {err}'); st.stop()
    st.success(f'Your data: {len(df):,} customers. Descriptive measures of this cohort, not causal estimates. The sensitivity screen still uses an assumed renewal response.')
    if notes:
        with st.expander(f'{len(notes)} assumption(s) made about your file'):
            for note in notes: st.markdown(f'- {note}')
    if measured['engagement']:
        with st.sidebar:
            engaged_labels=st.multiselect('Engagement labels that count as engaged',sorted(df.engagement.unique()),default=[l for l in sorted(df.engagement.unique()) if l in ENGAGED_DEFAULT] or sorted(df.engagement.unique())[:1])

def pct(v): return 'not measured' if v is None or (isinstance(v,float) and math.isnan(v)) else f'{v:.1%}'

source=st.multiselect('Acquisition channel',sorted(df.acquisition_source.unique()),default=sorted(df.acquisition_source.unique()))
engagement=st.multiselect('Engagement segment',sorted(df.engagement.unique()),default=sorted(df.engagement.unique()))
d=df[df.acquisition_source.isin(source)&df.engagement.isin(engagement)]
if d.empty:
    st.info('Select at least one acquisition channel and engagement segment.'); st.stop()
s=summary(d,engaged_labels)

st.subheader('The three-dimension framework')
st.markdown('**Customer value** · product engagement and realized outcomes  |  **Economic quality** · full-price renewals and contribution  |  **Choice integrity** · informed renewal and accessible cancellation')
dims=integrity_dimensions(d,engaged_labels)
v,e,choice=st.columns(3)
v.metric('Customer value · engaged share',pct(dims['customer_value']['engaged_share']) if measured['engagement'] else 'not measured')
e.metric('Economic quality · full-price share of renewers',f"{dims['economic_quality']['full_price_share_of_renewers']:.1%}")
choice.metric('Choice integrity · survey awareness',pct(dims['choice_integrity']['survey_awareness_rate']))
st.caption('Independent indicators: awareness comes from ' + ('modeled survey responses' if mode=='Simulated cohort' else 'your survey column, never inferred from activity') + ', while engagement measures product activity.')

st.subheader('01  What does retention actually represent?')
c=st.columns(4)
c[0].metric('Reported renewal rate',f"{s['renewal_rate']:.1%}")
c[1].metric('Full-price renewal rate',f"{s['full_price_renewal_rate']:.1%}")
c[2].metric('Discounted share of renewers',f"{s['discounted_share_of_renewers']:.1%}")
c[3].metric('Monthly contribution / eligible customer',f"${s['contribution_per_eligible_customer']:.2f}")
st.caption('Full-price renewal rate is measured against eligible customers; discount share is measured among renewers.')

st.subheader('02  Evidence of customer choice')
c=st.columns(3)
c[0].metric('Self-reported renewal awareness',pct(s['survey_awareness_rate']))
c[1].metric('Observed friction / cancellation attempt',pct(s['cancellation_friction_rate_among_attempts']) if measured['cancellation'] else 'not measured')
c[2].metric('Active + full-price share of renewers',pct(s['active_full_price_share_of_renewers']) if measured['engagement'] else 'not measured')
st.info('Interpretation: low engagement, billing continuity, and cancellation friction measure different things. Evaluate them independently.')

st.subheader('03  Cohort lens')
tab1,tab2=st.tabs(['Acquisition channels','Engagement levels'])
for tab,field in [(tab1,'acquisition_source'),(tab2,'engagement')]:
    with tab:
        g=group_summary(d,field,engaged_labels)
        shown=g[['group','customers','renewal_rate','discounted_share_of_renewers','contribution_per_eligible_customer']].copy()
        shown.columns=['Segment','Customers','Renewal rate','Discounted share of renewers','Monthly contribution / eligible']
        st.dataframe(shown.style.format({'Renewal rate':'{:.1%}','Discounted share of renewers':'{:.1%}','Monthly contribution / eligible':'${:.2f}'}),use_container_width=True,hide_index=True)

st.subheader('04  Financial sensitivity: what if we reduce discounts?')
st.caption('Scenario analysis based on a user-defined renewal response, rather than estimated treatment effects.')
left,right=st.columns(2)
with left: reduction=st.slider('Discount reduction (%)',0,100,20,5)
with right: loss=st.slider('Assumed renewal reduction (percentage points per 10% discount cut)',0.0,15.0,2.0,0.5)
res=scenario(d,reduction,loss/100,price if mode!='Simulated cohort' else PRICE_DEFAULT,service_cost if mode!='Simulated cohort' else SERVICE_COST_DEFAULT)
x,y,z=st.columns(3)
x.metric('Observed monthly contribution',f"${res['observed_contribution']:,.0f}")
y.metric('Scenario monthly contribution',f"${res['scenario_contribution']:,.0f}")
z.metric('Illustrative difference',f"${res['scenario_delta']:,.0f}")
st.caption('Next step: validate renewal response through a controlled, customer-protective experiment.')

st.subheader('05  VALUE decision framework')
for stage,explanation in [
 ('V · Verify the customer problem','Interview subscribers and finance leaders; examine billing awareness, engagement, complaints, and voluntary renewal evidence.'),
 ('A · Assess the business economics','Separate top-line renewal, full-price renewal, discounts, and net contribution.'),
 ('L · Launch a fair experiment','Compare compliant transparent renewal experiences and permitted incentive strategies with randomized assignment.'),
 ('U · Understand causal evidence','Pre-register profit and trust guardrails; estimate impact with confidence intervals and relevant downstream outcomes.'),
 ('E · Expand or exit','Scale only evidence-backed changes; stop when trust, compliance or economics deteriorate.')]:
    with st.expander(stage):st.write(explanation)

st.subheader('Download the data behind this view')
st.download_button('Download synthetic dataset CSV' if mode=='Simulated cohort' else 'Download your normalised data as CSV',d.to_csv(index=False),'synthetic_subscriptions.csv' if mode=='Simulated cohort' else 'normalised_subscriptions.csv','text/csv')
st.markdown('---')
st.caption('© 2026 Uta Knablein. All rights reserved. | Subscription Revenue Integrity')
