from django.db import models
from django.contrib.auth.models import User
from data_source.models import News, FundamentalAnalysisReport
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from datetime import datetime

# Create your models here.
class Member(models.Model):
    id_member= models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    phone = models.IntegerField(null=True)
    joined_date = models.DateField(null=True)
    avatar = models.ImageField(upload_to='member', null = True, blank=True,default = "")
    total_points = models.IntegerField(default=0, verbose_name='Tổng điểm')

    class Meta:
        verbose_name = 'Cập nhật thêm thông tin(bắc buộc)'
        verbose_name_plural = 'Cập nhật thêm thông tin(bắc buộc)'
    
    def __str__(self):
        return self.id_member.username

class Point(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    task_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm làm nhiệm vụ')
    share_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm chia sẻ')
    trade_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm mua bán')
    promotion_points = models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm khuyến mãi')
    used_point =models.IntegerField(default=0,null=True,blank=True, verbose_name='Điểm đã sử dụng')
    class Meta:
        verbose_name = 'Tổng điểm'
        verbose_name_plural = 'Tổng điểm'
    @property
    def total_points(self):
        return self.task_points + self.share_points + self.trade_points + self.promotion_points +self.used_point

    def __str__(self):
        return f"{self.user.id_member} - Total Points: {self.total_points}"

@receiver([post_save,post_delete] ,sender=News)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user = Member.objects.get(id_member__username = instance.username)
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
    user = Member.objects.get(id_member__username = instance.username)
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
    user.total_points = point.total_points
    user.save()


class SharePoint(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='received_points', verbose_name='Người nhận')
    points = models.IntegerField(verbose_name='Số điểm chia sẻ')
    description = models.TextField(null=True, blank =True,verbose_name='Diễn giải')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')

    class Meta:
        verbose_name = 'Chia sẻ điểm'
        verbose_name_plural = 'Chia sẻ điểm'

    def __str__(self):
        return f"Chia sẻ từ {self.recipient.id_member} - {self.points} points"
    
    
    # def clean(self):
    #     print (self.user)
    #     total_point = self.user.total_points
    #     if self.points > total_point:
    #         raise ValidationError("Số điểm chia sẻ không được lớn hơn số điểm bạn có.")

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        total_point = getattr(self.user, 'total_points', None)
        if total_point is not None and self.points > total_point:
            raise ValidationError("Số điểm chia sẻ không được lớn hơn số điểm bạn có.")
    
@receiver([post_save,post_delete] ,sender=SharePoint)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user_give = Member.objects.get(id_member__username = instance.user)
    user_recipient = Member.objects.get(id_member__username = instance.recipient)
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
    user = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='Người dùng')
    points = models.IntegerField(verbose_name='Số điểm')
    description = models.TextField(verbose_name='Mô tả')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')

    def __str__(self):
        return f"Promotion Point for {self.user.id_member}"

    class Meta:
        verbose_name = 'Điểm thưởng'
        verbose_name_plural = 'Điểm thưởng'

@receiver([post_save,post_delete] ,sender=PromotionPoint)
def update_user_points(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    user = Member.objects.get(id_member__username = instance.user)
    point = Point.objects.get(user=user)
    if created:
        point.promotion_points += instance.points
        point.save()
    else:
        promotion_count =PromotionPoint.objects.filter(user=instance.user)
        point.promotion_points = sum(item.points for item in promotion_count)
        point.save()
    user.total_points = point.total_points
    user.save()

def cal_used_point():
    point = Point.objects.all()
    today = datetime.now().date()
    for item in point:
        #last_login = point.user.id_member.last_login.date()
        if item.total_points >0: #and today==last_login:
            item.used_point -=1
            item.save()


