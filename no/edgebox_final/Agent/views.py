import json

import datetime, time

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection

from plugins.auth_corepro import AuthCorepro as agentauth
from Device.models import SubDevice
from .models import RegisterInfo
from django.http import JsonResponse
from django.core import serializers
import psutil


# /apis/agent/info
def Info(request):
    """
    用于提供Agent数据
    :param request: HttpRequest
    :return: Json
    """
    def auth():
        result =agentauth(ProductKey= vue_json["gatewayid"],
                  DeviceName= vue_json["gatewayname"],
                  DeviceSecret= vue_json["gatewaysercet"],
                  auth_url= vue_json["gatewaytokenapi"])
        return [result.username, result.password, result.mqtthost, result.mqttport ]

    if request.method == "POST":
        try:
            vue_json = json.loads(request.body.decode())["params"]
            # print(vue_json)
            result = auth()
            if all(result):
                RegisterInfo.objects.filter(gateway_trade_name = 'IoT').update(gateway_name = vue_json["gatewayname"],
                                                                               gateway_key = vue_json["gatewayid"],
                                                                               gateway_secret = vue_json["gatewaysercet"],
                                                                               gateway_tokenapi = vue_json["gatewaytokenapi"],
                                                                               gateway_location = vue_json["gatewaylocation"],
                                                                               gateway_iotid = result[0],
                                                                               gateway_iottoken = result[1],
                                                                               gateway_iothost = result[2],
                                                                               gateway_iotport = result[3],)

                conn = get_redis_connection('default')
                conn.hset("Agent", "name", vue_json["gatewayname"])
                conn.hset("Agent", "id", vue_json["gatewayid"])
                conn.hset("Agent", "sercet", vue_json["gatewaysercet"])
                conn.hset("Agent", "tokenapi", vue_json["gatewaytokenapi"])
                conn.hset("Agent", "location", vue_json["gatewaylocation"])

                return JsonResponse({
                    "status_code": 0,
                    "message": "注册修改成功",
                })
            else:
                return JsonResponse({
                    "status_code": 0,
                    "message": "注册修改出错: auth error",
                })
        except Exception as e:

            return JsonResponse({
                "status_code": 1,
                "error": "注册修改出错:"+str(e),
            })

    if request.method == "GET":

        # data = RegisterInfo.objects.create(gateway_name="EdgeBox003",
        #                                    gateway_key="6553791093879608705",
        #                                    gateway_secret="e3f3eeb045f0a19284ad03f64e101ce3f7fa15d135a7140e411fa29dbd269d7c",
        #                                    gateway_subdevice_num=0,
        #                                    gateway_model="IoT",
        #                                    gateway_trade_name="IoT",
        #                                    gateway_registration_time=datetime.datetime.now(),
        #                                    gateway_location="E5-4F",
        #                                    gateway_remark="EdgeBox边缘层网关测试版")
        # data.save()
        row_data = RegisterInfo.objects.all().values()[0]
        row_data['gateway_registration_time'] = row_data['gateway_registration_time'].strftime("%Y-%m-%d %H:%M:%S")
        row_data["gateway_subdevice_num"] = SubDevice.objects.all().count()
        row_data["status_code"] = 0
        return JsonResponse(row_data)


# /apis/agent/sysinfo
def sysInfo(request):
    """
    用于提供数据
    :param request: HttpRequest
    :return: Json
    """

    if request.method == "GET":
        data = {}
        data["status_code"] = 0
        # data["cpu_status"] = int(math.fsum(psutil.cpu_percent(interval=1, percpu=True)) // 4)  # 获得cpu当前使用率
        data["cpu_status"] = max(psutil.cpu_percent(interval=1, percpu=True))  # 获得cpu当前使用率
        data["memory_status"] = float(psutil.virtual_memory().percent)  # 获取当前内存使用情况
        data["disk_status"] = float(psutil.disk_usage("/").percent)  # 获取当前磁盘的使用率

        return JsonResponse(data)
