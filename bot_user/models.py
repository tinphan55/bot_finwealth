from django.db import models
from django.contrib.auth.models import User
from data_source.models import News, FundamentalAnalysisReport
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class UserInfo(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, default = '1q2w3e4r')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    total_points = models.IntegerField(default=0, verbose_name='Tổng điểm')
    

    def __str__(self):
        return self.username
    



class Point(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    task_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm làm nhiệm vụ')
    share_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm chia sẻ')
    trade_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm mua bán')
    promotion_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm khuyến mãi')
    used_point =models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm đã sử dụng')
    @property
    def total_points(self):

        return self.task_points + self.share_points + self.trade_points + self.promotion_points +self.used_point

    def __str__(self):
        return f"{self.user.username} - Total Points: {self.total_points}"

@receiver([post_save,post_delete] ,sender=News)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user = UserInfo.objects.get(username = instance.username)
    if created:
        point, created = Point.objects.get_or_create(user=user)
        point.task_points += 1
        point.save()
    else:
        news_count = News.objects.filter(username=instance.username).count()
        report_count =FundamentalAnalysisReport.objects.filter(username=instance.username).count()
        point = Point.objects.get(user=user)
        point.task_points = news_count+report_count*2
        point.save()
    user.total_points = point.total_points
    user.save()

@receiver([post_save,post_delete] ,sender=FundamentalAnalysisReport)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user = UserInfo.objects.get(username = instance.username)
    if created:
        point, created = Point.objects.get_or_create(user=user)
        point.task_points += 2
        point.save()
    else:
        news_count = News.objects.filter(username=instance.username).count()
        report_count =FundamentalAnalysisReport.objects.filter(username=instance.username).count()
        point = Point.objects.get(user=user)
        point.task_points = news_count+report_count*2
        point.save()


class SharePoint(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    recipient = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='received_points', verbose_name='Người nhận point')
    points = models.IntegerField(verbose_name='Số điểm chia sẻ')
    description = models.TextField(null=True, blank =True,verbose_name='Diễn giải')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')

    def __str__(self):
        return f"Chia sẻ từ {self.recipient.username} - {self.points} points"
    
    def clean(self):
        total_point = Point.objects.get(user=self.user).total_points
        if self.points > total_point:
            raise ValidationError("Số điểm chia sẻ không được lớn hơn số điểm bạn có.")
    
@receiver([post_save,post_delete] ,sender=SharePoint)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user_give = UserInfo.objects.get(username = instance.user)
    user_recipient = UserInfo.objects.get(username = instance.recipient)
    point_user_give, created_give = Point.objects.get_or_create(user=user_give)
    point_user_recipient, created_recipient = Point.objects.get_or_create(user=user_recipient)
    if created:
     
        point_user_give.share_points -= instance.points
        point_user_recipient.share_points += instance.points
        
    else:
   
        point_user_give_ifgive= SharePoint.objects.filter(user =user_give)
        point_user_give_ifrecipient =SharePoint.objects.filter(recipient =user_give )
        net_point1 = -sum(item.points for item in point_user_give_ifgive) + sum(item.points for item in point_user_give_ifrecipient )
    
        point_user_give.share_points = net_point1

        point_user_recipient_ifgive= SharePoint.objects.filter(user =user_recipient)
        point_user_recipient_ifrecipient =SharePoint.objects.filter(recipient = user_recipient)
        net_point2 = -sum(item.points for item in point_user_recipient_ifgive) + sum(item.points for item in point_user_recipient_ifrecipient )
        point_user_recipient.share_points  =net_point2

    
    point_user_give.save()
    point_user_recipient.save()

    user_give.total_points = point_user_give.total_points
    user_recipient.total_points = point_user_recipient.total_points
    user_give.save()
    user_recipient.save()


class PromotionPoint(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, verbose_name='Người dùng')
    points = models.IntegerField(verbose_name='Số điểm')
    description = models.TextField(verbose_name='Mô tả')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')

    def __str__(self):
        return f"Promotion Point for {self.user.username}"

    class Meta:
        verbose_name = 'Promotion Point'
        verbose_name_plural = 'Promotion Points'

@receiver([post_save,post_delete] ,sender=PromotionPoint)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user = UserInfo.objects.get(username = instance.user)
    point = Point.objects.get_or_create(user=user)
    if created:
        point.promotion_points += instance.points
        point.save()
    else:
        promotion_count =PromotionPoint.objects.filter(user=instance.user)
        point.promotion_points = sum(item.points for item in promotion_count)
        point.save()


def cal_used_point():
    point = Point.objects.all()
    for item in point:
        if item.total_points >0:
            item.used_point -=1
            item.save()