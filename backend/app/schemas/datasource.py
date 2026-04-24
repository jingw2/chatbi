from pydantic import BaseModel
from app.models.datasource import DBType


class DatasourceCreate(BaseModel):
    name: str
    db_type: DBType
    host: str
    port: int
    database: str
    username: str
    password: str
    readonly_user: str
    readonly_password: str


class DatasourceResponse(BaseModel):
    id: int
    name: str
    db_type: DBType
    host: str
    port: int
    database: str
    username: str
    created_by: int

    model_config = {"from_attributes": True}
