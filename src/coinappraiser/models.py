from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NumistaGrade = Literal["G", "VG", "F", "VF", "XF", "AU", "UNC"]


class Identification(BaseModel):
    country: str | None
    denomination: str | None
    year: int | None
    mint: str | None
    metal: str | None
    description: str
    confidence: float = Field(ge=0, le=1)


class ConditionAssessment(BaseModel):
    grade: NumistaGrade | None
    observed_wear: str
    rationale: str
    confidence: float = Field(ge=0, le=1)


class CatalogRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    source: str
    url: str
    country: str | None = None
    denomination: str | None = None
    year: int | None = None
    mint: str | None = None
    metal: str | None = None
    grade: str | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = None
    catalog_reference: str | None = None
    mintage: int | None = Field(default=None, ge=0)
    price_date: int | None = Field(default=None, ge=1)


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[CatalogRecord]


class PriceReference(CatalogRecord):
    match_score: int


class NumistaValue(BaseModel):
    grade: NumistaGrade
    price: float
    currency: str
    source_url: str
    catalog_reference: str | None
    price_date: int | None


class AppraisalResult(BaseModel):
    numista_value: NumistaValue | None
    numista_value_note: str
    condition_assessment: ConditionAssessment
    identification: Identification
    price_references: list[PriceReference]
    valuation_note: str
