from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Stage = Literal['new', 'contacted', 'qualified', 'won', 'lost']


class LeadFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    @field_validator('email', mode='before', check_fields=False)
    @classmethod
    def normalise_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class LeadCreate(LeadFields):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=254)
    company: str = Field(min_length=1, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    stage: Stage = 'new'


class LeadUpdate(LeadFields):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = Field(default=None, max_length=254)
    company: str | None = Field(default=None, min_length=1, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    stage: Stage | None = None

    @model_validator(mode='after')
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError('Provide at least one field to update.')
        for field in self.model_fields_set - {'phone'}:
            if getattr(self, field) is None:
                raise ValueError(f'{field} cannot be null.')
        return self


class LeadRead(LeadCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class LeadPage(BaseModel):
    items: list[LeadRead]
    total: int
    offset: int
    limit: int


class ImportIssue(BaseModel):
    row: int
    reason: str


class ImportResult(BaseModel):
    imported: int
    duplicates: int
    rejected: int
    issues: list[ImportIssue]
