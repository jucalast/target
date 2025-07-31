from pydantic import BaseModel

class AnalysisRequestBase(BaseModel):
description: str
    status: str

class AnalysisRequestCreate(AnalysisRequestBase):
pass

class AnalysisRequestRead(AnalysisRequestBase):
id: int

    class Config:
    orm_mode = True
