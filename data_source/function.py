from datetime import datetime, timedelta, time
import requests
from bs4 import BeautifulSoup
import json
from data_source.models import *
from data_source.posgress import *

def define_stock_date_to_sell(buy_date, days=2):
    next_trading_date = None
    # Tính ngày kết thúc
    end_date = buy_date + timedelta(days=days)
    # Lấy tất cả các ngày giao dịch từ buy_date đến end_date và sắp xếp theo thứ tự tăng dần
    trading_dates = DateTrading.objects.filter(date__gt=buy_date, date__lte=end_date).order_by('date')
    # Kiểm tra nếu có ngày giao dịch tiếp theo
    if trading_dates.exists():
        next_trading_date = trading_dates.first().date
    return next_trading_date

def save_fa_valuation():
    fa = StockFundamentalData.objects.all()
    for self in fa:
        stock = StockPriceFilter.objects.filter(ticker = self.ticker).order_by('-date_time').first()
        if stock:
            self.market_price = stock.close
        if self.bvps and self.market_price :
            self.p_b = round(self.market_price*1000/self.bvps,2)
            #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
            if self.p_b > 0 and self.p_b <=1 :
                rating_pb = 100 - (self.p_b-0) /(1-0)*(100-80)
            elif self.p_b >1 and self.p_b<=10:
                rating_pb = 80 - (self.p_b-1) /(10-1)*(80-50)
            elif self.p_b >10:
                rating_pb = 40
            else:
                rating_pb = 0
        else:
            rating_pb = 0
        if self.eps and self.market_price:
            self.p_e = round(self.market_price*1000/self.eps,2)
            #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
            if self.p_e > 0 and self.p_e <=1 :
                rating_pe = 100 - (self.p_e-0) /(1-0)*(100-80)
            elif self.p_e >1 and self.p_e<=10:
                rating_pe = 80 - (self.p_e-1) /(10-1)*(80-50)
            elif self.p_e >10:
                rating_pe = 40
            else:
                rating_pe = 0
        else:
            rating_pe = 0
        self.valuation_rating  = round(rating_pb*0.5+rating_pe*0.5,2)
        self.fundamental_rating = round(self.growth_rating*0.5 + self.valuation_rating*0.3 + self.stable_rating*0.2,2)
        self.save()

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
    date_trading = stock_df[stock_df['ticker'] == 'REE'][['date']].copy()
    # Thêm cột description
    date_trading['description'] = ""
    date_trading = date_trading.sort_values('date')
    date_trading = date_trading.reset_index(drop=True)
    date_trading.to_sql('data_source_datetrading', engine(), if_exists='replace', index=False)
    add_id_column_query = f"ALTER TABLE public.data_source_datetrading ADD id int8 NOT NULL GENERATED BY DEFAULT AS IDENTITY;"
    execute_query(add_id_column_query)

    print('Tai data chứng khoán xong')


def save_event_stock(stock):
    list_event =[]
    linkbase= 'https://www.stockbiz.vn/MarketCalendar.aspx?Symbol='+ stock
    r = requests.get(linkbase)
    soup = BeautifulSoup(r.text,'html.parser')
    table = soup.find('table', class_='dataTable')  # Tìm bảng chứa thông tin
    if table:
        rows = table.find_all('tr')  # Lấy tất cả các dòng trong bảng (loại bỏ dòng tiêu đề)
        cash_value= 0
        stock_value=0
        stock_option_value=0
        price_option_value=0
        dividend_type = 'order'
        for row in rows[1:]:  # Bắt đầu từ vị trí thứ hai (loại bỏ dòng tiêu đề)
            dividend  = {}
            columns = row.find_all('td')  # Lấy tất cả các cột trong dòng
            if len(columns) >= 3:  # Kiểm tra số lượng cột
                dividend['ex_rights_date'] = columns[0].get_text(strip=True)
                dividend['event'] = columns[4].get_text(strip=True)
                list_event.append(dividend)
                event = dividend['event'].lower()
                ex_rights_date = datetime.strptime(dividend['ex_rights_date'], '%d/%m/%Y').date()
                if ex_rights_date == datetime.now().date():
                    if 'tiền' in event:
                        dividend_type = 'cash'
                        cash = re.findall(r'\d+', event)  # Tìm tất cả các giá trị số trong chuỗi
                        if cash:
                            value1 = int(cash[-1])/1000  # Lấy giá trị số đầu tiên
                            cash_value += value1
                    elif 'cổ phiếu' in event and 'phát hành' not in event:
                        dividend_type = 'stock'
                        stock_values = re.findall(r'\d+', event)
                        if stock_values:
                            value2 = int(stock_values[-1])/int(stock_values[-2])
                            stock_value += value2
                    elif 'cổ phiếu' in event and 'giá' in event and 'tỷ lệ' in event:
                        dividend_type = 'option'
                        option = re.findall(r'\d+', event)
                        if option:
                                stock_option_value = int(option[-2])/int(option[-3])
                                price_option_value = int(option[-1])
        if dividend_type == 'order':
            pass
        else:
            DividendManage.objects.update_or_create(
                        ticker= stock,  # Thay thế 'Your_Ticker_Value' bằng giá trị ticker thực tế
                        date_apply=ex_rights_date,
                        defaults={
                            'type': dividend_type,
                            'cash': cash_value,
                            'stock': stock_value,
                            'price_option': price_option_value,
                            'stock_option':stock_option_value
                        }
                    )
    return list_event

def check_dividend():
    signal = Signaldaily.objects.filter(is_closed = False)
    for stock in signal:
        dividend = save_event_stock(stock.ticker)
    dividend_today = DividendManage.objects.filter(date_apply =datetime.now().date() )
    for i in dividend_today:
        i.save()
        
    
def check_update_analysis_and_send_notifications():
    # Lọc các bản ghi có modified_date max trong cùng ticker
    filtered_records = []
    # Lấy danh sách các ticker và modified_date max
    latest_records = FundamentalAnalysis.objects.values('ticker').annotate(max_modified_date=Max('modified_date'))
    for record in latest_records:
        ticker = record['ticker']
        max_modified_date = record['max_modified_date']
        ticker_records = FundamentalAnalysis.objects.filter(ticker=ticker, modified_date=max_modified_date)
        filtered_records.extend(ticker_records)
    # Lọc các record có modified_date max có ngày nhỏ hơn ngày hiện tại - 90 ngày
    current_date = datetime.now()
    threshold_date = current_date - timedelta(days=90)
    records_to_notify = [record for record in filtered_records if record.modified_date <= threshold_date]
    for record in records_to_notify:
        bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
        bot.send_message(
                chat_id='-870288807', 
                text=f"Cổ phiếu {record.ticker} đã quá 3 tháng chưa có cập nhật thông tin mới, hãy cập nhật ngay nhé Vũ/Thạch ơi!!!" )   
