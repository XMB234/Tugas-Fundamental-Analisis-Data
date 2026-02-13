import streamlit as st       # Untuk membangun aplikasi web interaktif
import pandas as pd          # Untuk manipulasi dan analisis data
import numpy as np           # Untuk operasi numerik
import matplotlib.pyplot as plt # Untuk membuat plot statis
import seaborn as sns        # Untuk visualisasi statistik yang lebih indah
import matplotlib.ticker as mticker # Untuk format sumbu plot
from pathlib import Path

st.set_page_config(layout="wide")

# --- Atur gaya Matplotlib untuk latar belakang gelap --- #
# Blok ini memastikan gaya tema gelap yang konsisten untuk semua plot
plt.style.use('dark_background')
plt.rcParams.update({
    "figure.facecolor": "black",
    "axes.facecolor": "black",
    "savefig.facecolor": "black",
    "text.color": "white",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "gray",
    "axes.edgecolor": "white",
    "patch.edgecolor": "white",
    "axes.titlecolor": "white",
    "legend.labelcolor": "white",
    "legend.title_fontsize": 'medium', # Pastikan judul legenda terlihat
    "legend.fontsize": 'small',        # Pastikan label legenda terlihat
})

# --- Muat Data --- #
@st.cache_data
def load_data():
    # Tentukan direktori data relatif terhadap file ini
    data_dir = Path(__file__).parent / "Data"

    # Muat semua file CSV yang diperlukan (menggunakan Path agar path relatif always benar)
    master_orders_df = pd.read_csv(data_dir / 'master_orders.csv')
    monthly_revenue_df = pd.read_csv(data_dir / 'monthly_revenue.csv')
    orders_monthly_df = pd.read_csv(data_dir / 'orders_monthly.csv')
    category_review_scores_df = pd.read_csv(data_dir / 'category_review_scores.csv')
    state_review_summary_df = pd.read_csv(data_dir / 'state_review_summary.csv')
    high_value_product_preferences_df = pd.read_csv(data_dir / 'high_value_product_preferences.csv', index_col=0)
    customer_value_df = pd.read_csv(data_dir / 'customer_value.csv')
    payment_customer_df = pd.read_csv(data_dir / 'payment_customer.csv')
    items_products_df = pd.read_csv(data_dir / 'items_products.csv') # Baru: Muat items_products

    # Konversi kolom 'month' ke objek datetime
    monthly_revenue_df['month'] = pd.to_datetime(monthly_revenue_df['month'])
    orders_monthly_df['month'] = pd.to_datetime(orders_monthly_df['month'])

    # Konversi kolom tanggal di master_orders_df
    date_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in date_cols:
        master_orders_df[col] = pd.to_datetime(master_orders_df[col], errors='coerce') # Gunakan errors='coerce' untuk menangani masalah parsing

    # Pastikan customer_unique_id bertipe string untuk penggabungan yang kuat
    master_orders_df['customer_unique_id'] = master_orders_df['customer_unique_id'].astype(str)

    # Muat rfm_segmentation_df dan pastikan 'customer_unique_id' dan 'Segment' ditangani dengan benar
    rfm_segmentation_df = pd.read_csv(data_dir / 'rfm_segmentation.csv')
    rfm_segmentation_df['customer_unique_id'] = rfm_segmentation_df['customer_unique_id'].astype(str)
    # Pastikan kolom 'Segment' ada dan bertipe string
    if 'Segment' not in rfm_segmentation_df.columns:
        st.error("Error: Kolom 'Segment' tidak ditemukan di rfm_segmentation.csv. Pastikan CSV berisi data tersegmentasi.")
        # Fallback atau munculkan error jika Segment penting dan hilang
        rfm_segmentation_df['Segment'] = 'Unknown'
    rfm_segmentation_df['Segment'] = rfm_segmentation_df['Segment'].astype(str)

    # Hapus kolom 'Segment' yang ada dari master_orders_df jika ada, untuk menghindari masalah dengan kolom yang kadaluarsa
    if 'Segment' in master_orders_df.columns:
        master_orders_df = master_orders_df.drop(columns=['Segment'])

    # Gabungkan 'Segment' yang ada dari rfm_segmentation_df kembali ke master_orders_df
    master_orders_df = master_orders_df.merge(
        rfm_segmentation_df[['customer_unique_id', 'Segment']],
        on='customer_unique_id',
        how='left'
    )

    return (
        master_orders_df, monthly_revenue_df, orders_monthly_df,
        rfm_segmentation_df, category_review_scores_df, state_review_summary_df,
        high_value_product_preferences_df, customer_value_df, payment_customer_df,
        items_products_df
    )

(
    master_orders_df, monthly_revenue_df, orders_monthly_df,
    rfm_segmentation_df, category_review_scores_df, state_review_summary_df,
    high_value_product_preferences_df, customer_value_df, payment_customer_df,
    items_products_df
) = load_data()


# --- Hitung KPI (berdasarkan data yang tidak difilter) --- #
# KPI ini akan ditampilkan di bagian paling atas.
total_revenue = master_orders_df['payment_value'].sum()
total_orders = master_orders_df['order_id'].nunique()
average_review_score = master_orders_df['review_score'].mean()
total_customers = master_orders_df['customer_unique_id'].nunique()

# --- Judul Dashboard --- #
st.title("E-commerce Data Analysis Dashboard")

# --- Kartu KPI --- #
st.subheader("Indikator Kinerja Utama (KPI)")
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric(label="Total Pendapatan", value=f"R${total_revenue:,.2f}")
with col_kpi2:
    st.metric(label="Total Pesanan", value=f"{total_orders:,}")
with col_kpi3:
    st.metric(label="Rata-rata Skor Ulasan", value=f"{average_review_score:.2f} / 5.0")
with col_kpi4:
    st.metric(label="Total Pelanggan", value=f"{total_customers:,}")

# --- Navigasi Sidebar --- #
st.sidebar.title("Navigasi Dashboard")
selected_section = st.sidebar.radio(
    "Pilih Bagian",
    [
        "Ringkasan Umum Data",
        "Analisis Kepuasan Pelanggan",
        "Analisis Pelanggan Bernilai Tinggi",
        "Analisis RFM",
        "Kesimpulan Utama Analisis"
    ]
)

# --- Konten berdasarkan Pilihan Sidebar --- #

