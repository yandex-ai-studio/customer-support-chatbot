from __future__ import annotations

import os

from chatkit.server import StreamingResult
from chatkit.store import Store
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.responses import JSONResponse

from .airline_client import fetch_customer_profile
from .chatkit_server import CustomerSupportServer
from .dynamodb import DynamoDBStore
from .memory_store import MemoryStore

app = FastAPI(title="ChatKit Customer Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_support_server: CustomerSupportServer | None = None


def get_server() -> CustomerSupportServer:
    global _support_server
    if _support_server is None:
        _support_server = CustomerSupportServer(_create_store())
    return _support_server


@app.post("/support/chatkit")
async def chatkit_endpoint(
        request: Request,
        server: CustomerSupportServer = Depends(get_server)
) -> Response:
    payload = await request.body()

    result = await server.process(payload, {"request": request})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")

    return JSONResponse(result)


@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str) -> Response:
    try:
        profile = await fetch_customer_profile(profile_id)
        return JSONResponse({"success": True, "profile": profile})
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


# Initialize store based on environment variable
def _create_store() -> Store:
    """Create the appropriate store based on environment configuration."""
    use_memory = os.environ.get("USE_MEMORY_STORE", "true").lower() == "true"

    if use_memory:
        return MemoryStore()
    else:
        # DynamoDB configuration
        store = DynamoDBStore(
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            table_prefix=os.environ.get("DYNAMODB_TABLE_PREFIX", "chatkit"),
            endpoint_url=os.environ.get("DYNAMODB_ENDPOINT_URL"),
        )

        # Create tables if AUTO_CREATE_TABLES=true
        if os.environ.get("AUTO_CREATE_TABLES", "false").lower() == "true":
            store.create_tables()

        return store
