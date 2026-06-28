"""
APL Logistics — Customer, Product & Profitability Performance Dashboard
Streamlit Web Application
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="APL Logistics | Profitability Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME / STYLING
# ============================================================
PRIMARY = "#1f3a5f"
TEAL = "#2a9d8f"
CORAL = "#e76f51"
GOLD = "#e9c46a"

st.markdown("""
<style>
    .main .block-container {padding-top: 1.5rem;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 700;}
    .stTabs [data-baseweb="tab-list"] {gap: 4px;}
    .stTabs [data-baseweb="tab"] {height: 42px; padding: 0 16px;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA LOADING (cached)
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_parquet("data.parquet")
    return df

df_full = load_data()

# ============================================================
# SIDEBAR — GLOBAL FILTERS
# ============================================================
st.sidebar.markdown("## 📦 APL Logistics")
st.sidebar.caption("Customer, Product & Profitability Performance Analysis")
st.sidebar.divider()
st.sidebar.markdown("### Filters")

segments = sorted(df_full['Customer Segment'].unique().tolist())
sel_segments = st.sidebar.multiselect("Customer Segment", segments, default=segments)

markets = sorted(df_full['Market'].unique().tolist())
sel_markets = st.sidebar.multiselect("Market", markets, default=markets)

regions_available = sorted(df_full[df_full['Market'].isin(sel_markets)]['Order Region'].unique().tolist())
sel_regions = st.sidebar.multiselect("Order Region", regions_available, default=regions_available)

categories = sorted(df_full['Category Name'].unique().tolist())
sel_categories = st.sidebar.multiselect("Category", categories, default=categories)

discount_range = st.sidebar.slider(
    "Discount Rate Range",
    min_value=0.0, max_value=float(df_full['Order Item Discount Rate'].max()),
    value=(0.0, float(df_full['Order Item Discount Rate'].max())),
    step=0.01, format="%.2f"
)

st.sidebar.divider()
st.sidebar.caption("Built for APL Logistics (KWE Group) | Unified Mentor Project 7518")

# Apply filters
df = df_full[
    (df_full['Customer Segment'].isin(sel_segments)) &
    (df_full['Market'].isin(sel_markets)) &
    (df_full['Order Region'].isin(sel_regions)) &
    (df_full['Category Name'].isin(sel_categories)) &
    (df_full['Order Item Discount Rate'].between(discount_range[0], discount_range[1]))
].copy()

if df.empty:
    st.warning("No data matches the selected filters. Please broaden your filter selection.")
    st.stop()

# ============================================================
# HEADER
# ============================================================
st.title("📦 Customer, Product & Profitability Performance Dashboard")
st.caption("Moving supply chain analytics from operational efficiency to commercial intelligence")

# ============================================================
# TOP-LEVEL KPI ROW
# ============================================================
total_revenue = df['Sales'].sum()
total_profit = df['Order Profit'].sum()
overall_margin = (total_profit / total_revenue * 100) if total_revenue else 0
total_orders = len(df)
total_customers = df['Customer Id'].nunique()
loss_pct = df['Is Loss Making'].mean() * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"${total_revenue/1e6:,.2f}M")
c2.metric("Total Profit", f"${total_profit/1e6:,.2f}M")
c3.metric("Profit Margin", f"{overall_margin:.2f}%")
c4.metric("Order Line Items", f"{total_orders:,}")
c5.metric("Loss-Making Orders", f"{loss_pct:.1f}%")

st.divider()

# ============================================================
# TABS — DASHBOARD MODULES
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Revenue & Profit Overview",
    "👥 Customer Value Dashboard",
    "📦 Product & Category Performance",
    "🏷️ Discount Impact Analyzer",
])

