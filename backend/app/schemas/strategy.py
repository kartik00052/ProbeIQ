from pydantic import BaseModel


class InterviewStrategy(BaseModel):
    """Internal, candidate-specific interview strategy.

    Never exposed to the frontend. Used only to steer question generation and
    evaluation later in the pipeline.
    """

    primary_areas: list[str]
    probe_areas: list[str]
    avoid_assuming: list[str]
