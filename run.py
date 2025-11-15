from daphne.server import Server
from AIModelBackend.asgi import application

server = Server(
    application=application,
    endpoints=["tcp:port=8082:interface=0.0.0.0"],
    websocket_max_message_size=10*1024*1024  # 10 MB
)

server.run()