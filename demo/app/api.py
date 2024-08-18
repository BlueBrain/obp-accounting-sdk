"""Api."""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing, asynccontextmanager
from typing import Any

from fastapi import FastAPI
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from obp_accounting_sdk import AsyncAccountingSessionFactory
from obp_accounting_sdk.constants import ServiceSubtype
from obp_accounting_sdk.errors import (
    AccountingReservationError,
    AccountingUsageError,
    InsufficientFundsError,
)

from .dependencies import AccountingSessionFactoryDep
from .schema import QueryRequest, QueryResponse
from .service import run_query

L = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[dict[str, Any]]:
    """Execute actions on server startup and shutdown."""
    L.info("Starting api")
    async with aclosing(AsyncAccountingSessionFactory()) as session_factory:
        yield {"session_factory": session_factory}


app = FastAPI(title="Demo", lifespan=lifespan)


@app.exception_handler(InsufficientFundsError)
async def insufficient_funds_error_handler(
    _request: Request, exc: InsufficientFundsError
) -> JSONResponse:
    """Handle insufficient funds errors."""
    L.error("Error: %r, cause: %r", exc, exc.__cause__)
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={"message": f"Error: {exc.__class__.__name__}"},
    )


@app.exception_handler(AccountingReservationError)
@app.exception_handler(AccountingUsageError)
async def accounting_error_handler(
    _request: Request, exc: AccountingReservationError | AccountingUsageError
) -> JSONResponse:
    """Handle accounting errors."""
    L.error("Error: %r, cause: %r", exc, exc.__cause__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"Error: {exc.__class__.__name__}"},
    )


@app.post("/query")
async def query(
    query_request: QueryRequest,
    accounting_session_factory: AccountingSessionFactoryDep,
) -> QueryResponse:
    """Execute a query."""
    proj_id = "00000000-0000-0000-0000-000000000001"
    estimated_count = len(query_request.input_text) * 3
    async with accounting_session_factory.oneshot_session(
        subtype=ServiceSubtype.ML_LLM,
        proj_id=proj_id,
        count=estimated_count,
    ) as acc_session:
        output_text = await run_query(query_request.input_text)
        actual_count = len(query_request.input_text) + len(output_text)
        acc_session.count = actual_count
    return QueryResponse(
        input_text=query_request.input_text,
        output_text=output_text,
    )
