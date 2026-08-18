CREATE EXTENSION IF NOT EXISTS citext;


-- 1. USERS
CREATE TABLE "users" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "email" citext UNIQUE NOT NULL,
  "username" citext UNIQUE NOT NULL,
  "password_hash" text NOT NULL,
  "name" text,
  "bio" text,
  "avatar_url" text,
  "is_active" boolean DEFAULT true,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);


-- 2. WORKSPACES
CREATE TABLE "workspaces" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "owner_id" uuid NOT NULL,
  "name" text NOT NULL,
  "description" text,
  "color" text DEFAULT '#3b82f6',
  "is_archived" boolean DEFAULT false,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);


-- 3. WORKSPACE MEMBERS
CREATE TABLE "workspace_members" (
  "workspace_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  "role" varchar(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
  "joined_at" timestamptz DEFAULT now(),
  PRIMARY KEY ("workspace_id", "user_id")
);


-- 4. BOARDS
CREATE TABLE "boards" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "workspace_id" uuid NOT NULL,
  "name" text NOT NULL,
  "description" text,
  "background_color" text,
  "background_image_url" text,
  "is_archived" boolean DEFAULT false,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);


-- 5. LISTS (колонки)
CREATE TABLE "lists" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "board_id" uuid NOT NULL,
  "name" text NOT NULL,
  "position" numeric(30,15) NOT NULL,
  "wip_limit" integer CHECK (wip_limit > 0),
  "is_archived" boolean DEFAULT false,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);


-- 6. CARDS
CREATE TABLE "cards" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "list_id" uuid NOT NULL,
  "board_id" uuid NOT NULL,
  "title" text NOT NULL,
  "description" text,
  "position" numeric(30,15) NOT NULL,
  "assignee_id" uuid,
  "due_date" timestamptz,
  "is_archived" boolean DEFAULT false,
  "archived_at" timestamptz,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);


-- 7. LABELS
CREATE TABLE "labels" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "board_id" uuid NOT NULL,
  "name" text NOT NULL,
  "color" text NOT NULL,
  "created_at" timestamptz DEFAULT now()
);


-- 8. CARD LABELS (M2M)
CREATE TABLE "card_labels" (
  "card_id" uuid NOT NULL,
  "label_id" uuid NOT NULL,
  PRIMARY KEY ("card_id", "label_id")
);


-- 9. CARD MEMBERS (M2M)
CREATE TABLE "card_members" (
  "card_id" uuid NOT NULL,
  "user_id" uuid NOT NULL,
  PRIMARY KEY ("card_id", "user_id")
);


-- 10. CHECKLISTS
CREATE TABLE "checklists" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "card_id" uuid NOT NULL,
  "title" text NOT NULL,
  "position" integer NOT NULL,
  "created_at" timestamptz DEFAULT now()
);


-- 11. CHECKLIST ITEMS
CREATE TABLE "checklist_items" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "checklist_id" uuid NOT NULL,
  "title" text NOT NULL,
  "is_completed" boolean DEFAULT false,
  "position" integer NOT NULL,
  "completed_at" timestamptz
);

-- 12. COMMENTS
CREATE TABLE "comments" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "card_id" uuid NOT NULL,
  "author_id" uuid NOT NULL,
  "content" text NOT NULL,
  "created_at" timestamptz DEFAULT now(),
  "updated_at" timestamptz DEFAULT now()
);

-- 13. ACTIVITIES (audit log)
CREATE TABLE "activities" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "board_id" uuid NOT NULL,
  "user_id" uuid,
  "action" varchar(50) NOT NULL,
  "entity_type" varchar(50),
  "entity_id" uuid,
  "metadata" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now()
);

-- 14. NOTIFICATIONS
CREATE TABLE "notifications" (
  "id" uuid PRIMARY KEY DEFAULT uuidv7(),
  "user_id" uuid NOT NULL,
  "type" varchar(50) NOT NULL,
  "title" text NOT NULL,
  "body" text,
  "entity_type" varchar(50),
  "entity_id" uuid,
  "is_read" boolean DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now()
);

-- FOREIGN KEYS

