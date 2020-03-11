#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/28 8:09
# @Author  : userzhang

import time
from paho.mqtt.client import Client


class mqtt_client_connect():

    def __init__(self,broker="10.129.7.199",port=1883,username="iot",password="iot123!",client_id="12345",keepalive=10,deviceinfo=""):
        self.broker=broker
        self.port=port
        self.username=username
        self.password=password
        self.deviceinfo=deviceinfo
        self.payload=None
        self.client_id=client_id
        self.num=0
        self.num1=0
        self.numerror=0
        self.flag=1
        self.keepalive=keepalive
        try:
            # self.mqttc=Client(clean_session=False,client_id="12345")
            self.mqttc = Client(client_id=self.client_id)
            self.mqttc.on_connect=self.on_connect
            self.mqttc.on_publish=self.on_publish
            self.mqttc.on_disconnect=self.on_disconnect
            self.mqttc.on_subscribe=self.on_subscribe
            self.mqttc.username_pw_set(self.username,self.password)
            self.mqttc.connect(self.broker,port=self.port,keepalive=self.keepalive)
            self.mqttc.loop_start()
        except:
            self.flag = 0
            # self.deviceinfo["textEdit"].append(">>>mqtt_client_connect error: mqttc connect failed Please check Broker and Port....")
            print("mqtt_client_connect error: mqttc connect failed Please check Broker and Port....")
            # return None
# ======================================================
    def on_connect(self,client, userdata, flags, rc):
        #rc为0 返回连接成功
        # strcurtime = time.strftime("%Y-%m-%d %H:%M:%S")
        if rc==0:
            self.flag = 1
            # self.deviceinfo["textEdit"].append(">>>"+strcurtime+" OnConnetc, rc: "+str(rc)+" successful "+str(client._username))
            print(" OnConnetc, rc: "+str(rc)+" successful "+str(client._username))
        #     if self.deviceinfo["pub"]=="":
        #         self.mqttc.subscribe(topic="/" + self.deviceinfo["Produckey"]+ "/" + self.deviceinfo["Devicename"] + "/property/post/reply", qos=1)
        #     else:
        #         self.mqttc.subscribe(topic=self.deviceinfo["pub"]+"/reply", qos=1)
        else:
            self.flag = 0
            # self.deviceinfo["textEdit"].append(">>>"+strcurtime+" OnConnetc, rc: "+str(rc)+" unsuccessful"+" "+str(client._username))
            print(" OnConnetc, rc: "+str(rc)+" unsuccessful"+" "+str(client._username))


    def on_disconnect(self,client, userdata, rc):

        self.flag = 0
        print(" Unexpected MQTT disconnection. Will auto-reconnect")


    def on_publish(self,client, userdata, mid):
        append=" OnPublish, mid: " + str(mid)+" "+str(client._username)
        # self.deviceinfo["textEdit"].append(">>>"+append)
        print(append)

    def on_subscribe(self,client, userdata, mid, granted_qos):
        append=" Subscribed: " + str(mid) + "   " + str(granted_qos)+" SUB successful "+str(client._username)
        print(append)
        # self.deviceinfo["textEdit"].append(">>>" + append)
        self.mqttc.on_message = self.on_message

    def on_message(self,client, userdata, msg):
        append=": " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload)+str(client._username)
        # self.deviceinfo["textEdit"].append(">>>" + append)
        print(append)








