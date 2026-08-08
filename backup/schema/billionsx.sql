-- ═══════════════════════════════════════════════════════════════════════════
-- Схема billionsx — витрина исполнителя. Снимок от 05.08.2026.
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ЗАЧЕМ ЭТОТ ЧЕРТЁЖ ПОЯВИЛСЯ
--
-- Ночная копия данных снимает все три схемы: public (продукт заказчика),
-- bx и billionsx (витрина исполнителя). Проверка восстановления в сборке
-- разворачивает копию в чистую базу, поднятую по чертежам из репозитория,
-- и сверяет число строк по каждой таблице.
--
-- Чертежей было два — public.sql и bx.sql, — а схем в копии три. Пятнадцать
-- таблиц billionsx разворачивать было некуда, и проверка сообщала: «в копии N,
-- восстановлено NaN». То есть копия снималась исправно, а развернуть её
-- полностью было нельзя, и узнали бы об этом в тот момент, когда разворачивать
-- понадобилось по-настоящему.
--
-- ЧТО ЗДЕСЬ ВИДНО НЕПРИЯТНОГО, И ЭТО НЕ ЧИНИТСЯ ЗДЕСЬ
--
-- 1. Перенос витрины сделан наполовину. Данные лежат в двух схемах сразу:
--    в bx пять таблиц (cases, products, settings, team, testimonials),
--    в billionsx пятнадцать. Какая из них источник для сайта — из схемы
--    не видно.
--
-- 2. Таблица с именем _bx_cases_old не мёртвая: на неё ссылается внешним
--    ключом живая billionsx.bx_case_metrics (44 строки), и на неё же —
--    _bx_testimonials_old. То есть «старая» таблица несущая, а суффикс _old
--    сообщает читающему обратное. Удаление такой таблицы по имени сломало бы
--    целостность — именно поэтому здесь ничего не удалено.
--
-- 3. Девять таблиц — остатки переноса и отладки: _bx_cases_old,
--    _bx_services_old, _bx_testimonials_old, _hero_anims, _hero_debug,
--    _hero_html, _moto_ctx, _tilda_anims, _tilda_images. Вместе это 535 строк,
--    которые каждую ночь попадают в копию заказчика. Разбор и снятие —
--    за полосой витрины, не за этой правкой.
--
-- Чертёж описывает то, что есть, а не то, как должно быть. Приведение схемы
-- в порядок — отдельная работа; пока она не сделана, копия обязана
-- разворачиваться.
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS billionsx;

