from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/esp32/data/$', consumers.ESP32DataConsumer.as_asgi()),
]