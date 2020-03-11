import json
import time
from random import choice

import serial
import serial.tools.list_ports
import numpy as np

from django.core import serializers
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from Agent.models import RegisterInfo
from Drive.models import Drive
from Drive.tasks import DriveForTransmit
from .models import SubDevice, EquipmentTemplateRtu, applyTemplateRtuInterface, applyTemplateTcpInterface, \
    Path, get_subdevicedata_model, get_smartdevicedata_model
from django.db.models import Avg, Sum, Max, Min, Count
from django_redis import get_redis_connection
from plugins.mqtt_pub_sub import mqtt_client_connect

# /apis/device/create
def Create(request):
    """
    用于创建一个新設備
    :param request: HttpRequest
    :return: Json
    """

    if request.method == "POST":
        try:
            vue_json = json.loads(request.body.decode())
            print(vue_json)

            if request.GET.get("select") is not None:
                select_devicename = vue_json.get("select_devicename")
                print(select_devicename)
                try:
                    subdevice = SubDevice.objects.get(subdevice_name=select_devicename)
                    print(subdevice)
                    return JsonResponse({
                        "status_code": 1,
                        "is_indb": 1
                    })
                except:
                    return JsonResponse({
                        'status_code': 0,
                        "is_indb": 0
                    })

            subdevice = SubDevice.objects.create(subdevice_name=vue_json["subdevice_name"],
                                                 subdevice_type=vue_json["subdevice_type"],
                                                 subdevice_position=vue_json["subdevice_position"],
                                                 subdevice_model=vue_json["subdevice_model"],
                                                 subdevice_remark=vue_json["subdevice_remark"])
            subdevice.save()

            # 为设备新建一张表
            cls = get_subdevicedata_model(vue_json["subdevice_name"])

            if not cls.is_exists():
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(cls)

            conn = get_redis_connection("default")
            conn.hset(vue_json["subdevice_name"], "device_enable", 0)
            conn.hset(vue_json["subdevice_name"], "drive_enable", 0)
            conn.hset(vue_json["subdevice_name"], "path_index", 0)
            return JsonResponse({
                "status_code": 0,
                "message": "创建成功"
            })

        except Exception as e:
            return JsonResponse({
                "status_code": 1,
                "error": str(e)
            })

# /apis/device/enable
def Enable(request):
    '''
    用户启用禁用设备接口
    :param request:
    :return:
    '''
    def set_disenable():
        conn.hset(subdevice, "device_enable", 0)
        keys = "path_{}_*".format(subdevice)
        path_keys = conn.keys(keys)
        for path_key in path_keys:
            conn.hset(path_key.decode(), "path_enable", 0)
            obj = Path.objects.filter(subdevice_name=subdevice).update(path_enable=False)

    if request.method == "POST":
        vue_json = json.loads(request.body.decode())
        print(vue_json)
        conn = get_redis_connection('default')
        subdevice = vue_json["subdevice_name"]
        enable = vue_json["enable"]
        obj = SubDevice.objects.filter(subdevice_name=subdevice).update(subdevice_enable=enable)
        if enable:
            conn.hset(subdevice, "device_enable", 1)
            return JsonResponse({
                "status_code": 0,
                "message": "启用成功"
            })
        else:
            set_disenable()
            return JsonResponse({
                "status_code": 0,
                "message": "禁用成功"
            })


# /apis/device/list
def List(request):
    """
    用于提供設備列表数据
    :param request: HttpRequest
    :return: Json
    """
    def status(row):
        conn = get_redis_connection("default")
        collect_drive = 0

        if int(conn.hget(row["subdevice_name"], 'drive_enable')):
            # row["subdevice_status"] = choice(["采集驱动&传输驱动", '传输驱动', '采集驱动','暂无驱动'])
            collect_drive = 1
        keys = "path_{}_*".format(row["subdevice_name"])
        path_keys = conn.keys(keys)
        path_drive = 0
        for path_key in path_keys:
            if int(conn.hget(path_key.decode(), "path_enable")):
                path_drive = 1
        if collect_drive + path_drive == 2:
            row["subdevice_status"] = "采集驱动&传输驱动"
        elif collect_drive + path_drive == 1:
            if collect_drive:
                row["subdevice_status"] = "采集驱动"
            if path_drive:
                row["subdevice_status"] = "传输驱动"
        else:
            row["subdevice_status"] = "暂无驱动运行"

        return row

    if request.method == "GET":

        row_data = SubDevice.objects.all().order_by('-id').values("subdevice_name", "subdevice_status",
                                                                  'subdevice_online_time', "subdevice_model",
                                                                  'subdevice_enable', 'subdevice_position',
                                                                  'subdevice_type')
        db = []
        for row in row_data:
            row["subdevice_online_time"] = row["subdevice_online_time"].strftime("%Y-%m-%d %H:%M:%S")
            row = status(row)
            db.append(row)

        return JsonResponse({
            "status_code": 0,
            "db": db
        })




