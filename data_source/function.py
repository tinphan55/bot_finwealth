from datetime import datetime, timedelta, time
import requests
from bs4 import BeautifulSoup
import json
from data_source.models import *
from data_source.posgress import *
from manage_bots.models import StrategyTrading

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

# CẦn chỉnh lại hàm khi cào từ VNDS về lại
def update_stock_valuation():
    yesterday = datetime.now().date() - timedelta(days=1)
    # Lọc các bản ghi FundamentalAnalysisReport tạo trong ngày hôm qua
    reports_created_yesterday = FundamentalAnalysisReport.objects.filter(modified_date__date=yesterday)
    for instance in reports_created_yesterday:
        tags_values = instance.tags.all()
        if instance.valuation is not None and len(tags_values) == 1:
            # Lấy hoặc tạo mới một StockOverview từ tên ticker trong tags_values
            stock, _ = StockOverview.objects.get_or_create(ticker=tags_values[0].name)
            target_price = instance.valuation
            if target_price > 1000:
                target_price= target_price/1000
            # Tạo mới hoặc cập nhật StockValuation
            try:
                stock_valuation, _ = StockValuation.objects.get_or_create(
                    ticker=stock,
                    type='Tạo tự động',
                    firm=instance.source,
                    report_date=instance.date,
                    report_price=StockPriceFilter.objects.get(ticker=tags_values[0].name, date=instance.date).close,
                    source='DCG', 
                    target_price = target_price
                )
            except Exception as e:
                pass

# def save_fa_valuation():
#     fa = StockFundamentalData.objects.all()
#     for self in fa:
#         stock = StockPriceFilter.objects.filter(ticker = self.ticker).order_by('-date_time').first()
#         if stock:
#             self.market_price = stock.close
#         if self.bvps and self.market_price :
#             self.p_b = round(self.market_price*1000/self.bvps,2)
#             #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
#             if self.p_b > 0 and self.p_b <=1 :
#                 rating_pb = 100 - (self.p_b-0) /(1-0)*(100-80)
#             elif self.p_b >1 and self.p_b<=10:
#                 rating_pb = 80 - (self.p_b-1) /(10-1)*(80-50)
#             elif self.p_b >10:
#                 rating_pb = 40
#             else:
#                 rating_pb = 0
#         else:
#             rating_pb = 0
#         if self.eps and self.market_price:
#             self.p_e = round(self.market_price*1000/self.eps,2)
#             #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
#             if self.p_e > 0 and self.p_e <=1 :
#                 rating_pe = 100 - (self.p_e-0) /(1-0)*(100-80)
#             elif self.p_e >1 and self.p_e<=10:
#                 rating_pe = 80 - (self.p_e-1) /(10-1)*(80-50)
#             elif self.p_e >10:
#                 rating_pe = 40
#             else:
#                 rating_pe = 0
#         else:
#             rating_pe = 0
#         self.valuation_rating  = round(rating_pb*0.5+rating_pe*0.5,2)
#         self.fundamental_rating = round(self.growth_rating*0.5 + self.valuation_rating*0.3 + self.stable_rating*0.2,2)
#         self.save()

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
        if len_date >260:
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

def return_json_data(data):
    data_dict = json.loads(data)
    data_list = data_dict['data']
    return data_list

def get_overview_stock(stock):
    url = f"https://finfo-api.vndirect.com.vn/v4/stocks?fields=code,shortName,companyName,companyNameEng,floor,status,listedDate&q=code:{stock}"
    payload = {}
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.vndirect.com.vn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.vndirect.com.vn/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    overview = json.loads(response.text)['data'][0]
    url = f"https://finfo-api.vndirect.com.vn/v4/company_profiles?q=code:{stock}"
    response = requests.request("GET", url, headers=headers, data=payload)
    json_data = return_json_data(response.text)
    vn_summary = json_data[0]['vnSummary']
    overview['introduce'] = vn_summary
    return overview


        
def save_valuation_stock_company(stock,days=360):
    url1 = "https://finfo-api.vndirect.com.vn/v4/recommendations?q=code:"
    url2 = "~reportDate:gte:"
    date = (datetime.now()-timedelta(days = days)).strftime("%Y-%m-%d")
    url3 = "&size=100&sort=reportDate:DESC"
    url = url1+stock+url2+date+url3
    payload = {}
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.vndirect.com.vn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.vndirect.com.vn/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.text
    return return_json_data(data)
    
