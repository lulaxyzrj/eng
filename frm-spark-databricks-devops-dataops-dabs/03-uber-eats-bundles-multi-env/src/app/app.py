"""
UberEats Operations Dashboard
Real-time monitoring of order funnel, revenue, and payment health.
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from databricks.sdk.config import Config
from databricks import sql
from datetime import datetime
import config

# =============================================================================
# CONFIGURATION
# =============================================================================
REFRESH_INTERVAL_SECONDS = 30  # Time to refresh: 10, 30, 60, etc.

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="UberEats Operations Dashboard",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# STYLING
# =============================================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .kpi-card {
        background: linear-gradient(145deg, #1e3a5f 0%, #2d5a87 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4ade80;
        margin: 8px 0;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-delta-positive { color: #4ade80; }
    .kpi-delta-negative { color: #f87171; }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e2e8f0;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #3b82f6;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(30, 58, 95, 0.5);
        border-radius: 12px;
        padding: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #1a1a2e 100%);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================
@st.cache_resource
def get_connection():
    """Create cached database connection."""
    cfg = Config()
    warehouse_id = config.get_warehouse_id()
    
    if not warehouse_id:
        st.error("❌ DATABRICKS_WAREHOUSE_ID not configured")
        st.stop()
    
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
    )


@st.cache_data(ttl=REFRESH_INTERVAL_SECONDS)
def run_query(query: str) -> pd.DataFrame:
    """Execute query with cache based on REFRESH_INTERVAL_SECONDS."""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()


# =============================================================================
# KPI COMPONENT
# =============================================================================
def render_kpi(label: str, value: str, delta: str = None, delta_positive: bool = True):
    """Render a KPI card."""
    delta_html = ""
    if delta:
        delta_class = "kpi-delta-positive" if delta_positive else "kpi-delta-negative"
        arrow = "↑" if delta_positive else "↓"
        delta_html = f'<div class="{delta_class}">{arrow} {delta}</div>'
    
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar():
    """Render sidebar with connection info and filters."""
    with st.sidebar:
        st.image("assets/uber-eats.png", width=200)
        st.title("UberEats Ops")
        
        st.markdown("---")
        
        st.markdown("### 🔗 Connection")
        target = config.get_target()
        catalog = config.get_catalog()
        warehouse = config.get_warehouse_id()
        
        status_color = "#4ade80" if warehouse else "#f87171"
        st.markdown(f"""
            <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; font-size: 0.85rem;">
                <div><strong>Environment:</strong> <span style="color: #60a5fa;">{target.upper()}</span></div>
                <div><strong>Catalog:</strong> {catalog}</div>
                <div><strong>Warehouse:</strong> <span style="color: {status_color};">{'✓ Connected' if warehouse else '✗ Not configured'}</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### 📅 Date Range")
        date_range = st.selectbox(
            "Select period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=0,
            label_visibility="collapsed"
        )
        
        days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": 9999}
        days = days_map[date_range]
        
        st.markdown("---")
        
        st.markdown("### 🔄 Data Refresh")
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.caption(f"Auto-refresh: {REFRESH_INTERVAL_SECONDS} seconds")
        
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        return days


