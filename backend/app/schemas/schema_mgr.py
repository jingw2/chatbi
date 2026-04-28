from pydantic import BaseModel


class TableResponse(BaseModel):
    id: int
    datasource_id: int
    table_name: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class TableUpdate(BaseModel):
    description: str | None = None
    is_active: bool | None = None


class ColumnResponse(BaseModel):
    id: int
    table_id: int
    column_name: str
    data_type: str
    description: str | None
    example_values: str | None
    notes: str | None
    embedding_id: str | None

    model_config = {"from_attributes": True}


class ColumnUpdate(BaseModel):
    description: str | None = None
    example_values: str | None = None
    notes: str | None = None


class SyncResponse(BaseModel):
    tables_synced: int
    columns_synced: int
    embeddings_queued: int
