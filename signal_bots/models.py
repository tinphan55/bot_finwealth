from django.db import models
from manage_bots.models import StrategyTrading
from django.dispatch import receiver
from django.db.models.signals import post_save
from telegram_bot.models import *
from data_source.models import *
from telegram import Bot

class Signal(models.Model):
    STATUS = [
        ('takeprofit', 'Chốt lời'),
        ('cutloss', 'Cắt lỗ'),]
    ticker = models.CharField(max_length=10, verbose_name = 'Cổ phiếu')
    date = models.DateField(verbose_name = 'Ngày cho tín hiệu')
    close = models.FloatField(default=0, verbose_name = 'Giá mua')
    milestone = models.FloatField(default=0, verbose_name = 'Mốc an toàn')
    signal = models.CharField(max_length=50, verbose_name = 'Tín hiệu')
    ratio_cutloss = models.FloatField(default=0, verbose_name = 'Tỷ lệ cắt lỗ tối ưu')
    strategy = models.ForeignKey(StrategyTrading,on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'Chiến lược')
    modified_date = models.DateTimeField(auto_now=True, verbose_name = 'Ngày tạo')
    is_closed = models.BooleanField(default=False, verbose_name='Đã chốt')
    cutloss_price = models.FloatField(default=0, verbose_name ='Giá cắt lỗ')
    take_profit_price = models.FloatField(default=0, verbose_name ='Giá chốt lời')
    is_adjust_divident = models.BooleanField(default=False)
    noted = models.CharField(max_length=20, choices=STATUS, null=True, blank=True, verbose_name='Trạng thái')
    date_closed_deal = models.DateField(null=True, blank=True)
    market_price = models.FloatField(default=0, verbose_name = 'Giá thị trường')
    wavefoot = models.FloatField(default=0, verbose_name = '% tăng giảm')
    rating_total = models.FloatField(default=0,verbose_name = 'Điểm kỹ thuật')
    rating_fundamental= models.FloatField(default=0,verbose_name = 'Điểm cơ bản')
    exit_price =models.FloatField(null=True, blank=True,verbose_name = 'Giá đóng')
    accumulation = models.IntegerField(null=True, blank=True,verbose_name = 'Ngày tích lũy')
    is_noti =models.BooleanField(default=False, verbose_name='Có thông báo')
    class Meta:
        verbose_name = 'Tín hiệu giao dịch'
        verbose_name_plural = 'Tín hiệu giao dịch'
    

    def __str__(self):
        return str(self.ticker) + str(self.strategy)
    
@receiver(post_save, sender=StockPriceFilter)
def create_cutloss_signal(sender, instance, created, **kwargs):
    if not created:
        signal  = Signal.objects.filter(ticker=instance.ticker, strategy=1,is_closed=False )  
        external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )
        for stock in signal:
            stock.market_price = instance.close
            stock.wavefoot = round((stock.market_price/stock.close - 1) * 100, 2)
            stock.save()
            if stock.take_profit_price<= instance.close:
                stock.exit_price = stock.take_profit_price
                stock.take_profit_price = round(stock.take_profit_price + stock.ratio_cutloss*stock.close/100,2)
                stock.save()
                for group in external_room:
                        bot = Bot(token=group.token.token)
                        # bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
                        try:
                            bot.send_message(
                                chat_id=group.chat_id, #room Khách hàng
                                # chat_id='-870288807',
                                text=f"Tín hiệu {stock.ticker} mua tại ngày {stock.date} đã vượt mốc chốt lời, giá chốt lời mới được nâng thêm 1R là {stock.take_profit_price} ")  
                        except:
                            pass
            new_time = time(00, 00, 0)
            today = datetime.now().date() 
            date_signal = datetime.combine(stock.date, new_time)
            date_check = difine_date_stock_on_account(date_signal).date()
            if stock.exit_price >= instance.close and today >=date_check:
                stock.is_closed = True
                stock.date_closed_deal = today
                stock.wavefoot = round((stock.exit_price/stock.close-1)*100,2)
                if stock.wavefoot > 0:
                    stock.noted ='takeprofit'
                    note = 'CHỐT LỜI'
                else:
                    stock.noted ='cutloss'
                    note = 'CẮT LỖ'
                stock.save()
                for group in external_room:
                    bot = Bot(token=group.token.token)
                    try:
                        bot.send_message(
                            chat_id=group.chat_id, #room Khách hàng
                            text=f"Có tín hiệu {note} cho cổ phiếu {stock.ticker} mua tại ngày {stock.date} với tỷ lệ lợi nhuận là {stock.wavefoot}%")  
                    except:
                        pass
                
                    
                       
            
@receiver(post_save,sender = Signal)
def sent_noti_telegram_signal(sender, instance, created, **kwargs):
    if not created and instance.is_noti ==True and instance.date ==datetime.now().date():
        # lated_signal = Signal.objects.filter(ticker=instance.ticker).order_by('-date').first()
        # if lated_signal.date + timedelta(days=3) > instance.date:
            analysis = FundamentalAnalysis.objects.filter(ticker__ticker=instance.ticker).order_by('-modified_date').first()
            external_room = ChatGroupTelegram.objects.filter(type = 'external',is_signal =True,rank ='1' )
            mesage =f"Tín hiệu {instance.signal} cp {instance.ticker} theo chiến lược {instance.strategy} , tỷ lệ cắt lỗ tối ưu là {instance.ratio_cutloss}%, điểm tổng hợp là {instance.rating_total}, điểm cơ bản là {instance.rating_fundamental} "
            if instance.accumulation and instance.accumulation > 0:
                mesage += f", số ngày tích lũy trước tăng là {instance.accumulation} \n"
            else:
                mesage += f"\n"
            if analysis and analysis.modified_date >= (datetime.now() - timedelta(days=6 * 30)):
                    mesage +=f"Thông tin cổ phiếu {instance.signal}:\n"
                    mesage += f"Ngày báo cáo {analysis.date}. P/E: {analysis.ticker.p_e}, P/B: {analysis.ticker.p_b}, Định giá {analysis.valuation}:\n"
                    mesage += f"{analysis.info}.\n"
                    mesage += f"Nguồn {analysis.source}"
            # bot = Bot(token='5881451311:AAEJYKo0ttHU0_Ztv3oGuf-rfFrGgajjtEk')
            # bot.send_message(
            #         chat_id='-870288807', 
            #         text=mesage)
            for group in external_room:
                bot = Bot(token=group.token.token)
                try:
                    bot.send_message(
                        chat_id=group.chat_id, #room Khách hàng
                        text=mesage)  
                except:
                    pass
