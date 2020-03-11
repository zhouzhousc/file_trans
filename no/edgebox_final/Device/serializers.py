#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/12 19:57
# @Author  : userzhang
# from rest_framework import serializers
# from .models import CollectData, M5Data
# from .models import SubDevice
#
#
#
# class SubDeviceSerializer(serializers.HyperlinkedModelSerializer):
#
#     # related_name 有关 自定义外键字段
#     collectdatas = serializers.HyperlinkedRelatedField(many=True,view_name='collectdata-detail', read_only=True)
#     # name=collectdatas
#     url = serializers.HyperlinkedIdentityField(view_name="subdevice-detail")
#     class Meta:
#         model = SubDevice
#         # 和"__all__"等价
#         fields = ("url", 'subdevice_name', 'subdevice_key', 'subdevice_secret',"collectdatas")
#
#
#
# class CollectDataSerializer(serializers.ModelSerializer):
#
#     # subdevice_id =serializers.PrimaryKeyRelatedField(many=True, read_only=True)
#     # subdevice_id = SubDeviceSerializer()
#     #自定义字段
#     subdevice_id = serializers.SerializerMethodField()
#     class Meta:
#         model = CollectData
#         # 和"__all__"等价
#         fields = ("id",'subdevice_id', 'data_type', 'data_status', 'data',
#                   'create_time')
#
#     #自定义字段获取关联字段
#     def get_subdevice_id(self, obj):
#         return obj.subdevice.id
#
#     #创建
#     def create(self, validated_data):
#         # 处理外键字段
#
#         return CollectData.objects.create(subdevice=self.context["subdevice"], **validated_data)
#
# class M5DataSerializer(serializers.HyperlinkedModelSerializer):
#
#     class Meta:
#         model = M5Data
#         # 和"__all__"等价
#
#         fields = ("url","id",'subdevice_name', 'data_type', 'data_status', 'data','create_time')