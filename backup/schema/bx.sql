-- Схема bx проекта ethnomir.app (лендинг Billions X). Снято 2026-07-28.
-- Заливается после supabase/schema/public.sql: представления в public ссылаются на эти таблицы.

SET check_function_bodies = off;

CREATE SCHEMA IF NOT EXISTS bx;

-- ПОСЛЕДОВАТЕЛЬНОСТИ

CREATE SEQUENCE IF NOT EXISTS bx.cases_id_seq;
CREATE SEQUENCE IF NOT EXISTS bx.content_id_seq;
CREATE SEQUENCE IF NOT EXISTS bx.images_id_seq;
CREATE SEQUENCE IF NOT EXISTS bx.products_id_seq;
CREATE SEQUENCE IF NOT EXISTS bx.team_id_seq;
CREATE SEQUENCE IF NOT EXISTS bx.testimonials_id_seq;

-- ТАБЛИЦЫ

CREATE TABLE IF NOT EXISTS bx.cases (
  id integer NOT NULL DEFAULT nextval('bx.cases_id_seq'::regclass),
  slug text NOT NULL,
  name text NOT NULL,
  city text NOT NULL,
  headline text NOT NULL,
  context text,
  game_changer text,
  products text[] DEFAULT '{}'::text[],
  color text DEFAULT '#007AFF'::text,
  logo_url text,
  images text[] DEFAULT '{}'::text[],
  tilda_page_id text,
  tilda_alias text,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  kpis jsonb DEFAULT '[]'::jsonb,
  timeline text,
  challenge text,
  solution text,
  results text[]
);

CREATE TABLE IF NOT EXISTS bx.content (
  id integer NOT NULL DEFAULT nextval('bx.content_id_seq'::regclass),
  block_type text NOT NULL,
  slug text NOT NULL,
  title text,
  subtitle text,
  body text,
  metadata jsonb DEFAULT '{}'::jsonb,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS bx.images (
  id integer NOT NULL DEFAULT nextval('bx.images_id_seq'::regclass),
  case_id integer,
  url text NOT NULL,
  alt_text text,
  source text DEFAULT 'tilda'::text,
  width integer,
  height integer,
  sort_order integer DEFAULT 0
);

CREATE TABLE IF NOT EXISTS bx.products (
  id integer NOT NULL DEFAULT nextval('bx.products_id_seq'::regclass),
  slug text NOT NULL,
  name text NOT NULL,
  tagline text,
  description text,
  icon_url text,
  color text DEFAULT '#007AFF'::text,
  features text[] DEFAULT '{}'::text[],
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS bx.settings (
  key text NOT NULL,
  value jsonb NOT NULL,
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bx.team (
  id integer NOT NULL DEFAULT nextval('bx.team_id_seq'::regclass),
  name text NOT NULL,
  role text NOT NULL,
  bio text,
  photo_url text,
  links jsonb DEFAULT '{}'::jsonb,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS bx.testimonials (
  id integer NOT NULL DEFAULT nextval('bx.testimonials_id_seq'::regclass),
  case_id integer,
  author_name text NOT NULL,
  author_role text NOT NULL,
  author_company text NOT NULL,
  quote text NOT NULL,
  revenue_impact text,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true
);

-- ПРИВЯЗКА ПОСЛЕДОВАТЕЛЬНОСТЕЙ

ALTER SEQUENCE bx.cases_id_seq OWNED BY bx.cases.id;
ALTER SEQUENCE bx.content_id_seq OWNED BY bx.content.id;
ALTER SEQUENCE bx.images_id_seq OWNED BY bx.images.id;
ALTER SEQUENCE bx.products_id_seq OWNED BY bx.products.id;
ALTER SEQUENCE bx.team_id_seq OWNED BY bx.team.id;
ALTER SEQUENCE bx.testimonials_id_seq OWNED BY bx.testimonials.id;

-- ОГРАНИЧЕНИЯ

ALTER TABLE bx.cases ADD CONSTRAINT cases_pkey PRIMARY KEY (id);
ALTER TABLE bx.content ADD CONSTRAINT content_pkey PRIMARY KEY (id);
ALTER TABLE bx.images ADD CONSTRAINT images_pkey PRIMARY KEY (id);
ALTER TABLE bx.products ADD CONSTRAINT products_pkey PRIMARY KEY (id);
ALTER TABLE bx.settings ADD CONSTRAINT settings_pkey PRIMARY KEY (key);
ALTER TABLE bx.team ADD CONSTRAINT team_pkey PRIMARY KEY (id);
ALTER TABLE bx.testimonials ADD CONSTRAINT testimonials_pkey PRIMARY KEY (id);
ALTER TABLE bx.cases ADD CONSTRAINT cases_slug_key UNIQUE (slug);
ALTER TABLE bx.content ADD CONSTRAINT content_slug_key UNIQUE (slug);
ALTER TABLE bx.products ADD CONSTRAINT products_slug_key UNIQUE (slug);
ALTER TABLE bx.images ADD CONSTRAINT images_case_id_fkey FOREIGN KEY (case_id) REFERENCES bx.cases(id) ON DELETE SET NULL;
ALTER TABLE bx.testimonials ADD CONSTRAINT testimonials_case_id_fkey FOREIGN KEY (case_id) REFERENCES bx.cases(id) ON DELETE SET NULL;

-- ФУНКЦИИ

-- ИНДЕКСЫ

-- ТРИГГЕРЫ

-- ЗАЩИТА НА УРОВНЕ СТРОК

ALTER TABLE bx.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE bx.content ENABLE ROW LEVEL SECURITY;
ALTER TABLE bx.images ENABLE ROW LEVEL SECURITY;
ALTER TABLE bx.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE bx.settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE bx.team ENABLE ROW LEVEL SECURITY;
ALTER TABLE bx.testimonials ENABLE ROW LEVEL SECURITY;

-- ПОЛИТИКИ ДОСТУПА

CREATE POLICY bx_cases_read ON bx.cases AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY bx_content_read ON bx.content AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY bx_images_read ON bx.images AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY bx_products_read ON bx.products AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY bx_settings_read ON bx.settings AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY bx_team_read ON bx.team AS PERMISSIVE FOR SELECT TO public USING (true);
CREATE POLICY bx_testimonials_read ON bx.testimonials AS PERMISSIVE FOR SELECT TO public USING (true);