# apis/device/type
def Type(request):
    '''
    用于提供添加设备的设备类型列表
    :param request: HttpRequest
    :return: Json
    '''

    if request.method == "GET":
        type_dict = ["生产设备类", "压铸设备类", "环境设备类", "机床设备类", "仪表设备类",
                     "注塑成型设备类", "包装设备类", "工控设备类", "传感器设备类", "SMT设备类",
                     "冲压设备类", "表面处理设备类", "运输设备类", "其他"]
        db = []
        for index, type_val in enumerate(type_dict):
            data = {"index": index, "value": type_val}
            db.append(data)

        return JsonResponse({
            "status_code": 0,
            "db": db
        })



# apis/device/protocollist

def protocolList(request):
    '''
    用于提供添加设备协议的协议类型列表
    :param request: HttpRequest
    :return: Json
    '''
    if request.method == "GET":
        protocolList = []

        type_1 = {
            "value": 'RS485/RS232/USB接口',
            "label": 'RS485/RS232/USB接口',
            "children": [
                {
                    "value": 'Modbus-RTU',
                    "label": 'Modbus-RTU'
                },
            ]
        }

        type_2 = {
            "value": 'Ethernet接口',
            "label": 'Ethernet接口',
            "children": [
                {
                    "value": 'Modbus-TCP',
                    "label": 'Modbus-TCP',
                },
                {
                    "value": 'OPC-UA',
                    "label": 'OPC-UA',
                    "disabled": True,
                },
                {
                    "value": 'MQTT',
                    "label": 'MQTT',
                    # "disabled": True,
                },
                {
                    "value": 'DB',
                    "label": 'DB',
                    "children": [
                        {
                            "value": 'MySQL',
                            "label": 'MySQL',
                            "disabled": True,
                        },
                        {
                            "value": 'SQLServer',
                            "label": 'SQLServer',
                            "disabled": True,
                        }, ]
                }
            ]
        }

        type_3 = {
            "value": '专有协议接口',
            "label": '专有协议接口',
            "children": [
                {
                    "value": 'PLC',
                    "label": 'PLC',
                    "children": [
                        {
                            "value": 'S7-200',
                            "label": 'S7-200',
                            "disabled": True,
                        },
                        {
                            "value": 'FX-3U',
                            "label": 'FX-3U',
                            "disabled": True,
                        },
                        {
                            "value": 'FX-5U',
                            "label": 'FX-5U',
                            "disabled": True,
                        }, ]
                },
                {
                    "value": 'Robot',
                    "label": 'Robot',
                    "children": [
                        {
                            "value": 'Foxbot',
                            "label": 'Foxbot',
                            "disabled": True,
                        },
                        {
                            "value": 'CR750',
                            "label": 'CR750',
                            "disabled": True,
                        }, ]
                },
                {
                    "value": 'SMT',
                    "label": 'SMT',
                    "disabled": True,
                }, {
                    "value": 'CNC',
                    "label": 'CNC',
                    "disabled": True,
                }
            ]
        }

        protocolList.append(type_1)
        protocolList.append(type_2)
        protocolList.append(type_3)
        return JsonResponse({
            "status_code": 0,
            "db": protocolList
        })


# apis/device/template/create

def templateCreate(request):
    '''
    用于创建一个新的设备模板
    :param request:
    :return:
    '''
    if request.method == "POST":
        try:
            vue_json = json.loads(request.body.decode())
            template_name = vue_json.get("template_name")
            template_remark = vue_json.get("template_remark")
            accordname = vue_json.get("accordname")[1]
            print(accordname)
            for row in vue_json.get("code_list"):
                # print(row)
                etr = EquipmentTemplateRtu.objects.create(etr_name = template_name,
                                                    etr_remark = template_remark,
                                                    etr_accordname =  accordname,
                                                    etr_code = row["function_code"],
                                                    etr_register = row["start_register"],
                                                    etr_register_num = row["register_num"],
                                                    etr_param = row["property"],
                                                    etr_format = row["format"],
                                                    etr_rule_sign = row["rule"]["sign"],
                                                    etr_rule_number = row["rule"]["number"])
                etr.save()
            return JsonResponse({
                "status_code": 0,
                "message": "创建成功"
            })
        except Exception as e:
            return JsonResponse({
                "status_code": 1,
                "error": str(e)
            })



# apis/device/template

