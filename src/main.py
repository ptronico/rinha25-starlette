import asyncio
import contextlib
import os
import socket

import httpx
from starlette.applications import Starlette

from .databases import TransactionsDB
from .queues import AsyncDeque
from .tasks import process_payment_queue, warm_up
from .urls import routes


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    app.state.hostname = socket.gethostname()
    other_instance = "api1" if app.state.hostname == "api2" else "api2"
    app.state.other_instance_url = f"http://{other_instance}:8000"
    app.state.db = TransactionsDB()
    app.state.other_instance_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=1,
            max_keepalive_connections=1,
            keepalive_expiry=300.0,
        )
    )
    app.state.payment_processor_client = httpx.AsyncClient(http2=True)
    app.state.queue = AsyncDeque()
    app.state.semaphore = asyncio.Semaphore(int(os.environ.get("SEMNUM", 5)))
    # async with httpx.AsyncClient(
    #     http2=True,
    #     # limits=httpx.Limits(
    #     #     keepalive_expiry=30,
    #     #     max_connections=10,
    #     #     max_keepalive_connections=5,
    #     # ),
    # ) as client:
    #     app.state.payment_processor_client = client
    for i in range(5):
        await asyncio.sleep(1)
        try:
            await warm_up(app)
        except Exception:
            pass
    asyncio.create_task(process_payment_queue(app))
    yield


app = Starlette(
    debug=False,
    lifespan=lifespan,
    routes=routes,
)
