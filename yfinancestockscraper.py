import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Konfigurasi halaman
st.set_page_config(
    page_title="📈 Yahoo Finance Data Scraper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan yang lebih menarik
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stApp {
        background:
radial-gradient(circle at 15% 15%, #111827 0%, transparent 40%),
radial-gradient(circle at 85% 85%, #0f172a 0%, transparent 40%),
#020617;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    h1 {
        color: #ffffff;
        font-weight: 700;
    }
    h2, h3 {
        color: #e0e0e0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e2130;
        border-radius: 5px;
        color: white;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📈 Yahoo Finance Data Scraper")
st.markdown("### Ekstrak data instrumen investasi dari Yahoo Finance")

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Pengaturan")
    
    # Input ticker
    ticker_input = st.text_input(
        "Masukkan Ticker Symbol",
        value="BBCA.JK",
        help="Contoh: AAPL (Apple), BBCA.JK (BCA), BTC-USD (Bitcoin), EURUSD=X (EUR/USD)"
    ).upper()
    
    # Pilihan periode
    st.markdown("### 📅 Periode Data")
    period_type = st.radio(
        "Tipe Periode",
        ["Preset", "Custom"],
        horizontal=True
    )
    
    if period_type == "Preset":
        period = st.selectbox(
            "Pilih Periode",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
            index=5
        )
        start_date = None
        end_date = None
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Tanggal Mulai",
                value=datetime.now() - timedelta(days=365)
            )
        with col2:
            end_date = st.date_input(
                "Tanggal Akhir",
                value=datetime.now()
            )
        period = None
    
    # Interval data
    interval = st.selectbox(
        "Interval Data",
        ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"],
        index=5,
        help="Interval 1m-1h hanya untuk periode ≤30 hari"
    )
    
    # Tombol scrape
    scrape_button = st.button("🔍 Ekstrak Data", type="primary", use_container_width=True)


# Fungsi untuk mendapatkan data
@st.cache_data(ttl=300)
def get_stock_data(ticker, period, interval, start, end):
    try:
        stock = yf.Ticker(ticker)
        if period:
            hist = stock.history(period=period, interval=interval)
        else:
            hist = stock.history(start=start, end=end, interval=interval)
        info = stock.info
        return hist, info
    except Exception as e:
        return None, None

# Fungsi untuk membuat candlestick chart
def create_candlestick_chart(data, ticker):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} Price Chart', 'Volume')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Volume bars
    colors = ['#26a69a' if close >= open else '#ef5350' 
              for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        template='plotly_dark',
        height=700,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
        font=dict(color='#e0e0e0')
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='#1e2130')
    fig.update_yaxes(showgrid=True, gridcolor='#1e2130')
    
    return fig

# Main content
if scrape_button:
    with st.spinner(f'🔄 Mengambil data untuk {ticker_input}...'):
        if period:
            hist_data, info_data = get_stock_data(ticker_input, period, interval, None, None)
        else:
            hist_data, info_data = get_stock_data(ticker_input, None, interval, start_date, end_date)
    
    if hist_data is not None and not hist_data.empty:
        st.success(f"✅ Data berhasil diambil untuk {ticker_input}!")
        
        # Tabs untuk organisasi konten
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "📈 Chart", 
            "📋 Data Table", 
            "📉 Statistics",
            "ℹ️ Company Info"
        ])
        
        # Tab 1: Overview
        with tab1:
            # Metrics row
            col1, col2, col3, col4, col5 = st.columns(5)
            
            current_price = hist_data['Close'][-1]
            prev_price = hist_data['Close'][-2] if len(hist_data) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            with col1:
                st.metric(
                    "Current Price",
                    f"{current_price:,.2f}",
                    f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
                )
            
            with col2:
                st.metric(
                    "High",
                    f"{hist_data['High'].max():,.2f}"
                )
            
            with col3:
                st.metric(
                    "Low",
                    f"{hist_data['Low'].min():,.2f}"
                )
            
            with col4:
                avg_volume = hist_data['Volume'].mean()
                st.metric(
                    "Avg Volume",
                    f"{avg_volume:,.0f}"
                )
            
            with col5:
                if len(hist_data) > 0:
                    total_return = ((current_price - hist_data['Close'][0]) / hist_data['Close'][0]) * 100
                    st.metric(
                        "Total Return",
                        f"{total_return:+.2f}%"
                    )
            
            st.markdown("---")
            
            # Mini chart
            st.markdown("### 📈 Price Movement")
            fig_mini = go.Figure()
            fig_mini.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#667eea', width=2),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)'
            ))
            fig_mini.update_layout(
                template='plotly_dark',
                height=600,
                hovermode='x unified',
                plot_bgcolor='#0e1117',
                paper_bgcolor='#0e1117',
                font=dict(color='#e0e0e0'),
                showlegend=False,
                xaxis=dict(showgrid=True, gridcolor='#1e2130'),
                yaxis=dict(showgrid=True, gridcolor='#1e2130')
            )
            st.plotly_chart(fig_mini, use_container_width=True)
        
        # Tab 2: Chart
        with tab2:
            st.markdown("### 🕯️ Candlestick Chart")
            candlestick_fig = create_candlestick_chart(hist_data, ticker_input)
            st.plotly_chart(candlestick_fig, use_container_width=True)
            
            
        # Tab 3: Data Table
        with tab3:
            st.markdown("### 📋 Historical Data")
            
            # Format dataframe
            display_df = hist_data.copy()
            display_df = display_df.reset_index()
            display_df.columns = [col.replace('_', ' ').title() if col != 'Date' else 'Date' 
                                  for col in display_df.columns]
            
            st.dataframe(
                display_df.style.format({
                    'Open': '{:,.2f}',
                    'High': '{:,.2f}',
                    'Low': '{:,.2f}',
                    'Close': '{:,.2f}',
                    'Volume': '{:,.0f}'
                }),
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = hist_data.to_csv()
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"{ticker_input}_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # Tab 4: Statistics
        with tab4:
            st.markdown("### 📊 Statistical Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Price Statistics")
                stats_df = hist_data[['Open', 'High', 'Low', 'Close']].describe()
                st.dataframe(stats_df.style.format('{:,.2f}'), use_container_width=True)
            
            with col2:
                st.markdown("#### Volume Statistics")
                vol_stats = hist_data['Volume'].describe().to_frame()
                st.dataframe(vol_stats.style.format('{:,.0f}'), use_container_width=True)
            
            # Returns calculation
            st.markdown("#### 📈 Returns Analysis")
            hist_data['Daily_Return'] = hist_data['Close'].pct_change() * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Daily Return", f"{hist_data['Daily_Return'].mean():.2f}%")
            with col2:
                st.metric("Volatility (Std)", f"{hist_data['Daily_Return'].std():.2f}%")
            with col3:
                sharpe = (hist_data['Daily_Return'].mean() / hist_data['Daily_Return'].std()) * (252 ** 0.5) if hist_data['Daily_Return'].std() != 0 else 0
                st.metric("Sharpe Ratio (Ann.)", f"{sharpe:.2f}")
            
            # Returns distribution
            fig_returns = go.Figure()
            fig_returns.add_trace(go.Histogram(
                x=hist_data['Daily_Return'].dropna(),
                nbinsx=50,
                name='Daily Returns',
                marker_color='#667eea'
            ))
            fig_returns.update_layout(
                title='Distribution of Daily Returns',
                template='plotly_dark',
                height=400,
                plot_bgcolor='#0e1117',
                paper_bgcolor='#0e1117',
                font=dict(color='#e0e0e0')
            )
            st.plotly_chart(fig_returns, use_container_width=True)
        
        # Tab 5: Company Info
        with tab5:
            st.markdown("### ℹ️ Company/Asset Information")
            
            if info_data:
                col1, col2 = st.columns(2)
                
                info_display = {}
                important_keys = [
                    'longName', 'symbol', 'sector', 'industry', 'country',
                    'marketCap', 'currency', 'exchange', 'quoteType',
                    'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'fiftyDayAverage',
                    'twoHundredDayAverage', 'dividendYield', 'beta',
                    'trailingPE', 'forwardPE', 'priceToBook'
                ]
                
                for key in important_keys:
                    if key in info_data and info_data[key]:
                        info_display[key.replace('_', ' ').title()] = info_data[key]
                
                # Split info into two columns
                items = list(info_display.items())
                mid = len(items) // 2
                
                with col1:
                    for key, value in items[:mid]:
                        if isinstance(value, (int, float)):
                            if 'Cap' in key or 'Market' in key:
                                st.markdown(f"**{key}:** {value:,.0f}")
                            elif 'Yield' in key or 'Beta' in key:
                                st.markdown(f"**{key}:** {value:.4f}")
                            else:
                                st.markdown(f"**{key}:** {value:,.2f}")
                        else:
                            st.markdown(f"**{key}:** {value}")
                
                with col2:
                    for key, value in items[mid:]:
                        if isinstance(value, (int, float)):
                            if 'Cap' in key or 'Market' in key:
                                st.markdown(f"**{key}:** {value:,.0f}")
                            elif 'Yield' in key or 'Beta' in key:
                                st.markdown(f"**{key}:** {value:.4f}")
                            else:
                                st.markdown(f"**{key}:** {value:,.2f}")
                        else:
                            st.markdown(f"**{key}:** {value}")
            else:
                st.info("Company information not available for this ticker.")
    
    elif hist_data is not None and hist_data.empty:
        st.error(f"❌ Tidak ada data yang ditemukan untuk ticker {ticker_input}. Pastikan ticker dan periode yang dipilih benar.")
    else:
        st.error(f"❌ Gagal mengambil data untuk ticker {ticker_input}. Periksa kembali ticker symbol.")

else:
    # Welcome screen
    st.info("👆 Masukkan ticker symbol di sidebar dan klik tombol 'Ekstrak Data' untuk memulai!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>📈 Yahoo Finance Data Scraper | Revaldy Hazza Daniswara</p>
</div>
""", unsafe_allow_html=True)