import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import numpy as np
import plotly.figure_factory as ff
from matplotlib import markers
from streamlit_option_menu import option_menu
from ta.volatility import BollingerBands
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
import datetime
from datetime import date
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score, mean_absolute_error

st.sidebar.info('SELAMAT DATANG (Versi Beta)')
st.title('ANALITIK SAHAM INDONESIA') 

def main():
    selected2 = option_menu(None, ["Home", "Data Emiten", "Screener", 'Prediksi'], icons=['house', 'file-earmark-text', 'sliders2-vertical', 'graph-up-arrow'], menu_icon="cast", default_index=0, orientation="horizontal")
    if selected2 == 'Data Emiten':
         dataframe()
    elif selected2 == 'Screener':
         #st.write('Penyaringan Saham (Tahap Pengembangan)')
         screener()
    elif selected2 == 'Prediksi':
         predict()
    else:
         tech_indicators()

#Halaman Utama
@st.cache_resource
def download_data(op, start_date, end_date):
    df = yf.download(op, start=start_date, end=end_date, progress=False)
    return df

#AMBIL KODE EMITEN DARI CSV

## Load the data
dataemiten = pd.read_csv('kodesaham.csv').sort_values('Kode')
 
## Get the list of countries
emiten = dataemiten['Kode'] + ' | ' + dataemiten['Nama Perusahaan']

 
## Create the select box
selected_emiten = st.sidebar.selectbox('Pilih Emiten:', emiten)

 
## Display the filtered data
st.header(selected_emiten.split(' | ')[1])

option = selected_emiten.split(' | ')[0] + ".JK"


#ganti value None
def ceknon(x):
    if x is not None:
       x = round(x,2)*100
       x = int(x)
       return x
    else:
       st.error('This is an error', icon="🚨")
        
#Display Persentil
detil = yf.Ticker(option)
L52 = detil.info['fiftyTwoWeekLow']
H52 = detil.info['fiftyTwoWeekHigh']
C = detil.info['currentPrice']
D = (H52-L52)/100 #format(1234, "8.,1f") 
P = (C - L52)/D
st.subheader(f"Harga terkini Rp{format(int(C),',d')}.- berada pada level {int(P)} dari skala 100", divider="rainbow")
om  = detil.info['operatingMargins']
dev = detil.info['payoutRatio']
roe = detil.info['returnOnEquity']

st.subheader(f"MarginOps : {ceknon(om)}%, DevPR : {ceknon(dev)}%, ROE : {ceknon(roe)}%", divider="rainbow")
st.info('Untuk jangka panjang perlu diperhatikan kisaran level harga kurang dari 10')


#Proses sidebar data
option = option.upper()
today = datetime.date.today()
duration = st.sidebar.number_input('Durasi Hari', value=1000)
before = today - datetime.timedelta(days=duration)
start_date = st.sidebar.date_input('Tanggal Awal', value=before)
end_date = st.sidebar.date_input('Tanggal Akhir', today)
if st.sidebar.button('Proses'):
    if start_date < end_date:
        st.sidebar.success('Tanggal Awal: `%s`\n\nTanggal Akhir: `%s`' %(start_date, end_date))
        download_data(option, start_date, end_date)
    else:
        st.sidebar.error('Terdapat Kesalahan: Tanggal akhir harus ditulis setelah tanggal awal')




data = download_data(option, start_date, end_date)
scaler = StandardScaler()

def tech_indicators():
    st.header('Teknikal Indikator')
    option = st.radio('Pilih Teknikal Indikator', ['Close', 'BB', 'MACD', 'RSI', 'EMA'])

    # Bollinger bands
    bb_indicator = BollingerBands(data.Close)
    bb = data
    bb['bb_h'] = bb_indicator.bollinger_hband()
    bb['bb_l'] = bb_indicator.bollinger_lband()
    # Creating a new dataframe
    bb = bb[['Close', 'bb_h', 'bb_l']]
    # MACD
    macd = MACD(data.Close).macd()
    # RSI
    rsi = RSIIndicator(data.Close).rsi()
    # SMA
    #sma = SMAIndicator(data.Close, window=14).sma_indicator()
    # EMA
    ema = EMAIndicator(data.Close).ema_indicator()

    if option == 'Close':
        st.write('Close Price')
        st.line_chart(data.Close)
    elif option == 'BB':
        st.write('BollingerBands')
        st.line_chart(bb)
    elif option == 'MACD':
        st.write('Moving Average Convergence Divergence')
        st.line_chart(macd)
    elif option == 'RSI':
        st.write('Relative Strength Indicator')
        st.line_chart(rsi)
    #elif option == 'SMA':
        #st.write('Simple Moving Average')
        #st.line_chart(sma)
    else:
        st.write('Exponential Moving Average')
        st.line_chart(ema)
    
    st.bar_chart(data.Volume)


