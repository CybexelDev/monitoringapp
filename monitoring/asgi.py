# import os

# os.environ.setdefault(
#     "DJANGO_SETTINGS_MODULE",
#     "monitoring.settings"
# )

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack

# from monitoringapp.chat.routing__ import websocket_urlpatterns


# django_asgi_app = get_asgi_application()


# application = ProtocolTypeRouter({
#     "http": django_asgi_app,

#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             websocket_urlpatterns
#         )
#     ),
# })




import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "monitoring.settings",
)

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})