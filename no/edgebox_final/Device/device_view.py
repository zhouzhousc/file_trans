#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/10/11 15:20
# @Author  : userzhang
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import viewsets
# from .serializers import CollectDataSerializer, M5DataSerializer, SubDeviceSerializer
# from .models import CollectData, M5Data, SubDevice

#
# class DataList(APIView):
#     """
#     所有的CollectData或者创建一条新的数据。
#     """
#     def get(self, request, format=None):
#         datalist = CollectData.objects.all().order_by("-id")[0:10]
#         serializer = CollectDataSerializer(datalist, many=True)
#         return Response(serializer.data)
#
#     def post(self, request, format=None):
#         try:
#             subdevice=SubDevice.objects.get(id=request.data["subdevice_id"])
#         except SubDevice.DoesNotExist:
#             raise Http404
#
#         serializer = CollectDataSerializer(data=request.data, context={"subdevice":subdevice})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class CollectDataViewSet(viewsets.ModelViewSet):
#     """
#     子设备 数据集所有的数据分页显示
#     """
#     queryset = CollectData.objects.all().order_by("id")
#     # queryset = CollectData.objects.filter(data_status=0)
#     serializer_class = CollectDataSerializer
#
# class M5DataViewSet(viewsets.ModelViewSet):
#     """
#     M5 数据集所有的数据分页显示
#     """
#     queryset = M5Data.objects.all().order_by("id")
#     serializer_class = M5DataSerializer
#
# class SubDeviceViewSet(viewsets.ReadOnlyModelViewSet):
#     '''
#     已注册的子设备详细信息列表
#     '''
#     queryset = SubDevice.objects.all().order_by("id")
#     serializer_class = SubDeviceSerializer
