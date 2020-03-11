#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/31 17:46
# @Author  : userzhang
import binascii
import codecs
import json
import threading
import time


from modbus_tk import modbus_rtu, modbus_tcp
import requests
import serial

from celery.task import Task
import django
from django_redis import get_redis_connection
from django.db import connection
from paho.mqtt import publish
import serial.tools.list_ports
django.setup()
from Device.models import get_subdevicedata_model, get_smartdevicedata_model
from plugins.mqtt_pub_sub import mqtt_client_connect as client

class DriveScanfM5(Task):
    name = "DriveScanfM5"
    conn = get_redis_connection("default")

    def run(self, *arg, **kwargs):
        '''
        :param arg:
        :param kwargs:
        :return:
        # 定時掃描任務
        '''
        m5_key = "m5_*"
        redis_com_list = {"COM1", "COM2", }  # COM1 COM2 為自帶外置RS232串口
        # s搜索缓存所有可用的端口号
        m5s = self.conn.keys(m5_key)
        try:
            # 有可能在遍历m5_devices时 设备就已经拔掉 rasie KeyError
            for m5 in m5s:
                b_info = self.conn.hgetall(m5.decode())
                info = {}
                for i, value in b_info.items():
                    info[i.decode()] = value.decode("utf-8")
                # 添加至redis_com_list 集合中
                redis_com_list.add(info["com"])
        except Exception as e:
            print(str(e) + " 設備連接異常中斷!")
        # time.sleep(3)
        print("redis_com_list" + str(redis_com_list))
        self.scanfPort(redis_com_list)

    def recv(self, ser):
        while True:
            data=ser.read_all()
            if data == "":
                continue
            else:
                break
            # time.sleep(0.02)
        return data


        # 扫描有回指令的端口号
    def scanfPort(self, redis_com_list):
        portList = list(serial.tools.list_ports.comports())
        for i in portList:
            try:
                if i[0] not in redis_com_list:
                    # 判断未曾确认的端口 已经打开的端口 语句会报错
                    with serial.Serial(i[0], baudrate=9600, timeout=3) as ser:
                        if ser.isOpen():
                            print(i[0] + " is open success ")
                            # 发送握手信息
                            ser.write("REMOTE INFORMATION\r".encode())#查看遠程信息 身份信息 轉發信息
                            # json_str = ser.readline().decode("gb2312").strip("\r\n")
                            json_str = ser.readline().decode().strip("\r\n")
                            json_str = ser.readline().decode().strip("\r\n")
                            print("head: ",json_str)

                            if self.is_json(json_str):
                                # 确认符合
                                head = json.loads(json_str)
                                # 握手成功！！！
                                print(i[0] + " 握手成功！！！")

                                self.cache(head, i[0]) # 保存到 Redis

                                ser.write("SMART DEVICE DATA\r".encode())  # 获取智能硬件采集的数据一直发送（2秒间隔），直到接收到其他指令才停止
                                json_str = ser.readline().decode().strip("\r\n")
                                json_str = ser.readline().decode().strip("\r\n")
                                print("data: " + json_str)
                                mythread = threading.Thread(target=self.m5_open_write, args=(i[0], 9600, head["smartDevice_name"]))
                                mythread.setDaemon(True)
                                mythread.start()

                    print(i[0] + " is close ")

                else:
                    print("no found ")
                    time.sleep(1)
            except Exception as e:
                print(i[0] + " is open fail " + str(e))
                time.sleep(1)

    def cache(self, head, com):
        m5device_name = head["smartDevice_name"]
        m5device_type = head["smartDevice_type"]
        m5device_com = com
        m5device_botelv = "9600"
        m5device_remark = head["smartDevice_remark"]
        m5device_forward = head["smartDevice_forward"]
        m5s = self.conn.keys("m5_*")
        self.no='m5_0'+str(len(m5s)+1) + "_%s"

        # redis_com_list.append(i[0])
        # 握手成功 添加在redis 中
        self.conn.hset(self.no % m5device_name, "name", m5device_name)
        self.conn.hset(self.no % m5device_name, "In", m5device_type)
        self.conn.hset(self.no % m5device_name, "com", m5device_com)
        self.conn.hset(self.no % m5device_name, "botelv", m5device_botelv)
        time_local = time.localtime(int(time.time()))
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        self.conn.hset(self.no % m5device_name, "create_time", dt)
        self.conn.hset(self.no % m5device_name, "Out", [i["smartDevicePath_type"] for i in m5device_forward])
        self.conn.hset(self.no % m5device_name, "remark", m5device_remark)
        self.conn.hset(self.no % m5device_name, "device_enable", 1)
        self.conn.hset(self.no % m5device_name, "path_index", 0)

        for index, path in enumerate(m5device_forward):
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_name",
                           path["smartDevicePath_name"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_type",
                           path["smartDevicePath_type"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_host", path["smartDevicePath_ip"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_port",
                           path["smartDevicePath_port"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_username",
                           path["smartDevicePath_user"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_pwd",
                           path["smartDevicePath_pwd"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_topic",
                           path["smartDevicePath_topic"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_remark",
                           path["smartDevicePath_remark"])
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_createtime",dt)

            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_enable",1)  # 默认启用
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_count", 0)  # 计数
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_index", 0)  #
            status = {
                "status_code": "1",
                "message": "路徑未開啟！"
            }
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_status", json.dumps(status))  # 状态
            self.conn.hset("m5path_%s_%d" % (m5device_name, index+1), "path_msg", '{"init":"初始化數據"}')  # 状态
        DriveForTransmit.apply_async(kwargs={"subdevice_name": self.no % m5device_name}, queue="worker_queue")


    def m5_open_write(self, com, botelv, device):
        time.sleep(0.5)
        try:
            cls = self.createtable(device)
            # 1. 打开端口
            with serial.Serial(com, baudrate=botelv, timeout=3) as ser:
                a = b = 0
                while ser.isOpen():
                    time.sleep(.1)
                    if int(self.conn.hget(self.no % device, "device_enable")) == 0:
                        print(com +" 通道被禁用！")
                        b = 0
                        ser.readline() #清除此时缓冲区数据  无效
                        time.sleep(3)
                    else:
                        data = ''
                        data = data.encode()
                        n = ser.inWaiting()
                        if n:
                            # data = data+ser.read(n)
                            data = data + ser.readline()
                        # n = ser.inWaiting()
                        if len(data) > 10:
                            b = 0
                            a = a + 1
                            if a == 1:
                                print(data)
                                print("第一条消息不全丢掉")
                            else:
                                # 2. 读取数据
                                json_str = data.decode("gb2312")
                                # json_dict = json.loads(json_str)
                                print(json_str)
                                # 3. 写入设备數據表
                                if not self.insert_db(json_str, device, cls):
                                    cls =self.createtable(device)
    
                        else:
                            # 计数120次就默认没有消息上来 退出循环、線程
                            b = b + 1
                            if b == 120:
                                self.conn.delete(self.no % device)
                                print("设备无消息 break")
                                break
        except Exception as e:
            device_key=self.no % device
            path_key="m5path_%s_%s"%(device, device_key.split("_")[1][1])
            print(path_key)
            self.conn.delete(device_key)
            self.conn.delete(path_key)
            cls.objects.all().delete()
            print("del "+self.no % device)
            # break

    def createtable(self, device):
        # 为设备新建一张表
        cls = get_smartdevicedata_model(self.no % device)
        if not cls.is_exists():
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(cls)
        return cls

    def insert_db(self, data, device, cls):
        # print(str(data))
        try:
            c = cls.objects.create(data=str(data), smartdevice_name=device)
            c.save()
        except Exception as err:
            print("err: "+str(err))
            return False
        print(self.no % device + " 採集儲存成功！")
        return True

    def is_json(self, json_str):
        try:
            json.loads(json_str)
            return True
        except:
            return False


class DriveModbusTcp(Task):
    name = "DriveModbusTcp"
    conn = get_redis_connection('default')

    def run(self, *arg, **kwarg):
        '''

        :param apply_interface:  采集驱动任务(Modbus TCP) 建立连接的条件
        :param apply_template:   采集驱动任务(Modbus TCP) 设备模板
        :return:  while 循环 break 条件驱动状态 缓存在redis
        '''
        # print("arg:", arg)
        # print("kwarg:", kwarg)
        apply_interface = kwarg["apply_interface"]
        apply_template = kwarg["apply_template"]
        self.key = apply_interface["apply_tcp_device"]
        self.cls = get_subdevicedata_model(self.key)

        print("start modbus tcp drive ",self.key)

        try:
            master = modbus_tcp.TcpMaster(host=apply_interface["apply_tcp_ip"],
                                          port=int(apply_interface["apply_tcp_port"]),
                                          timeout_in_sec=float(apply_interface["apply_tcp_timeout"]))
            var_list=self.init_val(apply_template, int(apply_interface["apply_tcp_slave"]))
            self.loop_start(var_list, master, float(apply_interface["apply_tcp_cycle"]))
            print("end modbus tcp drive ", self.key)
        except Exception as e:
            print(e)
        finally:
            if 'master' in locals().keys():
                master.close()
            self.conn.hset(self.key, "drive_enable", 0)

    def loop_start(self, var_list, master, cycle):
        # print(var_list)
        print(cycle)
        while int(self.conn.hget(self.key, "drive_enable").decode()):
            data = {}
            for var in var_list:
                data[var[0]] = master.execute(var[1], var[2], var[3], var[4])[0]
            # print(data) #采集的模板数据
            self.insert_db(data)
            time.sleep(cycle)
            # n=n-1
    def insert_db(self, data):
        # print(str(data))
        cls = self.cls.objects.create(data=str(data), subdevice_name = self.key)
        cls.save()
        print(self.key+" 採集儲存成功！")


    def init_val(self, apply_template, slave):
        var_list = []
        for etr in apply_template:
            # print(etr["etr_param"], etr["etr_code"], etr["etr_register"], etr["etr_register_num"])
            var_list.append([etr["etr_param"], slave, int(etr["etr_code"]), int(etr["etr_register"],16), int(etr["etr_register_num"],16) ])
        return var_list


class DriveModbusRtu(Task):
    name = "DriveModbusRtu"
    conn = get_redis_connection('default')

    def run(self, *arg, **kwarg):
        '''

        :param apply_interface:  采集驱动任务(Modbus RTU) 建立连接的条件
        :param apply_template:   采集驱动任务(Modbus RTU) 设备模板
        :return:  while 循环 break 条件驱动状态 缓存在redis
        '''
        apply_interface = kwarg["apply_interface"]
        apply_template = kwarg["apply_template"]
        self.key = apply_interface["apply_rtu_device"]
        self.cls = get_subdevicedata_model(self.key)

        print("start modbus rtu drive ", self.key)


        try:
            master = modbus_rtu.RtuMaster(
                serial.Serial(apply_interface["apply_rtu_com"],
                              baudrate=int(apply_interface["apply_rtu_botelv"]),
                              bytesize=int(apply_interface["apply_rtu_databit"]),
                              parity=apply_interface["apply_rtu_parity"][0],
                              stopbits=int(apply_interface["apply_rtu_stopbit"]),
                              xonxoff=0)
            )
            master.set_timeout(float(apply_interface["apply_rtu_timeout"]), )
            master.set_verbose(True)
            var_list = self.init_val(apply_template, int(apply_interface["apply_rtu_slave"]))
            self.loop_start(var_list, master, float(apply_interface["apply_rtu_cycle"]))
            print("end modbus rtu drive ", self.key)
        except Exception as e:
            print(e)
        finally:
            if 'master' in locals().keys():
                master.close()
            self.conn.hset(self.key, "drive_enable", 0)


    def loop_start(self, var_list, master, cycle):
        print(cycle)
        while int(self.conn.hget(self.key, "drive_enable").decode()):
            data = {}
            for var in var_list:
                data[var[0]] = master.execute(var[1], var[2], var[3], var[4])[0]
            # print(data) #采集的模板数据
            self.insert_db(data)
            time.sleep(cycle)

    def insert_db(self, data):
        # print(str(data))
        cls = self.cls.objects.create(data=str(data), subdevice_name = self.key)
        cls.save()
        print(self.key+" 採集儲存成功！")

    def init_val(self, apply_template, slave):
        var_list = []
        for etr in apply_template:
            # print(etr["etr_param"], etr["etr_code"], etr["etr_register"], etr["etr_register_num"])
            var_list.append([etr["etr_param"], slave, int(etr["etr_code"]), int(etr["etr_register"], 16),
                             int(etr["etr_register_num"], 16)])
        return var_list


class DriveForTransmit(Task):
    name = "DriveForTransmit"
    conn = get_redis_connection('default')
    mqttclient = ""

    def run(self, *arg, **kwarg):
        '''

        :param arg:
        :param kwarg: subdevice设备名 data_format 数据格式
        redis subdevice: device_enable 设备启用禁用
              path_subdevice_pathname: path_enable  设备路径启用禁用
        :return:
        '''
        # 获取设备名
        # 获取设备路径名称
        self.subdevice = kwarg["subdevice_name"]
        print("start  drive transmit "+self.subdevice)
        # self.keys = "path_{}_*".format(self.subdevice)
        self.keys =  "m5path_{}_*".format(self.subdevice.split("_")[2]) if "m5_0" == self.subdevice[:4] else "path_{}_*".format(self.subdevice)
        self.path_keys = self.conn.keys(self.keys)

        # cls = get_subdevicedata_model(self.subdevice)
        cls =  get_smartdevicedata_model(self.subdevice) if "m5_0" == self.subdevice[:4] else get_subdevicedata_model(self.subdevice)
        
        while True:
            # 大條件 設備是否禁用
            enable=self.conn.hget(self.subdevice, "device_enable")
            if not enable:
                break
            index = int(self.conn.hget(self.subdevice, "path_index"))
            result = self.transmit(index, cls)

            if result:  #所有路徑被禁用的情況 驅動停止
                break

            index = int(self.conn.hget(self.subdevice, "path_index"))
            self.conn.hset(self.subdevice, "path_index", index + 1)
            time.sleep(3)

        self.close_tip()
        print("end for drive transmit " + self.subdevice)

    def close_tip(self):
        status = {
                     "status_code": "1",
                     "message": "路徑未開啟！"
                 },
        self.path_keys = self.conn.keys(self.keys)
        for path_key in self.path_keys:
            key=path_key.decode()
            self.conn.hset(key, 'path_status', json.dumps(status))
            self.conn.hset(key, 'path_index', 0)

    def transmit(self, index, cls):
        # 路徑是否禁用
        n = 0
        self.path_keys = self.conn.keys(self.keys)
        path_length = len(self.path_keys)
        for path_key in self.path_keys:
            key=path_key.decode()
            print(key)
            type=self.conn.hget(key, "path_type").decode()
            if int(self.conn.hget(key, "path_enable")): #判斷路徑是否被禁用
                if type == "第三方MQTT" or type == "MQTT":
                    result = self.transmitformqtt(key, index, cls)
                    if result["status_code"] == "1":
                        print(self.subdevice+" "+result["error"]+str(index))
                        self.conn.hset(self.subdevice, "path_index", index - 1)

                elif self.conn.hget(key, "path_type").decode() == "CorePro Server":
                    self.transmitforcorepro(key, index, cls)
            else:
                print(self.subdevice +" "+ key +" 禁用")
                n += 1
                if n == path_length:
                    return True


    def transmitformqtt(self, key, index, cls):
        # 路徑名稱key, 設備名稱subdevice, Django 數據objects接口 cls
        mqtt_topic = self.conn.hget(key, "path_topic").decode()
        mqtt_host = self.conn.hget(key, "path_host").decode()
        mqtt_port = int(self.conn.hget(key, "path_port").decode())
        mqtt_username = self.conn.hget(key, "path_username").decode()
        mqtt_pwd = self.conn.hget(key, "path_pwd").decode()
        mqtt = [mqtt_host, mqtt_port, mqtt_username, mqtt_pwd, mqtt_topic]
        return self.mqttcore(key, index, cls, mqtt)


    def transmitforcorepro(self,key, index, cls):
        iot_topic = self.conn.hget(key, "path_topic").decode()
        iot_host = self.conn.hget(key, "path_host").decode()
        iot_port = int(self.conn.hget(key, "path_port").decode())
        iot_username = self.conn.hget(key, "path_username").decode()
        iot_pwd = self.conn.hget(key, "path_pwd").decode()
        iot = [iot_host, iot_port, iot_username, iot_pwd, iot_topic]
        if int(self.conn.hget(key, 'path_index')) == 0:
            # 路径的index 用来看是否 corepro 模组连接初始化
            timestamp = str(round(time.time() * 1000))
            self.mqttclient = client( broker= iot_host,
                                 port= iot_port,
                                 username= iot_username,
                                 password= iot_pwd,
                                 client_id=timestamp)

            self.mqttclient.mqttc.subscribe(topic=iot_topic+"/reply")
            self.conn.hset(key, 'path_index', 1) #初始化成功

        return self.iotcore( key, index, cls, self.mqttclient, iot)


    def iotcore(self, key, index, cls, mqttclient, iot):
        if self.mqttclient == "":
            self.conn.hset(key, 'path_index', 0)
            return False

        obj = cls.objects.filter(id=index).values("data")
        if obj.count() == 0:
            last_row = cls.objects.last()
            if last_row.id > index:
                # 行缺失
                return True

            else:
                # 傳輸數據索引大於總行數
                status = {
                             "status_code": "1",
                             "message": "設備無數據！"
                         },
                self.conn.hset(key, 'path_status', json.dumps(status))
                return False
        else:
            obj = obj[0]
            obj = json.loads(obj["data"].replace("'", '"'))
            data= self.corePro_format(key)
            data["app_params"][0].update(obj)
            data = json.dumps(data)

            mqttclient.mqttc.publish(topic=iot[-1], payload=data, qos=1)

            print(self.subdevice + " " + key + " " + "發佈成功! " + str(index))

            count = int(self.conn.hget(key, "path_count"))
            status_msg = {
                             "status_code": "0",
                             "message": "路徑运行正常！"
                         },
            self.conn.hset(key, 'path_status', json.dumps(status_msg))
            self.conn.hset(key, 'path_msg', data)
            self.conn.hset(key, 'path_count', count + 1)
            return True

    def mqttcore(self, key, index, cls, mqtt):
        obj =cls.objects.filter(id=index).values("data", "id", "smartdevice_name", "create_time") if "m5path" == key[:6] else cls.objects.filter(id=index).values("data", "id", "subdevice_name", "create_time")
        if obj.count() == 0:
            last_row = cls.objects.last()
            if last_row is None:
                status_msg = {
                    "status_code": "1",
                    "error": "设备无数据！"
                }
                return status_msg
            if last_row.id > index:
                # 行缺失
                status_msg = {
                    "status_code": "0",
                    "error": "行缺失！"
                }
                return status_msg

            else:
                #傳輸數據索引大於總行數
                status = {
                             "status_code": "1",
                             "error": "无数据更新！"
                         },
                self.conn.hset(key, 'path_status', json.dumps(status))
                return status
        else:
            obj = obj[0]
            obj["create_time"]=obj["create_time"].strftime("%Y-%m-%d %H:%M:%S")
            obj["data"] = json.loads(obj["data"].replace("'", '"'))
            data = json.dumps(obj)
            # 有客戶端連接會報錯
            try:
                publish.single(mqtt[-1] , payload=data,
                               hostname=mqtt[0],
                               port=mqtt[1],
                               auth={'username':mqtt[2], 'password':mqtt[3]})
                print(self.subdevice + " " + key + " " + "發佈成功! " + str(index))
                count = int(self.conn.hget(key, "path_count"))
                self.conn.hset(key, 'path_msg', data)
                self.conn.hset(key, 'path_count', count + 1)

                status_msg = {
                    "status_code": "0",
                    "message": "路徑运行正常！"
                }
                return status_msg
            except:
                status_msg = {
                    "status_code": "1",
                    "error": "網絡連接失敗！"
                }
                print(status_msg.get("error"))
                return status_msg
            finally:
                self.conn.hset(key, 'path_status', json.dumps(status_msg))

            

    def corePro_format(self, key):
        # 返回發佈在CorePro的數據格式
        return {
                  "system_params": {
                    "type": "",
                    "token": "",
                    "timestamp": str(time.time()),
                    "appid": self.conn.hget(key, "path_datatypeid").decode(),
                    "sign": "",
                    "messageid": str(time.time())
                  },
                  "app_params": [
                    {
                      "device_name": self.subdevice,
                      # "U0": 230,
                      # "I0": 120,
                      # "Mod": 123,
                      # "Ver": 3312,
                      # "Ur": 50,
                      # "Ir": 260,
                      # "Temp": 25
                    }
                    ]
                }