if selected_section == "Ringkasan Umum Data":
    st.header("1. Ringkasan Umum Data E-commerce")

    with st.expander("Distribusi Variabel Numerik"):
        st.subheader("Distribusi Variabel Numerik Utama")
        numeric_cols = [
            "payment_value", "total_price", "total_freight",
            "delivery_time_days", "total_items", "unique_sellers",
            "review_score"
        ]
        # --- Dedicated variable for log-scaled columns --- #
        log_scaled_cols = ["payment_value", "total_price", "total_freight", "delivery_time_days"]

        n_cols = 3
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols

        fig_num, axes_num = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        axes_num = axes_num.flatten() # Ratakan untuk iterasi mudah

        for i, col in enumerate(numeric_cols):
            ax = axes_num[i]
            if col in log_scaled_cols:
                sns.histplot(master_orders_df[col].dropna(), bins=50, kde=True, log_scale=True, ax=ax, color='cyan')
                ax.set_title(f"Distribusi {col.replace('_', ' ').title()} (Skala Log)", fontsize=10, color='white')
            elif col in ["total_items", "unique_sellers", "review_score"]:
                # Pastikan bins sesuai untuk nilai diskrit, misal, nilai maksimal + 1
                bins = int(master_orders_df[col].max()) if master_orders_df[col].nunique() > 1 else 1 # Tangani kasus nilai unik tunggal
                sns.histplot(master_orders_df[col].dropna(), bins=bins, kde=False, ax=ax, color='lime')
                ax.set_title(f"Distribusi {col.replace('_', ' ').title()}", fontsize=10, color='white')
            else:
                sns.histplot(master_orders_df[col].dropna(), bins=30, kde=True, ax=ax, color='gold')
                ax.set_title(f"Distribusi {col.replace('_', ' ').title()}", fontsize=10, color='white')
            ax.set_xlabel(col.replace('_', ' ').title(), fontsize=8, color='white')
            ax.set_ylabel("Frekuensi", fontsize=8, color='white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')

        for i in range(len(numeric_cols), len(axes_num)):
            fig_num.delaxes(axes_num[i]) # Hapus subplot kosong

        plt.tight_layout(rect=[0, 0, 1, 0.96]) # Sesuaikan layout untuk mencegah tumpang tindih judul
        fig_num.suptitle("Distribusi Variabel Numerik Utama", fontsize=14, color='white')
        st.pyplot(fig_num)
        plt.close(fig_num)
        st.markdown("""
        **Insight**: Visualisasi ini menunjukkan distribusi variabel numerik utama seperti nilai pembayaran, harga total, biaya pengiriman, dan waktu pengiriman. Mayoritas transaksi memiliki nilai rendah, dengan 'ekor panjang' dari transaksi bernilai tinggi. Waktu pengiriman bervariasi, dan skor ulasan cenderung tinggi. Skala log digunakan untuk mengatasi kemiringan data yang ekstrem.
        """
        )

    with st.expander("Distribusi Variabel Kategorikal"):
        st.subheader("Distribusi Variabel Kategorikal")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### Status Pesanan")
            order_status_summary_df = master_orders_df["order_status"].value_counts(normalize=True).mul(100).round(2).reset_index(name="Percentage (%)")
            order_status_summary_df.columns = ['order_status', 'Percentage (%)']
            fig_status, ax_status = plt.subplots(figsize=(6, 4))
            sns.barplot(x="Percentage (%)", y="order_status", data=order_status_summary_df, palette='viridis', ax=ax_status, hue="order_status", legend=False)
            ax_status.set_xlabel("Persentase (%)", color='white')
            ax_status.set_ylabel("Status Pesanan", color='white')
            ax_status.tick_params(axis='x', colors='white')
            ax_status.tick_params(axis='y', colors='white')
            for index, value in enumerate(order_status_summary_df["Percentage (%)"]):
                ax_status.text(value + 0.5, index, f'{value:.1f}%', va='center', fontsize=8, color='white')
            # Adjust xlim to provide enough space for labels
            ax_status.set_xlim(right=order_status_summary_df["Percentage (%)"].max() * 1.15) # Add 15% padding
            plt.tight_layout()
            st.pyplot(fig_status)
            plt.close(fig_status)
            st.markdown("""
            **Insight**: Hampir semua pesanan berhasil dikirim ('delivered'), menunjukkan efisiensi operasional yang tinggi. Persentase pesanan yang dibatalkan atau tidak tersedia sangat kecil, yang positif untuk kepuasan pelanggan.
            """
            )

        with col2:
            st.markdown("### Jumlah Metode Pembayaran per Pesanan")
            payment_types_summary_df = master_orders_df["payment_types"].value_counts(normalize=True).mul(100).round(2).reset_index(name="Percentage (%)")
            payment_types_summary_df.columns = ['payment_types', 'Percentage (%)']
            fig_payment, ax_payment = plt.subplots(figsize=(4, 4)) # Adjusted figsize to be more square-like for vertical bars
            sns.barplot(x="payment_types", y="Percentage (%)", data=payment_types_summary_df, palette='plasma', ax=ax_payment, hue="payment_types", legend=False) # Vertical bar plot
            ax_payment.set_xlabel("Jumlah Metode Pembayaran Digunakan", color='white') # Updated x-label
            ax_payment.set_ylabel("Persentase (%)", color='white') # Updated y-label
            ax_payment.tick_params(axis='x', colors='white')
            ax_payment.tick_params(axis='y', colors='white')
            for index, value in enumerate(payment_types_summary_df["Percentage (%)"]):
                ax_payment.text(index, value + 0.5, f'{value:.1f}%', ha='center', fontsize=8, color='white')
            plt.tight_layout()
            st.pyplot(fig_payment)
            plt.close(fig_payment)
            st.markdown("""
            **Insight**: Mayoritas pesanan hanya menggunakan satu jenis metode pembayaran. Ini menunjukkan preferensi pelanggan untuk proses pembayaran yang sederhana, atau mungkin transaksi yang tidak memerlukan beberapa metode pembayaran.
            """
            )

        with col3:
            st.markdown("### Distribusi Skor Ulasan")
            review_score_summary_df = master_orders_df["review_score"].value_counts(normalize=True).mul(100).round(2).reset_index(name="Percentage (%)")
            review_score_summary_df.columns = ['review_score', 'Percentage (%)']
            fig_review, ax_review = plt.subplots(figsize=(6, 4))
            sns.barplot(x="review_score", y="Percentage (%)", data=review_score_summary_df, palette='rocket_r', ax=ax_review, hue="review_score", legend=False)
            ax_review.set_xlabel("Skor Ulasan", color='white')
            ax_review.set_ylabel("Persentase (%)", color='white')
            ax_review.tick_params(axis='x', colors='white')
            ax_review.tick_params(axis='y', colors='white')
            for p in ax_review.patches:
                ax_review.annotate(
                    f'{p.get_height():.1f}%',
                    (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=8, color='white', xytext=(0, 5), textcoords='offset points'
                )
            # Adjust ylim to provide enough space for labels
            ax_review.set_ylim(top=review_score_summary_df["Percentage (%)"].max() * 1.15) # Add 15% padding
            plt.tight_layout()
            st.pyplot(fig_review)
            plt.close(fig_review)
            st.markdown("""
            **Insight**: Distribusi skor ulasan menunjukkan bahwa sebagian besar pelanggan memberikan skor tinggi (4 dan 5), menandakan tingkat kepuasan yang umumnya baik. Skor 5 adalah yang paling dominan, diikuti oleh skor 4. Skor rendah (1 dan 2) jauh lebih jarang muncul.
            """
            )

    with st.expander("Tren Berdasarkan Waktu"):
        st.subheader("Tren Berdasarkan Waktu")
        col_ts1, col_ts2 = st.columns(2)

        with col_ts1:
            st.markdown("### Volume Pesanan Bulanan")
            fig_orders_monthly, ax_orders_monthly = plt.subplots(figsize=(8, 4))
            ax_orders_monthly.plot(orders_monthly_df["month"], orders_monthly_df["order_count"], marker="o", color='cyan')
            ax_orders_monthly.set_title("Volume Pesanan Bulanan", fontsize=10, color='white')
            ax_orders_monthly.set_xlabel("Bulan", fontsize=8, color='white')
            ax_orders_monthly.set_ylabel("Jumlah Pesanan", fontsize=8, color='white')
            ax_orders_monthly.tick_params(labelsize=7, rotation=45, colors='white')
            ax_orders_monthly.grid(axis="y", linestyle="--", alpha=0.6)
            ax_orders_monthly.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
            plt.tight_layout()
            st.pyplot(fig_orders_monthly)
            plt.close(fig_orders_monthly)
            st.markdown("""
            **Insight**: Grafik menunjukkan tren pertumbuhan jumlah pesanan bulanan yang stabil dari akhir 2016 hingga pertengahan 2018. Ini mengindikasikan ekspansi pasar atau peningkatan adopsi platform. Penurunan tajam di akhir periode mungkin disebabkan oleh data yang tidak lengkap.
            """
            )

        with col_ts2:
            st.markdown("### Tren Pendapatan Bulanan")
            fig_monthly_revenue, ax_monthly_revenue = plt.subplots(figsize=(8, 4))
            ax_monthly_revenue.plot(monthly_revenue_df["month"], monthly_revenue_df["total_revenue"], marker="o", color='lime')
            ax_monthly_revenue.set_title("Tren Pendapatan Bulanan", fontsize=10, color='white')
            ax_monthly_revenue.set_xlabel("Bulan", fontsize=8, color='white')
            ax_monthly_revenue.set_ylabel("Pendapatan (R$)", fontsize=8, color='white')
            ax_monthly_revenue.tick_params(labelsize=7, rotation=45, colors='white')
            ax_monthly_revenue.grid(axis="y", linestyle="--", alpha=0.6)
            ax_monthly_revenue.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1_000_000:.1f}M'))
            plt.tight_layout()
            st.pyplot(fig_monthly_revenue)
            plt.close(fig_monthly_revenue)
            st.markdown("""
            **Insight**: Mirip dengan volume pesanan, pendapatan bulanan menunjukkan tren kenaikan yang konsisten, mencapai puncaknya pada pertengahan 2018. Ini mencerminkan pertumbuhan bisnis secara keseluruhan, dengan fluktuasi musiman yang mungkin terkait dengan event belanja.
            """
            )

