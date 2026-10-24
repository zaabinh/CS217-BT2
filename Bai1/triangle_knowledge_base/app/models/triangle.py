from enum import Enum
import math
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Variable(str, Enum):
    a = "a"
    b = "b"
    c = "c"
    A = "A"
    B = "B"
    C = "C"
    ha = "ha"
    hb = "hb"
    hc = "hc"
    S = "S"
    p = "p"
    r = "r"
    R = "R"


class SolveRequest(BaseModel):
    """Structural input validation; geometric validity belongs to the core."""

    model_config = ConfigDict(extra="forbid")

    facts: dict[Variable, float] = Field(default_factory=dict)
    goals: set[Variable] = Field(min_length=1)
    trace_targets: set[Variable] | None = Field(default=None, min_length=1)

    @field_validator("facts", mode="before")
    @classmethod
    def numeric_facts(cls, facts: object) -> object:
        if isinstance(facts, dict):
            for value in facts.values():
                if type(value) not in (int, float):
                    raise ValueError("Facts must be numbers, excluding booleans and strings")
                try:
                    finite = math.isfinite(value)
                except OverflowError:
                    finite = False
                if not finite:
                    raise ValueError("Facts must be finite representable numbers")
        return facts


class VariableInfo(BaseModel):
    """JSON metadata for presentation clients."""

    name: Variable
    description: str
    unit: str
    domain: str


def variable_metadata() -> list[VariableInfo]:
    """Describe the thirteen variables in their canonical order."""
    descriptions = (
        "Side opposite A", "Side opposite B", "Side opposite C",
        "Angle opposite a", "Angle opposite b", "Angle opposite c",
        "Altitude to a", "Altitude to b", "Altitude to c",
        "Area", "Semiperimeter", "Inradius", "Circumradius",
    )
    return [VariableInfo(
        name=v, description=description,
        unit="degrees" if v.value in ("A", "B", "C") else "length^2" if v == Variable.S else "length",
        domain="0 < value < 180" if v.value in ("A", "B", "C") else "value > 0",
    ) for v, description in zip(Variable, descriptions)]
