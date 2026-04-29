from pydantic import BaseModel
from app.models.knowledge_item import KnowledgeType


class KnowledgeItemCreate(BaseModel):
    datasource_id: int
    type: KnowledgeType
    title: str
    content: str


class KnowledgeItemUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class KnowledgeItemResponse(BaseModel):
    id: int
    datasource_id: int
    type: KnowledgeType
    title: str
    content: str
    embedding_id: str | None
    created_by: int

    model_config = {"from_attributes": True}
