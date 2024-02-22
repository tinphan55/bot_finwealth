import math
from django.db.models import Avg
import sys
from itertools import product
import numpy as np
from datetime import datetime, timedelta
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd
import matplotlib.pyplot as plt
import backtrader.analyzers as btanalyzers
from django.shortcuts import render
from statistics import mean
from data_source.models import *
from data_source.function import *
import numpy as np
from .models import *
import talib

risk =0.03

def add_test_value(group):
    group['tsi'] = np.where(
        (group['close'] > group['res'].shift(-1)),
        group['sup'],
        np.where(
            (group['close'] < group['sup'].shift(-1)),
            group['res'],
            np.nan
        ))
    return group

def calculate_sma(group):
    return group['close'].rolling(window=group['param_sma']).mean()

def accumulation_model(ticker, period=5):
    stock_prices = StockPriceFilter.objects.filter(ticker =ticker).values()
    df = pd.DataFrame(stock_prices) 
    df = df.sort_values(by='date', ascending=True).reset_index(drop=True)
    # Tính toán đường trung bình động với số điểm dữ liệu window
    df['sma'] = talib.EMA(df['close'], timeperiod=period)
    #Tính toán độ dốc của đường trung bình động
    df['gradients'] = np.gradient(df['sma'])
    df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
    gradients = df['gradients'].to_numpy()
    # Xác định mô hình tích lũy
    len_sideway =[]
    for item in gradients[1:]:
        sideway=True
        if item >0.1 or item <-0.1:
            sideway= False
            break
        else:
            len_sideway.append(item)
    return len(len_sideway)


def accumulation_model_df(df):
    df = df.sort_values(by=['ticker', 'date'], ascending=True).reset_index(drop=True)
    df['ema'] = df.groupby('ticker')['close'].transform(lambda x: talib.EMA(x, timeperiod=5))
    ema_counts = df.groupby("ticker")["ema"].count()
    tickers_with_4_ema_rows = ema_counts[ema_counts <= 4].index.tolist()
    df= df[~df['ticker'].isin(tickers_with_4_ema_rows)]
    df['gradients'] = df.groupby('ticker')['ema'].transform(lambda x: np.gradient(x))
    df['len_sideway'] = 0
    threshold = 0.1
    current_ticker = None
    current_count = 0
    for index, row in df.iterrows():
        if current_ticker != row['ticker']:
            current_ticker = row['ticker']
            current_count = 0  
            limit_count = 0
        if abs(row['gradients']) > threshold:
            limit_count += 1
        else:            
            current_count += 1
        if limit_count > 2:
            current_count = 0
            limit_count = 0
        df.at[index, 'len_sideway'] = current_count
    return df


def breakout_strategy_otmed(df, risk):
    strategy= StrategyTrading.objects.filter(name = 'Breakout ver 0.1', risk = risk).first()
    period = strategy.period
    num_raw =period + 5
    backtest = ParamsOptimize.objects.filter(strategy = strategy).values('ticker','param1','param2','param3','param4','param5','param6')
    df_param = pd.DataFrame(backtest)
    df['mean_vol'] = df.groupby('ticker')['volume'].transform('mean')
    df =df.loc[df['mean_vol']>50000].reset_index(drop=True)
    df = df.drop(['id', 'mean_vol'], axis=1)
    df['param_sma'] = df['ticker'].map(df_param.set_index('ticker')['param5'])
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0) & (df['volume'] == 0) | pd.isna(df['param_sma'])].index)
    df = accumulation_model_df(df)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df =df.reset_index(drop =True)
    df['param_multiply_volumn'] = df['ticker'].map(df_param.set_index('ticker')['param1'])
    df['param_change_day'] = df['ticker'].map(df_param.set_index('ticker')['param3'])
    df['param_rate_of_increase'] = df['ticker'].map(df_param.set_index('ticker')['param2'])
    df['param_ratio_cutloss'] = df['ticker'].map(df_param.set_index('ticker')['param4'])
    df['param_len_sideway'] = df['ticker'].map(df_param.set_index('ticker')['param6'])
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    df['sma'] = df.groupby('ticker').apply(
        lambda x: x['close'][::-1].rolling(window=x['param_sma'].astype(int).values[0]).mean()[::-1]).reset_index(drop=True)
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    buy = (df['close'] > 5) & (df['close'] > df['sma']) & (df['close'] > df['tsi']) & (df['volume'] > df['mavol']*df['param_multiply_volumn']) &  (df['mavol'] > 100000) & (df['high']/df['close']-1 < df['param_rate_of_increase']) & (df['close']/df['pre_close']-1 > df['param_change_day']) &(df['len_sideway']> df['param_len_sideway'])
    # cut_loss = df['close'] <= df['close']*(1-df['param_ratio_cutloss'])
    df['signal'] = np.where(buy, 'buy', 'newtral')
    return df


