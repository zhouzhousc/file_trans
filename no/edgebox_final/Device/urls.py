from django.conf.urls import url, include
# from user import views
from . import views
from . import device_view
from rest_framework.routers import DefaultRouter

# # 第一步注册主路由
# router = DefaultRouter()
# router.register('manage', device_view.SubDeviceViewSet, base_name="manage")
# router.register('collectdata', device_view.CollectDataViewSet, base_name="collectdata")


# app_name = 'user'
app_name = 'Device'
urlpatterns = [
    # url(r'^', include((router.urls, "router"), namespace="router")),
    url(r'^list/', views.List, name='list'),  #
    url(r'^enable', views.Enable, name='enable'),  #
    url(r'^create', views.Create, name='create'),  #
    url(r'^type/', views.Type, name='type'),  #
    url(r'^protocol/', views.protocolList, name='protocol'),  #
    url(r'^template$', views.templateList, name='template'),  #
    url(r'^template/create/', views.templateCreate, name='templatecreate'),  #
    url(r'^modbusrtuform/', views.modbusRtuForm, name='modbusrtufrom'),  #
    url(r'^modbustcpform/', views.modbusTcpForm, name='modbustcpform'),  #
    url(r'^template/apply/', views.templateApply, name='templateapply'),  #
    url(r'^apply$', views.showApply, name='showapply'),  #
    url(r'^data$', views.Data, name='data'),  #
    url(r'^path$', views.pathList, name='path'),  #
    url(r'^path/info$', views.pathInfo, name='pathinfo'),  #
    url(r'^path/enable$', views.pathEnable, name='pathenable'),  #
    url(r'^path/delete$', views.pathDelete, name='pathdelete'),  #
    url(r'^auth$', views.Auth, name='auth'),  #

    # url(r'^all$', device_view.DataList.as_view(), name='alldata'),

]