def shareholder_company(stock):
    url = f"https://finfo-api.vndirect.com.vn/v4/shareholders?sort=ownershipPct:desc&q=code:{stock}~ownershipPct:gte:5"
    payload = {}
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.vndirect.com.vn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.vndirect.com.vn/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.text
    data_list = return_json_data(data)
    return data_list

def save_fa_raw(stock):
    # chỉ số cơ bản niêm yết
    date = (datetime.now()- timedelta(days=1)).strftime('%Y-%m-%d')
    url = f"https://finfo-api.vndirect.com.vn/v4/ratios/latest?filter=ratioCode:MARKETCAP,NMVOLUME_AVG_CR_10D,PRICE_HIGHEST_CR_52W,PRICE_LOWEST_CR_52W,OUTSTANDING_SHARES,FREEFLOAT,BETA,PRICE_TO_EARNINGS,PRICE_TO_BOOK,DIVIDEND_YIELD,BVPS_CR,&where=code:{stock}~reportDate:gt:{date}&order=reportDate&fields=ratioCode,value"
    payload = {}
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.vndirect.com.vn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.vndirect.com.vn/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data1 =return_json_data(response.text)
    # chỉ số lợi nhuận
    url = f"https://finfo-api.vndirect.com.vn/v4/ratios/latest?filter=ratioCode:ROAE_TR_AVG5Q,ROAA_TR_AVG5Q,EPS_TR,&where=code:{stock}~reportDate:gt:2023-11-05&order=reportDate&fields=ratioCode,value"
    response = requests.request("GET", url, headers=headers, data=payload)
    data2 = return_json_data(response.text)
    data =data1 + data2
    return data
    

def compare_ratio_yearly(year):
    url = f"https://finfo-api.vndirect.com.vn/v4/ratios?q=code:VNM~ratioCode:NET_SALES_TR_GRYOY,NET_PROFIT_TR_GRYOY,OPERATING_EBIT_TR_GRYOY,GROSS_MARGIN_TR,ROAA_TR_AVG5Q,ROAE_TR_AVG5Q,DEBT_TO_EQUITY_AQ,DIVIDEND_YIELD,CFO_TO_SALES_TR,INTEREST_COVERAGE_TR,CPS_AQ~reportDate:{year}-12-31"
    payload = {}
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.vndirect.com.vn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.vndirect.com.vn/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data_list = response.text
    data = return_json_data(data_list)
    return data

type_report = {'balance_sheet': 1, 'income_statement': 2, 'direct_cash_flow_statement': 3, 'indirect_cash_flow_statement': 4}


def financial_statements(stock,report_type,previous_year,quarter=True ):
    if quarter ==True:
        quarter=1
    else:
        quarter=0
    year = datetime.now().year
    url = f"https://www.bsc.com.vn/api/Data/Finance/LastestFinancialReports?symbol={stock}&type={report_type}&year={year}&quarter={quarter}&count={previous_year}"
    payload = {}
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.vndirect.com.vn',
    'Pragma': 'no-cache',
    'Referer': 'https://www.vndirect.com.vn/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Cookie': 'NSC_XfcTfswfs_443=ffffffff091da14845525d5f4f58455e445a4a42378b'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.text
    data_dict = json.loads(data)
    return data_dict 

def save_income_statements():
    list_stock = StockOverview.objects.all()
    for stock in list_stock:
        print(stock)
        try:
            data = financial_statements(stock, 2, 5, False)
            if data:
                for item in data:
                    values_list = item.get('Values')
                    for values_data in values_list:
                        try:
                            income_statement = DataIncomeStatement(
                                ticker=stock,
                                code=item['ID'],
                                name=item['Name'],
                                parent_id=item['ParentID'],
                                expanded=item['Expanded'],
                                level=item['Level'],
                                field=item['Field'],
                                period=values_data['Period'],
                                year=values_data['Year'],
                                quarter=values_data['Quarter'],
                                value=values_data['Value']
                            )
                            income_statement.save()
                        except Exception as e:
                            print(f"Error saving income statement: {e}")
                            continue  # Bỏ qua phần tử lỗi và tiếp tục với phần tử tiếp theo trong danh sách
        except Exception as e:
            print(f"Error retrieving financial statements: {e}")
            continue
        time.sleep(30)