def breakout_strategy(df, period, num_raw=None):
    df = df.drop(df[(df['open'] == 0) & (df['close'] == 0)& (df['volume'] == 0)].index)
    df = accumulation_model_df(df)
    df = df.groupby('ticker', group_keys=False).apply(lambda x: x.sort_values('date', ascending=False).head(num_raw) if num_raw is not None else x.sort_values('date', ascending=False))
    df['res'] = df.groupby('ticker')['high'].transform(lambda x: x[::-1].rolling(window=period).max()[::-1])
    df['sup'] = df.groupby('ticker')['low'].transform(lambda x: x[::-1].rolling(window=period).min()[::-1])
    df['mavol'] = df.groupby('ticker')['volume'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df['sma'] = df.groupby('ticker')['close'].transform(lambda x: x[::-1].rolling(window=period).mean()[::-1])
    df = df.groupby('ticker', group_keys=False).apply(add_test_value)
    df['tsi'].fillna(method='ffill', inplace=True)
    df['pre_close'] = df.groupby('ticker')['close'].shift(-1)
    df['len_sideway'] = df.groupby('ticker')['len_sideway'].shift(-1)
    return df


def custom_date_parser(date_string):
      return pd.to_datetime(date_string, format='%Y-%m-%d')


# Can chinh lai xac dinh ngay khong giao dich
def define_stock_date_to_sell(buy_date, days=2):
    next_trading_date = None
    t_date = buy_date + timedelta(days=days)
    # Tính ngày kết thúc
    end_date = buy_date + timedelta(days=10)
    # Lấy tất cả các ngày giao dịch từ buy_date đến end_date và sắp xếp theo thứ tự tăng dần
    trading_dates = DateTrading.objects.filter(date__gt=t_date, date__lte=end_date).order_by('date')
    # Kiểm tra nếu có ngày giao dịch tiếp theo
    if trading_dates.exists():
        next_trading_date = trading_dates.first().date
    return next_trading_date


dict_params = {
        'multiply_volumn': 2,
        'rate_of_increase': 0.03,
        'change_day': 0.015,
        'risk': 0.03,
        'ratio_cutloss':0.05,
        'sma':20,
        'len_sideway':5,
            }



# df = pd.read_csv('test.csv', parse_dates=['date'], date_parser=custom_date_parser)
# test chiến lược

class PandasData(btfeed.PandasData):
    lines = ('tsi', 'mavol','pre_close','len_sideway' )  
    params = (
        ('datetime', 'date_time'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('tsi', 'tsi'),
        ('mavol', 'mavol'),
        ('pre_close', 'pre_close'),
        ('len_sideway','len_sideway'),

    )

class definesize(bt.Sizer):
    params = (
        ('risk', dict_params['risk']),
        ('ratio_cutloss',dict_params['ratio_cutloss']),
        ('retint', False),  # return an int size or rather the float value
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            risk1R = data.open[1]*self.params.ratio_cutloss
            size = math.floor(int(cash* self.params.risk/ risk1R))
        else:
            size = position.size

        if self.p.retint:
            size = math.floor(int(size))
        return size

class breakout_otm(bt.SignalStrategy):
    params = (
        ('multiply_volumn',dict_params['multiply_volumn'] ),
        ('rate_of_increase', dict_params['rate_of_increase'] ), # tăng so với phiên trước đó
        ('change_day', dict_params['change_day'] ),#thay đổi giữa giá đóng cửa và giá cao nhất
        ('risk', dict_params['risk']),
        ('ratio_cutloss',dict_params['ratio_cutloss'] ),
        ('sma',dict_params['sma'] ),
        ('len_sideway',dict_params['len_sideway'] )
    )
    def __init__(self, ticker, save_deal, strategy):
        #khai báo biến
        self.ticker = ticker
        self.save_deal = save_deal
        self.strategy = strategy
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=int(self.params.sma))
        self.trailing_sl = None  # Biến đồng hồ để lưu giá trị stop loss
        self.trailing_tp =None
        #điều kiện buy
        self.buy_price1 = self.data.close > self.data.tsi
        self.buy_vol = self.data.volume > self.data.mavol*self.params.multiply_volumn
        self.buy_minvol =self.data.mavol > 100000
        self.buy_price2 = self.data.high/self.data.close-1 < self.params.change_day
        self.buy_price3 = self.data.close/self.data.pre_close-1 > self.params.rate_of_increase
        self.buy_price4= self.data.close > self.sma
        self.buy_price5 = self.data.len_sideway >= self.params.len_sideway
        #plot view
        tsi = bt.indicators.SimpleMovingAverage(self.data.tsi, period=1)
        tsi.plotinfo.plotname = 'tsi'
    
    def next(self):
        if len(self.data)>2:
            if not self.position:
                if self.buy_price1 == True and self.buy_vol==True and self.buy_minvol==True and self.buy_price2 == True and self.buy_price3 ==True and self.buy_price4 ==True:
                    self.buy()
                    self.nav= self.broker.getcash()
                    self.R = self.nav*self.params.risk
                    self.buy_price = self.data.open[1]
                    self.qty = self.sizer.getsizing(data=self.data, isbuy=True)
                    self.buy_date =datetime.fromordinal(int(self.data.datetime[1]))
                    self.trailing_offset= self.buy_price*self.params.ratio_cutloss 
                    self.trailing_sl = round(self.buy_price - self.trailing_offset,2)  # Đặt stop loss ban đầu
                    self.trailing_tp = round(self.buy_price + self.trailing_offset*2,2)   
            else:
                # Kiểm tra giá hiện tại có vượt quá trailing_sl không
                if self.data.close > self.trailing_tp:
                    self.trailing_sl = self.trailing_tp
                    self.trailing_tp = self.trailing_tp+self.trailing_offset
                if self.data.close < self.trailing_sl:
                    self.date_sell =datetime.fromordinal(int(self.data.datetime[1]))
                    if self.date_sell >= define_stock_date_to_sell(self.buy_date):
                        self.close()
                        if self.save_deal ==True:
                            self.sell_price =self.data.open[1]
                            data = {
                            'nav': round(self.nav,2),
                            'date_buy':self.buy_date,
                            'buy_price':self.buy_price,
                            'qty': math.floor(int(self.qty)),
                            'date_sell':self.date_sell,
                            'sell_price': self.sell_price,
                            'ratio_pln': round((self.sell_price-self.buy_price)*self.qty*100/self.nav,2),
                            'len_days': (self.date_sell-self.buy_date).days,
                            'stop_loss':round(self.trailing_sl,2),
                            'take_profit': round(self.trailing_tp,2),
                            }
                            obj, created = TransactionBacktest.objects.update_or_create(strategy=self.strategy, ticker=self.ticker,date_buy = self.buy_date, defaults=data)     
                        
        return     
    
    # #giao dịch sẽ lấy giá open của phiên liền sau đó (không phải giá đóng cửa)
    # def notify_trade(self, trade):
    #     date_open = self.data.datetime.datetime().strftime('%Y-%m-%d')
    #     date_close = self.data.datetime.datetime().strftime('%Y-%m-%d')
    #     if trade.justopened:
    #         print('----TRADE OPENED----')
    #         print(self.sma)
    #         print('Date: {}'.format(date_open))
    #         print('Price: {}'.format(trade.price))# cũng là print('Price: {}'.format(self.data.open[0]))
    #         print('Size: {}'.format(trade.size))
    #     elif trade.isclosed:
    #         print('----TRADE CLOSED----')
    #         print('Date: {}'.format(date_close))
    #         print('Price: {}'.format(self.data.open[0]))
    #         print('Profit, Gross {}, Net {}'.format(
    #                                             round(trade.pnl,2),
    #                                             round(trade.pnlcomm,2)))
    #     else:
    #         return 


def evaluate_strategy(params,nav,commission,size_class,data,strategy_class, ticker, strategy):
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(nav)  # Số dư ban đầu
    cerebro.broker.setcommission(commission=commission)  # Phí giao dịch (0.15%)
    #add the sizer
    cerebro.addsizer(size_class, risk=params[3],ratio_cutloss=params[4])
    cerebro.addstrategy(strategy_class, 
                        ticker, False,strategy,
                        multiply_volumn=params[0], 
                        rate_of_increase=params[1], 
                        change_day=params[2], 
                        risk=params[3],
                        ratio_cutloss=params[4],
                        sma = params[5],
                        len_sideway  =params[6],
                        )
    # Chạy backtest và tính toán chỉ số hiệu suất
    cerebro.run()
    # Trả về chỉ số hiệu suất muốn tối ưu (ví dụ: tổng lợi nhuận, tỷ lệ Sharpe, ...)
    return cerebro.broker.getvalue() 

def rating_stock(strategy_pk):
    total =RatingStrategy.objects.filter(strategy=strategy_pk).first()
    list_stock = OverviewBacktest.objects.filter(strategy=strategy_pk,total_trades__gt=0)
    if list_stock:
        min_hold = min(i.average_trades_per_day for i in list_stock)
        max_hold = max(i.average_trades_per_day for i in list_stock)
        min_deal = min(i.total_trades for i in list_stock)
        max_deal = max(i.total_trades for i in list_stock)
        for stock in list_stock:
            stock.rating_profit = round((stock.deal_average_pnl-total.min_ratio_pln)/(total.max_ratio_pln-total.min_ratio_pln)*50+50,2)
            stock.rating_win_trade = round((stock.win_trade_ratio-total.min_win_trade_ratio)/(total.max_win_trade_ratio-total.min_win_trade_ratio)*50+50,2)
            stock.rating_day_hold = round(100 - (stock.average_trades_per_day-min_hold)/(max_hold-min_hold)*50 ,2)
            rating_number_deal = round((stock.total_trades - min_deal)/(max_deal-min_deal)*50+50,2)
            # profit: 30%, number_deal: 40% wintrade:20%, dayhold: 10%
            stock.rating_total = round(stock.rating_profit*0.3 + stock.rating_win_trade*0.2 + stock.rating_day_hold*0.1+ rating_number_deal*0.4,2)
            stock.save()
    return

def define_stock_not_test(strategy):
    list_all = []
    list_runned = []
    stock = OverviewBacktest.objects.filter(strategy=strategy)
    stock_source = StockPriceFilter.objects.values('ticker').annotate(avg_volume=Avg('volume'))
    stock_test= [ticker for ticker in stock_source if ticker['avg_volume'] > 100000]
    for i in stock:
        list_runned.append(i.ticker)
    for i in stock_test:
        list_all.append(i['ticker'])
    result = list(set(list_all)-set(list_runned))
    return result
    


def run_backtest(risk, begin_list, end_list):
    strategy_data = {
        'name': 'Breakout ver 0.1',
        'risk': risk,   
        'nav': 10000000,
        'commission' : 0.0015,
        'period':20}
    created = StrategyTrading.objects.update_or_create(name=strategy_data['name'],risk = risk, defaults=strategy_data)
    strategy = StrategyTrading.objects.filter(name=strategy_data['name'],risk = risk).first()
    stock_source = StockPriceFilter.objects.values('ticker').annotate(avg_volume=Avg('volume'))
    stock_test= [ticker for ticker in stock_source if ticker['avg_volume'] > 100000]
    # stock_test = define_stock_not_test(strategy)
    list_bug =[]
    for item in stock_test[begin_list:end_list]:
        ticker = item['ticker']
        # ticker = item
        print('------đang chạy:', ticker)
        try:
            stock_prices = StockPrice.objects.filter(ticker=ticker).values()
            df = pd.DataFrame(stock_prices)
            df = breakout_strategy(df, strategy.period)
            df = df.drop(['id','res','sup','gradients','ema'], axis=1) 
            df = df.sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
            df = df.fillna(0.0001)
            data = PandasData(dataname=df)
            #Chạy tối ưu hóa param
            # Khởi tạo các giá trị tham số muốn tối ưu
            multiply_volumn_values = [x / 2 for x in range(2, 5)]
            rate_of_increase_values = [0.01, 0.02, 0.03]
            change_day_values = [0.015, 0.02,0.025,0.03]
            risk_values = [risk]   
            ratio_cutloss = [0.05,0.07,0.1]
            sma = [20,50] 
            len_sideway = [3,5,10]
            #####test
            # multiply_volumn_values = [x / 2 for x in range(2, 3)]
            # rate_of_increase_values = [0.01]  # tăng so với phiên trước đó
            # change_day_values = [0.015, 0.02] 
            # risk_values = [risk]
            # ratio_cutloss = [0.05,0.06]
            # sma =[20]
            # Tạo danh sách các giá trị tham số
            param_values = [multiply_volumn_values, rate_of_increase_values, change_day_values, risk_values, ratio_cutloss, sma,len_sideway]
            # Tạo tất cả các tổ hợp tham số
            param_combinations = list(product(*param_values))

            # Tìm giá trị tối ưu bằng Grid Search
            best_params = None
            best_performance = None
            list_param_bug = []
            for params in param_combinations:
                # print(params)
                params = tuple(float(param) for param in params)  # Chuyển đổi các giá trị tham số sang kiểu số thực
                try:
                    performance = evaluate_strategy(params,nav=strategy.nav,commission= strategy.commission,size_class = definesize,data= data,strategy_class = breakout_otm,ticker =  ticker, strategy=strategy)
                    if best_performance is None or performance > best_performance:
                        best_params = params
                        best_performance = performance  
                        # print('chay ok:',best_performance)              
                except Exception as e:
                    list_param_bug.append(params)
                    if len(list_param_bug)>20:
                        print(f"Có lỗi trong test kịch bản {list_param_bug}: {str(e)}")
                        break
            if best_params:
                params_data = {
                        'multiply_volumn': best_params[0],  # vốn ban đầu
                        'rate_of_increase': best_params[1],  # phí giao dịch
                        'change_day':best_params[2],
                        'ratio_cutloss':best_params[4],
                        'sma':best_params[5],
                        'len_sideway':best_params[6],
                }

                params_feild = {
                        'param1': best_params[4],  # cat lo
                        'param2': best_params[1],  # phí giao dịch
                        'param3':best_params[2],
                        'param4':best_params[0],
                        'param5':best_params[5],
                        'param6':best_params[6],
                }

                obj, created = ParamsOptimize.objects.update_or_create(strategy = strategy,ticker=ticker, defaults=params_feild)
                print('Đã tạo param')

                # Tạo một phiên giao dịch Backtrader mới
                cerebro = bt.Cerebro()
                # Thêm dữ liệu và chiến lược vào cerebro
                cerebro.adddata(data)
                # thêm chiến lược thông số đã được tối ưu
                cerebro.addstrategy(breakout_otm, ticker,True,strategy,
                                    multiply_volumn= params_data['multiply_volumn'], 
                                    rate_of_increase=params_data['rate_of_increase'], 
                                    change_day=params_data['change_day'], 
                                    risk= risk,
                                    ratio_cutloss = params_data['ratio_cutloss'],
                                    sma = params_data['sma'],
                                    len_sideway  =params_data['len_sideway'])

                
                # Thiết lập thông số về kích thước vốn ban đầu và phí giao dịch
                cerebro.broker.setcash(strategy.nav)  # Số dư ban đầu
                cerebro.broker.setcommission(commission=strategy.commission)  # Phí giao dịch (0.15%)
                
                #add the sizer
                cerebro.addsizer(definesize, risk=risk,ratio_cutloss=params_data['ratio_cutloss'])
                
                # Analyzer
                cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='overviews')
                cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe_ratio')
                cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
                # Chạy backtest
                result = cerebro.run()
                result = result[0]
                #Get final portfolio Value
                port_value = round(cerebro.broker.getvalue(), 0)
                ratio_pln = (port_value - strategy.nav) / strategy.nav
                drawdown = result.analyzers.drawdown.get_analysis()['drawdown']
                overview = result.analyzers.overviews.get_analysis()
                sharpe_ratio = result.analyzers.sharpe_ratio.get_analysis()['sharperatio']
                total_closed_test = overview.total.get('closed')
                list_trade = TransactionBacktest.objects.filter(ticker =ticker, strategy = strategy)
                if total_closed_test and sharpe_ratio and total_closed_test > 0:
                    overview_data = {
                        'ratio_pln': round(ratio_pln*100, 3),  # tỷ suất lợi nhuận
                        'drawdown': round(drawdown, 3),  # Tìm hiểu
                        'sharpe_ratio': round(sharpe_ratio, 3),  # tìm hiểu
                        'total_trades': overview.total.get('total'),  # tổng số deal
                        'total_open_trades': overview.total.get('open'),  # deal đang mở, chưa chốt
                        'total_closed_trades': overview.total.get('closed'),  # đang đã đóng
                        'win_trade_ratio':round(overview.won.get('total')*100/overview.total.get('total'),2),
                        # Chuỗi giao dịch liên tiếp
                        'won_current_streak': overview.streak.won.get('current'),
                        'won_longest_streak': overview.streak.won.get('longest'),
                        'lost_current_streak': overview.streak.lost.get('current'),
                        'lost_longest_streak': overview.streak.lost.get('longest'),
                        # Thống kê giao dịch thắng
                        'won_total_trades': overview.won.get('total'),
                        'won_total_pnl': round(sum(i.ratio_pln for i in list_trade if i.ratio_pln>0 ), 2),
                        'won_average_pnl': round(mean(i.ratio_pln for i in list_trade if i.ratio_pln>0 ), 2),
                        'won_max_pnl': max(i.ratio_pln for i in list_trade if i.ratio_pln>0 ),
                        'lost_total_trades': overview.lost.get('total'),
                        'lost_total_pnl': round(sum(i.ratio_pln for i in list_trade if i.ratio_pln<0 ), 2),
                        'lost_average_pnl': round(mean(i.ratio_pln for i in list_trade if i.ratio_pln<0 ), 2),
                        'lost_max_pnl': min(i.ratio_pln for i in list_trade if i.ratio_pln<0 ),
                        #thống kê giao dịch long (mua)
                            # 'total_long_trades': overview.long.get('total'),
                            # 'total_long_pnl': round(overview.long.pnl.get('total') / nav, 2),
                            # 'total_long_average_pnl': round(overview.long.pnl.get('average') / nav, 2),
                            # 'won_long_trades': overview.long.won,
                            # 'won_long_total_pnl': round(overview.long.pnl.won.get('total') / nav, 2),
                            # 'won_long_average_pnl': round(overview.long.pnl.won.get('average') / nav, 2),
                            # 'won_long_max_pnl': round(overview.long.pnl.won.get('max') / nav, 2),
                            # 'lost_long_trades': overview.long.lost,
                            # 'lost_long_total_pnl': round(overview.long.pnl.lost.get('total') / nav, 2),
                            # 'lost_long_average_pnl': round(overview.long.pnl.lost.get('average') / nav, 2),
                            # 'lost_long_max_pnl': round(overview.long.pnl.lost.get('max') / nav, 2),
                        #thống kê giao dịch short (bán khống)
                            # 'total_short_trades': overview.short.get('total'),
                            # 'total_short_pnl': overview.short.pnl.get('total'),
                            # 'total_short_average_pnl': round(overview.short.pnl.get('average') / nav, 2),
                            # 'won_short_total_pnl': round(overview.short.pnl.won.get('total'), 2),
                            # 'won_short_average_pnl': round(overview.short.pnl.won.get('average') / nav, 2),
                            # 'won_short_max_pnl': round(overview.short.pnl.won.get('max') / nav, 2),
                            # 'lost_short_total_pnl': round(overview.short.pnl.lost.get('total') / nav, 2),
                            # 'lost_short_average_pnl': round(overview.short.pnl.lost.get('average') / nav, 2),
                            # 'lost_short_max_pnl': round(overview.short.pnl.lost.get('max') / nav, 2),
                            # 'lost_short_trades': overview.short.lost,
                            # 'won_short_trades': overview.short.won,
                        #thống kê số ngày nắm giữ của giao dịch
                        'total_trades_length': overview.len.get('total'),
                        'average_trades_per_day': round(overview.len.get('average'), 2),
                        'max_trades_per_day': overview.len.get('max'),
                        'min_trades_per_day': overview.len.get('min'),
                        'total_won_trades_length': overview.len.won.get('total'),
                        'average_won_trades_per_day': round(overview.len.won.get('average'),2),
                        'max_won_trades_per_day': overview.len.won.get('max'),
                        'min_won_trades_per_day': overview.len.won.get('min'),
                        'total_lost_trades_length': overview.len.lost.get('total'),
                        'average_lost_trades_per_day': round(overview.len.lost.get('average'),2),
                        'max_lost_trades_per_day': overview.len.lost.get('max'),
                        'min_lost_trades_per_day': overview.len.lost.get('min'),
                        'deal_average_pnl': round(sum(i.ratio_pln for i in list_trade )/overview.total.get('closed'),2),
                    }
                    obj, created = OverviewBacktest.objects.update_or_create(strategy=strategy,ticker=ticker, defaults=overview_data)
                    print('Đã tạo thông số trade')
            else:
                    print('Không tạo được thông số trade tối ưu')
        except Exception as e:
                print(f"Có lỗi với cổ phiếu {ticker}: {str(e)}")
                list_bug.append({ticker:str(e)})
    # chạy tổng kết        
    detail_stock = OverviewBacktest.objects.filter(strategy=strategy,total_trades__gt=0)
    if detail_stock:
        total = {
            'ratio_pln':round(mean(i.ratio_pln for i in detail_stock),2),
            'deal_average_pnl': round(mean(i.deal_average_pnl for i in detail_stock),2),
            'max_ratio_pln': max(i.deal_average_pnl for i in detail_stock),
            'min_ratio_pln': min(i.deal_average_pnl for i in detail_stock),
            'drawdown':round(mean(i.drawdown for i in detail_stock),2),
            'sharpe_ratio': round(mean(i.sharpe_ratio for i in detail_stock),2),
            'total_trades': sum(i.total_trades for i in detail_stock),
            'total_open_trades': sum(i.total_open_trades for i in detail_stock),
            'win_trade_ratio': round(mean(i.win_trade_ratio for i in detail_stock), 2),
            'max_win_trade_ratio': max(i.win_trade_ratio for i in detail_stock),
            'min_win_trade_ratio': min(i.win_trade_ratio for i in detail_stock),
            'total_closed_trades': sum(i.total_closed_trades for i in detail_stock),
            'won_total_trades': sum(i.won_total_trades for i in detail_stock),
            'won_total_pnl': round(sum(i.won_total_pnl for i in detail_stock),2),
            'won_average_pnl': round(mean(i.won_average_pnl for i in detail_stock), 2),
            'won_max_pnl': max(i.won_max_pnl for i in detail_stock),
            'lost_total_trades': sum(i.lost_total_trades for i in detail_stock),
            'lost_total_pnl': round(sum(i.lost_total_pnl for i in detail_stock),2),
            'lost_average_pnl': round(mean(i.lost_average_pnl for i in detail_stock), 2),
            'lost_max_pnl': min(i.lost_max_pnl for i in detail_stock),
            'total_trades_length': round(mean(i.total_trades_length for i in detail_stock), 2),
            'average_trades_per_day': round(mean(i.average_trades_per_day for i in detail_stock), 2),
            'max_trades_per_day': max(i.max_trades_per_day for i in detail_stock),
            'min_trades_per_day': min(i.min_trades_per_day for i in detail_stock),
            'total_won_trades_length': round(mean(i.total_won_trades_length for i in detail_stock), 2),
            'average_won_trades_per_day': round(mean(i.average_won_trades_per_day for i in detail_stock), 2),
            'max_won_trades_per_day': max(i.max_won_trades_per_day for i in detail_stock),
            'min_won_trades_per_day': min(i.min_won_trades_per_day or sys.maxsize for i in detail_stock),
            'total_lost_trades_length': round(mean(i.total_lost_trades_length for i in detail_stock), 2),
            'average_lost_trades_per_day': round(mean(i.average_lost_trades_per_day for i in detail_stock), 2),
            'max_lost_trades_per_day': max(i.max_lost_trades_per_day or -sys.maxsize-1 for i in detail_stock),
            'min_lost_trades_per_day' : min(i.min_lost_trades_per_day or sys.maxsize   for i in detail_stock if i.min_lost_trades_per_day),
        }
        obj = RatingStrategy.objects.update_or_create(strategy=strategy, defaults=total)

    print('Đã tạo tổng kết chiến lược')
    rating_stock(strategy)
    print('Đã tạo điểm tổng hợp')
    
    return list_bug




def run_backtest_one_stock(ticker,risk):
    strategy = StrategyTrading.objects.filter(name='Breakout',risk = risk).first()
    strategy_data = {
        'name': 'Breakout',
        'risk': risk,   
        'nav': 10000000,
        'commission' : 0.0015,
        'period':20}
    stock_prices = StockPrice.objects.filter(ticker=ticker).values()
    df = pd.DataFrame(stock_prices)
    df = breakout_strategy(df, 20)
    df = df.drop(['id','res','sup'], axis=1) 
    df = df.sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
    df = df.fillna(0.0001)
    data = PandasData(dataname=df)
    # Khởi tạo các giá trị tham số muốn tối ưu
    multiply_volumn_values = [x / 2 for x in range(2, 5)]
    rate_of_increase_values = [0.01, 0.02, 0.03]
    change_day_values = [0.015, 0.02,0.025,0.03]
    risk_values = [risk]   
    ratio_cutloss = [0.05,0.07,0.1]
    sma = [20,50]
    #Thêm tối ưu hóa
    # Tạo danh sách các giá trị tham số
    param_values = [multiply_volumn_values, rate_of_increase_values, change_day_values, risk_values, ratio_cutloss,sma]
    # Tạo tất cả các tổ hợp tham số
    param_combinations = list(product(*param_values))

    # Tìm giá trị tối ưu bằng Grid Search
    best_params = None
    best_performance = None

    for params in param_combinations:
        params = tuple(float(param) for param in params)  # Chuyển đổi các giá trị tham số sang kiểu số thực
        try:
            performance = evaluate_strategy(params,nav=strategy.nav,commission= strategy.commission,size_class = definesize,data= data,strategy_class = breakout_otm,ticker =  ticker, strategy=strategy)
            if best_performance is None or performance > best_performance:
                best_params = params
                best_performance = performance   
                    
        except Exception as e:
                    print(f"Có lỗi với kịch bản {params}: {str(e)}")
        params_data = {
                    'multiply_volumn': best_params[0],  # vốn ban đầu
                    'rate_of_increase': best_params[1],  # phí giao dịch
                    'change_day':best_params[2],
                    'risk': best_params[3],
                    'ratio_cutloss':best_params[4],
                    'sma':best_params[5],
            }         
    
    # Tạo một phiên giao dịch Backtrader mới
    cerebro = bt.Cerebro()
    # Thêm dữ liệu và chiến lược vào cerebro
    cerebro.adddata(data)
    # thêm chiến lược thông số đã được tối ưu
    cerebro.addstrategy(breakout_otm, ticker,True,strategy,
                                    multiply_volumn= params_data['multiply_volumn'], 
                                    rate_of_increase=params_data['rate_of_increase'], 
                                    change_day=params_data['change_day'], 
                                    risk= risk,
                                    ratio_cutloss = params_data['ratio_cutloss'],
                                    sma = params_data['sma'],)

                
    # Thiết lập thông số về kích thước vốn ban đầu và phí giao dịch
    cerebro.broker.setcash(strategy.nav)  # Số dư ban đầu
    cerebro.broker.setcommission(commission=strategy.commission)  # Phí giao dịch (0.15%)      
    #add the sizer
    cerebro.addsizer(definesize, risk=risk,ratio_cutloss=params_data['ratio_cutloss'])     
    # Chạy backtest
    result = cerebro.run()
    result = result[0]
    # cerebro.plot(style='candlestick')

    print("Các tham số tối ưu:", best_params)
    print("Hiệu suất tối ưu:", best_performance)

    
    # #Get final portfolio Value
    # port_value = round(cerebro.broker.getvalue(),0)
    # pnl = port_value - nav
    # ratio_pln = pnl/nav
    # drawdown = result.analyzers.drawdown.get_analysis()['drawdown']
    # overview = result.analyzers.overviews.get_analysis()
    # sharpe_ratio = result.analyzers.sharpe_ratio.get_analysis()['sharperatio']

    
    # #Print out the final result
    # print('----SUMMARY----')
    # print('Final Portfolio Value: ${}'.format(port_value))
    # print('P/L: ${}'.format(pnl))
    # print('drawdown:', drawdown)
    # print('Overview:', overview)
    # # cerebro.plot(style='candlestick')  # Thêm style='candlestick' để hiển thị biểu đồ dạng nến
    # # Tạo biểu đồ
        
    #     # Lưu biểu đồ vào một tệp hình ảnh
    #     # chart_path = os.path.join('stocklist/static', 'chart.png')
    #     # plt.savefig(chart_path)
    #     # Trích xuất thông tin kết quả backtest
    #     # trade_analysis = result[0]
    #     # Render template và trả về kết quả backtest    
    return 


def run_backtest_again(risk, begin_list, end_list):
    strategy_data = {
        'name': 'Breakout ver 0.1',
        'risk': risk,   
        'nav': 10000000,
        'commission' : 0.0015,
        'period':20}
    created = StrategyTrading.objects.update_or_create(name=strategy_data['name'],risk = risk, defaults=strategy_data)
    strategy = StrategyTrading.objects.filter(name=strategy_data['name'],risk = risk).first()
    stock_source = StockPriceFilter.objects.values('ticker').annotate(avg_volume=Avg('volume'))
    stock_test= [ticker for ticker in stock_source if ticker['avg_volume'] > 100000]
    backtest_tickers = OverviewBacktest.objects.values_list('ticker', flat=True)
    tickers = [item['ticker'] for item in stock_test]
    missing_tickers = [ticker for ticker in tickers if ticker not in backtest_tickers]
    missing_tickers.sort()
    list_bug =[]
    for item in missing_tickers[begin_list:end_list]:
        ticker = item
        # ticker = item
        print('------đang chạy:', ticker)
        try:
            stock_prices = StockPrice.objects.filter(ticker=ticker).values()
            df = pd.DataFrame(stock_prices)
            df = breakout_strategy(df, strategy.period)
            df = df.drop(['id','res','sup','gradients','ema'], axis=1) 
            df = df.sort_values('date', ascending=True).reset_index(drop=True)  # Sửa 'stock' thành biến stock để sử dụng giá trị stock được truyền vào hàm
            df = df.fillna(0.0001)
            data = PandasData(dataname=df)
            #Chạy tối ưu hóa param
            # Khởi tạo các giá trị tham số muốn tối ưu
            multiply_volumn_values = [x / 2 for x in range(2, 4)]
            rate_of_increase_values = [0.01, 0.03]
            change_day_values = [0.015,0.025,0.03]
            risk_values = [risk]   
            ratio_cutloss = [0.05,0.07,0.1]
            sma = [20,50] 
            len_sideway = [3]
            #####test
            # multiply_volumn_values = [x / 2 for x in range(2, 3)]
            # rate_of_increase_values = [0.01]  # tăng so với phiên trước đó
            # change_day_values = [0.015, 0.02] 
            # risk_values = [risk]
            # ratio_cutloss = [0.05,0.06]
            # sma =[20]
            # Tạo danh sách các giá trị tham số
            param_values = [multiply_volumn_values, rate_of_increase_values, change_day_values, risk_values, ratio_cutloss, sma,len_sideway]
            # Tạo tất cả các tổ hợp tham số
            param_combinations = list(product(*param_values))

            # Tìm giá trị tối ưu bằng Grid Search
            best_params = None
            best_performance = None
            list_param_bug = []
            for params in param_combinations:
                # print(params)
                params = tuple(float(param) for param in params)  # Chuyển đổi các giá trị tham số sang kiểu số thực
                try:
                    performance = evaluate_strategy(params,nav=strategy.nav,commission= strategy.commission,size_class = definesize,data= data,strategy_class = breakout_otm,ticker =  ticker, strategy=strategy)
                    if best_performance is None or performance > best_performance:
                        best_params = params
                        best_performance = performance  
                        # print('chay ok:',best_performance)              
                except Exception as e:
                    list_param_bug.append(params)
                    if len(list_param_bug)>20:
                        print(f"Có lỗi trong test kịch bản {list_param_bug}: {str(e)}")
                        break
            if best_params:
                params_data = {
                        'multiply_volumn': best_params[0],  # vốn ban đầu
                        'rate_of_increase': best_params[1],  # phí giao dịch
                        'change_day':best_params[2],
                        'ratio_cutloss':best_params[4],
                        'sma':best_params[5],
                        'len_sideway':best_params[6],
                }

                params_feild = {
                        'param1': best_params[4],  # cat lo
                        'param2': best_params[1],  # phí giao dịch
                        'param3':best_params[2],
                        'param4':best_params[0],
                        'param5':best_params[5],
                        'param6':best_params[6],
                }

                obj, created = ParamsOptimize.objects.update_or_create(strategy = strategy,ticker=ticker, defaults=params_feild)
                print('Đã tạo param')

                # Tạo một phiên giao dịch Backtrader mới
                cerebro = bt.Cerebro()
                # Thêm dữ liệu và chiến lược vào cerebro
                cerebro.adddata(data)
                # thêm chiến lược thông số đã được tối ưu
                cerebro.addstrategy(breakout_otm, ticker,True,strategy,
                                    multiply_volumn= params_data['multiply_volumn'], 
                                    rate_of_increase=params_data['rate_of_increase'], 
                                    change_day=params_data['change_day'], 
                                    risk= risk,
                                    ratio_cutloss = params_data['ratio_cutloss'],
                                    sma = params_data['sma'],
                                    len_sideway  =params_data['len_sideway'])

                
                # Thiết lập thông số về kích thước vốn ban đầu và phí giao dịch
                cerebro.broker.setcash(strategy.nav)  # Số dư ban đầu
                cerebro.broker.setcommission(commission=strategy.commission)  # Phí giao dịch (0.15%)
                
                #add the sizer
                cerebro.addsizer(definesize, risk=risk,ratio_cutloss=params_data['ratio_cutloss'])
                
                # Analyzer
                cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='overviews')
                cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe_ratio')
                cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
                # Chạy backtest
                result = cerebro.run()
                result = result[0]
                #Get final portfolio Value
                port_value = round(cerebro.broker.getvalue(), 0)
                ratio_pln = (port_value - strategy.nav) / strategy.nav
                drawdown = result.analyzers.drawdown.get_analysis()['drawdown']
                overview = result.analyzers.overviews.get_analysis()
                sharpe_ratio = result.analyzers.sharpe_ratio.get_analysis()['sharperatio']
                total_closed_test = overview.total.get('closed')
                list_trade = TransactionBacktest.objects.filter(ticker =ticker, strategy = strategy)
                if total_closed_test and sharpe_ratio and total_closed_test > 0:
                    overview_data = {
                        'ratio_pln': round(ratio_pln*100, 3),  # tỷ suất lợi nhuận
                        'drawdown': round(drawdown, 3),  # Tìm hiểu
                        'sharpe_ratio': round(sharpe_ratio, 3),  # tìm hiểu
                        'total_trades': overview.total.get('total'),  # tổng số deal
                        'total_open_trades': overview.total.get('open'),  # deal đang mở, chưa chốt
                        'total_closed_trades': overview.total.get('closed'),  # đang đã đóng
                        'win_trade_ratio':round(overview.won.get('total')*100/overview.total.get('total'),2),
                        # Chuỗi giao dịch liên tiếp
                        'won_current_streak': overview.streak.won.get('current'),
                        'won_longest_streak': overview.streak.won.get('longest'),
                        'lost_current_streak': overview.streak.lost.get('current'),
                        'lost_longest_streak': overview.streak.lost.get('longest'),
                        # Thống kê giao dịch thắng
                        'won_total_trades': overview.won.get('total'),
                        'won_total_pnl': round(sum(i.ratio_pln for i in list_trade if i.ratio_pln>0 ), 2),
                        'won_average_pnl': round(mean(i.ratio_pln for i in list_trade if i.ratio_pln>0 ), 2),
                        'won_max_pnl': max(i.ratio_pln for i in list_trade if i.ratio_pln>0 ),
                        'lost_total_trades': overview.lost.get('total'),
                        'lost_total_pnl': round(sum(i.ratio_pln for i in list_trade if i.ratio_pln<0 ), 2),
                        'lost_average_pnl': round(mean(i.ratio_pln for i in list_trade if i.ratio_pln<0 ), 2),
                        'lost_max_pnl': min(i.ratio_pln for i in list_trade if i.ratio_pln<0 ),
                        #thống kê giao dịch long (mua)
                            # 'total_long_trades': overview.long.get('total'),
                            # 'total_long_pnl': round(overview.long.pnl.get('total') / nav, 2),
                            # 'total_long_average_pnl': round(overview.long.pnl.get('average') / nav, 2),
                            # 'won_long_trades': overview.long.won,
                            # 'won_long_total_pnl': round(overview.long.pnl.won.get('total') / nav, 2),
                            # 'won_long_average_pnl': round(overview.long.pnl.won.get('average') / nav, 2),
                            # 'won_long_max_pnl': round(overview.long.pnl.won.get('max') / nav, 2),
                            # 'lost_long_trades': overview.long.lost,
                            # 'lost_long_total_pnl': round(overview.long.pnl.lost.get('total') / nav, 2),
                            # 'lost_long_average_pnl': round(overview.long.pnl.lost.get('average') / nav, 2),
                            # 'lost_long_max_pnl': round(overview.long.pnl.lost.get('max') / nav, 2),
                        #thống kê giao dịch short (bán khống)
                            # 'total_short_trades': overview.short.get('total'),
                            # 'total_short_pnl': overview.short.pnl.get('total'),
                            # 'total_short_average_pnl': round(overview.short.pnl.get('average') / nav, 2),
                            # 'won_short_total_pnl': round(overview.short.pnl.won.get('total'), 2),
                            # 'won_short_average_pnl': round(overview.short.pnl.won.get('average') / nav, 2),
                            # 'won_short_max_pnl': round(overview.short.pnl.won.get('max') / nav, 2),
                            # 'lost_short_total_pnl': round(overview.short.pnl.lost.get('total') / nav, 2),
                            # 'lost_short_average_pnl': round(overview.short.pnl.lost.get('average') / nav, 2),
                            # 'lost_short_max_pnl': round(overview.short.pnl.lost.get('max') / nav, 2),
                            # 'lost_short_trades': overview.short.lost,
                            # 'won_short_trades': overview.short.won,
                        #thống kê số ngày nắm giữ của giao dịch
                        'total_trades_length': overview.len.get('total'),
                        'average_trades_per_day': round(overview.len.get('average'), 2),
                        'max_trades_per_day': overview.len.get('max'),
                        'min_trades_per_day': overview.len.get('min'),
                        'total_won_trades_length': overview.len.won.get('total'),
                        'average_won_trades_per_day': round(overview.len.won.get('average'),2),
                        'max_won_trades_per_day': overview.len.won.get('max'),
                        'min_won_trades_per_day': overview.len.won.get('min'),
                        'total_lost_trades_length': overview.len.lost.get('total'),
                        'average_lost_trades_per_day': round(overview.len.lost.get('average'),2),
                        'max_lost_trades_per_day': overview.len.lost.get('max'),
                        'min_lost_trades_per_day': overview.len.lost.get('min'),
                        'deal_average_pnl': round(sum(i.ratio_pln for i in list_trade )/overview.total.get('closed'),2),
                    }
                    obj, created = OverviewBacktest.objects.update_or_create(strategy=strategy,ticker=ticker, defaults=overview_data)
                    print('Đã tạo thông số trade')
            else:
                    print('Không tạo được thông số trade tối ưu')
        except Exception as e:
                print(f"Có lỗi với cổ phiếu {ticker}: {str(e)}")
                list_bug.append({ticker:str(e)})
    # chạy tổng kết        
    detail_stock = OverviewBacktest.objects.filter(strategy=strategy,total_trades__gt=0)
    if detail_stock:
        total = {
            'ratio_pln':round(mean(i.ratio_pln for i in detail_stock),2),
            'deal_average_pnl': round(mean(i.deal_average_pnl for i in detail_stock),2),
            'max_ratio_pln': max(i.deal_average_pnl for i in detail_stock),
            'min_ratio_pln': min(i.deal_average_pnl for i in detail_stock),
            'drawdown':round(mean(i.drawdown for i in detail_stock),2),
            'sharpe_ratio': round(mean(i.sharpe_ratio for i in detail_stock),2),
            'total_trades': sum(i.total_trades for i in detail_stock),
            'total_open_trades': sum(i.total_open_trades for i in detail_stock),
            'win_trade_ratio': round(mean(i.win_trade_ratio for i in detail_stock), 2),
            'max_win_trade_ratio': max(i.win_trade_ratio for i in detail_stock),
            'min_win_trade_ratio': min(i.win_trade_ratio for i in detail_stock),
            'total_closed_trades': sum(i.total_closed_trades for i in detail_stock),
            'won_total_trades': sum(i.won_total_trades for i in detail_stock),
            'won_total_pnl': round(sum(i.won_total_pnl for i in detail_stock),2),
            'won_average_pnl': round(mean(i.won_average_pnl for i in detail_stock), 2),
            'won_max_pnl': max(i.won_max_pnl for i in detail_stock),
            'lost_total_trades': sum(i.lost_total_trades for i in detail_stock),
            'lost_total_pnl': round(sum(i.lost_total_pnl for i in detail_stock),2),
            'lost_average_pnl': round(mean(i.lost_average_pnl for i in detail_stock), 2),
            'lost_max_pnl': min(i.lost_max_pnl for i in detail_stock),
            'total_trades_length': round(mean(i.total_trades_length for i in detail_stock), 2),
            'average_trades_per_day': round(mean(i.average_trades_per_day for i in detail_stock), 2),
            'max_trades_per_day': max(i.max_trades_per_day for i in detail_stock),
            'min_trades_per_day': min(i.min_trades_per_day for i in detail_stock),
            'total_won_trades_length': round(mean(i.total_won_trades_length for i in detail_stock), 2),
            'average_won_trades_per_day': round(mean(i.average_won_trades_per_day for i in detail_stock), 2),
            'max_won_trades_per_day': max(i.max_won_trades_per_day for i in detail_stock),
            'min_won_trades_per_day': min(i.min_won_trades_per_day or sys.maxsize for i in detail_stock),
            'total_lost_trades_length': round(mean(i.total_lost_trades_length for i in detail_stock), 2),
            'average_lost_trades_per_day': round(mean(i.average_lost_trades_per_day for i in detail_stock), 2),
            'max_lost_trades_per_day': max(i.max_lost_trades_per_day or -sys.maxsize-1 for i in detail_stock),
            'min_lost_trades_per_day' : min(i.min_lost_trades_per_day or sys.maxsize   for i in detail_stock if i.min_lost_trades_per_day),
        }
        obj = RatingStrategy.objects.update_or_create(strategy=strategy, defaults=total)

    print('Đã tạo tổng kết chiến lược')
    rating_stock(strategy)
    print('Đã tạo điểm tổng hợp')
    
    return list_bug