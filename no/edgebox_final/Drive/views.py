import json

from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.


# apis/drive/list
from django_redis import get_redis_connection

from Device.models import applyTemplateRtuInterface, applyTemplateTcpInterface, EquipmentTemplateRtu
from Drive.models import Drive
from Drive.tasks import DriveModbusRtu, DriveModbusTcp


def driveList(request):
    '''

    :param request:
    :return:
    '''
    if request.method == "GET":
        query_set = Drive.objects.all().order_by('-id')
        if query_set.exists():
            json_db = json.loads(serializers.serialize("json", query_set))
            db = [i.pop("fields") for i in json_db]
            # print(db)

            return JsonResponse({
                "status_code": 0,
                "db": db
            })

        else:
            return JsonResponse({
                "status_code": 1,
                "error": "not data"
            })

# apis/drive/varlist

def varList(request):
    '''
    :param request:
    :return:
    '''
    if request.method == "GET":
        subdevice = request.GET.get("device_name")
        template_name = request.GET.get("template_name")
        conn = get_redis_connection('default')
        if template_name is None:
            return JsonResponse({
                "status_code": 1,
                "error": "请先应用模板！"
            })
        try:
            varlist = eval(conn.hget(subdevice, template_name + '_varlist').decode())
            print(varlist)
            return JsonResponse({
                "status_code": 0,
                'varlist': varlist
            })
        except:
            conn.hset(subdevice , template_name + '_varlist', [])
            return JsonResponse({
                "status_code": 0,
                'varlist': []
            })


    if request.method == "POST":
        vue_json = json.loads(request.body.decode())
        print(vue_json)
        conn = get_redis_connection('default')
        conn.hset(vue_json["device_name"], vue_json["template_name"]+'_varlist', vue_json["var_list"])

        return JsonResponse({
            "status_code": 0,
            "message": "操作成功！"
        })


def driveEnable(request):
    '''

    :param request:
    :return:
    '''
    def apply_template():
        template = EquipmentTemplateRtu.objects.filter(etr_name= vue_json["template_name"]).values()
        # print(template)
        return template

    def apply_interface():
        # interface = {}
        if vue_json["drive_type"] == "Modbus-RTU":
            interface = applyTemplateRtuInterface.objects.filter(apply_rtu_drive= vue_json["drive_name"],
                                                             apply_rtu_device= vue_json["device_name"]).values()[0]
            # print(interface)
            return interface
        elif vue_json["drive_type"] == "Modbus-TCP":
            interface = applyTemplateTcpInterface.objects.filter(apply_tcp_drive=vue_json["drive_name"],
                                                                 apply_tcp_device=vue_json["device_name"]).values()[0]
            return interface

    if request.method == "POST":
        vue_json = json.loads(request.body.decode())
        print(vue_json)
        conn = get_redis_connection('default')
        status = ""
        if vue_json["drive_type"] == "Modbus-RTU":
           apply = applyTemplateRtuInterface.objects.filter(apply_rtu_drive= vue_json["drive_name"],
                                                            apply_rtu_device= vue_json["device_name"]).\
                                                     update(apply_rtu_active = vue_json["enable"])

           if vue_json["enable"]:
               conn.hset(vue_json["device_name"], "drive_enable", 1)
               result = DriveModbusRtu.apply_async(kwargs={"apply_template":apply_template(), "apply_interface":apply_interface()},
                                                   queue= "worker_queue")
               status = "设备采集驱动启动成功！"

           else:
               conn.hset(vue_json["device_name"], "drive_enable", 0)
               status = "设备采集驱动已停止！"

           return JsonResponse({
               "status_code": 1,
               "message": status
           })
        elif vue_json["drive_type"] == "Modbus-TCP":
            apply = applyTemplateTcpInterface.objects.filter(apply_tcp_drive=vue_json["drive_name"],
                                                             apply_tcp_device=vue_json["device_name"]). \
                                                    update(apply_tcp_active=vue_json["enable"])
            if vue_json["enable"]:
                conn.hset(vue_json["device_name"], "drive_enable", 1)
                result = DriveModbusTcp.apply_async(kwargs={"apply_template": apply_template(),
                                                            "apply_interface": apply_interface()},
                                                     queue="worker_queue")
                status = "设备采集驱动启动成功！"

            else:
                conn.hset(vue_json["device_name"], "drive_enable", 0)
                status = "设备采集驱动已停止！"

            return JsonResponse({
                "status_code": 1,
                "message": status
            })
