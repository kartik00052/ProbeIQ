from fastapi import status


class ProbeIQError(Exception):
    """Base class for domain errors surfaced to API clients without stack traces."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class InvalidRequestError(ProbeIQError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_request"


class InvalidCandidateError(ProbeIQError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_candidate"


class CandidateNotFoundError(ProbeIQError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "candidate_not_found"


class CurriculumDayNotFoundError(ProbeIQError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "day_not_found"


class DataLoadError(ProbeIQError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "data_load_error"
