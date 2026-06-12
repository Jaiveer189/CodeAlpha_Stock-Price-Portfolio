import streamlit as st
from groq import Groq
import os

# -------------------------------------------------------
# PAGE CONFIG — must be the first Streamlit command
# -------------------------------------------------------
st.set_page_config(
    page_title="Stock Portfolio Tracker",
    page_icon="📈",
    layout="centered"
)

# -------------------------------------------------------
# FIX 1: Added color: #1a1a1a to .analysis-box so text
# is always dark regardless of Streamlit's theme
# FIX 2: Removed the HTML div approach for analysis —
# using st.markdown() directly so Groq's markdown
# (bold, headers, bullet points) renders properly
# -------------------------------------------------------
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .metric-container { background: #f8f9fa; border-radius: 10px; padding: 1rem; }
    .stButton > button { width: 100%; border-radius: 8px; height: 42px; font-weight: 500; }

    /* Section box for analysis — explicit dark text always */
    .analysis-wrapper {
        background: #f0f7ff;
        border-left: 4px solid #2563eb;
        border-radius: 0 10px 10px 0;
        padding: 1.25rem 1.5rem;
        margin-top: 1rem;
        color: #1a1a1a !important;   /* FIX: force dark text */
    }
    .analysis-wrapper p,
    .analysis-wrapper li,
    .analysis-wrapper h1,
    .analysis-wrapper h2,
    .analysis-wrapper h3 {
        color: #1a1a1a !important;   /* FIX: covers all child elements too */
    }
    .analysis-label {
        font-size: 12px;
        font-weight: 700;
        color: #2563eb !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# STOCK PRICE DICTIONARY
# -------------------------------------------------------
STOCK_PRICES = {
    "AAPL":  {"price": 190,  "name": "Apple"},
    "GOOGL": {"price": 2800, "name": "Google"},
    "AMZN":  {"price": 3400, "name": "Amazon"},
    "MSFT":  {"price": 300,  "name": "Microsoft"},
    "TSLA":  {"price": 700,  "name": "Tesla"},
    "NVDA":  {"price": 950,  "name": "Nvidia"},
    "META":  {"price": 580,  "name": "Meta"},
    "NFLX":  {"price": 680,  "name": "Netflix"},
}

# -------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

if "analysis" not in st.session_state:
    st.session_state.analysis = ""

# -------------------------------------------------------
# HEADER
# -------------------------------------------------------
st.title("📈 Stock Portfolio Tracker")
st.caption("Add stocks, calculate your investment value, and get AI-powered analysis")
st.divider()

# -------------------------------------------------------
# INPUT SECTION
# -------------------------------------------------------
st.subheader("Add a Stock")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    symbol = st.selectbox(
        "Stock symbol",
        options=[""] + list(STOCK_PRICES.keys()),
        format_func=lambda x: "Select a stock..." if x == ""
            else f"{x} — {STOCK_PRICES[x]['name']} (${STOCK_PRICES[x]['price']:,})"
    )

with col2:
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)

with col3:
    st.write("")
    st.write("")
    add_clicked = st.button("➕ Add Stock", type="primary")

# Handle add button click
if add_clicked:
    if not symbol:
        st.warning("Please select a stock symbol.")
    else:
        # Add to portfolio — if stock exists, add to quantity
        prev = st.session_state.portfolio.get(symbol, 0)
        st.session_state.portfolio[symbol] = prev + quantity
        st.session_state.analysis = ""
        st.success(f"✅ Added {quantity} shares of {symbol}")

st.divider()

# -------------------------------------------------------
# PORTFOLIO TABLE + METRICS
# -------------------------------------------------------
if st.session_state.portfolio:
    st.subheader("Your Portfolio")

    results          = []
    total_investment = 0

    for sym, qty in st.session_state.portfolio.items():
        price       = STOCK_PRICES[sym]["price"]
        name        = STOCK_PRICES[sym]["name"]
        stock_value = qty * price
        total_investment += stock_value
        results.append({
            "Symbol":      sym,
            "Company":     name,
            "Price/Share": f"${price:,}",
            "Quantity":    qty,
            "Total Value": f"${stock_value:,}",
        })

    # --- Metric cards ---
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Investment",  f"${total_investment:,}")
    m2.metric("📊 Stocks Held",       len(results))
    m3.metric("🔢 Total Shares",      sum(r["Quantity"] for r in results))

    st.write("")
    st.dataframe(results, use_container_width=True, hide_index=True)

    # --- Remove stock option ---
    with st.expander("🗑️ Remove a stock"):
        remove_sym = st.selectbox(
            "Select stock to remove",
            options=list(st.session_state.portfolio.keys()),
            key="remove_select"
        )
        if st.button("Remove", key="remove_btn"):
            del st.session_state.portfolio[remove_sym]
            st.session_state.analysis = ""
            st.rerun()

    st.divider()

    # -------------------------------------------------------
    # AI ANALYSIS
    # -------------------------------------------------------
    st.subheader("🤖 AI Analysis")

    if st.button("Analyze My Portfolio with AI", type="primary"):
        # Build portfolio summary string for the AI prompt
        lines = [
            f"{r['Symbol']} ({r['Company']}): {r['Quantity']} shares "
            f"@ {r['Price/Share']} = {r['Total Value']}"
            for r in results
        ]
        portfolio_text = "\n".join(lines)

        prompt = f"""You are a friendly financial portfolio advisor. Analyze this stock portfolio:

{portfolio_text}

Total investment: ${total_investment:,}

Please provide:
1. Portfolio Summary — what this portfolio looks like at a glance
2. Risk Assessment — is it too concentrated in one stock?
3. Diversification Feedback — are all stocks in the same sector?
4. Suggestions — what to consider adding or rebalancing
5. Plain English Verdict — one paragraph a beginner can understand

Use markdown formatting: bold headings with ##, bullet points with -.
Add emojis to each section heading.
Reminder: This is not financial advice.
"""

        try:
            with st.spinner("Analyzing your portfolio..."):
                client   = Groq(api_key=os.environ.get("GROQ_API_KEY"))
                response = client.chat.completions.create(
                    model      = "llama-3.3-70b-versatile",
                    messages   = [{"role": "user", "content": prompt}],
                    max_tokens = 1024,
                )
                st.session_state.analysis = response.choices[0].message.content

        except Exception as e:
            st.error(f"AI Error: {str(e)}")

    # -------------------------------------------------------
    # FIX 2: Render analysis using st.markdown() inside a
    # styled container so markdown (bold, bullets, headers)
    # all render correctly instead of showing raw symbols
    # -------------------------------------------------------
    if st.session_state.analysis:
        st.markdown('<div class="analysis-wrapper"><div class="analysis-label">AI Analysis</div></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(st.session_state.analysis)

else:
    # Empty state
    st.info("🗂️ Your portfolio is empty — add a stock above to get started.")