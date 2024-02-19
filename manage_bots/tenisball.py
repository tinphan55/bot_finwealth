
from data_source.models import *
from data_source.function import *
import talib
from .models import *



def tenisball_strategy(df):
    df = df.sort_values('date', ascending=True)
    df['Morning_Star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Harami'] = talib.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
    df['Piercing_Line'] = talib.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])
    df['Hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
    df['Dragonfly_Doji'] = talib.CDLDRAGONFLYDOJI(df['open'], df['high'], df['low'], df['close'])
    df['Morning_Star_Doji'] = talib.CDLMORNINGDOJISTAR(df['open'], df['high'], df['low'], df['close'])
    df['Inverted_Hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['pattern_rating']= df['Morning_Star']+df['Bullish_Harami'] +df['Piercing_Line']+df['Hammer']+df['Bullish_Engulfing']+df['Dragonfly_Doji']+df['Morning_Star_Doji']+df['Inverted_Hammer']
    df['ma200'] = df['close'].rolling(window=200).mean()
    df['mavol'] = df['volume'].rolling(window=200).mean()
    df['top'] = df['high'].rolling(window=5).max()
    df = df.sort_values('date', ascending=False)
    return df

def tenisball_strategy_otmed(df, risk):
    strategy= StrategyTrading.objects.filter(name = 'Tenisball_ver0.1', risk = risk).first()
    period = strategy.period
    backtest = ParamsOptimize.objects.filter(strategy = strategy).values('ticker','param1','param2','param3','param4')
    df_param = pd.DataFrame(backtest)
    df = df.sort_values('date', ascending=True)
    df = df.drop(['id','date_time'], axis=1)
    df['param_ma_backtest'] = df['ticker'].map(df_param.set_index('ticker')['param1'])
    df['param_ratio_backtest'] = df['ticker'].map(df_param.set_index('ticker')['param2'])
    df['param_ratio_cutloss'] = df['ticker'].map(df_param.set_index('ticker')['param3'])
    df['param_pattern_rating'] = df['ticker'].map(df_param.set_index('ticker')['param4'])
    df['Morning_Star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Harami'] = talib.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
    df['Piercing_Line'] = talib.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])
    df['Hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['Bullish_Engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
    df['Dragonfly_Doji'] = talib.CDLDRAGONFLYDOJI(df['open'], df['high'], df['low'], df['close'])
    df['Morning_Star_Doji'] = talib.CDLMORNINGDOJISTAR(df['open'], df['high'], df['low'], df['close'])
    df['Inverted_Hammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
    df['pattern_rating']= df['Morning_Star']+df['Bullish_Harami'] +df['Piercing_Line']+df['Hammer']+df['Bullish_Engulfing']+df['Dragonfly_Doji']+df['Morning_Star_Doji']+df['Inverted_Hammer']
    df['ma200'] = df['close'].rolling(window=200).mean()
    df['top'] = df['high'].rolling(window=5).max()
    df['mavol'] = df['volume'].rolling(window=20).mean()
    buy_trend = df['close'] > df['ma200'] #done
    buy_decrease = df['close'] < df['top'] #done
    buy_minvol =df['mavol'] > 100000 #done
    buy_pattern= df['pattern_rating'] >= df['param_pattern_rating'] #done
    buy_backtest_ma = df['close'] >= df['param_ma_backtest'] *df['param_ratio_backtest'] #done
    # signal_df=df[(df['pattern_rating'] >= df['param_pattern_rating'])&(df['mavol']>100000)&(df['close']>df['ma200'])&(df['close'] < df['top'])&(df['close'] >= df['param_ma_backtest'] *df['param_ratio_backtest'])]
    buy =  buy_trend & buy_decrease & buy_minvol & buy_pattern & buy_backtest_ma
    # cut_loss = df['close'] <= df['close']*(1-df['param_ratio_cutloss'])
    df['signal'] = np.where(buy, 'buy', 'newtral')
    return df

    