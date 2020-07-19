from django.db import models, connection

# Create your models here.
from edgebox_final.base_model import BaseModel



class SubDevice(BaseModel):
    '''子设备列表模型类'''

    subdevice_name= models.CharField(max_length=30, unique=True, verbose_name="子设备名称")
    subdevice_key= models.CharField(default="", max_length=100, verbose_name="子设备id")
    subdevice_secret= models.CharField(default="", max_length=200, verbose_name="子设备secret")
    subdevice_position= models.CharField(max_length=30, verbose_name="子设备位置")
    subdevice_model= models.CharField(max_length=30, verbose_name="子设备型号")
    subdevice_type= models.CharField(max_length=30, verbose_name="子设备类型")
    subdevice_remark= models.CharField(max_length=50, verbose_name="子设备描述")
    subdevice_online_time= models.DateTimeField(auto_now_add=True, verbose_name="最近上线时间")
    subdevice_status= models.CharField(max_length=30, default="离线", verbose_name="子设备运行状态")
    subdevice_enable= models.BooleanField(default=True, verbose_name="子设备激活使能")

    class Meta:
        db_table = 'gateway_subdevice_list'
        verbose_name = '网关子设备列表信息'
        verbose_name_plural = verbose_name


# 设备模板库
class EquipmentTemplateRtu(BaseModel):
    '''
    ModeBus Rtu 设备模板库Rtu 表 简称 etr
    '''
    FORMAT_CHOICES = (
        (0, "2进制输出"),
        (1, "10进制输出"),
        (2, "16进制输出"),
        (3, "IEEE-754输出")
    )

    etr_name        = models.CharField(max_length=30, verbose_name="模板名称")
    etr_remark      = models.CharField(max_length=30, verbose_name="模板描述")
    etr_accordname  = models.CharField(max_length=30, default="ModBus-RTU", verbose_name="模板协议名称")
    etr_code       = models.CharField(max_length=30, verbose_name="模板下发设备指令id")
    etr_register    = models.CharField(max_length=30, verbose_name="模板下发设备寄存器地址")
    etr_register_num= models.CharField(max_length=30, verbose_name="模板下发设备寄存器个数")
    etr_param       = models.CharField(max_length=50, verbose_name="模板返回设备数据的参数名")
    etr_format      = models.SmallIntegerField(default=0, choices=FORMAT_CHOICES, verbose_name="模板返回设备数据格式")
    etr_rule_sign   = models.CharField(max_length=30, null=True, verbose_name="模板返回数据计算符号")
    etr_rule_number = models.CharField(max_length=30, null=True, verbose_name="模板返回数据计算数字")

    class Meta:
        db_table = 'gateway_equipmenttemplatertu'
        verbose_name = 'ModBusRtu设备模板库'
        verbose_name_plural = verbose_name


class applyTemplateRtuInterface(BaseModel):
    '''
    应用Rtu设备模板接口信息
    '''
    apply_rtu_template = models.CharField(max_length=30, verbose_name="应用RTU接口模板名称")
    apply_rtu_device = models.CharField(max_length=30, verbose_name="应用RTU接口设备名称")
    apply_rtu_com = models.CharField(max_length=30, verbose_name="应用RTU接口串口号")
    apply_rtu_botelv = models.CharField(max_length=30, verbose_name="应用RTU接口波特率")
    apply_rtu_databit = models.CharField(max_length=30, verbose_name="应用RTU接口数据位")
    apply_rtu_parity = models.CharField(max_length=30, verbose_name="应用RTU接口奇偶校验")
    apply_rtu_stopbit = models.CharField(max_length=30, verbose_name="应用RTU接口停止位")
    apply_rtu_timeout = models.CharField(max_length=30, verbose_name="应用RTU接口回复超时")
    apply_rtu_cycle = models.CharField(max_length=30, verbose_name="应用RTU接口读写周期")
    apply_rtu_subordinate = models.CharField(max_length=30, verbose_name="应用RTU接口subordinate地址")
    apply_rtu_drive = models.CharField(max_length=30, verbose_name="应用RTU接口绑定的驱动名称")
    apply_rtu_active = models.BooleanField(default=True, verbose_name="应用RTU接口是否启动")

    class Meta:
        db_table = 'gateway_apply_template_rtu_interface'
        verbose_name = '应用RTU设备模板库记录'
        verbose_name_plural = verbose_name

