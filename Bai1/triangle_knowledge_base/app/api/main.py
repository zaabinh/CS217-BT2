"""FastAPI application factory, independent from the mathematical core."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..services.solver_service import SolverService
from .routes.solver import router


def create_app(service: SolverService | None = None) -> FastAPI:
    """Create an isolated application instance; clients share only the rule inventory."""
    application = FastAPI(title="Triangle Knowledge Base", version="1.0.0",
                          description="13 variables, 46 directed rules; angles in degrees.")
    application.state.solver = service if service is not None else SolverService()
    application.include_router(router, prefix="/api/v1")

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> JSONResponse:
        # Pydantic input/context may contain NaN, infinity or a ValueError object.
        # Return schema diagnostics without trying to JSON-encode those objects.
        return JSONResponse(status_code=422, content={"detail": [
            {key: item[key] for key in ("type", "loc", "msg") if key in item}
            for item in error.errors()
        ]})

    return application


app = create_app()
