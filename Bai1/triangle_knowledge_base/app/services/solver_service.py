"""Application entry point shared by every presentation adapter."""
from collections.abc import Mapping
from time import perf_counter
from pydantic import ValidationError

from ..core.inference_engine import InferenceEngine
from ..core.validator import TriangleValidator
from ..knowledge.rules import RuleRegistry, build_registry
from ..models import SolveRequest, SolveResponse, SolveStatus


class SolverService:
    """Normalize requests and orchestrate the same stateless core for CLI/API."""

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self.registry = registry if registry is not None else build_registry()
        self.engine = InferenceEngine(self.registry, TriangleValidator(self.registry))

    def solve(self, request: SolveRequest | Mapping[str, object]) -> SolveResponse:
        """Return INVALID for malformed service inputs; HTTP schemas use 422."""
        started = perf_counter()
        try:
            # Revalidate model instances too, since nested dictionaries are mutable.
            data = request.model_dump() if isinstance(request, SolveRequest) else request
            validated = SolveRequest.model_validate(data)
        except ValidationError as error:
            return SolveResponse(status=SolveStatus.INVALID, message=str(error), reason_code="INVALID_INPUT",
                                 diagnostics=[{"code": "INVALID_INPUT", "message": str(error)}],
                                 stats={"steps": 0, "time_ms": round((perf_counter()-started)*1000, 3),
                                        "termination_reason": "INVALID_INPUT"})
        return self.engine.solve(validated)
