import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DBType(str, enum.Enum):
    postgres = "postgres"
    mysql = "mysql"
    clickhouse = "clickhouse"
    doris = "doris"
    sqlite = "sqlite"


class Datasource(Base):
    __tablename__ = "datasources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    db_type: Mapped[DBType] = mapped_column(Enum(DBType), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(String(500), nullable=False)
    readonly_user: Mapped[str] = mapped_column(String(255), nullable=False)
    readonly_encrypted_password: Mapped[str] = mapped_column(String(500), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    schema_tables: Mapped[list["SchemaTable"]] = relationship(back_populates="datasource")
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(back_populates="datasource")
    workflows: Mapped[list["Workflow"]] = relationship(back_populates="datasource")