def dataframe():
    st.header('10 Data Terkini')
    st.dataframe(data.tail(10))



def predict():
    model = st.radio('Pilih Model Komputasi', ['LinearRegression', 'RandomForestRegressor', 'ExtraTreesRegressor', 'KNeighborsRegressor', 'XGBoostRegressor'])
    num = st.number_input('Prediksi harga saham beberapa hari ke depan?', value=5)
    num = int(num)
    if st.button('Prediksi Harga Saham'):
        if model == 'LinearRegression':
            engine = LinearRegression()
            model_engine(engine, num)
        elif model == 'RandomForestRegressor':
            engine = RandomForestRegressor()
            model_engine(engine, num)
        elif model == 'ExtraTreesRegressor':
            engine = ExtraTreesRegressor()
            model_engine(engine, num)
        elif model == 'KNeighborsRegressor':
            engine = KNeighborsRegressor()
            model_engine(engine, num)
        else:
            engine = XGBRegressor()
            model_engine(engine, num)


def model_engine(model, num):
    # getting only the closing price
    df = data[['Close']]
    # shifting the closing price based on number of days forecast
    df['preds'] = data.Close.shift(-num)
    # scaling the data
    x = df.drop(['preds'], axis=1).values
    x = scaler.fit_transform(x)
    # storing the last num_days data
    x_forecast = x[-num:]
    # selecting the required values for training
    x = x[:-num]
    # getting the preds column
    y = df.preds.values
    # selecting the required values for training
    y = y[:-num]

    #spliting the data
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.2, random_state=7)
    # training the model
    model.fit(x_train, y_train)
    preds = model.predict(x_test)
    st.text(f'AKURASI  {round(r2_score(y_test, preds)*100)}%')
            #\nMAE: {round(mean_absolute_error(y_test, preds))}%')
    # predicting stock price based on the number of days
    forecast_pred = model.predict(x_forecast)
    day = 1
    for i in forecast_pred:
        st.text(f'Hari ke-{day}: {round(i)}')
        day += 1

#Screener Grafik Kuadran
def screener():
    #sektor = pd.read_csv('PersentilN.csv').sort_values('Industri')
    #sektor = sektor['Industri'].unique()
    screenlevel = st.selectbox('Pilih Level Saham:', ['Saham35Persen','Saham25Persen','Saham20Persen'])
    #screensektor = st.selectbox('Pilih Sektor:', sektor)
    st.subheader('Tabular Hasil Screener')
    scr1 = pd.read_csv('PersentilN.csv', usecols=["Kode","Current","P","OpMargin","DevPR","RoE"])
    scr1 = scr1.fillna(0)
    if screenlevel == 'Saham20Persen':
       st.write('Screener Saham Harga Lebih Dari 5000')
       scr1=scr1.query("Current > 5000 and P<=10 and OpMargin >= 0.1")
    elif screenlevel == 'Saham25Persen':
       st.write('Screener Saham Harga Kurang Dari 5000')
       scr1=scr1.query("Current > 200 and Current <= 5000 and P<=10 and OpMargin >= 0.1")
    else:
       st.write('Screener Saham Harga Rentang 50-200')
       scr1=scr1.query("Current > 50 and Current <= 200 and P<=10 and OpMargin >= 0.1")
    pd.options.display.float_format = '{:,.0f}'.format
    scr1 = scr1.rename(columns = {"Emiten":"Kode","Current": "Harga", "int(P)": "Level", "OpMargin": "Margin Operasi", "DevPR": "DevPR", "RoE": "ROE"}).sort_values(['Harga','Level'])
    scr1
    
if __name__ == '__main__':
    main()
    
st.sidebar.info("Desain Jonaben & modifikasi oleh DwiA")