def templateList(request):
    '''
        用于提供设备模板列表
        :param request: HttpRequest
        :return: Json
        {
              name: 'HC31A电表',
              protocol: 'ModBus',
              createTime: '2019-05-25 13:52:47',
              description: 'HC31A电表配置模板',
              info: {
                row1: {
                  Aa:  ["0x000a",2],
                  Bb:  ["0x000a",2],
                  Cc:  ["0x000a",2],
                  Dd:  ["0x000a",2],
                },
                row2: {
                  Bb:  ["0x000a",2],
                  Cc:  ["0x000a",2],
                  Dd:  ["0x000a",2],
                }
              }
          }
        '''
    def select(etrs):
        templateList = []
        for etr in etrs:
            template = EquipmentTemplateRtu.objects.filter(etr_name=etr["etr_name"])
            data = {}
            data["name"] = etr["etr_name"]
            data["protocol"] = etr["etr_accordname"]
            data["description"] = etr["etr_remark"]
            data["info"] = []

            row = 0
            for index, tmp in enumerate(template):
                data["createTime"] = tmp.create_time.strftime("%Y-%m-%d %H:%M:%S")
                if index % 4 == 0:
                    data["info"].append({})
                    row += 1
                data["info"][row - 1][index] = { "property":tmp.etr_param,
                                                 "register":{
                                                     "startRegister": "0x" + tmp.etr_register,
                                                     "number": int(tmp.etr_register_num, 16),
                                                     "format":tmp.get_etr_format_display(),
                                                 }
                                                 }
            templateList.append(data)
        return templateList

    if request.method == "GET":
        templateList = []
        # print(request.GET)
        vue_List = list(request.GET.getlist("typeSelected[]"))
        subdevice = request.GET.get("subdevice")
        if subdevice != None:
            print("设备默认模板")
            apply_rtu = applyTemplateRtuInterface.objects.filter(apply_rtu_device= subdevice)
            apply_tcp = applyTemplateTcpInterface.objects.filter(apply_tcp_device= subdevice)
            if not apply_tcp and not apply_rtu:
                return JsonResponse({
                    "status_code": 1,
                    "db": []
                })
            elif apply_rtu and apply_tcp:
                template_name_rtu = apply_rtu[0].apply_rtu_template
                template_name_tcp = apply_tcp[0].apply_tcp_template
                if apply_rtu[0].create_time >  apply_tcp[0].create_time:
                    etrs = EquipmentTemplateRtu.objects.values("etr_name", "etr_accordname","etr_remark",)\
                                                    .filter(etr_name = template_name_rtu)\
                                                    .annotate(num=Count("etr_name"))
                    templateList = select(etrs)
                    return JsonResponse({
                        "status_code": 1,
                        "db": templateList
                    })
                else:
                    etrs = EquipmentTemplateRtu.objects.values("etr_name", "etr_accordname", "etr_remark", ) \
                        .filter(etr_name=template_name_tcp) \
                        .annotate(num=Count("etr_name"))
                    templateList = select(etrs)
                    return JsonResponse({
                        "status_code": 1,
                        "db": templateList
                    })
            elif apply_rtu:
                template_name_rtu = apply_rtu[0].apply_rtu_template
                etrs = EquipmentTemplateRtu.objects.values("etr_name", "etr_accordname", "etr_remark", ) \
                    .filter(etr_name=template_name_rtu) \
                    .annotate(num=Count("etr_name"))
                templateList = select(etrs)
                return JsonResponse({
                    "status_code": 1,
                    "db": templateList
                })
            elif apply_tcp:
                template_name_tcp = apply_tcp[0].apply_tcp_template
                etrs = EquipmentTemplateRtu.objects.values("etr_name", "etr_accordname", "etr_remark", ) \
                    .filter(etr_name=template_name_tcp) \
                    .annotate(num=Count("etr_name"))
                templateList = select(etrs)
                return JsonResponse({
                    "status_code": 1,
                    "db": templateList
                })


        if vue_List == []:
            print("选择协议模板")
            etrs = EquipmentTemplateRtu.objects.values("etr_name", "etr_accordname","etr_remark",)\
                .all()\
                .annotate(num=Count("etr_name"))
            templateList = select(etrs)
            return JsonResponse({
                "status_code": 1,
                "db": templateList
            })

        print("所有协议模板")
        etrs = EquipmentTemplateRtu.objects.values("etr_name", "etr_accordname","etr_remark",)\
            .filter(etr_accordname=vue_List[1])\
            .annotate(num=Count("etr_name"))
        # print(etrs)
        templateList = select(etrs)
        return JsonResponse({
            "status_code": 1,
            "db": templateList
        })

    if request.method == "POST":
        try:
            # print(request.body.decode())
            vue_json = json.loads(request.body.decode())
            print(vue_json)
            if request.GET.get("select") is not None:
                select_templatename = vue_json.get("select_templatename")
                print(select_templatename)
                etr = EquipmentTemplateRtu.objects.filter(etr_name=select_templatename).count()
                if etr:
                    return JsonResponse({
                        "status_code": 1,
                        "is_indb": 1
                    })
                return JsonResponse({
                    'status_code': 0,
                    "is_indb": 0
                })


        except Exception as e:
            return JsonResponse({
                "status_code": 1,
                "error": str(e)
            })


