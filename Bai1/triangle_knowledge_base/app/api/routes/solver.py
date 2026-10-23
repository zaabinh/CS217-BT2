"""HTTP adapters: validation, service calls and serializable metadata only."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request

from ...models import Rule, SolveRequest, SolveResponse, VariableInfo
from ...models.triangle import variable_metadata
from ...services.solver_service import SolverService

router = APIRouter()


def get_service(request: Request) -> SolverService:
    return request.app.state.solver


Service = Annotated[SolverService, Depends(get_service)]


@router.post("/solve", response_model=SolveResponse, tags=["solver"])
def solve(payload: SolveRequest, service: Service) -> SolveResponse:
    """HTTP 200 carries all four business statuses; schema errors use HTTP 422."""
    return service.solve(payload)


@router.get("/variables", response_model=list[VariableInfo], tags=["knowledge"])
def variables() -> list[VariableInfo]:
    return variable_metadata()


@router.get("/rules", response_model=list[Rule], tags=["knowledge"])
def rules(service: Service) -> list[Rule]:
    return list(service.registry)


@router.get("/rules/{id}", response_model=Rule, tags=["knowledge"])
def rule(id: str, service: Service) -> Rule:
    try:
        return service.registry.get(id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown rule: {id}") from error
