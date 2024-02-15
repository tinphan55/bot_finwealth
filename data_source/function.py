from datetime import datetime, timedelta, time
import requests
from bs4 import BeautifulSoup
import json
from data_source.models import *
from posgress import *



def get_all_info_stock_price():
    boardname = ['HOSE','HNX','UPCOM']
    linkstocklist='https://price.tpbs.com.vn/api/StockBoardApi/getStockList'
    linkstockquote ='https://price.tpbs.com.vn/api/SymbolApi/getStockQuote'
    stock_list =[]
    for i in boardname:
        r1= requests.post(linkstocklist,json =  {"boardName":i})
        k=json.loads(r1.text)
        list =json.loads(k['content'])
        stock_list= stock_list+list
    r = requests.post(linkstockquote,json = {"stocklist" : stock_list})
    b= json.loads(r.text)
    a = json.loads(b['content'])
    result = []
    date_time = datetime.now()
    count = 0
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        open=float(a[i]['ope'].replace(',', ''))
        low_price=float(a[i]['low'].replace(',', ''))
        high_price = float(a[i]['hig'].replace(',', ''))
        close=float(a[i]['mat'].replace(',', ''))
        volume=float(a[i]['tmv'].replace(',', '') )*10
        StockPrice.objects.create(
            ticker=ticker,
            date= date_time.date(),
            low =  low_price,
            high = high_price,
            open = open,
            close = close,
            volume= volume,
            date_time=date_time )


#lấy toàn bộ giá cổ phiếu
def get_info_stock_price_filter():
    boardname = ['HOSE','HNX','UPCOM']
    linkstocklist='https://price.tpbs.com.vn/api/StockBoardApi/getStockList'
    linkstockquote ='https://price.tpbs.com.vn/api/SymbolApi/getStockQuote'
    stock_list =[]
    for i in boardname:
        r1= requests.post(linkstocklist,json =  {"boardName":i})
        k=json.loads(r1.text)
        list =json.loads(k['content'])
        stock_list= stock_list+list
    r = requests.post(linkstockquote,json = {"stocklist" : stock_list})
    b= json.loads(r.text)
    a = json.loads(b['content'])
    result = []
    date_time = datetime.now()
    count = 0
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        open=float(a[i]['ope'].replace(',', ''))
        low_price=float(a[i]['low'].replace(',', ''))
        high_price = float(a[i]['hig'].replace(',', ''))
        close=float(a[i]['mat'].replace(',', ''))
        volume=float(a[i]['tmv'].replace(',', '') )*10
        created = StockPriceFilter.objects.update_or_create(
                ticker=ticker,
                date= date_time.date(),
            defaults={
            'low': low_price,
            'high': high_price,
            'open':open,
            'close': close,
            'volume': volume,
            'date_time':date_time, 
                        } )
        if created:
            count = count + 1
    if count >0:
        mindate = StockPriceFilter.objects.all().order_by('date').first().date
        maxdate=  StockPriceFilter.objects.all().order_by('-date').first().date
        len_date = (maxdate -mindate).days
        delete = 0
        if len_date >201:
            delete = StockPriceFilter.objects.filter(date=mindate).delete()
    return f"Tạo mới tổng {count} cổ phiếu, và xóa {delete} cổ phiếu cũ " 

def get_list_stock_price(list_stock):
    # list_stock = list(Transaction.objects.values_list('stock', flat=True).distinct())
    number =len(list_stock)
    linkstockquote ='https://price.tpbs.com.vn/api/SymbolApi/getStockQuote'
    r = requests.post(linkstockquote,json = {"stocklist" : list_stock })
    b= json.loads(r.text)
    a = json.loads(b['content'])
    date_time = datetime.now()
    for i in range (0,len(a)):
        ticker=a[i]['sym']
        open=float(a[i]['ope'].replace(',', ''))
        low_price=float(a[i]['low'].replace(',', ''))
        high_price = float(a[i]['hig'].replace(',', ''))
        close=float(a[i]['mat'].replace(',', ''))
        volume=float(a[i]['tmv'].replace(',', '') )*10
        StockPriceFilter.objects.update_or_create(
                ticker=ticker,
                date= date_time.date(),
            defaults={
           'low': low_price,
            'high': high_price,
            'open':open,
            'close': close,
            'volume': volume,
            'date_time':date_time
                        } )
    return StockPriceFilter.objects.all().order_by('-date')[:number]


def get_omo_info():
    linkbase= 'https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/hdtttt/ttm'
    r = requests.get(linkbase)
    soup = BeautifulSoup(r.text,'html.parser')
    data=[]
    rows = soup.find_all('td') 
    for td in rows:
        data.append(td.get_text(strip=True))
    x = data.index('KẾT QUẢ ĐẤU THẦU THỊ TRƯỜNG MỞ')
    y = data.index('Ghi chú:')
    data_new =data[x:y]
    data_new = [x for x in data_new if x != '']
    date_string  = data_new[1]
    # Tách thành phần ngày, tháng và năm từ chuỗi
    date_components = date_string.split()
    day = int(date_components[1])
    month = int(date_components[3])
    year = int(date_components[5])
    # Tạo đối tượng date
    date_omo = datetime.datetime(year, month, day).date()
    volume_omo = data_new[-1].replace('.', '')
    volume_omo = float(volume_omo.replace(',', '.')) / (-1000)
    rate_omo = float(data_new[-3].replace(',', '.'))
    insert_query = f"INSERT INTO tbomovietnam (date,rate,volume) VALUES ('{date_omo}', {rate_omo},{volume_omo})"
    execute_query(insert_query)
    return date_omo,volume_omo,rate_omo