# apis/device/modbusrtufrom

def modbusRtuForm(request):
    '''
    用于提供Modbus-RTU的from表单select
    :param request:
    :return:
    '''
    if request.method == "GET":

        form = {}
        port_list = list(serial.tools.list_ports.comports())
        serialList = [ {"index":v[0], "value":v[1].split("(")[0]} for v in port_list]
        # serialList[0]["disabled"] = True
        # serialList[1]["disabled"] = True
        bitList = [ {"index":v, "value":"bit"} for i, v in enumerate(["5", "6", "7", '8'])]
        baudRateList = [ {"index":v, "value":"bps"} for i, v in enumerate(["1200", "2400", "4800", '9600',"19200", "38400", "115200"])]
        parityList = [ {"index":v, "value":v} for i, v in enumerate(["None,无校验", "Even,偶校验", 'Odd,奇校验'])]
        stopBitList = [ {"index":v, "value":"bit"} for i, v in enumerate(["0", "1", "2"])]
        timeoutList = [ {"index":v, "value":"second"} for i, v in enumerate(["0.3", "0.5", "0.8", "1.0", "2.0" ,'3.0'])]
        cycleList = [{"index": str(round(v, 1)), "value": "second"} for i, v in enumerate(np.arange(0.3, 5.1, 0.1))]
        addressList = [{"index":i, "value":i} for i in range(0, 248,1)]
        drive_name = Drive.objects.filter(drive_type = "Modbus-RTU").values("drive_name")
        driveList = [ {"index": drive["drive_name"], "value":drive["drive_name"]} for drive in drive_name]
        # driveList = [{"index":"ModbusRtuDemo", "value":"ModbusRtuDemo"} for i in range(0, 1, 1)]

        form["serialList"] = serialList
        form["baudRateList"] = baudRateList
        form["stopBitList"] = stopBitList
        form["bitList"] = bitList
        form["parityList"] = parityList
        form["timeoutList"] = timeoutList
        form["cycleList"] = cycleList
        form["addressList"] = addressList
        form["driveList"] = driveList
        return JsonResponse({
            "status_code": 0,
            "db": form
        })


# apis/device/modbustcpfrom

def modbusTcpForm(request):
    '''
    用于提供Modbus-Tcp的from表单select
    :param request:
    :return:
    '''
    if request.method == "GET":

        form = {}
        cycleList = [{"index": str(round(v, 1)), "value": "second"} for i, v in enumerate(np.arange(0.3, 5.1, 0.1))]
        timeoutList = [ {"index":v, "value":"second"} for i, v in enumerate(["1.0", "2.0" ,'3.0','4.0', '5.0'])]
        addressList = [{"index":i, "value":i} for i in range(0, 248,1)]
        drive_name = Drive.objects.filter(drive_type = "Modbus-TCP").values("drive_name")
        driveList = [ {"index": drive["drive_name"], "value":drive["drive_name"]} for drive in drive_name]
        # driveList = [{"index":"ModbusTcpDriveDemo", "value":"ModbusTcpDriveDemo"} for i in range(0, 1, 1)]
        form["timeoutList"] = timeoutList
        form["cycleList"] = cycleList
        form["addressList"] = addressList
        form["driveList"] = driveList
        return JsonResponse({
            "status_code": 0,
            "db": form
        })


# apis/device/auth

def Auth(request):
    '''
    用于提供MQTT 客户端测试接口
    :param request:
    :return:
    '''
    def mqtt_auth():
        try:
            print(mqtt_ip, mqtt_port)
            mqttclient = mqtt_client_connect(broker=mqtt_ip, port=int(mqtt_port), username=mqtt_username, password=mqtt_pwd)
            if mqttclient.flag == 0:
                return 0
            elif mqttclient.flag == 1:
                mqttclient.mqttc.loop_stop()
                mqttclient.mqttc.disconnect()
                return 1
        except:
            return 0

    if request.method == "GET":

        auth_type=request.GET.get("authtype")
        if auth_type == "第三方MQTT":
            mqtt_ip = request.GET.get("host")
            mqtt_port = request.GET.get("port")
            mqtt_username = request.GET.get("username")
            mqtt_pwd = request.GET.get("pwd")
            result = mqtt_auth()
            if result == 0:
                return JsonResponse({
                    "status_code": 1,
                    "error": "连接失败！"
                })

        return JsonResponse({
            "status_code": 0,
            "message": "测试连接成功！"
        })


# apis/device/pathinfo

