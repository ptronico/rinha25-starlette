import asyncio
import contextlib
import os
import socket

import httpx
from starlette.applications import Starlette

from .databases import TransactionsDB
from .semaphore import ElasticSemaphore
from .urls import routes


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    app.state.hostname = socket.gethostname()
    other_instance = "api1" if app.state.hostname == "api2" else "api2"
    app.state.other_instance_url = f"http://{other_instance}:8000"
    app.state.db = TransactionsDB()
    app.state.queue = asyncio.Queue()
    app.state.other_instance_client = httpx.AsyncClient(http2=True)
    app.state.payment_processor_client = httpx.AsyncClient(http2=True)
    app.state.semaphore = ElasticSemaphore(int(os.environ.get("SEMAPHORE", 4)))
    yield


app = Starlette(
    debug=False,
    lifespan=lifespan,
    routes=routes,
)