-- ── ТАБЛИЦЫ ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS billionsx._bx_cases_old (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  slug text NOT NULL,
  client_name text NOT NULL,
  client_logo_url text,
  tagline_ru text,
  tagline_en text,
  location_city text,
  location_country text,
  tier integer DEFAULT 5 NOT NULL,
  tier_label_ru text,
  hero_image_url text,
  hero_video_url text,
  market_context_ru text,
  market_context_en text,
  company_context_ru text,
  company_context_en text,
  game_changer_ru text,
  game_changer_en text,
  result_headline_ru text,
  result_headline_en text,
  quote_text text,
  quote_source text,
  quote_source_logo_url text,
  services_provided text[],
  meta_title text,
  meta_description text,
  sort_order integer DEFAULT 0,
  is_featured boolean DEFAULT false,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx._bx_services_old (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  slug text NOT NULL,
  tier_id uuid,
  name_ru text NOT NULL,
  name_en text,
  subtitle_ru text,
  subtitle_en text,
  description_ru text NOT NULL,
  description_en text,
  price_amount integer,
  price_display text,
  price_old_amount integer,
  price_model text DEFAULT 'fixed'::text,
  price_note_ru text,
  icon_url text,
  cover_image_url text,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  is_featured boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx._bx_testimonials_old (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  person_name text NOT NULL,
  person_title_ru text,
  person_title_en text,
  person_photo_url text,
  quote_ru text NOT NULL,
  quote_en text,
  before_ru text,
  after_ru text,
  net_worth_display text,
  case_id uuid,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx._hero_anims (
  idx integer,
  context text
);

CREATE TABLE IF NOT EXISTS billionsx._hero_debug (
  part text,
  content text
);

CREATE TABLE IF NOT EXISTS billionsx._hero_html (
  html text
);

CREATE TABLE IF NOT EXISTS billionsx._moto_ctx (
  part text,
  val text
);

CREATE TABLE IF NOT EXISTS billionsx._tilda_anims (
  block_id text,
  anim_style text,
  anim_duration text,
  anim_delay text,
  anim_distance text,
  anim_scale text,
  elem_type text,
  context text
);

CREATE TABLE IF NOT EXISTS billionsx._tilda_images (
  url text,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx.bx_case_metrics (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  case_id uuid,
  icon text DEFAULT 'award'::text,
  value_ru text NOT NULL,
  value_en text,
  sort_order integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx.bx_client_logos (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  name text NOT NULL,
  logo_url text NOT NULL,
  industry text,
  is_fortune500 boolean DEFAULT false,
  website_url text,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx.bx_config (
  key text NOT NULL,
  value jsonb NOT NULL,
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx.bx_methodology (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  slug text NOT NULL,
  name text NOT NULL,
  label_ru text NOT NULL,
  label_en text,
  simple_ru text NOT NULL,
  simple_en text,
  detailed_ru text,
  detailed_en text,
  icon_url text,
  color_accent text,
  animation_type text,
  pipeline_position integer NOT NULL,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx.bx_pages (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  slug text NOT NULL,
  title_ru text NOT NULL,
  title_en text,
  subtitle_ru text,
  subtitle_en text,
  meta_description text,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  config jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS billionsx.bx_pricing_tiers (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  slug text NOT NULL,
  name text NOT NULL,
  subtitle_ru text,
  subtitle_en text,
  description_ru text,
  description_en text,
  price_range_display text,
  target_revenue_ru text,
  color_accent text,
  icon_name text,
  sort_order integer DEFAULT 0,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now()
);

-- ── ОГРАНИЧЕНИЯ ──────────────────────────────────────────────────────────────
-- Порядок важен: внешний ключ ставится после того, как есть таблица-родитель.

ALTER TABLE billionsx._bx_cases_old ADD CONSTRAINT bx_cases_pkey PRIMARY KEY (id);
ALTER TABLE billionsx._bx_cases_old ADD CONSTRAINT bx_cases_slug_key UNIQUE (slug);
ALTER TABLE billionsx._bx_services_old ADD CONSTRAINT bx_services_pkey PRIMARY KEY (id);
ALTER TABLE billionsx._bx_services_old ADD CONSTRAINT bx_services_slug_key UNIQUE (slug);
ALTER TABLE billionsx._bx_testimonials_old ADD CONSTRAINT bx_testimonials_pkey PRIMARY KEY (id);
ALTER TABLE billionsx.bx_case_metrics ADD CONSTRAINT bx_case_metrics_pkey PRIMARY KEY (id);
ALTER TABLE billionsx.bx_client_logos ADD CONSTRAINT bx_client_logos_pkey PRIMARY KEY (id);
ALTER TABLE billionsx.bx_config ADD CONSTRAINT bx_config_pkey PRIMARY KEY (key);
ALTER TABLE billionsx.bx_methodology ADD CONSTRAINT bx_methodology_pkey PRIMARY KEY (id);
ALTER TABLE billionsx.bx_methodology ADD CONSTRAINT bx_methodology_slug_key UNIQUE (slug);
ALTER TABLE billionsx.bx_pages ADD CONSTRAINT bx_pages_pkey PRIMARY KEY (id);
ALTER TABLE billionsx.bx_pages ADD CONSTRAINT bx_pages_slug_key UNIQUE (slug);
ALTER TABLE billionsx.bx_pricing_tiers ADD CONSTRAINT bx_pricing_tiers_pkey PRIMARY KEY (id);
ALTER TABLE billionsx.bx_pricing_tiers ADD CONSTRAINT bx_pricing_tiers_slug_key UNIQUE (slug);

ALTER TABLE billionsx._bx_services_old ADD CONSTRAINT bx_services_tier_id_fkey FOREIGN KEY (tier_id) REFERENCES billionsx.bx_pricing_tiers(id);
ALTER TABLE billionsx._bx_testimonials_old ADD CONSTRAINT bx_testimonials_case_id_fkey FOREIGN KEY (case_id) REFERENCES billionsx._bx_cases_old(id);
ALTER TABLE billionsx.bx_case_metrics ADD CONSTRAINT bx_case_metrics_case_id_fkey FOREIGN KEY (case_id) REFERENCES billionsx._bx_cases_old(id) ON DELETE CASCADE;

-- ── ИНДЕКСЫ ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_bx_case_metrics_case ON billionsx.bx_case_metrics USING btree (case_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_bx_cases_featured ON billionsx._bx_cases_old USING btree (is_featured) WHERE (is_featured = true);
CREATE INDEX IF NOT EXISTS idx_bx_cases_slug ON billionsx._bx_cases_old USING btree (slug);
CREATE INDEX IF NOT EXISTS idx_bx_cases_tier ON billionsx._bx_cases_old USING btree (tier, sort_order);
CREATE INDEX IF NOT EXISTS idx_bx_client_logos_industry ON billionsx.bx_client_logos USING btree (industry);
CREATE INDEX IF NOT EXISTS idx_bx_services_slug ON billionsx._bx_services_old USING btree (slug);
CREATE INDEX IF NOT EXISTS idx_bx_services_tier ON billionsx._bx_services_old USING btree (tier_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_bx_testimonials_case ON billionsx._bx_testimonials_old USING btree (case_id);

-- ── ЗАЩИТА НА УРОВНЕ СТРОК ───────────────────────────────────────────────────
-- Витрина читается снаружи без входа — это её назначение. Правила чтения
-- открывают только то, что помечено активным; таблицы остатков и отладки
-- правил не имеют вовсе, то есть закрыты.

ALTER TABLE billionsx._bx_cases_old ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._bx_services_old ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._bx_testimonials_old ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._hero_anims ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._hero_debug ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._hero_html ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._moto_ctx ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._tilda_anims ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx._tilda_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx.bx_case_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx.bx_client_logos ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx.bx_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx.bx_methodology ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx.bx_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE billionsx.bx_pricing_tiers ENABLE ROW LEVEL SECURITY;

CREATE POLICY bx_cases_public_read ON billionsx._bx_cases_old FOR SELECT TO PUBLIC USING ((is_active = true));
CREATE POLICY bx_services_public_read ON billionsx._bx_services_old FOR SELECT TO PUBLIC USING ((is_active = true));
CREATE POLICY bx_testimonials_public_read ON billionsx._bx_testimonials_old FOR SELECT TO PUBLIC USING ((is_active = true));
CREATE POLICY bx_case_metrics_public_read ON billionsx.bx_case_metrics FOR SELECT TO PUBLIC USING (true);
CREATE POLICY bx_client_logos_public_read ON billionsx.bx_client_logos FOR SELECT TO PUBLIC USING ((is_active = true));
CREATE POLICY bx_config_public_read ON billionsx.bx_config FOR SELECT TO PUBLIC USING (true);
CREATE POLICY bx_methodology_public_read ON billionsx.bx_methodology FOR SELECT TO PUBLIC USING ((is_active = true));
CREATE POLICY bx_pages_public_read ON billionsx.bx_pages FOR SELECT TO PUBLIC USING ((is_active = true));
CREATE POLICY bx_pricing_tiers_public_read ON billionsx.bx_pricing_tiers FOR SELECT TO PUBLIC USING ((is_active = true));