def pathInfo(request):
    '''
    用于提供数据转发页面的狀態詳情
    :param request:
    :return:
    '''
    if request.method == "GET":
        subdevice = request.GET.get("subdevice")
        path_name = request.GET.get("path_name")
        path_type = request.GET.get("path_type")
       
        path_key ="m5path_{}_{}".format(subdevice.split("_")[2],subdevice.split("_")[1][1]) if "m5_0" == subdevice[0:4] else "path_{}_{}".format(subdevice, path_name)
        conn = get_redis_connection("default")
        status = json.loads(conn.hget(path_key, "path_status").decode())

        if path_type == "第三方MQTT" or path_type == "MQTT":
            sub = [{
                "host": conn.hget(path_key, "path_host").decode(),
                "port": conn.hget(path_key, "path_port").decode(),
                "sub": conn.hget(path_key, "path_topic").decode()
            }]
        elif path_type == 'CorePro Server':
            sub = [{
                "host": conn.hget(path_key, "path_host").decode(),
                "port": conn.hget(path_key, "path_port").decode(),
                "sub": conn.hget(path_key, "path_topic").decode()
            }]

        return JsonResponse({
            'status': status,
            'sub': sub
        })

# apis/device/path/delete

def pathDelete(request):
    '''
     用于提供数据转发页面的删除转发路径的接口
    :param request:
    :return:
    '''
    if request.method == "POST":
        try:
            vue_json = json.loads(request.body.decode())
            conn = get_redis_connection('default')
            subdevice = vue_json["subdevice_name"]
            path_name = vue_json["path_name"]
            key = "path_{}_{}".format(subdevice, path_name)
            obj = Path.objects.filter(path_name=path_name, subdevice_name=subdevice)
            obj.delete()
            conn.delete(key)
            return JsonResponse({
                "status_code": 0,
                "message": "操作成功！"
            })
        except:
            return JsonResponse({
                "status_code": 1,
                "message": "操作失败！"
            })


# apis/device/path/enable

def pathEnable(request):
    '''
    用于提供数据转发页面的创建转发路径接口
    :param request:
    :return:
    '''

    def run_transmit_task():
        """
        判断缓存里面设备path的enable if num(enable)==1 run task
        :return:
        """
        # keys = "path_{}_*".format(subdevice)
        keys =  "m5path_{}_*".format(subdevice.split("_")[2]) if "m5_0" == subdevice[:4] else "path_{}_*".format(subdevice)

        path_keys = conn.keys(keys)
        num =0
        for path in path_keys:
            enable=conn.hget(path.decode(), "path_enable")
            if int(enable):
                num +=1
        print("num:",num)
        if num == 1:
            result = DriveForTransmit.apply_async(kwargs={"subdevice_name": subdevice},queue="worker_queue")

    def check_enable():

        if int(conn.hget(subdevice, "device_enable")):
            conn.hset(key, "path_enable", 1)
            return 1
        else:
            return 0

    if request.method == "POST":
        vue_json = json.loads(request.body.decode())
        print(vue_json)
        conn = get_redis_connection('default')
        subdevice = vue_json["subdevice_name"]
        path_name = vue_json["path_name"]
        enable = vue_json["enable"]
        key =  "m5path_{}_{}".format(subdevice.split("_")[2],subdevice.split("_")[1][1]) if "m5_0" == subdevice[:4] else "path_{}_{}".format(subdevice, path_name)
        # key = "path_{}_{}".format(subdevice, path_name)
        if enable:
            result = check_enable()  #判斷設備的啟用狀態
            if result:
                run_transmit_task()
                if "m5_0" != subdevice[:4]:
                    obj = Path.objects.filter(path_name=path_name, subdevice_name=subdevice).update(path_enable=enable)
                return JsonResponse({
                    "status_code": 0,
                    "message": "启用成功"
                })
            else:
                return JsonResponse({
                    "status_code": 1,
                    "message": "設備被禁用, 在设备列表可重新启用该设备！"
                })
        else:
            if "m5_0" != subdevice[:4]:
                obj = Path.objects.filter(path_name=path_name, subdevice_name=subdevice).update(path_enable=enable)
            conn.hset(key, "path_enable", 0)
            return JsonResponse({
                "status_code": 0,
                "message": "禁用成功"
            })

# apis/device/path

