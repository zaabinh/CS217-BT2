from enum import Enum
from pydantic import BaseModel, Field
from .triangle import Variable


class SolveStatus(str, Enum):
    SOLVED = "SOLVED"
    UNRESOLVED = "UNRESOLVED"
    INVALID = "INVALID"
    INCONSISTENT = "INCONSISTENT"

class InferenceStep(BaseModel):
    """One accepted derivation, with unrounded input and output values."""
    step: int = Field(ge=1)
    rule_id: str
    group: str
    inputs: dict[Variable, float]
    output: Variable
    value: float
    formula: str


class SolveResponse(BaseModel):
    """Shared result contract for CLI, services and HTTP clients."""
    status: SolveStatus
    facts: dict[Variable, float] = Field(default_factory=dict)
    missing: list[Variable] = Field(default_factory=list)
    trace: list[InferenceStep] = Field(default_factory=list)
    message: str