def save_balancesheet():
    list_stock  =StockOverview.objects.all()
    for stock in list_stock:
        data = financial_statements(stock,1,5,False)
        if data:
            for item in data:
                try:
                    values_data = item.get('Values')[0]  # Giả sử chỉ có một phần tử trong danh sách Values
                    # Kiểm tra xem bản ghi có tồn tại trong cơ sở dữ liệu hay không
                    existing_record = DataBalanceSheet.objects.filter(ticker =stock, period=values_data['Period'], name=item['Name']).first()
                    if existing_record:
                        continue
                    balance_sheet = DataBalanceSheet(
                        ticker =stock,
                        id=item['ID'],
                        name=item['Name'],
                        parent_id=item['ParentID'],
                        expanded=item['Expanded'],
                        level=item['Level'],
                        field=item['Field'],
                        period=values_data['Period'],
                        year=values_data['Year'],
                        quarter=values_data['Quarter'],
                        value=values_data['Value']
                    )
                    balance_sheet.save()
                except Exception as e:
                    print(f"Error saving balance sheet: {e}")
                    continue
        time.sleep(30)



#chạy 1 tháng 1 lần
def process_data_list():
    date = datetime.now().date() - timedelta(days=7)
    list_stock = StockPriceFilter.objects.filter(date=date)
    for item in list_stock:    
        data = shareholder_company(item.ticker)
        for object in data:
            try:
                ticker = StockOverview.objects.get(ticker=item.ticker)
                shareholder_name = object['shareholderName']
                role_type = object['roleType']
                number_of_shares = object['numberOfShares']
                ownership_pct = object['ownershipPct']
                effective_date = datetime.strptime(object['effectiveDate'], '%Y-%m-%d').date()
                stock_shareholder, created = StockShareholder.objects.get_or_create(
                    ticker=ticker,
                    shareholder_name=shareholder_name,
                    defaults={
                        'role_type': role_type,
                        'number_of_shares': number_of_shares,
                        'ownership_pct': ownership_pct,
                        'effective_date': effective_date
                    }
                )
                if not created:
                    # Nếu đã tồn tại, cập nhật các trường dữ liệu
                    stock_shareholder.role_type = role_type
                    stock_shareholder.number_of_shares = number_of_shares
                    stock_shareholder.ownership_pct = ownership_pct
                    stock_shareholder.effective_date = effective_date
                    stock_shareholder.save()
            except Exception as e:
                print(f"Lỗi xảy ra khi lưu giá trị: {data}. Lỗi: {str(e)}")
        data_list  =save_valuation_stock_company(item.ticker,days=360)
        for data in data_list:
            try:
                print(item.ticker)
                ticker = StockOverview.objects.get(ticker=data['code'])
                firm = data['firm']
                type = data['type']
                report_date = datetime.strptime(data['reportDate'], '%Y-%m-%d').date()
                source = data['source']
                report_price = data['reportPrice']
                target_price = data['targetPrice']
                stock_valuation, created = StockValuation.objects.get_or_create(
                    ticker=ticker,
                    firm=firm,
                    report_date=report_date,
                    defaults={
                        'source': source,
                        'report_price': report_price,
                        'target_price': target_price
                    }
                )
                if not created:
                    # Nếu đã tồn tại, cập nhật các trường dữ liệu
                    stock_valuation.source = source
                    stock_valuation.report_price = report_price
                    stock_valuation.target_price = target_price
                    stock_valuation.save()
            except Exception as e:
                print(f"Lỗi xảy ra khi lưu giá trị: {data}. Lỗi: {str(e)}")
        time.sleep(30)


import time


#Chạy 1 ngày 1 lần
def update_tbstockoverviewdatatrading():
    list_stock = StockOverview.objects.all()
    for item in list_stock:
        try:
            stock_overview = StockOverview.objects.get(ticker=item.ticker)
            data = save_fa_raw(item.ticker)
            defaults = {}
            # Map ratioCode to the corresponding field name in the model
            field_mapping = {
                'MARKETCAP': 'marketcap',
                'NMVOLUME_AVG_CR_10D': 'volume_avg_cr_10d',
                'PRICE_HIGHEST_CR_52W': 'price_highest_cr_52w',
                'PRICE_LOWEST_CR_52W': 'price_lowest_cr_52w',
                'OUTSTANDING_SHARES': 'outstanding_shares',
                'FREEFLOAT': 'freefloat',
                'BETA': 'beta',
                'PRICE_TO_EARNINGS': 'price_to_earnings',
                'PRICE_TO_BOOK': 'price_to_book',
                'DIVIDEND_YIELD': 'dividend_yield',
                'BVPS_CR': 'bvps_cr',
                'ROAE_TR_AVG5Q': 'roae_tr_avg5q',
                'ROAA_TR_AVG5Q': 'roaa_tr_avg5q',
                'EPS_TR': 'eps_tr'
            }
            # Iterate over the data and populate the defaults dictionary
            for record in data:
                field_name = field_mapping.get(record['ratioCode'])
                if field_name is not None and record.get('value') is not None:
                    defaults[field_name] = record['value']
                else:
                    for key, value in record.items():
                        defaults[key.lower()] = 0

            obj, created = StockOverviewDataTrading.objects.update_or_create(
                ticker=stock_overview,
                defaults=defaults
            )
            time.sleep(30)
        except Exception as e:
            print(f"Error processing {item.ticker}: {e}")
            continue
        