def pathList(request):
    '''
    用于提供数据转发页面的创建转发路径接口
    :param request:
    :return:
    '''
    if request.method == "GET":
        conn = get_redis_connection("default")
        subdevice_name = request.GET.get("subdevice")
        if "m5_0" == subdevice_name[:4]:
            device = subdevice_name.split("_")[2]
            key = "m5path_{}_*".format(device)
            paths = conn.keys(key)
            path_list = [{"addressName": conn.hget(path, "path_name").decode(),
                          'type': conn.hget(path, "path_type").decode(),
                          "createTime":conn.hget(path, "path_createtime").decode(),
                          "switch": True if int(conn.hget(path, "path_enable").decode()) else False,
                          "mesNumber": int(conn.hget(path, "path_count").decode()),
                          "path_msg": json.loads(conn.hget(path, "path_msg").decode())
                          } for path in paths]

            return JsonResponse({
                "status_code": 0,
                "db": path_list,
            })
                
        path_key = "path_{}_".format(subdevice_name)
        db = Path.objects.filter(subdevice_name = subdevice_name).order_by("-id").values()
        path_list = [ {"addressName":path["path_name"],
                       'type':path["path_type"],
                       "createTime":path["create_time"].strftime("%Y-%m-%d %H:%M:%S"),
                       "switch":path["path_enable"],
                       "mesNumber": int(conn.hget(path_key+path["path_name"], "path_count")),
                       "path_msg": json.loads(conn.hget(path_key+path['path_name'], "path_msg").decode())
                       } for path in db ]

        return JsonResponse({
            "status_code": 0,
            "db": path_list,
        })
    if request.method == "POST":
        vue_json = json.loads(request.body.decode())
        conn = get_redis_connection('default')
        if request.GET.get("select") is not None:
            select_path = vue_json.get("select_path")
            # print(select_path)
            path = Path.objects.filter(path_name=select_path).count()
            if path:
                return JsonResponse({
                    "status_code": 1,
                    "is_indb": 1
                })
            return JsonResponse({
                'status_code': 0,
                "is_indb": 0
            })
        else:
            subdevice = vue_json["subdevice"]
            key = 'path_'+vue_json["subdevice"]+'_'+vue_json["params"]["name"]
            count = Path.objects.filter(subdevice_name = key).count()
            if count == 4:
                return JsonResponse({
                    "status_code": 1,
                    "error": "每台设备四条转发路径上限！",
                })
            # print(vue_json)

            if "MQTT" in  vue_json["path_type"]:
                vue_json = vue_json["params"]
                print("MQTT")
                path = Path.objects.create(path_name=vue_json["name"], path_type = "第三方MQTT",
                                           subdevice_name = subdevice, path_ip = vue_json["ip"],
                                           path_port =vue_json["port"], path_sub =vue_json["pubtopic"], path_enable = False )
                path.save()

                conn.hset(key, "path_type", "第三方MQTT")
                conn.hset(key, "path_name", vue_json["name"])
                conn.hset(key, "path_host", vue_json["ip"])
                conn.hset(key, "path_port", vue_json["port"])
                conn.hset(key, "path_username", vue_json["userName"])
                conn.hset(key, "path_pwd", vue_json["pwd"])
                conn.hset(key, "path_topic", vue_json["pubtopic"])
                conn.hset(key, "path_index", 0)
                conn.hset(key, "path_count", 0)
                status = {
                    "status_code": "1",
                    "message": "路徑未開啟！"
                }
                conn.hset(key, "path_status", json.dumps(status))
                conn.hset(key, "path_msg", '{"init":"初始化數據"}')
                conn.hset(key, "path_enable", 0)

            elif vue_json["path_type"] == "CorePro Server":
                print("CorePro", vue_json)
                vue_json = vue_json["params"]
                path = Path.objects.create(path_name=vue_json["name"], path_type="CorePro Server",
                                           subdevice_name=subdevice, path_ip="",
                                           path_port="" , path_sub=vue_json["datatopic"], path_enable = False)
                path.save()

                row_data = RegisterInfo.objects.last()

                conn.hset(key, "path_type", "CorePro Server")
                conn.hset(key, "path_name", vue_json["name"])
                conn.hset(key, "path_host", row_data.gateway_iothost)
                conn.hset(key, "path_port", row_data.gateway_iotport)
                conn.hset(key, "path_username", row_data.gateway_iotid)
                conn.hset(key, "path_pwd", row_data.gateway_iottoken)
                conn.hset(key, "path_topic", vue_json["datatopic"])
                conn.hset(key, "path_datatype", vue_json["datatype"])
                conn.hset(key, "path_datatypeid", vue_json["datatypeid"])
                conn.hset(key, "path_index", 0)
                conn.hset(key, "path_count", 0)
                status = {
                            "status_code": "1",
                            "message": "驅動未開啟！"
                        }
                conn.hset(key, "path_status", json.dumps(status))
                conn.hset(key, "path_msg", '{"init":"初始化數據"}')
                conn.hset(key, "path_enable", 0)

            return JsonResponse({
                "status_code": 0,
                "message": "创建成功",
            })

# apis/device/data

