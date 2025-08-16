from starlette.routing import Route

from .endpoints import pay, ping, summary

routes = [
    Route("/payments", endpoint=pay, methods=["POST"]),
    Route("/payments-summary", endpoint=summary, methods=["GET"]),
    Route("/ping", endpoint=ping, methods=["GET"]),
]
