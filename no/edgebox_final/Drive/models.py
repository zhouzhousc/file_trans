from django.db import models

# Create your models here.
from edgebox_final.base_model import BaseModel


class Drive(BaseModel):
    '''驱动程序管理模型类'''

    drive_name= models.CharField(max_length=30, verbose_name="驱动名称")
    drive_type= models.CharField(max_length=30, verbose_name="驱动类型")
    drive_path= models.CharField(max_length=150, verbose_name="驱动路径")
    drive_remark= models.CharField(max_length=150, verbose_name="驱动描述")

    class Meta:
        db_table = 'gateway_drive_list'
        verbose_name = '网关子设备列表信息'
        verbose_name_plural = verbose_name

# Drive.objects.create(drive_name = "ModbusRtuDemo", drive_type = "Modbus-RTU", drive_path = "sys", drive_remark = "Modbus_Rtu测试版本")
# Drive.objects.create(drive_name = "ModbusTcpDemo", drive_type = "Modbus-TCP", drive_path = "sys", drive_remark = "Modbus_Tcp测试版本")