def Data(request):
    '''
    用于提供特征提取页面表格数据
    :param request:
    :return:
    '''
    if request.method == "GET":
        subdevice = request.GET.get("subdevice")
        template_name = request.GET.get("template_name")
        if template_name is None:
            return JsonResponse({
                "status_code": 1,
                'message': "应用模板不能为空！"
            })
        conn = get_redis_connection("default")
        varlist = []
        try:
            varlist = eval(conn.hget(subdevice, template_name + '_varlist').decode())
        except:
            conn.hset(subdevice , template_name + '_varlist', [])

        row = int(request.GET.get("row"))
        
        cls =  get_smartdevicedata_model(subdevice) if "m5_0" == subdevice[:4] else get_subdevicedata_model(subdevice)
        if row:
            #用于提供特征提取页面的设备URI 最近n条数据
            print("row:", row)
           
            
            row_last_data = cls.objects.values("data","id", 'create_time').order_by("-id")[:row]
            db = [ json.loads(i["data"].replace("'", '"')) for i in row_last_data]
            print(db)
            for index, row in enumerate(db):
                add_json = {
                    "id": row_last_data[index]["id"],
                    "create_time": row_last_data[index]["create_time"].strftime("%Y-%m-%d %H:%M:%S")
                    }
                row.update(add_json)
            print(db)
            data_db = []
            for row in db:
                data = {}
                if varlist == []:
                    for i in row:
                        data[i] = row[i]
                else:
                    for i in row:
                        if i in varlist:
                            data[i] = row[i]
                data_db.append(data)
            # db = [ {i: row[i]}  for i in row for row in db if i in varlist]
            # print(db)

            Total = cls.objects.count()

            return JsonResponse({
                "status_code": 0,
                "subdevice": subdevice,
                "Total": Total,
                "db": data_db,
            })

        else:
            # 默认 row=0 选最后一条
            print(request.META)
            # header = '{}://{}:{}'.format(request.scheme, request.META["HTTP_X_FORWARDED_FOR"],
            #                              request.META["SERVER_PORT"])
            header = '{}://{}'.format(request.scheme, request.META["HTTP_HOST"])
            try:
                print("row:", row)
                row_last_data = cls.objects.values("data", "create_time").last()
                row_last_data["create_time"] = row_last_data["create_time"].strftime("%Y-%m-%d %H:%M:%S")
                # print(row_last_data["create_time"])
                data = json.loads(row_last_data["data"].replace("'",'"'))
                if varlist == []:
                    tablaData = [{"property": i, "value": v, "create_time": row_last_data["create_time"]} for i, v in data.items()]
                else:
                    tablaData = [ {"property":i, "value":v, "create_time":row_last_data["create_time"]} for i, v  in data.items() if i in varlist]
                Total = cls.objects.count()

                key_list=[]
                for key in data:
                    key_list.append({
                        "key":key,
                        "label":key,
                        "disabled": False
                    })
                return JsonResponse({
                    "status_code": 0,
                    "tableData": tablaData,
                    "formatData": data,
                    "Total": Total,
                    "URI": "{header}/apis/device/data?subdevice={subdevice}&template_name={template_name}&row=30".format(header= header,subdevice=subdevice, template_name=template_name),
                    "key": key_list,
                })
            except:
                return JsonResponse({
                    "status_code": 0,
                    "tableData": [],
                    "formatData": {},
                    "Total": 0,
                    "URI": "null",
                    "key": [],
                })

# apis/device/apply