class applyTemplateTcpInterface(BaseModel):
    '''
    应用Tcp设备模板接口信息
    '''
    apply_tcp_template = models.CharField(max_length=30, verbose_name="应用TCP接口模板名称")
    apply_tcp_device = models.CharField(max_length=30, verbose_name="应用TCP接口设备名称")
    apply_tcp_ip = models.CharField(max_length=30, verbose_name="应用TCP接口IP地址")
    apply_tcp_port = models.CharField(max_length=30, verbose_name="应用TCP接口端口号")
    apply_tcp_timeout = models.CharField(max_length=30, verbose_name="应用TCP接口回复超时")
    apply_tcp_cycle = models.CharField(max_length=30, verbose_name="应用TCP接口读写周期")
    apply_tcp_subordinate = models.CharField(max_length=30, verbose_name="应用TCP接口subordinate地址")
    apply_tcp_drive = models.CharField(max_length=30, verbose_name="应用TCP接口绑定的驱动名称")
    apply_tcp_active = models.BooleanField(default=True,  verbose_name="应用TCP接口是否启动")

    class Meta:
        db_table = 'gateway_apply_template_tcp_interface'
        verbose_name = '应用TCP设备模板库记录'
        verbose_name_plural = verbose_name



def get_subdevicedata_model(subdevice_name):
    table_name = 'gateway_{0}_data'.format(subdevice_name)

    DATATYPE=(
        (0, "属性"),
        (1, "事件"),
        (2, "报警"),
    )
    DATASTATUS=(
        (0, "未发送"),
        (1, "已发送"),
    )

    class SubdeviceMetaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + subdevice_name  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class SubdeviceData(BaseModel):
        __metaclass__ = SubdeviceMetaclass
        subdevice_name = models.CharField(max_length=30, verbose_name="子设备名称")
        # subdevice= models.ForeignKey('Device.SubDevice', related_name="collectdatas", to_field='subdevice_name', on_delete=models.CASCADE, verbose_name='子设备名称')
        data_type = models.SmallIntegerField(default=0, choices=DATATYPE, verbose_name="子设备数据类型")
        data_status = models.SmallIntegerField(default=0, choices=DATASTATUS, verbose_name="数据状态")
        data = models.CharField(max_length=2000, verbose_name="子设备采集数据")

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name
            indexes = [models.Index(fields=['id']), ] # 給id 字段添加索引

    return SubdeviceData


def get_smartdevicedata_model(smartdevice_name):
    table_name = '{0}_data'.format(smartdevice_name)

    DATATYPE=(
        (0, "属性"),
        (1, "事件"),
        (2, "报警"),
    )
    DATASTATUS=(
        (0, "未发送"),
        (1, "已发送"),
    )

    class M5Metaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + smartdevice_name  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class M5Data(BaseModel):
        __metaclass__ = M5Metaclass
        smartdevice_name = models.CharField(max_length=30, verbose_name="子设备名称")
        data_type = models.SmallIntegerField(default=0, choices=DATATYPE, verbose_name="子设备数据类型")
        data_status = models.SmallIntegerField(default=0, choices=DATASTATUS, verbose_name="数据状态")
        data = models.CharField(max_length=2000, verbose_name="子设备采集数据")

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name
            indexes = [models.Index(fields=['id']), ] # 給id 字段添加索引

    return M5Data


class Path(BaseModel):
    '''数据转发模块的路径模板'''

    subdevice_name = models.CharField(max_length=30, verbose_name='子设备名称')
    path_name = models.CharField(max_length=30, verbose_name='子设备路径名称')
    path_type = models.CharField(max_length=30, verbose_name='子设备路径类型')
    path_ip = models.CharField(max_length=30, verbose_name='子设备路径网络地址')
    path_port = models.CharField(max_length=30, verbose_name='子设备路径网络端口号')
    path_sub = models.CharField(max_length=30, verbose_name='子设备路径发布主题')
    path_number = models.IntegerField(default=0, verbose_name='子设备路径上行消息数')
    path_enable = models.BooleanField(default=True,  verbose_name="子设备路径是否启动")

    class Meta:
        db_table = 'gateway_path'
        verbose_name = 'M5网关子设备转发路径'
        verbose_name_plural = verbose_name
