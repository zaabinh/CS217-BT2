from pydantic import BaseModel, ConfigDict, Field, model_validator
from .triangle import Variable

class Rule(BaseModel):
    """Serializable rule metadata, deliberately independent of executors."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^R(0[1-9]|[1-3][0-9]|4[0-6])$")
    group: str = Field(pattern=r"^Q(0[1-9]|10)$")
    inputs: tuple[Variable, ...] = Field(min_length=1)
    output: Variable
    formula: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_direction(self) -> "Rule":
        if len(set(self.inputs)) != len(self.inputs) or self.output in self.inputs:
            raise ValueError("Rule inputs must be unique and exclude the output")
        return self
