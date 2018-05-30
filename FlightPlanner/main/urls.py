from django.conf.urls import url

from . import views

app_name = 'main'

urlpatterns = [
    url('^$', views.upload_file, name='upload_file')
]