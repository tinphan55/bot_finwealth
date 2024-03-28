from django.db import models
from datetime import datetime, timedelta, time
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save, post_delete,pre_save
from django.dispatch import receiver
import fitz  # PyMuPDF
import os
from django.core.exceptions import ValidationError
import re
import hashlib
from django.db.models import Max, Min,  Avg
from django.core.exceptions import ValidationError
from fuzzywuzzy import fuzz


# Create your models here.
def clean_text(text):
    # Loại bỏ các dấu xuống dòng và dấu cách dư thừa trong văn bản
    cleaned_text = re.sub(r'[\r\n]+', ' ', text)  # Loại bỏ dấu xuống dòng
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)  # Loại bỏ dấu cách dư thừa
    return cleaned_text

def pdf_text_extract(pdf_path, source, max_leng):
    doc = fitz.open(pdf_path)
    current_extracted_text = ""  # Biến lưu trữ extracted_text hiện tại
    num_pages = len(doc)  # Số lượng trang trong tệp PDF
    extracted_texts = []  # Danh sách các extracted_text
    for i, page in enumerate(doc):
        if i == num_pages - 1:
            break

        # Rút trích văn bản từ trang
        text_blocks = page.get_text('blocks')
        for block in text_blocks:
            for lines in block:
                lines = str(lines)
                # Kiểm tra xem dòng bắt đầu bằng "Biểu đồ" hoặc "Bảng"
                if lines.strip().startswith(("Biểu đồ", "Bảng")):
                    continue  # Bỏ qua dòng này
                if len(lines) > 100:
                    lines = lines.replace("Chúng tôi", source)
                    lines = lines.replace("chúng tôi", source)
                    lines =clean_text(lines)
                    current_extracted_text += lines
    if len(current_extracted_text) <= max_leng:
        extracted_texts.append(current_extracted_text)
    else:
        while len(current_extracted_text) > max_leng:
            last_period_index = current_extracted_text.rfind(". ", 0, max_leng)
            if last_period_index != -1:
                extracted_text = current_extracted_text[:last_period_index + 1]
                remaining_text = current_extracted_text[last_period_index + 1:]
            else:
                extracted_text = current_extracted_text[:max_leng-5]
                remaining_text = current_extracted_text[max_leng-5:]

            # Thêm extracted_text vào danh sách extracted_texts
            extracted_texts.append(extracted_text)
            # Gán remaining_text cho current_extracted_text để kiểm tra tiếp
            current_extracted_text = remaining_text
        

        if current_extracted_text:
            # Thêm extracted_text cuối cùng vào danh sách extracted_texts nếu còn dư
            extracted_texts.append(current_extracted_text)
    
    return extracted_texts



class DateTrading(models.Model):
    date = models.DateField(unique=False)
    description = models.TextField(max_length=255, blank=True)
    def __str__(self):
        return str(self.date) 
    class Meta:
         verbose_name = 'Ngày giao dịch'
         verbose_name_plural = 'Ngày giao dịch'