# =============================================================================
# TAB: OVERVIEW (KPIs from multiple gold tables)
# =============================================================================
def render_overview(days: int):
    """Render overview tab with key KPIs."""
    st.markdown('<div class="section-header">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    catalog = config.get_catalog()
    gold = config.get_schema("gold")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Orders (from order_completion_daily)
    with col1:
        query = f"""
            SELECT SUM(total_orders) as total_orders
            FROM {catalog}.{gold}.order_completion_daily
            WHERE order_date >= DATE_SUB(CURRENT_DATE(), {days})
        """
        try:
            df = run_query(query)
            val = df['total_orders'].iloc[0] if not df.empty and df['total_orders'].iloc[0] else 0
            value = f"{int(val):,}"
        except:
            value = "N/A"
        render_kpi("Total Orders", value)
    
    # Total Revenue (from order_revenue_by_status)
    with col2:
        query = f"""
            SELECT SUM(total_revenue) as revenue
            FROM {catalog}.{gold}.order_revenue_by_status
        """
        try:
            df = run_query(query)
            val = df['revenue'].iloc[0] if not df.empty and df['revenue'].iloc[0] else 0
            value = f"R${val/1000:.1f}K" if val >= 1000 else f"R${val:,.0f}"
        except:
            value = "N/A"
        render_kpi("Total Revenue", value)
    
    # Completion Rate (from order_completion_daily)
    with col3:
        query = f"""
            SELECT AVG(completion_rate_pct) as rate
            FROM {catalog}.{gold}.order_completion_daily
            WHERE order_date >= DATE_SUB(CURRENT_DATE(), {days})
        """
        try:
            df = run_query(query)
            val = df['rate'].iloc[0] if not df.empty and df['rate'].iloc[0] else 0
            value = f"{val:.1f}%"
        except:
            value = "N/A"
        render_kpi("Completion Rate", value)
    
    # Payment Success (from payment_health)
    with col4:
        query = f"""
            SELECT 
                SUM(succeeded) * 100.0 / NULLIF(SUM(total_payments), 0) as success_rate
            FROM {catalog}.{gold}.payment_health
        """
        try:
            df = run_query(query)
            val = df['success_rate'].iloc[0] if not df.empty and df['success_rate'].iloc[0] else 0
            value = f"{val:.1f}%"
        except:
            value = "N/A"
        render_kpi("Payment Success", value)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    # Order Completion Trend
    with col1:
        st.markdown('<div class="section-header">📈 Daily Completion Trend</div>', unsafe_allow_html=True)
        query = f"""
            SELECT order_date, total_orders, completed_orders, delivered_orders, completion_rate_pct
            FROM {catalog}.{gold}.order_completion_daily
            WHERE order_date >= DATE_SUB(CURRENT_DATE(), {days})
            ORDER BY order_date
        """
        try:
            df = run_query(query)
            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['order_date'], y=df['total_orders'], 
                    name='Total', mode='lines+markers', line=dict(color='#3b82f6', width=2)))
                fig.add_trace(go.Scatter(x=df['order_date'], y=df['delivered_orders'], 
                    name='Delivered', mode='lines+markers', line=dict(color='#4ade80', width=2)))
                fig.update_layout(
                    template='plotly_dark',
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="", yaxis_title="Orders", height=300,
                    legend=dict(orientation='h', y=-0.15))
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No order data available")
        except Exception as e:
            st.warning(f"Could not load order trend: {e}")
    
    # Payment Daily Trend
    with col2:
        st.markdown('<div class="section-header">💰 Daily Payment Volume</div>', unsafe_allow_html=True)
        query = f"""
            SELECT payment_date_key, total_payments, succeeded, total_amount, success_rate_pct
            FROM {catalog}.{gold}.payment_daily
            WHERE payment_date_key >= DATE_SUB(CURRENT_DATE(), {days})
            ORDER BY payment_date_key
        """
        try:
            df = run_query(query)
            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df['payment_date_key'], y=df['total_amount'], 
                    name='Volume (R$)', marker_color='#4ade80'))
                fig.update_layout(
                    template='plotly_dark',
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="", yaxis_title="Volume (R$)", height=300)
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No payment data available")
        except Exception as e:
            st.warning(f"Could not load payment trend: {e}")


