from django.conf.urls import url, include
# from user import views
from . import views


# app_name = 'user'
app_name = 'Device'
urlpatterns = [
    url(r'^list/', views.driveList, name='drivelist'),  #
    url(r'^enable/', views.driveEnable, name='driveenable'),  #
    url(r'^varlist/', views.varList, name='varlist'),  #
]
