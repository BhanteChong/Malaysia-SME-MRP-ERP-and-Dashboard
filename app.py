import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import init_database, get_products, get_sales, add_sale, load_demo_data

# Page config
st.set_page_config(
    page_title="Malaysia SME System",
    page_icon="🇲🇾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-friendly CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 18px;
        margin: 5px 0;
        border-radius: 10px;
    }
    .product-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px;
        text-align: center;
    }
    .cart-item {
        background: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
    }
    .total-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-size: 24px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'industry' not in st.session_state:
    st.session_state.industry = 'retail'

conn = init_database()

# Header with industry selector
col1, col2 = st.columns([2, 1])
with col1:
    st.title("🇲🇾 Malaysia SME System")
with col2:
    industry = st.selectbox(
        "🔄 Industry",
        ['retail', 'manufacturing', 'consulting'],
        index=['retail', 'manufacturing', 'consulting'].index(st.session_state.industry),
        format_func=lambda x: {'retail': '🛒 Retail/F&B', 'manufacturing': '�icing: MFG', 'consulting': '💼 Consulting'}[x]
    )
    if industry != st.session_state.industry:
        st.session_state.industry = industry
        load_demo_data(conn, industry)
        st.session_state.cart = []
        st.rerun()

# Navigation
tab1, tab2, tab3 = st.tabs(["💰 POS", "📊 Dashboard", "📦 Inventory"])

# === POS TAB ===
with tab1:
    products = get_products(conn)
    
    col_products, col_cart = st.columns([2, 1])
    
    with col_products:
        st.subheader("📱 Tap to Add")
        
        # Product grid - 2 columns for mobile
        cols = st.columns(2)
        for idx, row in products.iterrows():
            with cols[idx % 2]:
                if st.button(
                    f"{row['name']}\nRM {row['price']:.2f}",
                    key=f"prod_{row['id']}",
                    use_container_width=True
                ):
                    st.session_state.cart.append({
                        'id': row['id'],
                        'name': row['name'],
                        'price': row['price'],
                        'qty': 1
                    })
                    st.rerun()
    
    with col_cart:
        st.subheader("🛒 Cart")
        
        if st.session_state.cart:
            total = 0
            for i, item in enumerate(st.session_state.cart):
                col_item, col_del = st.columns([3, 1])
                with col_item:
                    st.write(f"**{item['name']}** - RM {item['price']:.2f}")
                with col_del:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                total += item['price']
            
            st.markdown("---")
            st.markdown(f"""
                <div class="total-box">
                    <strong>TOTAL: RM {total:.2f}</strong>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            if st.button("✅ CONFIRM SALE", type="primary", use_container_width=True):
                for item in st.session_state.cart:
                    add_sale(conn, item['id'], item['qty'], item['price'])
                st.session_state.cart = []
                st.success("✅ Sale recorded!")
                st.balloons()
                st.rerun()
            
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info("👆 Tap products to add")

# === DASHBOARD TAB ===
with tab2:
    sales = get_sales(conn)
    products = get_products(conn)
    
    if len(sales) > 0:
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Sales", f"RM {sales['total'].sum():,.2f}")
        with col2:
            st.metric("📦 Transactions", len(sales))
        with col3:
            st.metric("📈 Avg Sale", f"RM {sales['total'].mean():,.2f}")
        
        st.markdown("---")
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            daily = sales.groupby('sale_date')['total'].sum().reset_index()
            fig1 = px.line(daily, x='sale_date', y='total', 
                          title='📈 Daily Sales Trend',
                          labels={'total': 'RM', 'sale_date': 'Date'})
            fig1.update_layout(height=300)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_chart2:
            by_cat = sales.groupby('category')['total'].sum().reset_index()
            fig2 = px.pie(by_cat, values='total', names='category',
                         title='🥧 Sales by Category')
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Top products
        st.subheader("🏆 Top Products")
        top = sales.groupby('name')['total'].sum().sort_values(ascending=False).head(5)
        fig3 = px.bar(x=top.values, y=top.index, orientation='h',
                     labels={'x': 'RM', 'y': 'Product'})
        fig3.update_layout(height=250)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No sales data yet. Make some sales in POS tab!")

# === INVENTORY TAB ===
with tab3:
    products = get_products(conn)
    
    st.subheader("📦 Stock Levels")
    
    # Low stock warning
    low_stock = products[products['stock'] < 50]
    if len(low_stock) > 0:
        st.warning(f"⚠️ {len(low_stock)} items low on stock!")
    
    # Stock chart
    fig = px.bar(products, x='name', y='stock', color='category',
                 title='Current Inventory')
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.dataframe(
        products[['name', 'price', 'stock', 'category']],
        use_container_width=True,
        hide_index=True
    )

# Footer
st.markdown("---")
st.markdown(
    "<center>🇲🇾 Built for Malaysian SMEs | Tap anywhere to start!</center>",
    unsafe_allow_html=True
)
