import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

import httpx
from starlette.applications import Starlette

# async def scale_semaphore(app: Starlette):
#     semaphore: ElasticSemaphore = app.state.semaphore
#     while True:
#         cpu = psutil.cpu_percent(interval=None)
#         if cpu < 40:
#             new_semaphore_val = app.state.semaphore_min_val
#         elif cpu > 80:
#             new_semaphore_val = app.state.semaphore_max_val
#         if new_semaphore_val != app.state.semaphore_val:
#             app.state.semaphore_val = new_semaphore_val
#             semaphore.set_value(app.state.semaphore_val)
#         logging.warning(f"CPU: {cpu} SemVal: {app.state.semaphore_val} QueueSize: {app.state.queue.qsize()}")
#         await asyncio.sleep(2)


async def process_payment(app: Starlette, raw_message: str):
    async with app.state.semaphore:
        data = {
            "amount": 19.9,
            "correlationId": str(uuid.uuid4()),
            "requestedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000") + "Z",
        }
        base_url = os.environ.get("PROCESSOR_DEFAULT_URL", "http://payment-processor-default:8080")
        try:
            response: httpx.Response = await app.state.payment_processor_client.post(
                f"{base_url}/payments",
                json=data,
            )
            response.raise_for_status()
            if response.status_code == 200:
                app.state.db.add(datetime_str=data["requestedAt"])
            else:
                logging.warning(f"Error on default payment processor: {response.status_code} {response.text}")
        except httpx.HTTPStatusError:
            asyncio.create_task(process_payment(app, raw_message))


async def get_summary(app: Starlette, start_date: str, end_date: str) -> dict:
    origin: str = app.state.hostname
    url = f"{app.state.other_instance_url}/payments-summary?from={start_date}&to={end_date}&origin={origin}"
    try:
        response: httpx.Response = await app.state.other_instance_client.get(url)
        return response.json()
    except Exception:
        raise
