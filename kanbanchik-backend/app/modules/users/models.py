from uuid import UUID
from uuid_extension import uuid7
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import CITEXT

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Связи таблиц
    # Владеделец пространсва
    owned_workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace", back_populates = "owner", lazy = "raise", foreign_keys="Workspace.owner_id"
    )
    # Участник пространств (через промежуточную таблицу)
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="user", lazy="raise"
    )
    # # Карточки, назначенные пользователю
    # assigned_cards: Mapped[list["Card"]] = relationship(
    #     "Card", back_populates="assignee", lazy="raise", foreign_keys="Card.assignee_id"
    # )
    # # Карточки, где пользователь является участником (M2M)
    # card_memberships: Mapped[list["CardMember"]] = relationship(
    #     "CardMember", back_populates="user", lazy="raise"
    # )
    # # Комментарии, написанные пользователем
    # comments: Mapped[list["Comment"]] = relationship(
    #     "Comment", back_populates="author", lazy="raise"
    # )
    # # Активности, созданные пользователем
    # activities: Mapped[list["Activity"]] = relationship(
    #     "Activity", back_populates="user", lazy="raise"
    # )
    # # Уведомления, адресованные пользователю
    # notifications: Mapped[list["Notification"]] = relationship(
    #     "Notification", back_populates="user", lazy="raise"
    # )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
