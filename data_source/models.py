from django.db import models
from datetime import datetime, timedelta, time
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save, post_delete,pre_save
from django.dispatch import receiver
import fitz  # PyMuPDF
from docx import Document

# Create your models here.

def pdf_text_extract(pdf_path,source):
    doc = fitz.open(pdf_path)

    num_pages = len(doc)  # Số lượng trang trong tệp PDF
    extracted_text = []  # Danh sách văn bản đã rút trích từ PDF

    for i, page in enumerate(doc):
        if i == num_pages - 1:
            break  # Kết thúc vòng lặp nếu đó là trang cuối

        # Rút trích văn bản từ trang
        text_blocks = page.get_text('blocks')
        for block in text_blocks:
            for lines in block:
                lines = str(lines)
                if len(lines) > 100:
                    lines = lines.replace("Chúng tôi", source)
                    lines = lines.replace("chúng tôi", source)
                    extracted_text.append(lines)

    return extracted_text


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
    company_name  = models.CharField(max_length=200,verbose_name='Tên công ty') 
    stock_exchange = models.CharField(max_length=200,verbose_name='Sàn niêm yết')
    listed_date= models.DateField(max_length=200,verbose_name='Ngày niêm yết')
    introduce = models.CharField(max_length=200,verbose_name='Giới thiệu')
    

  

class StockFundamentalData(models.Model):
    ticker = models.ForeignKey(StockOverview,on_delete=models.CASCADE,verbose_name = 'Cổ phiếu' )
    eps = models.FloatField(null=True, verbose_name = 'EPS')
    roa = models.FloatField(null=True, verbose_name = 'ROA')
    roe = models.FloatField(null=True, verbose_name = 'ROE')
    dept_ratio = models.FloatField(null=True, verbose_name = 'Tỷ lệ nợ')
    bvps = models.FloatField( null=True,verbose_name = 'BVPS')
    market_price = models.FloatField( null=True,verbose_name = 'Giá thị trường')
    p_e = models.FloatField( null=True,verbose_name = 'P/E')
    p_b= models.FloatField( null=True,verbose_name = 'P/B')
    growth_rating = models.FloatField(null=True,verbose_name = 'Điểm tăng trưởng')
    stable_rating = models.FloatField(null=True,verbose_name = 'Điểm an toàn')
    valuation_rating = models.FloatField(null=True,verbose_name = 'Điểm định giá')
    fundamental_rating  = models.FloatField(null=True,verbose_name = 'Điểm cơ bản')

    class Meta:
        verbose_name = 'Dữ liệu cơ bản'
        verbose_name_plural = 'Dữ liệu cơ bản'

    def __str__(self):
        return self.ticker
    


class FundamentalAnalysisReport(models.Model):
    source = models.CharField(max_length=100, blank=True, verbose_name='Nguồn')
    modified_date = models.DateTimeField(auto_now=True ,verbose_name='Ngày tạo')
    content = models.TextField(verbose_name='Nội dung',null=True, blank=True)
    valuation = models.FloatField(null=True, blank=True, verbose_name='Định giá')
    date = models.DateField(verbose_name='Ngày báo cáo')
    tags = models.ManyToManyField('Tag')
    file = models.FileField(upload_to='reports/', validators=[FileExtensionValidator(['pdf', 'docx'])], verbose_name='Tệp đính kèm')

    class Meta:
        verbose_name = 'Báo cáo phân tích'
        verbose_name_plural = 'Báo cáo phân tích'
    
    def save(self, *args, **kwargs):
        if self.file:
            self.content = pdf_text_extract(self.file.path, self.source)
            # Xóa trường self.file

        super(FundamentalAnalysisReport, self).save(*args, **kwargs)
    

   

class Tag (models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.name}"

def save_fa():
    fa = StockFundamentalData.objects.all()
    for self in fa:
        if self.roa:
            #roa từ 0-25 có điểm từ 50-90
            if self.roa > 0 and self.roa <=25 :
                rating_roa = (self.roa-0) /(25-0)*40+50
            elif self.roa >25:
                rating_roa = 100
            else:
                rating_roa = 0
        else:
            rating_roa = 0
        if self.roe:
            if self.roe >0 and self.roe <=25:
                rating_roe = (self.roe-0) /(25-0)*40+50
            elif self.roe >25:
                rating_roe = 100
            else:
                rating_roe = 0
        else:
            rating_roe = 0
        self.growth_rating = round(rating_roa*0.5 + rating_roe*0.5,2)
        
        if self.dept_ratio:
            #dept từ 0-1: 80-100 điểm, 1-5: 50-80 điểm, 5-10: 20 - 50, trên 10: 20
            if self.dept_ratio > 0 and self.dept_ratio <=1 :
                rating_dept = 100 - (self.dept_ratio-0) /(1-0)*(100-80)
            elif self.dept_ratio >1 and self.dept_ratio<=5:
                rating_dept = 80 - (self.dept_ratio-1) /(5-1)*(80-50)
            elif self.dept_ratio >5 and self.dept_ratio<=10:
                rating_dept = 50 - (self.dept_ratio-5) /(10-5)*(50-20)
            elif self.dept_ratio >10:
                rating_dept = 10
            else:
                rating_dept = 0
        else:
            rating_dept = 0
        self.stable_rating  = round(rating_dept,2)
        self.save()
    return
       
    
        
    



   

