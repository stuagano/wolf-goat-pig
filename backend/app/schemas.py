from pydantic import BaseModel

class Rule(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        orm_mode = True 