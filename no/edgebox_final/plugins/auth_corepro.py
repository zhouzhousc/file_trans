#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/10/4 15:48
# @Author  : userzhang

import hashlib
import hmac
import time
import json
import requests


class AuthCorepro(object):

    def __init__(self,ProductKey='6453387282597968558',DeviceName='B5device',DeviceSecret='b442f2b99ecfd290ebf28f42b31266187fd23aedd24393f509fd412097100f4e318f047d53d61af2e461c5e41ad6cee89e65b1063d7eead2bb9914637cbed414',
                 auth_url='https://service-o8bikfta-1256676747.ap-guangzhou.apigateway.myqcloud.com/release/corepro_deviceauth/mqtt_auth?X-MicroService-Name=beacon-corepro-deviceauth&X-NameSpace-Code=default-code',
                 btn=None):

        # ---------------- device 三元組 --------------------
        self.ProductKey = ProductKey
        self.DeviceName = DeviceName
        self.DeviceSecret = DeviceSecret

        # --------------------- 鑒權URL -----------------------
        self.auth_url = auth_url

        # ------sign timestamp username password mqtthost mqttport  -----
        self.sign=None
        self.timestamp=None
        self.username = ""
        self.password = ""
        self.mqtthost = ""
        self.mqttport = ""
        self.btn=btn

        self.get_auth_sign()
        self.get_username_pwd()

    # ------------------ 获取sign 签名 -----------------------------------
    def get_auth_sign(self):
        try:
            DeviceSecret = bytearray.fromhex(self.DeviceSecret)
            self.timestamp = str(round((time.time() * 1000)))
            # print(self.timestamp)
            sign_content = ''.join(('clientId',self.ProductKey,'-',self.DeviceName,'deviceName', self.DeviceName, 'productKey', self.ProductKey, 'timestamp', self.timestamp))
            sign_content = bytes(sign_content, encoding='utf-8')
            sign_method = hashlib.sha256
            self.sign = hmac.new(DeviceSecret, sign_content, sign_method).hexdigest()
        except Exception as e:
            print(str(e))

        # print(self.sign)

    # -------------------- post请求 获取Token -----------------------------
    def get_username_pwd(self):
        try:
            params={  "productKey":self.ProductKey,
                      "deviceName":self.DeviceName,
                      "sign":self.sign,
                      "timestamp":self.timestamp,
                      "signmethod":"HmacSHA256",
                      "clientId":self.ProductKey+'-'+self.DeviceName
                    }
            session = requests.Session()
            session.trust_env = False
            r=session.post(self.auth_url,data=params,timeout=5)
            data=r.text
            data=json.loads(data)
            # print(type(data))
            if not data["errmsg"]=="":
                print(self.DeviceName+" 鉴权失败！................"+data["errmsg"])



            elif data["errmsg"]=="":
                self.mqtthost = data["payload"][0]["iotHost"]
                self.mqttport = data["payload"][0]["iotPort"]
                self.username=data["payload"][0]["iotId"]
                self.password=data["payload"][0]["iotToken"]
                print(self.DeviceName+" 鉴权成功！................")

        except:

            print("requests.post error： Http Connect failed or Timeout please check you network")





#  # 实例
# B5device=auth_corepro(
#     ProductKey='6453668283668082833',
#     DeviceName='P115XK828',
#     DeviceSecret='188c8a493e14354ed0ae164db678ff55446f97a13abfd3430f2e6f98f8d3b6dfe7b48efae725977c15af5f1207efd7b462ab4d8a3e556e15c856cc940b0c2a6e'
# )

# print(B5device.username,B5device.password,B5device.mqtthost,B5device.mqttport)
# #
# B5device=auth_corepro(
#     ProductKey='6513234635034637560',
#     DeviceName='meter_test_01',
#     DeviceSecret='4ccec2480ac50bf0571220a01f1ad6d5e6585958319b9f47bd0575399e565171',
#     auth_url="http://service-de8elrpo-1255000335.apigw.fii-foxconn.com/release/corepro/auth/mqtt/?X-NameSpace-Code=corepro&X-MicroService-Name=corepro-device-auth"
# )
#
# print(B5device.username,B5device.password,B5device.mqtthost,B5device.mqttport)