def showApply(request):
    '''
    用于提供特征提取页面模板接口数据
    :param request:
    :return:
    '''
    def rtu(apply_rtu):
        apply_interface = []
        apply_interface.append(["驱动名称", apply_rtu[0].apply_rtu_drive])
        apply_interface.append(["驱动类型", "Modbus-RTU"])

        apply_interface.append(["驱动状态", apply_rtu[0].apply_rtu_active])
        apply_interface.append(["Slave地址", apply_rtu[0].apply_rtu_slave])
        apply_interface.append(["串口号", apply_rtu[0].apply_rtu_com])
        apply_interface.append(["波特率", apply_rtu[0].apply_rtu_botelv])
        apply_interface.append(["奇偶校验", apply_rtu[0].apply_rtu_parity])
        apply_interface.append(["数据位", apply_rtu[0].apply_rtu_databit])
        apply_interface.append(["停止位", apply_rtu[0].apply_rtu_stopbit])
        apply_interface.append(["回复超时", apply_rtu[0].apply_rtu_timeout])
        apply_interface.append(["读写周期", apply_rtu[0].apply_rtu_cycle])
        return apply_interface
    def tcp(apply_tcp):
        apply_interface=[]
        apply_interface.append(["驱动名称", apply_tcp[0].apply_tcp_drive])
        apply_interface.append(["驱动类型", "Modbus-TCP"])
        apply_interface.append(["驱动状态", apply_tcp[0].apply_tcp_active])
        apply_interface.append(["Slave地址", apply_tcp[0].apply_tcp_slave])
        apply_interface.append(["IP地址", apply_tcp[0].apply_tcp_ip])
        apply_interface.append(["端口号", apply_tcp[0].apply_tcp_port])
        apply_interface.append(["回复超时", apply_tcp[0].apply_tcp_timeout])
        apply_interface.append(["读写周期", apply_tcp[0].apply_tcp_cycle])
        return apply_interface


    if request.method == "GET":
        subdevice = request.GET.get("subdevice")
        # print(subdevice)
        conn = get_redis_connection("default")

        if "m5_0" == subdevice[:4]:
            smart_device = subdevice
            varlist = list()
            varlist.append(['通道序號', smart_device.split("_")[1]])
            varlist.append(['設備名稱', conn.hget(smart_device, "name").decode()])
            varlist.append(['採集狀態', "驅動採集正常" if int(conn.hget(smart_device, "device_enable")) else "驅動採集異常"])
            varlist.append(['串口号',conn.hget(smart_device, "com").decode()])
            varlist.append(['波特率',conn.hget(smart_device, "botelv").decode()])
            varlist.append(['In', conn.hget(smart_device, "In").decode()])
            varlist.append(["Out", conn.hget(smart_device, "Out" ).decode()])
            varlist.append(['握手時間', conn.hget(smart_device, "create_time").decode()])
            varlist.append(['採集描述', conn.hget(smart_device, "remark").decode()])
            return JsonResponse({
                "status_code": 1,
                "db": varlist,
                "template_name": "System"
    
            })
        if int(conn.hget(subdevice, "drive_enable")):
            applyTemplateRtuInterface.objects.filter(apply_rtu_device=subdevice ). \
                                                update(apply_rtu_active=True)
            applyTemplateTcpInterface.objects.filter(apply_tcp_device=subdevice). \
                update(apply_tcp_active=True)
        else:
            applyTemplateRtuInterface.objects.filter(apply_rtu_device=subdevice). \
                update(apply_rtu_active=False)
            applyTemplateTcpInterface.objects.filter(apply_tcp_device=subdevice). \
                update(apply_tcp_active=False)

        apply_rtu = applyTemplateRtuInterface.objects.filter(apply_rtu_device=subdevice)
        apply_tcp = applyTemplateTcpInterface.objects.filter(apply_tcp_device=subdevice)
        # print(apply_tcp, apply_rtu)
        if not apply_tcp and not apply_rtu:
            return JsonResponse({
                "status_code": 1,
                "db": []
            })
        elif apply_rtu and apply_tcp:
            if apply_rtu[0].create_time > apply_tcp[0].create_time:
                return JsonResponse({
                    "status_code": 1,
                    "db": rtu(apply_rtu),
                    "template_name" : apply_rtu[0].apply_rtu_template

                })
            else:
                return JsonResponse({
                    "status_code": 1,
                    "db": tcp(apply_tcp),
                    "template_name": apply_tcp[0].apply_tcp_template

                })
        elif apply_rtu:
            return JsonResponse({
                "status_code": 1,
                "db": rtu(apply_rtu),
                "template_name": apply_rtu[0].apply_rtu_template

            })
        elif apply_tcp:
            return JsonResponse({
                "status_code": 1,
                "db": tcp(apply_tcp),
                "template_name": apply_tcp[0].apply_tcp_template

            })



# apis/device/template/apply/

def templateApply(request):
    '''
    用于提供Modbus-Tcp的from表单select
    :param request:
    :return:
    '''
    if request.method == "POST":
        # print(request.body.decode())
        vue_json = json.loads(request.body.decode())
        print(vue_json)
        if vue_json.get("type") == "rtu":
            obj = applyTemplateRtuInterface.objects.filter(apply_rtu_device= vue_json["subdevice_name"],)
            obj.delete()
            obj = applyTemplateRtuInterface.objects.create(apply_rtu_template=vue_json["template_name"],
                                                           apply_rtu_device= vue_json["subdevice_name"],
                                                           apply_rtu_com = vue_json["serial"],
                                                           apply_rtu_botelv= vue_json["baudRate"],
                                                           apply_rtu_databit = vue_json["databit"],
                                                           apply_rtu_parity = vue_json["parity"],
                                                           apply_rtu_stopbit = vue_json["stopBit"],
                                                           apply_rtu_timeout = vue_json["timeout"],
                                                           apply_rtu_cycle = vue_json["cycle"],
                                                           apply_rtu_slave = vue_json["address"],
                                                           apply_rtu_drive = vue_json["drive"],
                                                           apply_rtu_active = False)
            obj.save()
        elif vue_json.get("type") == "tcp":
            obj = applyTemplateTcpInterface.objects.filter(apply_tcp_device=vue_json["subdevice_name"], )
            obj.delete()
            obj = applyTemplateTcpInterface.objects.create(apply_tcp_template=vue_json["template_name"],
                                                           apply_tcp_device=vue_json["subdevice_name"],
                                                           apply_tcp_ip=vue_json["ip"],
                                                           apply_tcp_port=vue_json["port"],
                                                           apply_tcp_timeout=vue_json["timeout"],
                                                           apply_tcp_slave=vue_json["address"],
                                                           apply_tcp_drive=vue_json["drive"],
                                                           apply_tcp_cycle=vue_json["cycle"],
                                                           apply_tcp_active=False)
            obj.save()
        return JsonResponse({
            "status_code": 0,
            "message": "模板应用成功"
        })

