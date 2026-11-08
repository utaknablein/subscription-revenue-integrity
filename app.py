"""Subscription Revenue Integrity: interactive research prototype."""
import streamlit as st
import pandas as pd
from model import make_customers, summary, group_summary, scenario, integrity_dimensions

st.set_page_config(page_title='Subscription Revenue Integrity',page_icon='◈',layout='wide')
st.title('Subscription Revenue Integrity')
st.caption('Are we building customer loyalty or merely recording renewals?')
st.warning('Research demonstration using simulated customer data. Figures illustrate decisions and assumptions rather than findings about a real business.')
with st.sidebar:
    st.header('Simulation controls')
    n=st.slider('Synthetic customers',1000,30000,12000,1000)
    seed=st.number_input('Reproducible random seed',min_value=0,max_value=99999,value=42)

@st.cache_data
def data(n, seed):return make_customers(n,seed)
df=data(n,seed)
source=st.multiselect('Acquisition channel',sorted(df.acquisition_source.unique()),default=sorted(df.acquisition_source.unique()))
engagement=st.multiselect('Engagement segment',sorted(df.engagement.unique()),default=sorted(df.engagement.unique()))
d=df[df.acquisition_source.isin(source)&df.engagement.isin(engagement)]
if d.empty:
    st.info('Select at least one acquisition channel and engagement segment.'); st.stop()
s=summary(d)

st.subheader('The three-dimension framework')
st.markdown('**Customer value** · product engagement and realized outcomes  |  **Economic quality** · full-price renewals and contribution  |  **Choice integrity** · informed renewal and accessible cancellation')
dims=integrity_dimensions(d)
v,e,choice=st.columns(3)
v.metric('Customer value · engaged share',f"{dims['customer_value']['engaged_share']:.1%}")
e.metric('Economic quality · full-price share of renewers',f"{dims['economic_quality']['full_price_share_of_renewers']:.1%}")
choice.metric('Choice integrity · survey awareness',f"{dims['choice_integrity']['survey_awareness_rate']:.1%}")
st.caption('Independent indicators: awareness comes from modeled survey responses, while engagement measures product activity.')

st.subheader('01  What does retention actually represent?')
c=st.columns(4)
c[0].metric('Reported renewal rate',f"{s['renewal_rate']:.1%}")
c[1].metric('Full-price renewal rate',f"{s['full_price_renewal_rate']:.1%}")
c[2].metric('Discounted share of renewers',f"{s['discounted_share_of_renewers']:.1%}")
c[3].metric('Monthly contribution / eligible customer',f"${s['contribution_per_eligible_customer']:.2f}")
st.caption('Full-price renewal rate is measured against eligible customers; discount share is measured among renewers.')

st.subheader('02  Evidence of customer choice')
c=st.columns(3)
c[0].metric('Self-reported renewal awareness',f"{s['survey_awareness_rate']:.1%}")
c[1].metric('Observed friction / cancellation attempt',f"{s['cancellation_friction_rate_among_attempts']:.1%}")
c[2].metric('Active + full-price share of renewers',f"{s['active_full_price_share_of_renewers']:.1%}")
st.info('Interpretation: low engagement, billing continuity, and cancellation friction measure different things. Evaluate them independently.')

st.subheader('03  Cohort lens')
tab1,tab2=st.tabs(['Acquisition channels','Engagement levels'])
for tab,field in [(tab1,'acquisition_source'),(tab2,'engagement')]:
    with tab:
        g=group_summary(d,field)
        shown=g[['group','customers','renewal_rate','discounted_share_of_renewers','contribution_per_eligible_customer']].copy()
        shown.columns=['Segment','Customers','Renewal rate','Discounted share of renewers','Monthly contribution / eligible']
        st.dataframe(shown.style.format({'Renewal rate':'{:.1%}','Discounted share of renewers':'{:.1%}','Monthly contribution / eligible':'${:.2f}'}),use_container_width=True,hide_index=True)

st.subheader('04  Financial sensitivity: what if we reduce discounts?')
st.caption('Scenario analysis based on a user-defined renewal response, rather than estimated treatment effects.')
left,right=st.columns(2)
with left: reduction=st.slider('Discount reduction (%)',0,100,20,5)
with right: loss=st.slider('Assumed renewal reduction (percentage points per 10% discount cut)',0.0,15.0,2.0,0.5)
res=scenario(d,reduction,loss/100)
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

st.subheader('Download reproducible synthetic data')
st.download_button('Download synthetic dataset CSV',d.to_csv(index=False),'synthetic_subscriptions.csv','text/csv')
st.markdown('---')
st.caption('© 2026 Uta Knablein. All rights reserved. | Subscription Revenue Integrity')
