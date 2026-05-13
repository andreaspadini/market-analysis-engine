from __future__ import annotations
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ..api_impl_v1 import ApiErrorV1
from ..errors_v1 import ErrorEnvelopeV1, ErrorCodeV1, internal_error

from .routers import router


def _http_status_for_envelope(env: ErrorEnvelopeV1) -> int:
    # Transport mapping (no business logic): stable mapping by error_code.
    code = env.error_code
    if code == ErrorCodeV1.NOT_FOUND:
        return 404
    if code in (
        ErrorCodeV1.INVALID_REQUEST,
        ErrorCodeV1.INVALID_CONFIG,
        ErrorCodeV1.INVALID_VERSION,
        ErrorCodeV1.INVALID_ARTIFACT_REF,
        ErrorCodeV1.INVALID_INTENT,
    ):
        return 400
    if code == ErrorCodeV1.INTERNAL_ERROR:
        return 500
    # Future-proof default:
    return 500


def create_app() -> FastAPI:
    # REA-1: deterministic DEBUG logging for runtime/adapter/pipeline/api (no prints)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s:%(message)s",
        force=True,  # override uvicorn's default logging config
    )

    # Make sure our namespaces emit DEBUG
    for ns in ("api", "runtime", "pipeline", "adapters"):
        logging.getLogger(ns).setLevel(logging.DEBUG)
        logging.getLogger(ns).propagate = True

    app = FastAPI(
        title="Orchestrator O6 DEV Transport",
        version="dev",
    )

    # DEV-only CORS enablement (O6-T1): GUI local integration on Vite default port 5173.
    # Boundary: transport-only; no DTO/service/runtime changes.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiErrorV1)
    async def _api_error_handler(_req: Request, exc: ApiErrorV1) -> JSONResponse:
        env = exc.envelope
        return JSONResponse(
            status_code=_http_status_for_envelope(env),
            content=env.to_dict(),
        )

    @app.exception_handler(Exception)
    async def _unknown_error_handler(_req: Request, exc: Exception) -> JSONResponse:
        # Keep consistent ErrorEnvelopeV1 shape, but don't leak internals by default.
        env = internal_error(
            "1.0",
            message="Internal error",
            details={"reason": type(exc).__name__},
        )
        return JSONResponse(status_code=500, content=env.to_dict())

    app.include_router(router)

    return app