# =============================================================================
# TAB: ORDER FUNNEL
# =============================================================================
def render_order_funnel(days: int):
    """Render order funnel analysis."""
    catalog = config.get_catalog()
    gold = config.get_schema("gold")
    
    # Live Funnel
    st.markdown('<div class="section-header">🔄 Live Order Funnel</div>', unsafe_allow_html=True)
    
    query = f"""
        SELECT status_name, status_sequence, order_count
        FROM {catalog}.{gold}.order_funnel_live
        ORDER BY status_sequence
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = go.Figure(go.Funnel(
                    y=df['status_name'],
                    x=df['order_count'],
                    textinfo="value+percent initial",
                    marker=dict(color=px.colors.sequential.Blues_r[:len(df)]),
                    connector=dict(line=dict(color="#1e3a5f", width=2))
                ))
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=40, b=0), height=450
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📊 Current Distribution")
                total = df['order_count'].sum()
                for _, row in df.iterrows():
                    pct = (row['order_count'] / total * 100) if total > 0 else 0
                    st.markdown(f"""
                        <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">{row['status_name']}</div>
                            <div style="color: #4ade80; font-size: 1.4rem; font-weight: 700;">{int(row['order_count']):,}</div>
                            <div style="color: #60a5fa; font-size: 0.85rem;">{pct:.1f}%</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No funnel data available")
    except Exception as e:
        st.warning(f"Could not load funnel data: {e}")
    
    # Transition Times
    st.markdown('<div class="section-header">⏱️ Average Transition Times</div>', unsafe_allow_html=True)
    
    query = f"""
        SELECT transition_name, avg_minutes, transition_count
        FROM {catalog}.{gold}.order_transitions
        ORDER BY avg_minutes DESC
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            fig = px.bar(df, x='avg_minutes', y='transition_name', orientation='h',
                template='plotly_dark', color='avg_minutes',
                color_continuous_scale='Reds',
                labels={'avg_minutes': 'Avg Minutes', 'transition_name': ''})
            fig.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False, height=350,
                yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transition data available")
    except Exception as e:
        st.warning(f"Could not load transition data: {e}")
    
    # Hourly Heatmap
    st.markdown('<div class="section-header">🕐 Orders by Hour</div>', unsafe_allow_html=True)
    
    query = f"""
        SELECT status_date_key, status_hour, SUM(unique_orders) as orders
        FROM {catalog}.{gold}.order_funnel_hourly
        WHERE status_date_key >= DATE_SUB(CURRENT_DATE(), {days})
        GROUP BY status_date_key, status_hour
        ORDER BY status_date_key, status_hour
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            # Pivot for heatmap - days as rows, hours as columns
            df['day_of_week'] = pd.to_datetime(df['status_date_key']).dt.dayofweek
            pivot = df.groupby(['day_of_week', 'status_hour'])['orders'].sum().unstack(fill_value=0)
            
            days_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
            fig = px.imshow(pivot.values,
                labels=dict(x="Hour of Day", y="Day of Week", color="Orders"),
                x=[f"{h:02d}:00" for h in pivot.columns],
                y=[days_labels[i] for i in pivot.index],
                color_continuous_scale='Blues', template='plotly_dark')
            fig.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hourly data available")
    except Exception as e:
        st.warning(f"Could not load hourly data: {e}")