-- workspaces → users
ALTER TABLE "workspaces" ADD FOREIGN KEY ("owner_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- workspace_members → workspaces + users
ALTER TABLE "workspace_members" ADD FOREIGN KEY ("workspace_id") REFERENCES "workspaces" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "workspace_members" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- boards → workspaces
ALTER TABLE "boards" ADD FOREIGN KEY ("workspace_id") REFERENCES "workspaces" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- lists → boards
ALTER TABLE "lists" ADD FOREIGN KEY ("board_id") REFERENCES "boards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- cards → lists + boards + users(assignee)
ALTER TABLE "cards" ADD FOREIGN KEY ("list_id") REFERENCES "lists" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "cards" ADD FOREIGN KEY ("board_id") REFERENCES "boards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "cards" ADD FOREIGN KEY ("assignee_id") REFERENCES "users" ("id") ON DELETE SET NULL DEFERRABLE INITIALLY IMMEDIATE;

-- labels → boards
ALTER TABLE "labels" ADD FOREIGN KEY ("board_id") REFERENCES "boards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- card_labels → cards + labels
ALTER TABLE "card_labels" ADD FOREIGN KEY ("card_id") REFERENCES "cards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "card_labels" ADD FOREIGN KEY ("label_id") REFERENCES "labels" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- card_members → cards + users
ALTER TABLE "card_members" ADD FOREIGN KEY ("card_id") REFERENCES "cards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "card_members" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- checklists → cards
ALTER TABLE "checklists" ADD FOREIGN KEY ("card_id") REFERENCES "cards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- checklist_items → checklists
ALTER TABLE "checklist_items" ADD FOREIGN KEY ("checklist_id") REFERENCES "checklists" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- comments → cards + users
ALTER TABLE "comments" ADD FOREIGN KEY ("card_id") REFERENCES "cards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "comments" ADD FOREIGN KEY ("author_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;

-- activities → boards + users
ALTER TABLE "activities" ADD FOREIGN KEY ("board_id") REFERENCES "boards" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;
ALTER TABLE "activities" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE SET NULL DEFERRABLE INITIALLY IMMEDIATE;

-- notifications → users
ALTER TABLE "notifications" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE DEFERRABLE INITIALLY IMMEDIATE;


-- TRIGGERS: auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON "users"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_workspaces_updated_at BEFORE UPDATE ON "workspaces"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_boards_updated_at BEFORE UPDATE ON "boards"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_lists_updated_at BEFORE UPDATE ON "lists"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_cards_updated_at BEFORE UPDATE ON "cards"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_comments_updated_at BEFORE UPDATE ON "comments"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- INDEXES
-- workspace_members: поиск workspace'ов пользователя
CREATE INDEX idx_workspace_members_user ON "workspace_members"("user_id");

-- boards: активные доски в workspace (partial index)
CREATE INDEX idx_boards_workspace_active ON "boards"("workspace_id") WHERE "is_archived" = false;

-- lists: колонки на доске с сортировкой по position (partial)
CREATE INDEX idx_lists_board_position ON "lists"("board_id", "position") WHERE "is_archived" = false;

-- cards: основной запрос — карточки в колонке с сортировкой (partial)
CREATE INDEX idx_cards_list_position ON "cards"("list_id", "position") WHERE "is_archived" = false;

-- cards: фильтрация по доске (partial, денормализация)
CREATE INDEX idx_cards_board_active ON "cards"("board_id") WHERE "is_archived" = false;

-- cards: фильтрация по исполнителю (partial)
CREATE INDEX idx_cards_assignee ON "cards"("assignee_id") WHERE "is_archived" = false AND "assignee_id" IS NOT NULL;

-- cards: фильтрация по дедлайну (partial)
CREATE INDEX idx_cards_due_date ON "cards"("due_date") WHERE "is_archived" = false AND "due_date" IS NOT NULL;

-- labels: метки доски
CREATE INDEX idx_labels_board ON "labels"("board_id");

-- card_labels: поиск карточек по метке (PK = (card_id, label_id), но поиск по label_id требует отдельный индекс)
CREATE INDEX idx_card_labels_label ON "card_labels"("label_id");

-- card_members: поиск карточек пользователя (PK = (card_id, user_id), но поиск по user_id требует отдельный индекс)
CREATE INDEX idx_card_members_user ON "card_members"("user_id");

-- checklists: чек-листы карточки
CREATE INDEX idx_checklists_card ON "checklists"("card_id");

-- checklist_items: пункты чек-листа
CREATE INDEX idx_checklist_items_checklist ON "checklist_items"("checklist_id");

-- comments: комментарии карточки, новые сверху
CREATE INDEX idx_comments_card ON "comments"("card_id", "created_at" DESC);

-- activities: лог доски, новые сверху
CREATE INDEX idx_activities_board ON "activities"("board_id", "created_at" DESC);

-- activities: активность пользователя
CREATE INDEX idx_activities_user ON "activities"("user_id", "created_at" DESC);

-- notifications: непрочитанные уведомления пользователя
CREATE INDEX idx_notifications_user_unread ON "notifications"("user_id", "is_read", "created_at" DESC);