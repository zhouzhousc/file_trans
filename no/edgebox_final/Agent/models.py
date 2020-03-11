from django.db import models

# Create your models here.
from edgebox_final.base_model import BaseModel

class RegisterInfo(BaseModel):
    '''网关产品注册信息模型类'''
    gateway_name = models.CharField(max_length=30, verbose_name="网关唯一名称")
    gateway_key = models.CharField(max_length=100, verbose_name="网关id")
    gateway_secret = models.CharField(max_length=200, verbose_name="网关秘钥")
    gateway_tokenapi = models.CharField(max_length=200, verbose_name="网关鉴权URl")
    gateway_subdevice_num = models.IntegerField(default=0, verbose_name="网关子设备数量")
    gateway_model = models.CharField(max_length=30, verbose_name="网关型号")
    gateway_trade_name = models.CharField(max_length=30, verbose_name="网关厂商名称")
    gateway_registration_time = models.DateTimeField(verbose_name="网关注册时间")
    gateway_location = models.CharField(max_length=30, verbose_name="网关位置信息")
    gateway_iotid = models.CharField(max_length=30, default="", verbose_name="用户名")
    gateway_iottoken = models.CharField(max_length=30, default="", verbose_name="密码")
    gateway_iotport = models.CharField(max_length=30, default="", verbose_name="端口")
    gateway_iothost = models.CharField(max_length=30, default="", verbose_name="ip地址")
    gateway_remark = models.CharField(max_length=50, verbose_name="网关描述")

    class Meta:
        db_table = 'gateway_register_info'
        verbose_name = '网关产品注册信息'
        verbose_name_plural = verbose_name