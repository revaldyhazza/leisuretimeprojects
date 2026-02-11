import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pmdarima import auto_arima
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(
    page_title="Peramalan Runtun Waktu (Time Series)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan yang lebih menarik
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 1rem;
    }
    h2 {
        color: #2c3e50;
        padding-top: 1rem;
    }
    .stApp {
        background:
radial-gradient(circle at 15% 15%, #111827 0%, transparent 40%),
radial-gradient(circle at 85% 85%, #0f172a 0%, transparent 40%),
#020617;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        color: black;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# Judul aplikasi
st.title("📈 Peramalan Runtun Waktu (Time Series)")
st.caption("Metode yang digunakan adalah ARIMA dengan opsi parameter Seasonal")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    # Upload file
    st.subheader("1️⃣ Upload Data")
    uploaded_file = st.file_uploader(
        "Upload file CSV atau Excel",
        type=['xlsx', 'xls'],
        help="File harus berisi kolom tanggal dan kolom nilai numerik"
    )
    
    st.markdown("---")
   

# Main content
if uploaded_file is not None:
    try:
        # Baca file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Preview data
        with st.expander("👀 Preview Data", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Jumlah Baris", df.shape[0])
            with col2:
                st.metric("Jumlah Kolom", df.shape[1])
            with col3:
                st.metric("Missing Values", df.isnull().sum().sum())
            
            st.dataframe(df.head(10), use_container_width=True)
        
        # Sidebar - Pemilihan kolom
        with st.sidebar:
            st.subheader("2️⃣ Pilih Kolom")
            
            date_column = st.selectbox(
                "Kolom Tanggal",
                options=df.columns.tolist(),
                help="Pilih kolom yang berisi data tanggal/waktu"
            )
            
            value_column = st.selectbox(
                "Kolom Nilai",
                options=[col for col in df.columns if col != date_column],
                help="Pilih kolom yang berisi nilai untuk diprediksi"
            )
            
            st.markdown("---")
            st.subheader("3️⃣ Parameter Forecasting")
            
            # Split ratio
            train_ratio = st.slider(
                "Rasio Data Training (%)",
                min_value=60,
                max_value=95,
                value=80,
                step=5,
                help="Persentase data untuk training"
            )
            
            # Forecast periods
            forecast_periods = st.number_input(
                "Periode Forecasting",
                min_value=1,
                max_value=365,
                value=30,
                step=1,
                help="Jumlah periode ke depan yang akan diprediksi"
            )
            
            # Seasonal
            seasonal = st.checkbox(
                "Seasonal (SARIMA)",
                value=False,
                help="Aktifkan jika data memiliki pola musiman"
            )
            
            if seasonal:
                m_value = st.number_input(
                    "Periode Seasonal (m)",
                    min_value=2,
                    max_value=365,
                    value=12,
                    help="Jumlah periode dalam satu siklus musiman"
                )
            
            st.markdown("---")
            run_forecast = st.button("🚀 Jalankan Forecasting", type="primary", use_container_width=True)
        
        # Proses forecasting
        if run_forecast:
            with st.spinner("🔄 Memproses data dan melakukan forecasting..."):
                try:
                    # Persiapan data
                    df_copy = df.copy()
                    df_copy[date_column] = pd.to_datetime(df_copy[date_column])
                    df_copy = df_copy.sort_values(date_column)
                    df_copy.set_index(date_column, inplace=True)
                    
                    # Ambil data nilai
                    data = df_copy[value_column].dropna()
                    
                    # Split data
                    train_size = int(len(data) * (train_ratio / 100))
                    train_data = data[:train_size]
                    test_data = data[train_size:]
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Auto ARIMA
                    status_text.text("🔍 Mencari parameter ARIMA terbaik...")
                    progress_bar.progress(25)
                    
                    if seasonal:
                        model_auto = auto_arima(
                            train_data,
                            seasonal=True,
                            m=m_value,
                            suppress_warnings=True,
                            stepwise=True,
                            trace=False
                        )
                    else:
                        model_auto = auto_arima(
                            train_data,
                            seasonal=False,
                            suppress_warnings=True,
                            stepwise=True,
                            trace=False
                        )
                    
                    progress_bar.progress(50)
                    
                    # Fitting model
                    status_text.text("🎯 Melatih model ARIMA...")
                    order = model_auto.order
                    
                    if seasonal:
                        seasonal_order = model_auto.seasonal_order
                        model = ARIMA(train_data, order=order, seasonal_order=seasonal_order)
                    else:
                        model = ARIMA(train_data, order=order)
                    
                    model_fit = model.fit()
                    
                    progress_bar.progress(75)
                    
                    # Prediksi
                    status_text.text("📊 Membuat prediksi...")
                    
                    # Prediksi untuk data test
                    if len(test_data) > 0:
                        predictions_test = model_fit.forecast(steps=len(test_data))
                        
                        # Metrik evaluasi
                        mae = mean_absolute_error(test_data, predictions_test)
                        rmse = np.sqrt(mean_squared_error(test_data, predictions_test))
                        mape = np.mean(np.abs((test_data - predictions_test) / test_data)) * 100
                    
                    # Prediksi untuk future
                    # Refit dengan semua data
                    if seasonal:
                        model_full = ARIMA(data, order=order, seasonal_order=seasonal_order)
                    else:
                        model_full = ARIMA(data, order=order)
                    
                    model_full_fit = model_full.fit()
                    forecast_future = model_full_fit.forecast(steps=forecast_periods)
                    
                    # Buat tanggal untuk forecast
                    last_date = data.index[-1]
                    freq = pd.infer_freq(data.index)
                    if freq is None:
                        freq = 'D'  # Default ke harian
                    
                    future_dates = pd.date_range(
                        start=last_date,
                        periods=forecast_periods + 1,
                        freq=freq
                    )[1:]
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Selesai!")
                    
                    # Hapus progress bar
                    import time
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Tampilkan hasil
                    st.markdown("---")
                    st.header("📊 Hasil Forecasting")
                    
                    # Parameter model
                    st.subheader("🎯 Parameter Model ARIMA")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>Order (p,d,q)</h3>
                            <h2>{order}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if seasonal:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Seasonal Order</h3>
                                <h2>{seasonal_order}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>Model Type</h3>
                                <h2>ARIMA</h2>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>AIC</h3>
                            <h2>{model_full_fit.aic:.2f}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Metrik evaluasi (jika ada test data)
                    if len(test_data) > 0:
                        st.subheader("📈 Metrik Evaluasi (Test Set)")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("MAE", f"{mae:.2f}")
                        with col2:
                            st.metric("RMSE", f"{rmse:.2f}")
                        with col3:
                            st.metric("MAPE", f"{mape:.2f}%")
                    
                    # Visualisasi
                    st.subheader("📉 Visualisasi Forecasting")
                    
                    # Create plotly figure
                    fig = go.Figure()
                    
                    # Data historis
                    fig.add_trace(go.Scatter(
                        x=train_data.index,
                        y=train_data.values,
                        mode='lines',
                        name='Data Training',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    
                    # Data test
                    if len(test_data) > 0:
                        fig.add_trace(go.Scatter(
                            x=test_data.index,
                            y=test_data.values,
                            mode='lines',
                            name='Data Test (Aktual)',
                            line=dict(color='#2ca02c', width=2)
                        ))
                        
                        # Prediksi test
                        fig.add_trace(go.Scatter(
                            x=test_data.index,
                            y=predictions_test,
                            mode='lines',
                            name='Prediksi Test',
                            line=dict(color='#ff7f0e', width=2, dash='dash')
                        ))
                    
                    # Forecast future
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=forecast_future,
                        mode='lines',
                        name='Forecast Future',
                        line=dict(color='#d62728', width=2, dash='dot')
                    ))
                    
                    # Get confidence interval
                    forecast_result = model_full_fit.get_forecast(steps=forecast_periods)
                    forecast_ci = forecast_result.conf_int()
                    
                    # Add confidence interval
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=forecast_ci.iloc[:, 1],
                        mode='lines',
                        name='Upper Bound',
                        line=dict(width=0),
                        showlegend=False
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=forecast_ci.iloc[:, 0],
                        mode='lines',
                        name='Confidence Interval (95%)',
                        fill='tonexty',
                        fillcolor='rgba(214, 39, 40, 0.2)',
                        line=dict(width=0)
                    ))
                    
                    fig.update_layout(
                        title='Forecasting Time Series dengan ARIMA',
                        xaxis_title='Tanggal',
                        yaxis_title=value_column,
                        hovermode='x unified',
                        height=500,
                        template='plotly_white',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabel hasil forecast
                    st.subheader("📋 Hasil Forecast Future")
                    
                    forecast_df = pd.DataFrame({
                        'Tanggal': future_dates,
                        'Prediksi': forecast_future.values,
                        'Lower Bound': forecast_ci.iloc[:, 0].values,
                        'Upper Bound': forecast_ci.iloc[:, 1].values
                    })
                    
                    st.dataframe(forecast_df, use_container_width=True)
                    
                    # Download hasil
                    csv = forecast_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Hasil Forecast (CSV)",
                        data=csv,
                        file_name=f"forecast_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    # Model summary
                    with st.expander("📝 Model Summary"):
                        st.text(model_full_fit.summary())
                    
                    # Residual analysis
                    with st.expander("🔬 Analisis Residual"):
                        residuals = model_full_fit.resid
                        
                        fig_residual = make_subplots(
                            rows=1, cols=2,
                            subplot_titles=('Residual Plot', 'Residual Distribution')
                        )
                        
                        # Residual plot
                        fig_residual.add_trace(
                            go.Scatter(
                                x=list(range(len(residuals))),
                                y=residuals,
                                mode='markers',
                                name='Residuals',
                                marker=dict(color='#1f77b4')
                            ),
                            row=1, col=1
                        )
                        
                        # Histogram
                        fig_residual.add_trace(
                            go.Histogram(
                                x=residuals,
                                name='Distribution',
                                marker=dict(color='#ff7f0e')
                            ),
                            row=1, col=2
                        )
                        
                        fig_residual.update_layout(
                            height=400,
                            showlegend=False,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig_residual, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {str(e)}")
                    st.info("💡 Pastikan kolom yang dipilih memiliki format yang benar dan tidak ada missing values yang berlebihan.")
    
    except Exception as e:
        st.error(f"❌ Error saat membaca file: {str(e)}")
        st.info("💡 Pastikan file yang diupload adalah file CSV atau Excel yang valid.")

else:
    # Landing page
    st.info("👆 Silakan upload file data time series di sidebar untuk memulai")
    
    #Fitur
    st.markdown("---")
    st.subheader("✨ Fitur Aplikasi")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🎯 Auto ARIMA**
        - Parameter optimal otomatis oleh Auto ARIMA
        - Kustomisasi Seasonal Parameter
        - Seleksi berbasis Akaike Information Criterion (AIC)
        """)
    
    with col2:
        st.markdown("""
        **📊 Visualisasi Interaktif**
        - Grafik yang informatif
        - Confidence interval
        - Analisis residual
        """)
    
    with col3:
        st.markdown("""
        **📈 Metrik Evaluasi**
        - MAE, RMSE, MAPE
        - Model summary
        - Export hasil
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Made with Streamlit | Time Series Forecasting App</p>
    </div>
    """,
    unsafe_allow_html=True
)