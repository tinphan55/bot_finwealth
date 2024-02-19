from django.db import models
from datetime import datetime, timedelta, time
# Create your models here.

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



class StockFundamentalData(models.Model):
    ticker = models.CharField(max_length=15,  verbose_name = 'Cổ phiếu' ) 
    name  = models.CharField(max_length=200,verbose_name='Tên công ty') 
    stock_exchange = models.CharField(max_length=200,verbose_name='Sàn niêm yến')
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
    
class FundamentalAnalysis(models.Model):
    ticker = models.ForeignKey(StockFundamentalData,on_delete=models.CASCADE, null=True, blank=True,verbose_name = 'Cổ phiếu' )
    source = models.CharField(max_length=100,null=True, blank=True,verbose_name = 'Nguồn')
    modified_date = models.DateTimeField(auto_now=True ,verbose_name = 'Ngày tạo')
    info = models.TextField(max_length=2000, verbose_name = 'Nội dung')
    valuation = models.FloatField(null=True, blank=True, verbose_name = 'Định giá')
    date = models.DateField(null=True, blank=True, verbose_name = 'Ngày báo cáo')
    
    class Meta:
        verbose_name = 'Báo cáo phân tích'
        verbose_name_plural = 'Báo cáo phân tích'

   

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
       
    
        
    

