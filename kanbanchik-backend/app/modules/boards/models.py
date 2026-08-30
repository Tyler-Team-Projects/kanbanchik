from uuid import UUID
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uuid_extension import uuid7
from app.db.base import Base


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    background_color: Mapped[str | None] = mapped_column(String, nullable=True)
    background_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Связи таблиц

    # Рабочее пространство, которому принадлежит доска
    # workspace: Mapped["Workspace"] = relationship(
    #     "Workspace", back_populates="boards", lazy="raise"
    # )

    # Колонки, принадлежащие доске
    lists: Mapped[list["List"]] = relationship(
        "List", back_populates="board", lazy="raise", cascade="all, delete-orphan"
    )

    # labels, принадлежащие доске
    # labels: Mapped[List["Label"]] = relationship(
    #     "Label", back_populates="board", lazy="raise", cascade="all, delete-orphan"
    # )

    # activities, принадлежащий доске
    # activities: Mapped[List["Activity"]] = relationship(
    #     "Activity", back_populates="board", lazy="raise", cascade="all, delete-orphan"
    # )

    def __repr__(self) -> str:
        return f"<Board(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"