def static_above_ma():
    query_get_df_transation = f"select ticker,date, close from portfolio_stockpricefilter order by ticker,date"    
    df_transaction = read_sql_to_df(1,query_get_df_transation)
    df_transaction ['MA200'] = df_transaction .groupby('ticker')['close'].rolling(window=200).mean().reset_index(0, drop=True)
    df_transaction ['MA100'] = df_transaction .groupby('ticker')['close'].rolling(window=100).mean().reset_index(0, drop=True)
    df_transaction ['MA50'] = df_transaction .groupby('ticker')['close'].rolling(window=50).mean().reset_index(0, drop=True)
    df_transaction ['MA20'] = df_transaction .groupby('ticker')['close'].rolling(window=20).mean().reset_index(0, drop=True)
    data_for_day = df_transaction[(df_transaction['date'].dt.date == date) & (df_transaction['close'] > 0)]
    if data_for_day.shape[0] > 0:
        count_ma200 = round((data_for_day['close'] > data_for_day['MA200']).sum() / data_for_day.shape[0] * 100, 2)
        count_ma100 = round((data_for_day['close'] > data_for_day['MA100']).sum() / data_for_day.shape[0] * 100, 2)
        count_ma50 = round((data_for_day['close'] > data_for_day['MA50']).sum() / data_for_day.shape[0] * 100, 2)
        count_ma20 = round((data_for_day['close'] > data_for_day['MA20']).sum() / data_for_day.shape[0] * 100, 2)
    else:
        count_ma200 = 0
        count_ma100 = 0
        count_ma50 = 0
        count_ma20 = 0
    query_get_vnindex = f"select close from portfolio_sectorprice where date = '{date}' and ticker = 'VNINDEX' " 
    vnindex = query_data(query_get_vnindex)
    if vnindex:
        close = vnindex[0][0]
    if len(data_for_day)>0:
        insert_query = f"INSERT INTO tbstockmarketvnstaticma (date,count_ma200,count_ma100,count_ma50,count_ma20, vnindex) VALUES ('{date}', {count_ma200},{count_ma100},{count_ma50},{count_ma20},{close})"
        execute_query(insert_query)
    return date, count_ma200,count_ma100,count_ma50,count_ma20, close


def metakit_sector_data_import():
    # Đường dẫn tới thư mục chứa các file CSV
    folder_path = "C:\\ExportData\\Sector"
    # Tạo một danh sách để lưu trữ tất cả các DataFrame từ các file CSV
    dfs = []
    # Duyệt qua tất cả các file trong thư mục
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            # Loại bỏ phần ".csv" ở cuối và sử dụng tên file làm cột 'name'
            name = os.path.splitext(filename)[0]
            file_path = os.path.join(folder_path, filename)
            # Đọc file CSV, bỏ dòng đầu tiên
            df = pd.read_csv(file_path, header=0, index_col=False)
            df['ticker'] = name
            dfs.append(df)
    # Nối tất cả các DataFrame thành một DataFrame tổng
    sector_df = pd.concat(dfs, ignore_index=True)
    sector_df['date'] = pd.to_datetime(sector_df['date'], format='%d-%b-%y').dt.strftime('%Y-%m-%d')
    # data = sector_df.to_dict(orient='records')
    # SectorPrice.objects.all().delete()
    # # Lưu các đối tượng SectorPrice mới vào cơ sở dữ liệu bằng bulk_create
    # SectorPrice.objects.bulk_create([SectorPrice(**item) for item in data])
    # # In ra DataFrame tổng
    # print(sector_df)
    sector_df.to_sql('portfolio_sectorprice', engine(), if_exists='replace', index=False)


def metakit_stock_price_import():
    # Đường dẫn tới thư mục chứa các file CSV
    folder_path = "C:\\ExportData\\Stock"
    # Tạo một danh sách để lưu trữ tất cả các DataFrame từ các file CSV
    dfs = []
    # Duyệt qua tất cả các file trong thư mục
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            # Loại bỏ phần ".csv" ở cuối và sử dụng tên file làm cột 'name'
            name = os.path.splitext(filename)[0]
            file_path = os.path.join(folder_path, filename)
            # Đọc file CSV, bỏ dòng đầu tiên
            df = pd.read_csv(file_path, header=0, index_col=False)
            df['ticker'] = name
            dfs.append(df)
    # Nối tất cả các DataFrame thành một DataFrame tổng
    stock_df = pd.concat(dfs, ignore_index=True)
    stock_df['date'] = pd.to_datetime(stock_df['date'], format='%d-%b-%y').dt.strftime('%Y-%m-%d')
    stock_df = stock_df.sort_values('date')
    stock_df['date_time'] = pd.to_datetime(stock_df['date']) + pd.Timedelta(hours=14, minutes=45)
    stock_df = stock_df.reset_index(drop=True)
    # dòng này sẽ gây lỗi với Django, không migrate được data
    stock_df.to_sql('data_source_stockprice', engine(), if_exists='replace', index=False)
    add_id_stockprice_column_query = f"ALTER TABLE public.data_source_stockprice ADD id int8 NOT NULL GENERATED BY DEFAULT AS IDENTITY;"
    execute_query(add_id_stockprice_column_query)
    date_trading = stock_df[stock_df['ticker']=='REE']['date']
    date_trading.to_sql('data_source_datetrading', engine(), if_exists='replace', index=False)
    add_id_column_query = f"ALTER TABLE public.data_source_datetrading ADD id int8 NOT NULL GENERATED BY DEFAULT AS IDENTITY;"
    execute_query(add_id_column_query)

    print('Tai data chứng khoán xong')