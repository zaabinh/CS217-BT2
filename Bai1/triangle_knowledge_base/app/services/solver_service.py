"""Application entry point shared by every presentation adapter."""
from collections.abc import Mapping
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
        try:
            # Revalidate model instances too, since nested dictionaries are mutable.
            data = request.model_dump() if isinstance(request, SolveRequest) else request
            validated = SolveRequest.model_validate(data)
        except ValidationError as error:
            return SolveResponse(status=SolveStatus.INVALID, message=str(error))
        return self.engine.solve(validated)
