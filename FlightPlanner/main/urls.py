from django.conf.urls import url

from . import views

app_name = 'main'

urlpatterns = [
    url('^$', views.upload_file, name='upload_file'),
    url('^map$', views.input_map, name='input_map'),
    url('^render_map/(?P<name>[\w\-]+)$', views.render_map, name='render_map'),
    url('^test$', views.test, name='test'),
]