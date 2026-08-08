from pydantic import BaseModel, Field


class Module(BaseModel):
    n: int = Field(ge=1)
    title: str
    days: tuple[int, int]


class Day(BaseModel):
    day: int = Field(ge=1)
    title: str
    type: str
    tools: list[str]
    objectives: list[str]


class Curriculum(BaseModel):
    cohort: str
    modules: list[Module]
    days: list[Day]