elif selected_section == "Analisis Kepuasan Pelanggan":
    st.header("2. Analisis Kepuasan Pelanggan (Faktor Review Score)")
    st.write("Faktor-faktor apa saja yang paling berpengaruh terhadap kepuasan pelanggan (review score) pada platform e-commerce?")

    with st.expander("Top & Bottom Kategori Produk berdasarkan Rata-rata Review Score"):
        st.subheader("Top & Bottom Kategori Produk berdasarkan Rata-rata Review Score")
        top_bottom_categories = (
            category_review_scores_df
            .sort_values('avg_review_score', ascending=False)
            .pipe(lambda df: pd.concat([df.head(10), df.tail(10)]))
        )
        fig_cat_review, ax_cat_review = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x='avg_review_score',
            y='product_category_name_english',
            data=top_bottom_categories,
            ax=ax_cat_review,
            palette='coolwarm',
            hue='product_category_name_english',
            legend=False
        )
        ax_cat_review.set_title('Top & Bottom Kategori Produk berdasarkan Rata-rata Review Score', fontsize=12, color='white')
        ax_cat_review.set_xlabel('Rata-rata Review Score', fontsize=10, color='white')
        ax_cat_review.set_ylabel('Kategori Produk', fontsize=10, color='white')
        ax_cat_review.tick_params(axis='x', colors='white')
        ax_cat_review.tick_params(axis='y', colors='white')
        for index, value in enumerate(top_bottom_categories['avg_review_score']):
            ax_cat_review.text(value + 0.05, index, f'{value:.2f}', va='center', fontsize=8, color='white')
        plt.tight_layout()
        st.pyplot(fig_cat_review)
        plt.close(fig_cat_review)
        st.markdown("""
        **Insight**: Kategori produk seperti 'cds_dvds_musicals' dan 'fashion_childrens_clothes' memiliki skor ulasan rata-rata tertinggi, menunjukkan kepuasan tinggi di segmen tersebut. Sebaliknya, 'security_and_services' dan 'office_furniture' memiliki skor terendah, menyoroti area untuk perbaikan. Ini menunjukkan bahwa jenis produk sangat mempengaruhi kepuasan.
        """
        )

    with st.expander("Top & Bottom Negara Bagian berdasarkan Rata-rata Review Score"):
        st.subheader("Top & Bottom Negara Bagian berdasarkan Rata-rata Review Score")
        top_bottom_states = (
            state_review_summary_df
            .sort_values('avg_review_score', ascending=False)
            .pipe(lambda df: pd.concat([df.head(10), df.tail(10)]))
        )
        fig_state_review, ax_state_review = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x='avg_review_score',
            y='customer_state',
            data=top_bottom_states,
            ax=ax_state_review,
            palette='coolwarm',
            hue='customer_state',
            legend=False
        )
        ax_state_review.set_title('Top & Bottom Negara Bagian berdasarkan Rata-rata Review Score', fontsize=12, color='white')
        ax_state_review.set_xlabel('Rata-rata Review Score', fontsize=10, color='white')
        ax_state_review.set_ylabel('Negara Bagian', fontsize=10, color='white')
        ax_state_review.tick_params(axis='x', colors='white')
        ax_state_review.tick_params(axis='y', colors='white')
        for index, value in enumerate(top_bottom_states['avg_review_score']):
            ax_state_review.text(value + 0.05, index, f'{value:.2f}', va='center', fontsize=8, color='white')
        plt.tight_layout()
        st.pyplot(fig_state_review)
        plt.close(fig_state_review)
        st.markdown("""
        **Insight**: Kepuasan pelanggan bervariasi secara geografis. Negara bagian seperti AP, AM, dan PR menunjukkan skor ulasan lebih tinggi, mungkin karena logistik yang lebih baik atau kualitas produk yang lebih sesuai. Sebaliknya, RR, AL, dan MA memiliki skor lebih rendah, menunjukkan area yang memerlukan perhatian khusus.
        """
        )

    with st.expander("Delivery Time vs Review Score"):
        st.subheader("Delivery Time vs Review Score")
        fig_delivery_review, ax_delivery_review = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            x="review_score",
            y="delivery_time_days",
            data=master_orders_df,
            showfliers=False,
            ax=ax_delivery_review
        )
        ax_delivery_review.set_title("Delivery Time vs Review Score", fontsize=12, color='white')
        ax_delivery_review.set_xlabel("Review Score", fontsize=10, color='white')
        ax_delivery_review.set_ylabel("Delivery Time (Days)", fontsize=10, color='white')
        ax_delivery_review.grid(axis='y', linestyle='--', alpha=0.6)
        ax_delivery_review.tick_params(axis='x', colors='white')
        ax_delivery_review.tick_params(axis='y', colors='white')
        plt.tight_layout()
        st.pyplot(fig_delivery_review)
        plt.close(fig_delivery_review)
        st.markdown("""
        **Insight**: Ada korelasi negatif yang jelas antara waktu pengiriman dan skor ulasan: semakin lama waktu pengiriman, semakin rendah skor ulasan yang diberikan pelanggan. Pesanan dengan skor 1.0 memiliki rata-rata waktu pengiriman terlama (sekitar 21 hari), menegaskan pentingnya pengiriman yang cepat untuk kepuasan.
        """
        )

    with st.expander("Review Score Distribution by Order Status"):
        st.subheader("Review Score Distribution by Order Status")
        fig_status_review, ax_status_review = plt.subplots(figsize=(12, 7))
        sns.boxplot(
            x="order_status",
            y="review_score",
            data=master_orders_df,
            palette='coolwarm',
            hue="order_status",
            legend=False,
            showfliers=False,
            ax=ax_status_review
        )
        ax_status_review.set_title("Review Score Distribution by Order Status", fontsize=14, color='white')
        ax_status_review.set_xlabel("Order Status", fontsize=12, color='white')
        ax_status_review.set_ylabel("Review Score", fontsize=12, color='white')
        ax_status_review.tick_params(axis='x', rotation=45, colors='white')
        ax_status_review.tick_params(axis='y', colors='white')
        ax_status_review.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig_status_review)
        plt.close(fig_status_review)
        st.markdown("""
        **Insight**: Status pesanan secara langsung memengaruhi kepuasan. Pesanan yang 'canceled' atau 'unavailable' memiliki skor ulasan sangat rendah atau tidak ada, sementara pesanan yang berhasil 'delivered' memiliki skor yang jauh lebih tinggi. Ini adalah indikator langsung keberhasilan transaksi.
        """
        )

    with st.expander("Matriks Korelasi Antar Variabel Utama"):
        st.subheader("Matriks Korelasi Antar Variabel Utama")
        numeric_for_corr = [
            "payment_value", "total_price", "total_freight",
            "delivery_time_days", "total_items", "unique_sellers",
            "review_score"
        ]
        corr_matrix = master_orders_df[numeric_for_corr].corr()
        fig_corr, ax_corr = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            linewidths=0.5,
            linecolor="white",
            cbar_kws={"shrink": 0.8},
            ax=ax_corr,
            annot_kws={"color": "white"}
        )
        ax_corr.set_title("Matriks Korelasi Antar Variabel Utama", fontsize=14, color='white')
        ax_corr.tick_params(axis='x', colors='white')
        ax_corr.tick_params(axis='y', colors='white')
        plt.tight_layout()
        st.pyplot(fig_corr)
        plt.close(fig_corr)
        st.markdown("""
        **Insight**: Heatmap korelasi menunjukkan bahwa `delivery_time_days` memiliki korelasi negatif terkuat dengan `review_score` (-0.33), sekali lagi menekankan pentingnya pengiriman yang cepat. `total_price` dan `payment_value` memiliki korelasi yang sangat kuat, seperti yang diharapkan. Faktor lain seperti `total_items` dan `unique_sellers` memiliki korelasi sangat lemah dengan `review_score`.
        """
        )

