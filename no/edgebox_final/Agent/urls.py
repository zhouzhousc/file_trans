from django.conf.urls import url
# from user import views
from . import views

# app_name = 'user'
app_name = 'Agent'
urlpatterns = [
    url(r'^info/', views.Info, name='info'),  #
    url(r'^sysinfo/', views.sysInfo, name='sysinfo'),  #
]
