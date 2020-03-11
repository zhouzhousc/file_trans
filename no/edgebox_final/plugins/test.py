# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @Time    : 2019/10/23 19:12
# # @Author  : userzhang
# import json
# import time
#
# from paho.mqtt import publish
#
# from plugins.auth_corepro import AuthCorepro as auth
# from plugins.mqtt_pub_sub import mqtt_client_connect as client
#
# auth_url = "http://service-de8elrpo-1255000335.apigw.fii-foxconn.com/release/corepro/auth/mqtt/?X-NameSpace-Code=corepro&X-MicroService-Name=corepro-device-auth"
# agent = auth(   DeviceName="Edgebox006",
#                 ProductKey="6591108752476297855",
#                 DeviceSecret="e5892975ba8964299480cb31e7fd1414ae21c023b0839c3f012cc7702601ee88",
#                 auth_url=auth_url)
# print(agent.username, agent.password, agent.mqtthost, agent.mqttport)
#
#
# data_type = "HC001"
# data_type_id = "datakeywqbhs0RZwQlCdrsVnBDZ"
# data_topic = "/data/6591108752476297855/HC001/data/gateway"
# data_format = {
#                   "system_params": {
#                     "type": "",
#                     "token": "",
#                     "timestamp": str(time.time()),
#                     "appid": "datakeywqbhs0RZwQlCdrsVnBDZ",
#                     "sign": "",
#                     "messageid": str(time.time())
#                   },
#                   "app_params": [
#                     {
#                       "device_name": "HC001",
#                       "U0": 230,
#                       "I0": 120,
#                       "Mod": 123,
#                       "Ver": 3312,
#                       "Ur": 50,
#                       "Ir": 260,
#                       "Temp": 25
#                     }
#                     ]
#                 }
#
# #
# # timestamp = str(round(time.time() * 1000))
# # mqttclient = client(broker="10.124.128.19",
# #                                  port=int(1883),
# #                                  username="6591108752476297855_Edgebox006",
# #                                  password='NytH6308vzo546m2XpXs9',
# #                                  client_id=timestamp)
# #
# # mqttclient.mqttc.subscribe(topic=data_topic+"/reply")
# #
# # n=5
# # while n:
# #     mqttclient.mqttc.publish(topic=data_topic, payload=json.dumps(data_format),qos=1)
# #     n = n-1
# #     time.sleep(3)
# #
# # mqttclient.mqttc.loop_stop()
# # mqttclient.mqttc.disconnect()
#
#
# publish.single(data_topic , payload=json.dumps(data_format),
#                            hostname="10.124.128.19",
#                            port=1883,
#                            auth={'username':"6591108752476297855_Edgebox006", 'password':"NytH6308vzo546m2XpXs9"})