elif selected_section == "Analisis Pelanggan Bernilai Tinggi":
    st.header("3. Analisis Pelanggan Bernilai Tinggi")
    st.write("Karakteristik pelanggan seperti apa yang memberikan nilai transaksi tertinggi, dan bagaimana pola perilaku belanjanya?")

    with st.expander("Top Pelanggan Berdasarkan Total Pengeluaran"):
        st.subheader("Top Pelanggan Berdasarkan Total Pengeluaran")
        top_customers_spending = (
            rfm_segmentation_df[['customer_unique_id', 'Monetary', 'Segment']]
            .sort_values(by='Monetary', ascending=False)
            .head(10)
            .rename(columns={'Monetary': 'Total Pengeluaran'})
        )
        st.dataframe(top_customers_spending.style.format({"Total Pengeluaran": "R$ {:,.2f}"}))
        st.markdown("""
        **Insight**: Pelanggan teratas berdasarkan total pengeluaran menunjukkan bahwa nilai transaksi tertinggi seringkali berasal dari pembelian tunggal atau sangat sedikit dengan nilai pesanan yang sangat besar, bukan frekuensi pembelian yang tinggi. Ini menyoroti segmen pelanggan 'High Value' yang didorong oleh besarnya nilai setiap transaksi.
        """
        )

    with st.expander("Preferensi Kategori Produk Pelanggan Bernilai Tinggi"):
        st.subheader("Preferensi Kategori Produk Pelanggan Bernilai Tinggi")
        high_value_customer_ids = rfm_segmentation_df[
            rfm_segmentation_df['Segment'] == 'Champions'
        ]['customer_unique_id']

        high_value_orders = master_orders_df[
            master_orders_df['customer_unique_id'].isin(high_value_customer_ids)
        ]

        high_value_product_data = high_value_orders.merge(
            items_products_df,
            on='order_id',
            how='inner'
        )

        if not high_value_product_data.empty:
            high_value_product_preferences_filtered = (
                high_value_product_data
                ['product_category_name_english']
                .value_counts()
                .rename_axis("product_category_name_english")
                .reset_index(name="Number of Orders")
            )
            high_value_product_preferences_filtered["Percentage (%)"] = (
                high_value_product_preferences_filtered["Number of Orders"]
                / high_value_product_preferences_filtered["Number of Orders"].sum() * 100
            ).round(1)

            fig_hv_products, ax_hv_products = plt.subplots(figsize=(10, 5))
            sns.barplot(
                x="Number of Orders",
                y="product_category_name_english",
                data=high_value_product_preferences_filtered.head(10),
                ax=ax_hv_products,
                palette='viridis',
                hue="product_category_name_english",
                legend=False
            )
            for p in ax_hv_products.patches:
                ax_hv_products.annotate(
                    f'{int(p.get_width())}',
                    (p.get_width(), p.get_y() + p.get_height() / 2),
                    ha='left', va='center', fontsize=8, color='white',
                    xytext=(5, 0), textcoords='offset points'
                )
            ax_hv_products.set_title("Top 10 Kategori Produk untuk Pelanggan Bernilai Tinggi (Champions)", color='white')
            ax_hv_products.set_xlabel("Jumlah Pesanan", color='white')
            ax_hv_products.set_ylabel("Kategori Produk", color='white')
            ax_hv_products.grid(axis="x", linestyle="--", alpha=0.4)
            ax_hv_products.tick_params(axis='x', colors='white')
            ax_hv_products.tick_params(axis='y', colors='white')
            plt.tight_layout()
            st.pyplot(fig_hv_products)
            plt.close(fig_hv_products)
            st.markdown("""
            **Insight**: Pelanggan bernilai tinggi ('Champions') menunjukkan preferensi yang kuat terhadap kategori produk tertentu seperti 'bed_bath_table', 'computers_accessories', dan 'furniture_decor'. Ini mengindikasikan bahwa produk rumah tangga, teknologi, dan dekorasi adalah daya tarik utama bagi segmen ini, memberikan peluang untuk penawaran yang ditargetkan.
            """
            )
        else:
            st.write("Tidak ada data untuk preferensi produk pelanggan bernilai tinggi dengan filter saat ini.")

    with st.expander("Distribusi Frekuensi Pembelian per Pelanggan"):
        st.subheader("Distribusi Frekuensi Pembelian per Pelanggan")
        fig_freq_dist, ax_freq_dist = plt.subplots(figsize=(10, 5))
        sns.histplot(customer_value_df["total_orders"], bins=30, ax=ax_freq_dist, color='orange')
        ax_freq_dist.set_title("Distribusi Jumlah Pesanan per Pelanggan", fontsize=12, color='white')
        ax_freq_dist.set_xlabel("Total Pesanan", fontsize=10, color='white')
        ax_freq_dist.set_ylabel("Jumlah Pelanggan", fontsize=10, color='white')
        ax_freq_dist.grid(axis='y', linestyle="--", alpha=0.6)
        ax_freq_dist.tick_params(axis='x', colors='white')
        ax_freq_dist.tick_params(axis='y', colors='white')
        plt.tight_layout()
        st.pyplot(fig_freq_dist)
        plt.close(fig_freq_dist)
        st.markdown("""
        **Insight**: Sebagian besar pelanggan memiliki frekuensi pembelian yang sangat rendah, seringkali hanya satu pesanan. Ini menunjukkan bahwa meskipun ada pelanggan dengan nilai transaksi tinggi, mereka tidak selalu melakukan pembelian berulang secara sering. Model bisnis ini cenderung berorientasi pada transaksi besar satu kali.
        """
        )

    with st.expander("Frekuensi vs Rata-rata Nilai Pesanan"):
        st.subheader("Frekuensi vs Rata-rata Nilai Pesanan")
        fig_freq_aov, ax_freq_aov = plt.subplots(figsize=(10, 6))
        sns.scatterplot(
            x="total_orders",
            y="avg_order_value",
            data=customer_value_df,
            alpha=0.5,
            ax=ax_freq_aov,
            color='gold'
        )
        ax_freq_aov.set_title("Frekuensi vs Rata-rata Nilai Pesanan", fontsize=12, color='white')
        ax_freq_aov.set_xlabel("Total Pesanan", fontsize=10, color='white')
        ax_freq_aov.set_ylabel("Rata-rata Nilai Pesanan (R$)", fontsize=10, color='white')
        ax_freq_aov.grid(axis='both', linestyle="--", alpha=0.6)
        ax_freq_aov.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
        ax_freq_aov.tick_params(axis='x', colors='white')
        ax_freq_aov.tick_params(axis='y', colors='white')
        plt.tight_layout()
        st.pyplot(fig_freq_aov)
        plt.close(fig_freq_aov)
        st.markdown("""
        **Insight**: Scatter plot mengkonfirmasi bahwa sebagian besar pelanggan memiliki frekuensi pesanan yang rendah (umumnya 1), tetapi dengan rentang nilai pesanan rata-rata yang bervariasi, termasuk beberapa outlier dengan nilai yang sangat tinggi. Ini menegaskan bahwa pelanggan bernilai tinggi tidak selalu merupakan pembeli yang sering, melainkan mereka yang melakukan pembelian besar pada satu atau sedikit kesempatan.
        """
        )

    with st.expander("Kompleksitas Pembayaran vs Nilai Pelanggan"):
        st.subheader("Kompleksitas Pembayaran vs Nilai Pelanggan")
        fig_payment_value_scatter, ax_payment_value_scatter = plt.subplots(figsize=(10, 6))
        sns.scatterplot(
            x="payment_types",
            y="total_spent",
            data=payment_customer_df,
            alpha=0.5,
            ax=ax_payment_value_scatter,
            color='lightblue'
        )
        ax_payment_value_scatter.set_title("Kompleksitas Pembayaran vs Nilai Pelanggan", fontsize=12, color='white')
        ax_payment_value_scatter.set_xlabel("Jumlah Jenis Pembayaran yang Digunakan", color='white')
        ax_payment_value_scatter.set_ylabel("Total Pengeluaran (R$)", color='white')
        ax_payment_value_scatter.grid(axis='both', linestyle="--", alpha=0.6)
        ax_payment_value_scatter.tick_params(axis='x', colors='white')
        ax_payment_value_scatter.tick_params(axis='y', colors='white')
        plt.tight_layout()
        st.pyplot(fig_payment_value_scatter)
        plt.close(fig_payment_value_scatter)
        st.markdown("""
        **Insight**: Tidak ada korelasi yang jelas antara jumlah jenis pembayaran yang digunakan dan total pengeluaran pelanggan. Pelanggan bernilai tinggi tidak cenderung menggunakan lebih banyak jenis pembayaran. Hal ini menunjukkan bahwa kompleksitas metode pembayaran bukan faktor pembeda signifikan untuk mengidentifikasi pelanggan bernilai tinggi.
        """
        )

