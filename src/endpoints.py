import asyncio

from starlette.responses import Response

from .databases import TransactionsDB
from .responses import OrjsonResponse
from .tasks import get_summary, process_payment


async def pay(request):
    asyncio.create_task(process_payment(request.app, "m"))
    return Response(status_code=202)


async def summary(request):
    response = {}
    param_from = request.query_params["from"]
    param_to = request.query_params["to"]
    db: TransactionsDB = request.app.state.db

    if "origin" not in request.query_params:
        response = await get_summary(app=request.app, start_date=param_from, end_date=param_to)

    default_amount, default_requests = db.summary(
        start_datetime_str=param_from,
        end_datetime_str=param_to,
    )
    default_amount += response.get("default", {}).get("totalAmount", 0)
    default_requests += response.get("default", {}).get("totalRequests", 0)

    return OrjsonResponse(
        content={
            "default": {
                "totalAmount": round(default_amount, 2),
                "totalRequests": default_requests,
            },
            "fallback": {
                "totalAmount": 0,
                "totalRequests": 0,
            },
        }
    )


async def ping(request):
    return OrjsonResponse(
        content={
            "hostname": request.app.state.hostname,
        }
    )