# ------------------------------------------------------------
# TAB 1: REVENUE & PROFIT OVERVIEW
# ------------------------------------------------------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Profit Waterfall: Winners vs Losses")
        winners = df.loc[df['Order Profit'] > 0, 'Order Profit'].sum()
        losses = df.loc[df['Order Profit'] < 0, 'Order Profit'].sum()
        net = df['Order Profit'].sum()
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Profit from Winners", "Loss Drag", "Net Profit"],
            y=[winners, losses, net],
            connector={"line": {"color": "rgba(100,100,100,0.4)"}},
            increasing={"marker": {"color": TEAL}},
            decreasing={"marker": {"color": CORAL}},
            totals={"marker": {"color": PRIMARY}},
            text=[f"${winners:,.0f}", f"${losses:,.0f}", f"${net:,.0f}"],
            textposition="outside",
        ))
        fig.update_layout(height=420, showlegend=False, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Revenue vs Profit by Market")
        mkt = df.groupby('Market', as_index=False).agg(revenue=('Sales','sum'), profit=('Order Profit','sum'))
        mkt['margin_pct'] = mkt['profit']/mkt['revenue']*100
        mkt = mkt.sort_values('revenue', ascending=False)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=mkt['Market'], y=mkt['revenue'], name='Revenue', marker_color=PRIMARY), secondary_y=False)
        fig.add_trace(go.Scatter(x=mkt['Market'], y=mkt['margin_pct'], name='Margin %', mode='lines+markers',
                                   line=dict(color=CORAL, width=3), marker=dict(size=9)), secondary_y=True)
        fig.update_yaxes(title_text="Revenue ($)", secondary_y=False)
        fig.update_yaxes(title_text="Margin (%)", secondary_y=True)
        fig.update_layout(height=420, margin=dict(t=10), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Order Status Breakdown")
        stat = df.groupby('Order Status', as_index=False).agg(revenue=('Sales','sum'), profit=('Order Profit','sum'), orders=('Sales','count'))
        stat = stat.sort_values('revenue', ascending=False)
        fig = px.bar(stat, x='Order Status', y=['revenue','profit'], barmode='group',
                     color_discrete_sequence=[PRIMARY, TEAL])
        fig.update_layout(height=400, margin=dict(t=10), yaxis_title="USD ($)", legend_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Delivery Status vs Profit Margin")
        dlv = df.groupby('Delivery Status', as_index=False).agg(revenue=('Sales','sum'), profit=('Order Profit','sum'))
        dlv['margin_pct'] = dlv['profit']/dlv['revenue']*100
        fig = px.bar(dlv.sort_values('margin_pct'), x='Delivery Status', y='margin_pct',
                     color='margin_pct', color_continuous_scale='RdYlGn', text_auto='.2f')
        fig.update_layout(height=400, margin=dict(t=10), yaxis_title="Profit Margin (%)", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 2: CUSTOMER VALUE DASHBOARD
# ------------------------------------------------------------
with tab2:
    cust = df.groupby(['Customer Id'], as_index=False).agg(
        revenue=('Sales','sum'), profit=('Order Profit','sum'), orders=('Sales','count'),
        segment=('Customer Segment','first'), name_f=('Customer Fname' if 'Customer Fname' in df.columns else 'Customer Id','first')
    )
    if 'Customer Name' in df.columns:
        cust_name = df.groupby('Customer Id', as_index=False)['Customer Name'].first()
        cust = cust.merge(cust_name, on='Customer Id')
    cust['margin_pct'] = cust['profit']/cust['revenue']*100
    cust_sorted = cust.sort_values('profit', ascending=False).reset_index(drop=True)
    cust_sorted['rank_pct'] = (cust_sorted.index+1)/len(cust_sorted)*100

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 15 Customers by Profit")
        top15 = cust_sorted.head(15)
        label_col = 'Customer Name' if 'Customer Name' in top15.columns else 'Customer Id'
        fig = px.bar(top15.sort_values('profit'), x='profit', y=label_col, orientation='h',
                     color='profit', color_continuous_scale='Tealgrn', text_auto='.0f')
        fig.update_layout(height=480, margin=dict(t=10), coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("⚠️ Bottom 15 Customers by Profit")
        bottom15 = cust_sorted.tail(15)
        fig = px.bar(bottom15.sort_values('profit'), x='profit', y=label_col, orientation='h',
                     color='profit', color_continuous_scale='Reds_r', text_auto='.0f')
        fig.update_layout(height=480, margin=dict(t=10), coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Customer Value Tiers")
    def tier(pct):
        if pct <= 10: return 'Top 10% (Champions)'
        elif pct <= 30: return 'Next 20% (High-Value)'
        elif pct <= 70: return 'Middle 40% (Core)'
        elif pct <= 90: return 'Next 20% (Low-Value)'
        else: return 'Bottom 10% (At-Risk/Loss)'
    cust_sorted['Value Tier'] = cust_sorted['rank_pct'].apply(tier)
    tier_order = ['Top 10% (Champions)','Next 20% (High-Value)','Middle 40% (Core)','Next 20% (Low-Value)','Bottom 10% (At-Risk/Loss)']
    tier_sum = cust_sorted.groupby('Value Tier').agg(customers=('Customer Id','count'), total_profit=('profit','sum')).reindex(tier_order)
    tier_sum['pct_of_profit'] = tier_sum['total_profit']/cust_sorted['profit'].sum()*100

    col3, col4 = st.columns([3,2])
    with col3:
        fig = px.bar(tier_sum.reset_index(), x='Value Tier', y='pct_of_profit', color='pct_of_profit',
                     color_continuous_scale='RdYlGn', text_auto='.1f', category_orders={'Value Tier': tier_order})
        fig.update_layout(height=380, margin=dict(t=10), coloraxis_showscale=False, yaxis_title="% of Total Profit")
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        st.dataframe(tier_sum.style.format({'total_profit':'${:,.0f}','pct_of_profit':'{:.1f}%'}), use_container_width=True)

    st.subheader("Customer Segment Contribution")
    seg = df.groupby('Customer Segment', as_index=False).agg(
        customers=('Customer Id','nunique'), revenue=('Sales','sum'), profit=('Order Profit','sum'))
    seg['margin_pct'] = seg['profit']/seg['revenue']*100
    seg['profit_per_customer'] = seg['profit']/seg['customers']
    st.dataframe(seg.style.format({'revenue':'${:,.0f}','profit':'${:,.0f}','margin_pct':'{:.2f}%','profit_per_customer':'${:,.2f}'}),
                 use_container_width=True)

# ------------------------------------------------------------
# TAB 3: PRODUCT & CATEGORY PERFORMANCE
# ------------------------------------------------------------
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 15 Products by Revenue")
        prod = df.groupby('Product Name', as_index=False).agg(revenue=('Sales','sum'), profit=('Order Profit','sum'), orders=('Sales','count'))
        prod['margin_pct'] = prod['profit']/prod['revenue']*100
        top_prod = prod.sort_values('revenue', ascending=False).head(15)
        fig = px.bar(top_prod.sort_values('revenue'), x='revenue', y='Product Name', orientation='h',
                     color='margin_pct', color_continuous_scale='RdYlGn', text_auto='.2s')
        fig.update_layout(height=520, margin=dict(t=10), yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Category Profitability Heatmap (by Discount Band)")
        top_cats = df.groupby('Category Name')['Sales'].sum().sort_values(ascending=False).head(12).index
        sub = df[df['Category Name'].isin(top_cats)]
        heat = sub.groupby(['Category Name','Discount Band'], observed=True).apply(
            lambda g: g['Order Profit'].sum()/g['Sales'].sum()*100 if g['Sales'].sum() else np.nan
        ).unstack()
        heat = heat.reindex(top_cats)
        fig = px.imshow(heat, text_auto='.1f', color_continuous_scale='RdYlGn', aspect='auto',
                         labels=dict(color="Margin %"))
        fig.update_layout(height=520, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Department-Level Profitability")
    dept = df.groupby('Department Name', as_index=False).agg(revenue=('Sales','sum'), profit=('Order Profit','sum'), orders=('Sales','count'))
    dept['margin_pct'] = dept['profit']/dept['revenue']*100
    dept = dept.sort_values('revenue', ascending=False)
    fig = px.scatter(dept, x='revenue', y='margin_pct', size='orders', color='Department Name',
                      hover_name='Department Name', size_max=50)
    fig.update_layout(height=420, margin=dict(t=10), xaxis_title="Revenue ($)", yaxis_title="Profit Margin (%)")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Full Product Profitability Table"):
        st.dataframe(prod.sort_values('revenue', ascending=False).style.format(
            {'revenue':'${:,.2f}','profit':'${:,.2f}','margin_pct':'{:.2f}%'}), use_container_width=True)

# ------------------------------------------------------------
# TAB 4: DISCOUNT IMPACT ANALYZER
# ------------------------------------------------------------
with tab4:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Profit Margin by Discount Band")
        band = df.groupby('Discount Band', observed=True).agg(revenue=('Sales','sum'), profit=('Order Profit','sum'), orders=('Sales','count')).reset_index()
        band['margin_pct'] = band['profit']/band['revenue']*100
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=band['Discount Band'], y=band['margin_pct'], name='Margin %', marker_color=TEAL), secondary_y=False)
        fig.add_trace(go.Scatter(x=band['Discount Band'], y=band['orders'], name='Order Volume', mode='lines+markers',
                                   line=dict(color=CORAL, width=3)), secondary_y=True)
        fig.update_yaxes(title_text="Margin (%)", secondary_y=False)
        fig.update_yaxes(title_text="Order Volume", secondary_y=True)
        fig.update_layout(height=420, margin=dict(t=10), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Discount Rate vs Profit Ratio (scatter)")
        sample = df.sample(min(5000, len(df)), random_state=42)
        fig = px.scatter(sample, x='Order Item Discount Rate', y='Order Item Profit Ratio',
                          color='Order Item Profit Ratio', color_continuous_scale='RdYlGn', opacity=0.5)
        fig.update_layout(height=420, margin=dict(t=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🎛️ What-If Discount Scenario Simulator")
    st.caption("Estimate the margin impact of applying a uniform discount rate shift across currently filtered orders.")

    colA, colB = st.columns([1,2])
    with colA:
        shift = st.slider("Adjust discount rate by (percentage points)", -10.0, 10.0, 0.0, step=0.5)
        st.metric("Simulated Avg Discount Rate", f"{(df['Order Item Discount Rate'].mean()*100 + shift):.2f}%")

    with colB:
        # Simple linear approximation using observed band-level margin trend (regression on band midpoints)
        band_mid = {'0%':0,'0-5%':2.5,'5-10%':7.5,'10-15%':12.5,'15-20%':17.5,'20%+':22.5}
        band2 = band.copy()
        band2['mid'] = band2['Discount Band'].map(band_mid)
        coeffs = np.polyfit(band2['mid'], band2['margin_pct'], 1)
        current_avg_disc = df['Order Item Discount Rate'].mean()*100
        new_disc = current_avg_disc + shift
        current_margin_est = np.polyval(coeffs, current_avg_disc)
        new_margin_est = np.polyval(coeffs, new_disc)
        delta_margin = new_margin_est - current_margin_est
        new_profit_est = total_revenue * (new_margin_est/100)

        fig = go.Figure(go.Indicator(
            mode="number+delta",
            value=new_margin_est,
            delta={'reference': current_margin_est, 'valueformat':'.2f', 'suffix':' pts'},
            number={'suffix': '%', 'valueformat':'.2f'},
            title={"text": "Estimated Profit Margin"}
        ))
        fig.update_layout(height=200, margin=dict(t=40,b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"At an average discount rate of **{new_disc:.2f}%**, estimated profit margin is **{new_margin_est:.2f}%**, "
                f"implying total profit of approximately **${new_profit_est:,.0f}** on current filtered revenue "
                f"(linear trend approximation based on observed discount-band margins; for directional guidance only).")

    st.divider()
    st.subheader("Categories With Highest Average Discount Rate")
    cat_disc = df.groupby('Category Name', as_index=False).agg(
        orders=('Sales','count'), avg_discount=('Order Item Discount Rate','mean'),
        revenue=('Sales','sum'), profit=('Order Profit','sum'))
    cat_disc = cat_disc[cat_disc['orders']>=50]
    cat_disc['margin_pct'] = cat_disc['profit']/cat_disc['revenue']*100
    cat_disc = cat_disc.sort_values('avg_discount', ascending=False).head(15)
    fig = px.bar(cat_disc.sort_values('avg_discount'), x='avg_discount', y='Category Name', orientation='h',
                 color='margin_pct', color_continuous_scale='RdYlGn', text_auto='.1%')
    fig.update_layout(height=480, margin=dict(t=10), xaxis_title="Avg Discount Rate", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Data source: APL Logistics order-line dataset (180,519 order items, 20,652 customers) | "
           "Generated for Unified Mentor Project ID 7518")
