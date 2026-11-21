from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
Id = Annotated[str, StringConstraints(max_length=64)]


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class In(BaseModel):
    model_config = ConfigDict(extra="forbid")