# =============================================================================
# TAB: REVENUE
# =============================================================================
def render_revenue(days: int):
    """Render revenue analytics."""
    catalog = config.get_catalog()
    gold = config.get_schema("gold")
    
    st.markdown('<div class="section-header">💵 Revenue by Order Status</div>', unsafe_allow_html=True)
    
    # Revenue by Status (Funnel with values)
    query = f"""
        SELECT current_status, current_status_sequence, order_count, total_revenue, avg_ticket
        FROM {catalog}.{gold}.order_revenue_by_status
        ORDER BY current_status_sequence
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = go.Figure(go.Funnel(
                    y=df['current_status'],
                    x=df['total_revenue'],
                    textinfo="value",
                    texttemplate="R$%{value:,.0f}",
                    marker=dict(color=px.colors.sequential.Greens_r[:len(df)]),
                    connector=dict(line=dict(color="#1e3a5f", width=2))
                ))
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=40, b=0), height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 💰 Revenue at Risk")
                # Revenue not yet delivered
                delivered_statuses = ['Delivered', 'Completed']
                at_risk = df[~df['current_status'].isin(delivered_statuses)]['total_revenue'].sum()
                delivered = df[df['current_status'].isin(delivered_statuses)]['total_revenue'].sum()
                
                st.markdown(f"""
                    <div style="background: rgba(0,0,0,0.2); padding: 20px; border-radius: 8px; margin-bottom: 12px;">
                        <div style="color: #94a3b8; font-size: 0.85rem;">Delivered Revenue</div>
                        <div style="color: #4ade80; font-size: 2rem; font-weight: 700;">R${delivered:,.0f}</div>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); padding: 20px; border-radius: 8px;">
                        <div style="color: #94a3b8; font-size: 0.85rem;">In Progress (At Risk)</div>
                        <div style="color: #f59e0b; font-size: 2rem; font-weight: 700;">R${at_risk:,.0f}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Avg Ticket
                avg_ticket = df['avg_ticket'].mean()
                st.markdown(f"""
                    <div style="background: rgba(0,0,0,0.2); padding: 20px; border-radius: 8px; margin-top: 12px;">
                        <div style="color: #94a3b8; font-size: 0.85rem;">Avg Ticket</div>
                        <div style="color: #60a5fa; font-size: 2rem; font-weight: 700;">R${avg_ticket:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No revenue data available")
    except Exception as e:
        st.warning(f"Could not load revenue data: {e}")
    
    # Daily Completion Metrics
    st.markdown('<div class="section-header">📊 Daily Completion Metrics</div>', unsafe_allow_html=True)
    
    query = f"""
        SELECT order_date, total_orders, completed_orders, delivered_orders, 
               completion_rate_pct, avg_completion_minutes
        FROM {catalog}.{gold}.order_completion_daily
        WHERE order_date >= DATE_SUB(CURRENT_DATE(), {days})
        ORDER BY order_date
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            fig = make_subplots(rows=1, cols=2,
                subplot_titles=("Orders by Day", "Completion Rate %"))
            
            fig.add_trace(go.Bar(x=df['order_date'], y=df['total_orders'], 
                name='Total', marker_color='#3b82f6'), row=1, col=1)
            fig.add_trace(go.Bar(x=df['order_date'], y=df['delivered_orders'], 
                name='Delivered', marker_color='#4ade80'), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df['order_date'], y=df['completion_rate_pct'], 
                name='Completion %', mode='lines+markers', marker_color='#f59e0b', 
                fill='tozeroy'), row=1, col=2)
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=350, showlegend=True, legend=dict(orientation='h', y=-0.15),
                barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completion data available")
    except Exception as e:
        st.warning(f"Could not load completion data: {e}")


