from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Integer, Numeric, Boolean, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uuid_extension import uuid7
from app.db.base import Base


class List(Base):
    __tablename__ = "lists"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    board_id: Mapped[UUID] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[Decimal] = mapped_column(
        Numeric(30, 15),
        nullable=False
    )
    wip_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Связи (закомментированы до создания соответствующих моделей)
    # board: Mapped["Board"] = relationship(
    #     "Board", back_populates="lists", lazy="raise"
    # )
    # cards: Mapped[list["Card"]] = relationship(
    #     "Card", back_populates="list", lazy="raise", cascade="all, delete-orphan"
    # )

    def __repr__(self) -> str:
        return f"<List(id={self.id}, name={self.name}, board_id={self.board_id}, position={self.position})>"