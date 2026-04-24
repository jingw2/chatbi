from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SchemaTable(Base):
    __tablename__ = "schema_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    datasource_id: Mapped[int] = mapped_column(ForeignKey("datasources.id"), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    datasource: Mapped["Datasource"] = relationship(back_populates="schema_tables")
    columns: Mapped[list["SchemaColumn"]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
