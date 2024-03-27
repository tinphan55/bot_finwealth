import math
from .models import *
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from data_source.models import *
from telegram import Bot
from django.db.models import F
from manage_bots.models import  *
import talib
import numpy as np
import requests
from bs4 import BeautifulSoup
from manage_bots.divergences import *
from django.db.models import Avg
from manage_bots.breakout import *
from manage_bots.tenisball import *



def date_filter_breakout_strategy(df, risk, date_filter, strategy):
    df = breakout_strategy_otmed(df, risk)
    df['milestone'] = np.where(df['signal']== 'buy',df['res'],0)
    df_signal = df.loc[(df['signal'] =='buy')&(df['close']>3), ['ticker','close', 'date', 'signal','milestone','param_ratio_cutloss','len_sideway']].sort_values('date', ascending=True)
    signal_today = df_signal.loc[pd.to_datetime(df_signal['date']).dt.date==date_filter].reset_index(drop=True)
    buy_today =[]
    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            data = {}
            data['strategy'] = strategy
            data['ticker'] = row['ticker']
            data['close'] = row['close']
            data['date'] = row['date']
            data['signal'] = 'Mua mới'
            data['milestone'] = row['milestone']
            data['ratio_cutloss'] = round(row['param_ratio_cutloss']*100,0)
            data['accumulation'] = row['len_sideway']
            signal_previous = Signal.objects.filter(ticker=data['ticker'],strategy=strategy ,is_closed =False ).order_by('-date').first()
            if signal_previous:
                data['signal'] = 'Tăng tỷ trọng'
            lated_signal = Signal.objects.filter(ticker=data['ticker'],strategy=strategy , date = date_filter).order_by('-date').first()
            #check nếu không có tín hiệu nào trước đó hoặc tín hiệu đã có nhưng ngược với tín hiệu hiện tại 
            if lated_signal is None:
                back_test= OverviewBacktest.objects.filter(ticker=data['ticker'],strategy=strategy).first()
                # fa = StockFundamentalData.objects.filter(ticker =data['ticker'] ).first()
                if back_test:
                    data['rating'] = back_test.rating_total
                    # data['fundamental'] = fa.fundamental_rating
                    if data['rating'] > 50:# and data['fundamental']> 50:
                        buy_today.append(data)
    # tạo lệnh mua tự động
    buy_today.sort(key=lambda x: x['rating'], reverse=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    for index, row in signal_today.iterrows():
           # gửi tín hiệu vào telegram
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tín hiệu {row['signal']} cp {row['ticker']}, chiến lược breakout" )   
    return buy_today





def date_filter_tenisball_strategy(df, risk, date_filter, strategy):
    df = tenisball_strategy_otmed(df, risk)
    df_signal = df.loc[(df['close']>3)&(df['signal']=='buy'), ['ticker','close', 'date','signal','param_ratio_cutloss']].sort_values('date', ascending=True)
    signal_today = df_signal.loc[pd.to_datetime(df_signal['date']).dt.date==date_filter].reset_index(drop=True)
    buy_today =[]
    if len(signal_today) > 0:
        for index, row in signal_today.iterrows():
            data = {}
            data['strategy'] = strategy
            data['accumulation'] = 0
            data['ticker'] = row['ticker']
            data['close'] = row['close']
            data['date'] = row['date']
            data['signal'] = 'Mua mới'
            data['ratio_cutloss'] = round(row['param_ratio_cutloss']*100,0)
            signal_previous = Signal.objects.filter(ticker=data['ticker'],strategy=strategy ,is_closed =False ).order_by('-date').first()
            if signal_previous:
                data['signal'] = 'Tăng tỷ trọng'
            lated_signal = Signal.objects.filter(ticker=data['ticker'],strategy=strategy , date = date_filter).order_by('-date').first()
            #check nếu không có tín hiệu nào trước đó hoặc tín hiệu đã có nhưng ngược với tín hiệu hiện tại 
            if lated_signal is None:
                back_test= OverviewBacktest.objects.filter(ticker=data['ticker'],strategy=strategy).first()
                if back_test:
                    data['rating'] = back_test.rating_total
                    if data['rating'] > 50:
                        buy_today.append(data)
    # tạo lệnh mua tự động
    buy_today.sort(key=lambda x: x['rating'], reverse=True)
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    for index, row in signal_today.iterrows():
           # gửi tín hiệu vào telegram
            bot.send_message(
                chat_id='-870288807', 
                text=f"Tín hiệu {row['signal']} cp {row['ticker']}, chiến lược tenisball" )   
    return buy_today


def detect_divergences(P=20, order=5, K=2):
    bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
    stock_source = StockPriceFilter.objects.values('ticker').annotate(avg_volume=Avg('volume'))
    stock_test= [ticker for ticker in stock_source if ticker['avg_volume'] > 100000]
    mesage =''
    for item in stock_test:
        stock_prices = StockPriceFilter.objects.filter(ticker=item['ticker']).values()
        df = pd.DataFrame(stock_prices)
        data = df.drop(columns=['id','date_time','open','low','high','volume'])
        data =  data.sort_values('date').reset_index(drop=True)
        df = RSIDivergenceStrategy(data, P, order, K)
        date_filter = datetime.today().date()
        df_today = df[(pd.to_datetime(df['date']).dt.date == date_filter) & (df['signal'] !='')]
        if len(df_today)>0:
            df_today = df_today[['ticker','signal']].reset_index(drop =True)
            mesage += f"Cổ phiếu {df_today['ticker'][0]} có tín hiệu {df_today['signal'][0]}"
        bot.send_message(
                chat_id='-870288807', 
                text=mesage)
    return mesage




def filter_stock_muanual( risk,strategy_1):
    print('đang chạy')
    strategy_breakout= StrategyTrading.objects.filter(name =strategy_1 , risk = risk).first()
    # strategy_tenisball= StrategyTrading.objects.filter(name =strategy_2 , risk = risk).first()
    now = datetime.today()
    date_filter = now.date()
    # Lấy ngày giờ gần nhất trong StockPriceFilter
    latest_update = StockPriceFilter.objects.all().order_by('-date').first().date_time
    # Tính khoảng thời gian giữa now và latest_update (tính bằng giây)
    time_difference = (now - latest_update).total_seconds()
    close_section = datetime(now.year, now.month, now.day, 15, 0, 0)  # Tạo thời điểm 15:00:00 cùng ngày
    open_section = datetime(now.year, now.month, now.day, 9, 0, 0)  # Tạo thời điểm 15:00:00 cùng ngày
    # Kiểm tra điều kiện để thực hiện hàm get_info_stock_price_filter()
    if 0 <= now.weekday() <= 4 and open_section <= now  and time_difference > 900:
        get_info_stock_price_filter()
        print('tải data xong')
    else:
        print('Không cần tải data')
    stock_prices = StockPriceFilter.objects.all().values()
    # lọc ra top cổ phiếu có vol>100k
    df = pd.DataFrame(stock_prices)  
    df['date']= pd.to_datetime(df['date']).dt.date
    # chuyển đổi df theo chiến lược
    breakout_buy_today = date_filter_breakout_strategy(df, risk, date_filter, strategy_breakout)
    # tenisball_buy_today = date_filter_tenisball_strategy(df, risk, date_filter, strategy_tenisball)
    buy_today = breakout_buy_today  #+tenisball_buy_today
    print('Cổ phiếu là:', buy_today)
    return buy_today
     


def filter_stock_daily(risk=0.03):
    strategy_1='Breakout ver 0.1'
    # strategy_2='Tenisball_ver0.1'
    buy_today = filter_stock_muanual(risk,strategy_1)#,strategy_2)
    date_filter = datetime.today().date() 
    # external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )
    num_stock = len(buy_today)
    max_signal = min(num_stock, 5)

    if max_signal >0:
        for ticker in buy_today[:max_signal]:
            price = StockPriceFilter.objects.filter(ticker = ticker['ticker']).order_by('-date').first().close
            cut_loss_price = round(price*(100-ticker['ratio_cutloss'])/100,2)
            take_profit_price = round(price*(1+ticker['ratio_cutloss']/100*2),2)
            try:
                created = Signal.objects.create(
                        ticker = ticker['ticker'],
                        close = ticker['close'],
                        date = ticker['date'],
                        # milestone =ticker['milestone'],
                        signal = ticker['signal'],
                        ratio_cutloss = round(ticker['ratio_cutloss'],2),
                        strategy = ticker['strategy'],
                        take_profit_price = take_profit_price,
                        cutloss_price =cut_loss_price,
                        exit_price = cut_loss_price,
                        rating_total = ticker['rating'],
                        # rating_fundamental = ticker['fundamental'] ,
                        accumulation = ticker['accumulation']
                    )
            
            except Exception as e:
                        pass
                   
    return 