# =============================================================================
# TAB: PAYMENTS
# =============================================================================
def render_payments(days: int):
    """Render payment health analytics."""
    catalog = config.get_catalog()
    gold = config.get_schema("gold")
    
    # Payment Health by Method
    st.markdown('<div class="section-header">💳 Payment Health by Method</div>', unsafe_allow_html=True)
    
    query = f"""
        SELECT method, total_payments, succeeded, failed, pending, refunded,
               total_amount, success_rate_pct, failure_rate_pct
        FROM {catalog}.{gold}.payment_health
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            total_payments = df['total_payments'].sum()
            total_succeeded = df['succeeded'].sum()
            total_failed = df['failed'].sum()
            total_amount = df['total_amount'].sum()
            
            with col1:
                render_kpi("Total Payments", f"{int(total_payments):,}")
            with col2:
                render_kpi("Succeeded", f"{int(total_succeeded):,}", 
                          f"{total_succeeded/total_payments*100:.1f}%", True)
            with col3:
                render_kpi("Failed", f"{int(total_failed):,}", 
                          f"{total_failed/total_payments*100:.1f}%", False)
            with col4:
                render_kpi("Volume", f"R${total_amount/1000:.1f}K")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Stacked Bar - Payment Status by Method
            with col1:
                st.markdown("### 📊 Payment Status by Method")
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Succeeded', x=df['method'], y=df['succeeded'], marker_color='#4ade80'))
                fig.add_trace(go.Bar(name='Failed', x=df['method'], y=df['failed'], marker_color='#f87171'))
                fig.add_trace(go.Bar(name='Pending', x=df['method'], y=df['pending'], marker_color='#f59e0b'))
                fig.add_trace(go.Bar(name='Refunded', x=df['method'], y=df['refunded'], marker_color='#94a3b8'))
                fig.update_layout(
                    template='plotly_dark', barmode='stack',
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=350, legend=dict(orientation='h', y=-0.15))
                st.plotly_chart(fig, use_container_width=True)
            
            # Success Rate by Method
            with col2:
                st.markdown("### 📈 Success Rate by Method")
                fig = px.bar(df.sort_values('success_rate_pct'),
                    x='success_rate_pct', y='method', orientation='h',
                    template='plotly_dark', color='success_rate_pct',
                    color_continuous_scale='RdYlGn', range_color=[80, 100])
                fig.update_layout(
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    coloraxis_showscale=False, height=350,
                    xaxis_title="Success Rate %", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No payment health data available")
    except Exception as e:
        st.warning(f"Could not load payment health: {e}")
    
    # Payment Failures
    st.markdown('<div class="section-header">❌ Payment Failures Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        query = f"""
            SELECT failure_reason, failure_count, failed_amount, failure_pct
            FROM {catalog}.{gold}.payment_failures
            ORDER BY failure_count DESC
        """
        try:
            df = run_query(query)
            if not df.empty:
                fig = px.pie(df, values='failure_count', names='failure_reason',
                    template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Set3,
                    hole=0.4)
                fig.update_layout(
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No failure data available")
        except Exception as e:
            st.warning(f"Could not load failure data: {e}")
    
    # Payment by Provider
    with col2:
        query = f"""
            SELECT provider, total_payments, total_amount, success_rate_pct,
                   avg_platform_fee, avg_provider_fee
            FROM {catalog}.{gold}.payment_by_provider
            ORDER BY total_amount DESC
        """
        try:
            df = run_query(query)
            if not df.empty:
                fig = px.bar(df, x='provider', y='total_amount',
                    template='plotly_dark', color='success_rate_pct',
                    color_continuous_scale='RdYlGn', range_color=[90, 100],
                    labels={'total_amount': 'Volume (R$)', 'provider': 'Provider'})
                fig.update_layout(
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=300, coloraxis_colorbar_title="Success %")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No provider data available")
        except Exception as e:
            st.warning(f"Could not load provider data: {e}")
    
    # Payment Daily Trend
    st.markdown('<div class="section-header">📅 Daily Payment Trend</div>', unsafe_allow_html=True)
    
    query = f"""
        SELECT payment_date_key, total_payments, succeeded, failed, 
               total_amount, success_rate_pct
        FROM {catalog}.{gold}.payment_daily
        WHERE payment_date_key >= DATE_SUB(CURRENT_DATE(), {days})
        ORDER BY payment_date_key
    """
    
    try:
        df = run_query(query)
        if not df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(go.Bar(x=df['payment_date_key'], y=df['total_amount'],
                name='Volume (R$)', marker_color='#3b82f6'), secondary_y=False)
            fig.add_trace(go.Scatter(x=df['payment_date_key'], y=df['success_rate_pct'],
                name='Success Rate %', mode='lines+markers', marker_color='#4ade80',
                line=dict(width=3)), secondary_y=True)
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=300, legend=dict(orientation='h', y=-0.2))
            fig.update_yaxes(title_text="Volume (R$)", secondary_y=False)
            fig.update_yaxes(title_text="Success Rate %", secondary_y=True, range=[80, 100])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No daily payment data available")
    except Exception as e:
        st.warning(f"Could not load daily payment data: {e}")


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    """Main application entry point."""
    st_autorefresh(interval=REFRESH_INTERVAL_SECONDS * 1000, key="datarefresh")
    
    days = render_sidebar()
    
    st.markdown("""
        <h1 style="text-align: center; color: #e2e8f0; margin-bottom: 8px;">
            🍔 UberEats Operations Dashboard
        </h1>
        <p style="text-align: center; color: #94a3b8; margin-bottom: 32px;">
            Real-time monitoring of orders, revenue, and payment health
        </p>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔄 Order Funnel", "💰 Revenue", "💳 Payments"])
    
    with tab1:
        render_overview(days)
    with tab2:
        render_order_funnel(days)
    with tab3:
        render_revenue(days)
    with tab4:
        render_payments(days)


if __name__ == "__main__":
    main()