class StockPrice(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()#auto_now_add=True)
    open = models.FloatField()
    high =models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume =models.FloatField()
    date_time = models.DateTimeField(default=datetime.now)
    
    def __str__(self):
        return str(self.ticker) +str("_")+ str(self.date)
    
class StockPriceFilter(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()#auto_now_add=True)
    open = models.FloatField()
    high =models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume =models.FloatField()
    date_time = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return str(self.ticker) + str(self.date)

class SectorListName(models.Model):
    ticker = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

class SectorPrice(models.Model):
    ticker = models.CharField(max_length=10)
    date = models.DateField()#auto_now_add=True)
    open = models.FloatField()
    high =models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume =models.FloatField()
    date_time = models.DateTimeField(default=datetime.now)
    
    def __str__(self):
        return str(self.ticker) +str("_")+ str(self.date)


class StockOverview(models.Model):
    ticker = models.CharField(max_length=15,  verbose_name = 'Cổ phiếu' ) 
    company_name  = models.CharField(max_length=400,verbose_name='Tên công ty') 
    stock_exchange = models.CharField(max_length=400,verbose_name='Sàn niêm yết')
    listed_date= models.DateField(verbose_name='Ngày niêm yết')
    introduce = models.TextField(null=True,blank=True,verbose_name='Giới thiệu')
    def __str__(self):
        return self.ticker
    
class StockShareholder(models.Model):
    ticker = models.ForeignKey(StockOverview,on_delete=models.CASCADE,verbose_name = 'Cổ phiếu' )
    shareholder_name = models.CharField(max_length=400)
    role_type = models.CharField(max_length=50)
    number_of_shares = models.FloatField()
    ownership_pct = models.FloatField()
    effective_date = models.DateField()

    def __str__(self):
        return self.ticker.ticker
  

class StockOverviewDataTrading(models.Model):
    ticker = models.ForeignKey(StockOverview, on_delete=models.CASCADE, verbose_name='Cổ phiếu')
    price = models.FloatField(default=0, verbose_name='Giá thị trường')
    marketcap = models.FloatField(default=0, verbose_name='Market Cap')
    volume_avg_cr_10d = models.FloatField(default=0, verbose_name='Volume Average CR 10D')
    volume_avg_cr_20d = models.FloatField(default=0, verbose_name='Volume Average CR 20D')
    volume_avg_cr_50d = models.FloatField(default=0, verbose_name='Volume Average CR 50D')
    volume_avg_cr_100d = models.FloatField(default=0, verbose_name='Volume Average CR 100D')
    volume_avg_cr_200d = models.FloatField(default=0, verbose_name='Volume Average CR 200D')
    price_highest_cr_52w = models.FloatField(default=0, verbose_name='Price Highest CR 52W')
    price_lowest_cr_52w = models.FloatField(default=0, verbose_name='Price Lowest CR 52W')
    outstanding_shares = models.FloatField(default=0, verbose_name='Outstanding Shares')
    freefloat = models.FloatField(default=0, verbose_name='Free Float')
    beta = models.FloatField(default=0, verbose_name='Beta')
    price_to_earnings = models.FloatField(default=0, verbose_name='Price to Earnings')
    price_to_book = models.FloatField(default=0, verbose_name='Price to Book')
    dividend_yield = models.FloatField(default=0, verbose_name='Dividend Yield')
    bvps_cr = models.FloatField(default=0, verbose_name='BVPS CR')
    roae_tr_avg5q = models.FloatField(default=0, verbose_name='ROAE TR AVG5Q')
    roaa_tr_avg5q = models.FloatField(default=0, verbose_name='ROAA TR AVG5Q')
    eps_tr = models.FloatField(default=0, verbose_name='EPS TR')
    avg_target_price = models.FloatField(default=0, verbose_name='avg_target_price')
    up_size = models.FloatField(default=0, verbose_name='up size')
    def __str__(self):
        return self.ticker.ticker

    def save(self, *args, **kwargs):
        # Calculate checksum and save the object
        self.price = StockPriceFilter.objects.filter(ticker = self.ticker).order_by('-date').first().close
        self.marketcap = self.outstanding_shares*self.price*1000
        if self.eps_tr:
            self.price_to_earnings = round(self.price*1000/self.eps_tr ,3)
        if self.bvps_cr:
            self.price_to_book = round(self.price*1000/self.bvps_cr,3)
        self.price_highest_cr_52w = StockPriceFilter.objects.filter(ticker =self.ticker).aggregate(max_close=Max('close'))['max_close']
        self.price_lowest_cr_52w  = StockPriceFilter.objects.filter(ticker =self.ticker).aggregate(min_close=Min('close'))['min_close']
        self.volume_avg_cr_10d = round(StockPriceFilter.objects.filter(ticker =self.ticker).order_by('-date_time')[:10].aggregate(avg_volume_10=Avg('volume'))['avg_volume_10'],3)
        self.volume_avg_cr_20d = round(StockPriceFilter.objects.filter(ticker =self.ticker).order_by('-date_time')[:20].aggregate(avg_volume_20=Avg('volume'))['avg_volume_20'],3)
        self.volume_avg_cr_50d = round(StockPriceFilter.objects.filter(ticker =self.ticker).order_by('-date_time')[:50].aggregate(avg_volume_50=Avg('volume'))['avg_volume_50'],3)
        self.volume_avg_cr_200d = round(StockPriceFilter.objects.filter(ticker =self.ticker).order_by('-date_time')[:200].aggregate(avg_volume_200=Avg('volume'))['avg_volume_200'],3)
        valuation = StockValuation.objects.filter(ticker__ticker = self.ticker)
        avg_target_price  = valuation.aggregate(avg_target_price=Avg('target_price'))['avg_target_price']
        if self.avg_target_price !=0:
            self.avg_target_price =round(avg_target_price,3)
            self.up_size = round(self.avg_target_price/self.price -1,3)
        super(StockOverviewDataTrading, self).save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Dữ liệu cơ bản'
        verbose_name_plural = 'Dữ liệu cơ bản'

    def __str__(self):
        return self.ticker.ticker

@receiver(post_save, sender=StockPriceFilter)
def save_model_stockoverviewdatatrading(sender, instance, created, **kwargs):
    try:
        stock_overview_data_trading = StockOverviewDataTrading.objects.get(ticker__ticker=instance.ticker)
        # Update existing instance
        # stock_overview_data_trading.some_field = instance.some_value
        stock_overview_data_trading.save()
    except StockOverviewDataTrading.DoesNotExist:
        # Create new instance if not found
        stock_overview_data_trading = StockOverviewDataTrading.objects.create(ticker__ticker=instance.ticker)
        # Set other fields if necessary
        # stock_overview_data_trading.some_field = instance.some_value
        stock_overview_data_trading.save()
    
class StockValuation(models.Model):
    ticker = models.ForeignKey(StockOverview,on_delete=models.CASCADE,verbose_name = 'Cổ phiếu' )
    firm = models.CharField(max_length=100)
    type = models.CharField(max_length=50,)
    report_date = models.DateField()
    source = models.CharField(max_length=50)
    report_price = models.FloatField()
    target_price = models.FloatField()

    def __str__(self):
        return self.ticker.ticker
    


class StockRatioData(models.Model):
    ticker = models.ForeignKey(StockOverview,on_delete=models.CASCADE,verbose_name = 'Cổ phiếu' )
    report_date = models.DateField()
    item_code = models.CharField(max_length=100)
    ratio_code = models.CharField(max_length=100)
    item_name = models.CharField(max_length=255)
    value = models.FloatField()

    def __str__(self):
        return self.ticker.ticker
    
class FundamentalAnalysisReport(models.Model):
    username = models.CharField(max_length=100,null=True, blank=True, verbose_name='Người chia sẽ')
    name = models.CharField(max_length=100, blank=True,null=True, verbose_name='Tên báo cáo')
    source = models.CharField(max_length=100, blank=True, verbose_name='Nguồn')
    modified_date = models.DateTimeField(auto_now=True ,verbose_name='Ngày tạo')
    valuation = models.FloatField(null=True, blank=True, verbose_name='Định giá')
    date = models.DateField(verbose_name='Ngày báo cáo')
    tags = models.ManyToManyField('Tag')
    file = models.FileField(upload_to='reports/', validators=[FileExtensionValidator(['pdf', 'docx'])], verbose_name='Tệp đính kèm')
    file_checksum = models.CharField(max_length=64, blank=True, verbose_name='Checksum của tệp')

    def clean(self):
        # Override clean method to check for duplicate file
        if self.file:
            # Calculate checksum of the file
            file_checksum = self.calculate_checksum(self.file)
            # Check if any other report already has this checksum
            if FundamentalAnalysisReport.objects.exclude(id=self.id).filter(file_checksum=file_checksum).exists():
                raise ValidationError('Báo cáo đã được tải lên')

    def calculate_checksum(self, file):
        checksum = hashlib.sha256()
        for chunk in file.chunks():
            checksum.update(chunk)
        return checksum.hexdigest()

    def save(self, *args, **kwargs):
        # Calculate checksum and save the object
        if not self.pk:
            self.file_checksum = self.calculate_checksum(self.file)
            if self.file:
                self.name = os.path.basename(self.file.name)
        
        super(FundamentalAnalysisReport, self).save(*args, **kwargs)
     
    
    class Meta:
        verbose_name = 'Báo cáo phân tích'
        verbose_name_plural = 'Báo cáo phân tích'
    
    def __str__(self):
        return str(self.name) 



    
class FundamentalAnalysisReportSegment(models.Model):
    report = models.ForeignKey(FundamentalAnalysisReport,on_delete=models.CASCADE,verbose_name = 'Báo cáo' )
    segment = models.TextField(verbose_name='Nội dung',null=True, blank=True)
    class Meta:
        verbose_name = 'Nội dung báo cáo'
        verbose_name_plural = 'Nội dung báo cáo'
  
    


@receiver(post_save, sender=FundamentalAnalysisReport)
def create_report_segment(sender, instance, created, **kwargs):
    if created:
        pdf_path = instance.file.path
        source = instance.source
        extracted_text = pdf_text_extract(pdf_path, source,5000)

        for text in extracted_text:
            segment = FundamentalAnalysisReportSegment(report=instance, segment=text)
            segment.save()
     
class News(models.Model):
    username = models.CharField(max_length=100,null=True, blank=True, verbose_name='Người chia sẽ')
    source = models.CharField(max_length=100, blank=True, verbose_name='Nguồn')
    modified_date = models.DateTimeField(auto_now=True ,verbose_name='Ngày tạo')
    tags = models.CharField(max_length=100, blank=True, verbose_name='Cổ phiếu')
    content = models.TextField(verbose_name = 'Nội dung')

    class Meta:
        verbose_name = 'Thông tin'
        verbose_name_plural = 'Thông tin'


    def clean(self):
        similarity_threshold = 80  # Ngưỡng tương đồng mong muốn (ở đây là 80%)
        existing_news = News.objects.exclude(pk=self.pk)

        for news in existing_news:
            similarity_ratio = fuzz.partial_ratio(self.content, news.content)
            if similarity_ratio >= similarity_threshold:
                raise ValidationError("Nội dung quá giống với nội dung đã tồn tại")
        super().clean()
        
    

class Tag (models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.name}"

# def save_fa():
#     fa = StockFundamentalData.objects.all()
#     for self in fa:
#         if self.roa:
#             #roa từ 0-25 có điểm từ 50-90
#             if self.roa > 0 and self.roa <=25 :
#                 rating_roa = (self.roa-0) /(25-0)*40+50
#             elif self.roa >25:
#                 rating_roa = 100
#             else:
#                 rating_roa = 0
#         else:
#             rating_roa = 0
#         if self.roe:
#             if self.roe >0 and self.roe <=25:
#                 rating_roe = (self.roe-0) /(25-0)*40+50
#             elif self.roe >25:
#                 rating_roe = 100
#             else:
#                 rating_roe = 0
#         else:
#             rating_roe = 0
#         self.growth_rating = round(rating_roa*0.5 + rating_roe*0.5,2)
        
#         if self.dept_ratio:
#             #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
#             if self.dept_ratio > 0 and self.dept_ratio <=1 :
#                 rating_dept = 100 - (self.dept_ratio-0) /(1-0)*(100-80)
#             elif self.dept_ratio >1 and self.dept_ratio<=5:
#                 rating_dept = 80 - (self.dept_ratio-1) /(5-1)*(80-50)
#             elif self.dept_ratio >5 and self.dept_ratio<=10:
#                 rating_dept = 50 - (self.dept_ratio-5) /(10-5)*(50-20)
#             elif self.dept_ratio >10:
#                 rating_dept = 10
#             else:
#                 rating_dept = 0
#         else:
#             rating_dept = 0
#         self.stable_rating  = round(rating_dept,2)
#         self.save()
#     return
       
    
        


class IncomeStatement(models.Model):
    ticker = models.ForeignKey(StockOverview, on_delete=models.CASCADE, verbose_name='Cổ phiếu')
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    parent_id = models.IntegerField()
    expanded = models.BooleanField()
    level = models.IntegerField()
    field = models.CharField(max_length=255, blank=True, null=True)
    # Giả sử Period sẽ được lưu dưới dạng CharField với độ dài đủ lớn để chứa chuỗi "Q4 2023"
    period = models.CharField(max_length=10)
    year = models.IntegerField()
    quarter = models.IntegerField()
    value = models.FloatField()

    def __str__(self):
        return f"IncomeStatement - id: {self.id}, name: {self.name}, period: {self.period}"


class BalanceSheet(models.Model):
    ticker = models.ForeignKey(StockOverview, on_delete=models.CASCADE, verbose_name='Cổ phiếu')
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    parent_id = models.IntegerField()
    expanded = models.BooleanField()
    level = models.IntegerField()
    field = models.CharField(max_length=255, blank=True, null=True)
    period = models.CharField(max_length=10)
    year = models.IntegerField()
    quarter = models.IntegerField()
    value = models.FloatField(null=True)  # Cho phép giá trị là null

    def __str__(self):
        return f"BalanceSheet - id: {self.id}, name: {self.name}, period: {self.period}"