elif selected_section == "Analisis RFM":
    st.header("4. Analisis RFM (Recency, Frequency, Monetary)")

    with st.expander("Distribusi Pelanggan Berdasarkan Segmen RFM"):
        st.subheader("Distribusi Pelanggan Berdasarkan Segmen RFM")
        rfm_segment_summary_df = (
            rfm_segmentation_df["Segment"]
            .value_counts(normalize=True)
            .mul(100)
            .round(1)
            .reset_index(name="Persentase (%)")
        )
        rfm_segment_summary_df = rfm_segment_summary_df.rename(columns={'index': 'Segment'})

        fig_rfm_dist, ax_rfm_dist = plt.subplots(figsize=(8, 5))
        sns.barplot(
            x="Segment",
            y="Persentase (%)",
            data=rfm_segment_summary_df,
            palette='viridis',
            hue="Segment",
            legend=False,
            ax=ax_rfm_dist
        )
        ax_rfm_dist.set_title("Distribusi Pelanggan Berdasarkan Segmen RFM", fontsize=12, color='white')
        ax_rfm_dist.set_xlabel("Segmen RFM", color='white')
        ax_rfm_dist.set_ylabel("Persentase Pelanggan (%)", color='white')
        ax_rfm_dist.tick_params(axis='x', rotation=30, colors='white')
        ax_rfm_dist.tick_params(axis='y', colors='white')
        ax_rfm_dist.set_ylim(0, rfm_segment_summary_df["Persentase (%)"].max() * 1.15) # Adjust ylim for labels
        for p in ax_rfm_dist.patches:
            percentage = f'{p.get_height():.1f}%'
            x = p.get_x() + p.get_width() / 2
            y = p.get_height()
            ax_rfm_dist.annotate(percentage, (x, y), ha='center', va='bottom', fontsize=8, color='white', xytext=(0, 5), textcoords='offset points')
        plt.tight_layout()
        st.pyplot(fig_rfm_dist)
        plt.close(fig_rfm_dist)
        st.markdown("""
        **Insight**: Segmen 'Others' dan 'At Risk' memiliki proporsi pelanggan terbesar, mengindikasikan sebagian besar basis pelanggan tidak aktif baru-baru ini atau berada dalam kelompok 'lain-lain'. Segmen 'Champions' dan 'New Customers' memiliki ukuran yang serupa, menunjukkan keseimbangan antara pelanggan terbaik dan yang baru diperoleh.
        """
        )

    with st.expander("Rata-rata Metrik RFM per Segmen"):
        st.subheader("Rata-rata Metrik RFM per Segmen")
        rfm_avg_metrics_readable_df = (
            rfm_segmentation_df
            .groupby("Segment")[["Recency", "Frequency", "Monetary"]]
            .mean()
            .round(2)
            .rename(columns={
                "Recency": "Avg Recency (Hari)",
                "Frequency": "Avg Frequency (Pesanan)",
                "Monetary": "Avg Monetary Value (R$)"
            })
            .sort_values("Avg Recency (Hari)", ascending=True)
            .reset_index()
        )

        fig_avg_rfm, axes_avg_rfm = plt.subplots(1, 3, figsize=(18, 5))

        sns.barplot(x="Segment", y="Avg Recency (Hari)", data=rfm_avg_metrics_readable_df, palette="Blues_r", hue="Segment", legend=False, ax=axes_avg_rfm[0])
        axes_avg_rfm[0].set_title("Rata-rata Recency", fontsize=12, color='white')
        axes_avg_rfm[0].set_xlabel("Segmen RFM", color='white')
        axes_avg_rfm[0].set_ylabel("Hari Sejak Pembelian Terakhir", color='white')
        axes_avg_rfm[0].tick_params(axis='x', colors='white')
        axes_avg_rfm[0].tick_params(axis='y', colors='white')
        for p in axes_avg_rfm[0].patches:
            axes_avg_rfm[0].annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2, p.get_height()), ha="center", va="bottom", fontsize=8, color='white')

        sns.barplot(x="Segment", y="Avg Frequency (Pesanan)", data=rfm_avg_metrics_readable_df, palette="Greens_r", hue="Segment", legend=False, ax=axes_avg_rfm[1])
        axes_avg_rfm[1].set_title("Rata-rata Frekuensi", fontsize=12, color='white')
        axes_avg_rfm[1].set_xlabel("Segmen RFM", color='white')
        axes_avg_rfm[1].set_ylabel("Jumlah Pesanan", color='white')
        axes_avg_rfm[1].tick_params(axis='x', colors='white')
        axes_avg_rfm[1].tick_params(axis='y', colors='white')
        for p in axes_avg_rfm[1].patches:
            axes_avg_rfm[1].annotate(f"{p.get_height():.1f}", (p.get_x() + p.get_width() / 2, p.get_height()), ha="center", va="bottom", fontsize=8, color='white')

        sns.barplot(x="Segment", y="Avg Monetary Value (R$)", data=rfm_avg_metrics_readable_df, palette="Oranges_r", hue="Segment", legend=False, ax=axes_avg_rfm[2])
        axes_avg_rfm[2].set_title("Rata-rata Nilai Moneter", fontsize=12, color='white')
        axes_avg_rfm[2].set_xlabel("Segmen RFM", color='white')
        axes_avg_rfm[2].set_ylabel("Pengeluaran Rata-rata (R$)", color='white')
        axes_avg_rfm[2].tick_params(axis='x', colors='white')
        axes_avg_rfm[2].tick_params(axis='y', colors='white')
        for p in axes_avg_rfm[2].patches:
            axes_avg_rfm[2].annotate(f"{p.get_height():,.0f}", (p.get_x() + p.get_width() / 2, p.get_height()), ha="center", va="bottom", fontsize=8, color='white')

        plt.tight_layout()
        st.pyplot(fig_avg_rfm)
        plt.close(fig_avg_rfm)
        st.markdown("""
        **Insight**: Pelanggan 'Champions' memiliki Recency terendah (paling baru berbelanja) dan Monetary tertinggi, menjadikannya pelanggan paling berharga. 'New Customers' juga memiliki Recency rendah tetapi Frequency rendah, menunjukkan potensi pertumbuhan. 'At Risk' memiliki Recency tinggi, tetapi Frequency dan Monetary moderat, memerlukan strategi re-engagement.
        """
        )

    with st.expander("Rata-rata Skor Ulasan per Segmen RFM"):
        st.subheader("Rata-rata Skor Ulasan per Segmen RFM")
        rfm_review_scores_filtered = (
            master_orders_df
            .groupby("Segment", as_index=False)["review_score"]
            .mean()
            .round(2)
            .sort_values("review_score", ascending=False)
        )
        fig_rfm_review, ax_rfm_review = plt.subplots(figsize=(11, 6))
        sns.barplot(
            data=rfm_review_scores_filtered,
            x="Segment",
            y="review_score",
            palette="viridis",
            hue="Segment",
            legend=False,
            ax=ax_rfm_review
        )
        ax_rfm_review.set_title("Rata-rata Skor Ulasan per Segmen RFM", fontsize=15, weight="bold", color='white')
        ax_rfm_review.set_xlabel("Segmen RFM", fontsize=12, color='white')
        ax_rfm_review.set_ylabel("Rata-rata Skor Ulasan", fontsize=12, color='white')
        ax_rfm_review.set_ylim(0, 5) # Ensure y-axis doesn't go below 0
        ax_rfm_review.grid(axis="y", linestyle="--", alpha=0.4)
        ax_rfm_review.tick_params(axis='x', colors='white')
        ax_rfm_review.tick_params(axis='y', colors='white')
        for p in ax_rfm_review.patches:
            ax_rfm_review.annotate(
                f"{p.get_height():.2f}",
                (p.get_x() + p.get_width() / 2, p.get_height()),
                ha="center", va="bottom", fontsize=10, xytext=(0, 5), textcoords="offset points", color='white'
            )
        plt.tight_layout()
        st.pyplot(fig_rfm_review)
        plt.close(fig_rfm_review)
        st.markdown("""
        **Insight**: Segmen 'Champions' dan 'New Customers' menunjukkan skor ulasan rata-rata tertinggi, yang diharapkan karena mereka adalah pelanggan paling terlibat atau baru. Menariknya, 'Loyal Customers' memiliki skor terendah di antara segmen yang dikategorikan, menunjukkan bahwa loyalitas tidak selalu berarti kepuasan puncak dan memerlukan investigasi lebih lanjut.
        """
        )

    with st.expander("Distribusi Geografis Segmen RFM (Top Negara Bagian)"):
        st.subheader("Distribusi Geografis Segmen RFM (Top Negara Bagian)")

        customer_geo_segment_counts = (
            master_orders_df.groupby(["customer_state", "Segment"])["customer_unique_id"]
            .nunique() # Count unique customers within each state-segment group
            .reset_index(name="Total Customers")
        )

        total_customers_per_state_geo = (
            master_orders_df.groupby("customer_state")["customer_unique_id"]
            .nunique()
            .reset_index(name="Total Customers in State")
        )

        customer_geo_segment_percent = customer_geo_segment_counts.merge(
            total_customers_per_state_geo, on="customer_state", how="left"
        )
        customer_geo_segment_percent["Segment Percentage (%)"] = (
            customer_geo_segment_percent["Total Customers"]
            / customer_geo_segment_percent["Total Customers in State"]
            * 100
        ).round(2)

        top_10_states = (
            total_customers_per_state_geo
            .sort_values("Total Customers in State", ascending=False)
            .head(10)["customer_state"]
        )

        pivoted_data_percent = (
            customer_geo_segment_percent[
                customer_geo_segment_percent["customer_state"].isin(top_10_states)
            ]
            .pivot_table(
                index="customer_state",
                columns="Segment",
                values="Segment Percentage (%)",
                fill_value=0
            )
            .loc[top_10_states]
        )

        fig_geo_segment, ax_geo_segment = plt.subplots(figsize=(14, 8))
        pivoted_data_percent.plot(
            kind="bar",
            stacked=True,
            colormap="crest",
            edgecolor="white",
            ax=ax_geo_segment
        )

        for container in ax_geo_segment.containers:
            for i, patch in enumerate(container.patches):
                height = patch.get_height()
                # Adjust text position for better visibility inside or just outside bars
                if height > 5: # Threshold for displaying label
                    x = patch.get_x() + patch.get_width() / 2
                    y = patch.get_y() + height / 2
                    ax_geo_segment.text(x, y, f'{height:.1f}%',
                                        ha='center', va='center', fontsize=7, color='white',
                                        rotation=90 if height < 10 else 0)

        ax_geo_segment.set_title("Komposisi Segmen RFM di 10 Negara Bagian Teratas", fontsize=15, weight="bold", color='white')
        ax_geo_segment.set_xlabel("Negara Bagian Pelanggan", fontsize=12, color='white')
        ax_geo_segment.set_ylabel("Distribusi Pelanggan (%)", fontsize=12, color='white')
        ax_geo_segment.tick_params(axis='x', colors='white')
        ax_geo_segment.tick_params(axis='y', colors='white')
        ax_geo_segment.grid(axis="y", linestyle="--", alpha=0.5)

        ax_geo_segment.legend(title="Segmen RFM", bbox_to_anchor=(1.02, 1), loc="upper left", title_fontsize='medium', facecolor='black', edgecolor='white', labelcolor='white')
        plt.tight_layout()
        st.pyplot(fig_geo_segment)
        plt.close(fig_geo_segment)
        st.markdown("""
        **Insight**: Sao Paulo (SP) secara konsisten memiliki jumlah pelanggan tertinggi di seluruh segmen RFM. Distribusi proporsional segmen RFM relatif konsisten di negara bagian teratas, menunjukkan pola perilaku pelanggan yang serupa di wilayah utama. Ini memberikan peluang untuk kampanye regional yang tertarget, misalnya, fokus pada re-engagement di wilayah dengan proporsi pelanggan 'At Risk' yang lebih tinggi.
        """
        )

