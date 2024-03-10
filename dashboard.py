# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 12:05:35 2024

@author: ASUS
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule = 'D', on='order_approved_at').agg({
        'order_id':'nunique',
        'payment_value':'sum'
        })
    
    daily_orders_df = daily_orders_df.reset_index()
    return daily_orders_df
   
    
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby('product_category_name_english').product_id.nunique().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_bystate_df(df):
    bystate_df = df.groupby(by='customer_state').customer_unique_id.nunique().sort_values(ascending=False).reset_index()
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by='customer_unique_id', as_index=False).agg({
        'order_approved_at':'max',
        'order_id':'nunique',
        'payment_value':'sum'
        })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df['max_order_timestamp'] = rfm_df['max_order_timestamp'].dt.date
    recent_date = df['order_approved_at'].dt.date.max()
    rfm_df['recency'] = rfm_df['max_order_timestamp'].apply(lambda x: (recent_date - x).days)
    rfm_df.drop('max_order_timestamp', axis=1, inplace=True)
    rfm_df = pd.DataFrame(rfm_df)
    return rfm_df

def create_monthly_df(df):
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    monthly_df = df.resample(rule='M', on='order_purchase_timestamp').agg({
        'order_id':'nunique',
        'payment_value':'sum'
        })
    
    monthly_df.index = monthly_df.index.strftime('%Y-%m')
    monthly_df = monthly_df.reset_index()
    
    last_sixmonths = monthly_df.iloc[-6:]
    return last_sixmonths
    

all_df = pd.read_csv('all_data.csv')

datetime_columns = ['order_approved_at','order_estimated_delivery_date']
all_df.sort_values(by='order_approved_at', inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])
    
min_date = all_df['order_approved_at'].min()
max_date = all_df['order_approved_at'].max()

with st.sidebar:
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
        )
    
main_df = all_df[(all_df['order_approved_at'] >= str(start_date)) &
                 (all_df['order_approved_at'] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)
rfm_df = pd.DataFrame(rfm_df)
last_sixmonths = create_monthly_df(main_df)


st.header('Brazilian E-Commerce Data Analysis')
st.subheader('Order Harian')

col1, col2 = st.columns(2)


with col1:
    total_orders = daily_orders_df.order_id.sum()
    st.metric('Total Pesanan', value=total_orders)
    
with col2:
    total_revenue = format_currency(daily_orders_df.payment_value.sum(), "BRL", locale='es_CO')
    st.metric('Total Revenue', value=total_revenue)

fig, ax = plt.subplots(figsize=(16,8))
ax.plot(
        daily_orders_df['order_approved_at'],
        daily_orders_df['order_id'],
        marker='o',
        linewidth=2,
        color='#90CAF9')

ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

st.subheader('Produk dengan Performa Terbaik dan Terburuk')

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35,15))

colors = ['#90CAF9', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3']

sns.barplot(x='product_id', y='product_category_name_english', data = sum_order_items_df.head(), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel('Jumlah Penjualan', fontsize=30)
ax[0].set_title('Produk dengan Performa Terbaik', loc='center', fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x='product_id', y='product_category_name_english',data=sum_order_items_df.sort_values(by='product_id', ascending=True).head(), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel('Jumlah Penjualan', fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position('right')
ax[1].yaxis.tick_right()
ax[1].set_title('Produk dengan Performa Terburuk', loc='center', fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

fig, ax = plt.subplots(figsize=(20,10))
colors = ['#90CAF9', '#D3D3D3', '#D3D3D3', '#D3D3D3', '#D3D3D3']
sns.barplot(
    x='customer_unique_id',
    y='customer_state',
    data=bystate_df.sort_values(by='customer_unique_id', ascending=False),
    palette=colors,
    ax=ax
 )

st.subheader('Jumlah Pelanggan Berdasarkan State')

ax.set_title('Jumlah Pelanggan Berdasarkan State', loc='center', fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader('Jumlah Pesanan Enam Bulan Terakhir')

fig = plt.figure(figsize=(10,5))
plt.plot(
    last_sixmonths['order_purchase_timestamp'],
    last_sixmonths['order_id'],
    marker = 'o',
    linewidth=3,
    color = '#00f6a8'
)
plt.title('Jumlah Pesanan 6 Bulan Terakhir', loc='center', fontsize=20)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
st.pyplot(fig)


st.subheader('Jumlah Pendapatan Enam Bulan Terakhir')
fig = plt.figure(figsize=(10,5))
plt.plot(
    last_sixmonths['order_purchase_timestamp'],
    last_sixmonths['payment_value'],
    marker='o',
    linewidth=3,
    color='#00f6a8'
)
plt.title('Jumlah Pendapatan 6 Bulan Terakhir', loc='center', fontsize=20)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

st.pyplot(fig)

st.subheader('Penilaian Parameter RFM')

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric('Rata-rata Recency (Hari)', value=avg_recency)
    
with col2:
    avg_frequency = round(rfm_df.frequency.mean(),2)
    st.metric('Rata-rata Frequency', value=avg_frequency)
    
with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), 'BRL', locale='es_CO')
    st.metric('Rata-rata Monetary', value=avg_monetary)