def update_stockdataratio_yearly():
    list_stock = StockOverview.objects.all()
    for object in list_stock:
        print (object.ticker)
        list_year = ['2020', '2021', '2022', '2023']
        for year in list_year:
            data = compare_ratio_yearly(year)
            ticker = StockOverview.objects.get(ticker=object.ticker)
            for item in data:
                try:
                    report_date = item.get('reportDate')
                    ratio_code=item.get('ratioCode')
                    defaults = {
                        'item_name':item.get('itemName'),
                        'value': round(item.get('value'),3)
                    }
                    stock_data, created = StockRatioData.objects.get_or_create(ticker=ticker, report_date=report_date,ratio_code=ratio_code, defaults=defaults)
                    if not created:
                        # Bản ghi đã tồn tại, bạn có thể thực hiện các thao tác khác tại đây
                        pass
                except Exception as e:
                    # Xử lý lỗi ở đây, hoặc bỏ qua lỗi và tiếp tục vòng lặp
                    pass
        time.sleep(30)        

def delete_file_pdf():
    reports_with_file = FundamentalAnalysisReport.objects.filter(file__isnull=False)
    for report in reports_with_file:
        report.file.delete()

import os
import fitz  # PyMuPDF

def split_pdfs_in_directory(input_dir, output_dir, max_pages=240, max_size_mb=19):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            input_pdf = os.path.join(input_dir, filename)
            if has_text(input_pdf):
                output_subdir = os.path.join(output_dir, os.path.splitext(filename)[0])
                os.makedirs(output_subdir, exist_ok=True)
                split_pdf(input_pdf, output_subdir, max_pages, max_size_mb)

def split_pdf(input_pdf, output_dir, max_pages=240, max_size_mb=19):
    pdf_filename = os.path.basename(input_pdf)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_document = fitz.open(input_pdf)
    num_pages = pdf_document.page_count

    num_files = num_pages // max_pages + (1 if num_pages % max_pages != 0 else 0)

    page_count = 0
    file_count = 1
    pdf_writer = fitz.open()

    for page_num in range(num_pages):
        pdf_writer.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        page_count += 1

        # Kiểm tra xem có đạt tới số trang tối đa hoặc kích thước tệp tối đa không
        if (page_count == max_pages) or (get_pdf_length(pdf_writer) / (1024 * 1024) > max_size_mb):
            output_pdf = os.path.join(output_dir, f'output_{file_count}_{pdf_filename}')
            pdf_writer.save(output_pdf)
            print(f'Created {output_pdf}')

            # Reset các biến đếm và tạo một tệp PDF mới
            page_count = 0
            file_count += 1
            pdf_writer = fitz.open()

    # Lưu tệp PDF cuối cùng nếu còn trang cần xử lý
    if page_count > 0:
        output_pdf = os.path.join(output_dir, f'output_{file_count}_{pdf_filename}')
        pdf_writer.save(output_pdf)
        print(f'Created {output_pdf}')

    pdf_document.close()

def get_pdf_length(pdf_document):
    data = pdf_document.write()
    return len(data)

def has_text(input_pdf):
    pdf_document = fitz.open(input_pdf)
    has_text = any(page.get_text() for page in pdf_document)
    pdf_document.close()
    return has_text



# Sử dụng hàm:
input_dir = r'C:\Users\PC\Downloads\ebook'  # Thay đổi đường dẫn đến thư mục chứa tệp PDF
output_dir = r'C:\Users\PC\Downloads\ebook\output'  # Thay đổi đường dẫn thư mục xuất
# split_pdfs_in_directory(input_dir, output_dir)



