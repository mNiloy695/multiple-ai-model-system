import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIModelBackend.settings')

django.setup() 


from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from ai_model import routing
from channels.generic.websocket import AsyncWebsocketConsumer

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
    
#     async def receive(self, text_data=None, bytes_data=None):
#         # handle large payload here
#         pass

#     # Override max_size if needed (works for bytes_data)
#     max_message_size = 10 * 1024 * 1024  # 10 MB
# # ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  
    "websocket": URLRouter(
        routing.websocket_urlpatterns  
    ),
})
