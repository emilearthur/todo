"""Model for evaluation endpoint."""

from typing import Optional, Union

from app.models.core import CoreModel, DateTimeModelMixin
from app.models.todo import TodoPublic
from app.models.user import UserPublic
from pydantic import confloat, conint


class EvaluationBase(CoreModel):
    """All common characteristics of evaluation."""

    no_show: bool = False
    headline: Optional[str]
    comment: Optional[str]
    professionalism: Optional[conint(ge=0, le=5)]
    completeness: Optional[conint(ge=0, le=5)]
    efficiency: Optional[conint(ge=0, le=5)]
    overall_rating: Optional[conint(ge=0, le=5)]


class EvaluationCreate(EvaluationBase):
    """Create evaluation model."""

    overall_rating: conint(ge=0, le=5)


class EvaluationUpdate(EvaluationBase):
    """Update evalution model."""

    pass


class EvaluationInDB(DateTimeModelMixin, EvaluationBase):
    """Model for data in DB."""

    tasktaker_id: int
    todo_id: int


class EvaluationPublic(EvaluationInDB):
    """Evaluation in Public."""

    owner: Optional[Union[int, UserPublic]]
    taker: Optional[UserPublic]
    todo: Optional[TodoPublic]


class EvaluationAggregate(CoreModel):
    """Evaluation Aggregate Model."""

    avg_professionalism: confloat(ge=0, le=5)
    avg_completeness: confloat(ge=0, le=5)
    avg_efficiency: confloat(ge=0, le=5)
    avg_overall_rating: confloat(ge=0, le=5)
    max_overall_rating: conint(ge=0, le=5)
    min_overall_rating: conint(ge=0, le=5)
    one_stars: conint(ge=0)
    two_stars: conint(ge=0)
    three_stars: conint(ge=0)
    four_stars: conint(ge=0)
    five_stars: conint(ge=0)
    total_evaluations: conint(ge=0)
    total_no_show: conint(ge=0)