elif selected_section == "Kesimpulan Utama Analisis":
    st.header("4. Kesimpulan Utama Analisis")

    with st.expander("Kesimpulan Pertanyaan Bisnis 1: Faktor apa saja yang paling berpengaruh terhadap kepuasan pelanggan (review score) pada platform e-commerce?"):
        st.subheader("Kesimpulan Pertanyaan Bisnis 1: Faktor apa saja yang paling berpengaruh terhadap kepuasan pelanggan (review score) pada platform e-commerce?")
        st.markdown("""
        Faktor-faktor utama yang paling berpengaruh terhadap kepuasan pelanggan, sebagaimana tercermin dari `review_score`, adalah:

        1.  **Waktu Pengiriman (`delivery_time_days`)**: Ini adalah faktor paling dominan dengan korelasi negatif yang kuat. Semakin lama waktu pengiriman, semakin rendah `review_score` yang diberikan pelanggan. Pesanan dengan skor 1.0 memiliki rata-rata waktu pengiriman terlama (sekitar 21 hari), sedangkan skor 5.0 memiliki rata-rata waktu pengiriman tercepat (sekitar 10 hari).
        2.  **Status Pesanan (`order_status`)**: Status pesanan secara langsung memengaruhi kepuasan. Pesanan yang dibatalkan (`canceled`) atau tidak tersedia (`unavailable`) menghasilkan `review_score` yang sangat rendah atau tidak ada. Sebaliknya, pesanan yang berhasil terkirim (`delivered`) memiliki rata-rata `review_score` yang jauh lebih tinggi.
        3.  **Kategori Produk (`product_category_name_english`)**: Terdapat variasi kepuasan yang signifikan antar kategori. Kategori seperti `cds_dvds_musicals` dan `fashion_childrens_clothes` memiliki skor tinggi, sedangkan `security_and_services` dan `office_furniture` cenderung memiliki skor rendah.
        4.  **Lokasi Pelanggan (`customer_state`)**: Ada perbedaan geografis dalam kepuasan pelanggan, menunjukkan bahwa faktor regional (misalnya, logistik atau ketersediaan produk) mungkin berperan. Negara bagian seperti AP, AM, dan PR menunjukkan skor ulasan rata-rata yang lebih tinggi, sementara RR, AL, dan MA memiliki skor yang lebih rendah.

        Faktor-faktor seperti total harga produk, ongkos kirim (dalam batas normal), jumlah item, jumlah penjual unik, dan jumlah metode pembayaran tidak menunjukkan korelasi kuat atau pola signifikan dengan `review_score`.
        """
        )

    with st.expander("Kesimpulan Pertanyaan Bisnis 2: Karakteristik pelanggan seperti apa yang memberikan nilai transaksi tertinggi, dan bagaimana pola perilaku belanjanya?"):
        st.subheader("Kesimpulan Pertanyaan Bisnis 2: Karakteristik pelanggan seperti apa yang memberikan nilai transaksi tertinggi, dan bagaimana pola perilaku belanjanya?")
        st.markdown("""
        Pelanggan dengan nilai transaksi tertinggi (segmen 'High Value' atau kontributor pendapatan terbesar dalam RFM seperti 'At Risk' dan 'Champions') memiliki karakteristik dan pola perilaku belanja sebagai berikut:

        1.  **Karakteristik Pelanggan Bernilai Transaksi Tertinggi**:
            *   **Nilai Pesanan Rata-rata Tinggi**: Mereka dicirikan oleh nilai rata-rata pesanan (`avg_order_value`) yang sangat tinggi, bukan oleh frekuensi pembelian yang sering. Pelanggan 'High Value' memiliki rata-rata pengeluaran dan nilai pesanan yang jauh lebih tinggi dibandingkan segmen lainnya.
            *   **Kontribusi Pendapatan Signifikan**: Segmen 'At Risk' dan 'Champions' adalah kontributor pendapatan terbesar, menunjukkan bahwa pelanggan yang berisiko (dulunya aktif) dan pelanggan juara adalah kunci bagi total pendapatan.

        2.  **Pola Perilaku Belanja**:
            *   **Frekuensi Pembelian Rendah**: Sebagian besar pelanggan, termasuk yang bernilai tinggi, adalah pembeli tunggal atau memiliki frekuensi pembelian yang sangat rendah (`total_orders` rata-rata mendekati 1). Ini mengindikasikan model bisnis yang lebih mengarah pada transaksi besar satu kali daripada pembelian berulang yang sering.
            *   **Preferensi Produk Spesifik**: Pelanggan bernilai tinggi menunjukkan preferensi yang jelas terhadap kategori produk tertentu. Kategori teratas yang sering dibeli oleh mereka adalah `bed_bath_table`, `computers_accessories`, `furniture_decor`, `health_beauty`, dan `watches_gifts`.
            *   **Konsentrasi Geografis**: Pelanggan bernilai tinggi, seperti semua segmen RFM, terkonsentrasi di wilayah geografis tertentu, terutama Sao Paulo (SP), yang merupakan pasar utama dengan kontribusi pendapatan tertinggi.
            *   **Kompleksitas Pembayaran Tidak Signifikan**: Tidak ada korelasi signifikan antara jumlah jenis pembayaran yang digunakan (`payment_types`) dan total pengeluaran, menunjukkan bahwa kompleksitas pembayaran bukan pembeda untuk pelanggan bernilai tinggi.
        """
        )
