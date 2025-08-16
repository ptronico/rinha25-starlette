import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

import httpx
from starlette.applications import Starlette


async def process_payment_queue(app: Starlette):
    while True:
        message = await app.state.queue.pop()
        asyncio.create_task(process_payment(app, raw_message=message))


async def process_payment(app: Starlette, raw_message: str):
    async with app.state.semaphore:
        data = {
            "amount": 19.9,
            "correlationId": str(uuid.uuid4()),
            "requestedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000") + "Z",
            # "requestedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
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
            await app.state.queue.re_push("m")
            # await asyncio.sleep(0.1)
        except Exception:
            raise


async def get_summary(app: Starlette, start_date: str, end_date: str) -> dict:
    return {}
    async with app.state.semaphore:
        origin: str = app.state.hostname
        url = f"{app.state.other_instance_url}/payments-summary?from={start_date}&to={end_date}&origin={origin}"
        try:
            response: httpx.Response = await app.state.other_instance_client.get(url)
            return response.json()
        except Exception:
            raise


async def warm_up(app: Starlette):
    await asyncio.sleep(0)
    await get_summary(app, start_date="2020-01-01T00:00:00.000Z", end_date="2030-01-01T00:00:00.000Z")
    base_url = os.environ.get("PROCESSOR_DEFAULT_URL", "http://payment-processor-default:8080")
    try:
        httpx.Response = await app.state.payment_processor_client.get(
            f"{base_url}/payments/service-health",
            timeout=5,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logging.warning(e)
    except Exception:
        raise
