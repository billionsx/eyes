# ЭФИР НА ДОМЕНЕ vrajs.com · CLOUDFLARE, ПО ШАГАМ

Что получится: `https://vrajs.com` — живой эфир департамента, который сам
пересобирается каждым прогоном (каждая хроника в репозиторий → Cloudflare
Pages перевыкладывает страницу автоматически). Ни сервера, ни билда, ни
платы: страница уже лежит готовой в `dashboard/`.

ФАКТ 27.07.2026 (снимок панели основателя): зона `vrajs.com` уже в аккаунте
`d5cbe19470dc38599873eabfe148e6d1` (тот же аккаунт, где живёт D1 проекта
ISKCON), план **free**, DNS Setup **Full**, статус — «Your domain is now
protected by Cloudflare». Значит **шаг 1 закрыт**, начинать с шага 2.

---
## Шаг 1 · Зона домена в Cloudflare — ЗАКРЫТ 27.07.2026

Зона активна, ничего делать не нужно. Прямая ссылка на зону:
https://dash.cloudflare.com/d5cbe19470dc38599873eabfe148e6d1/vrajs.com

Если когда-нибудь понадобится повторить на другом домене: **Add a domain** →
имя → план **Free** → Cloudflare выдаёт два своих nameserver'а
(`…ns.cloudflare.com`) → вписать их у регистратора вместо текущих NS →
**Check nameservers now** → статус зоны **Active**.

---
## Шаг 2 · Проект Pages из репозитория

1. Открыть **Workers & Pages** этого аккаунта:
   https://dash.cloudflare.com/d5cbe19470dc38599873eabfe148e6d1/workers-and-pages
   → кнопка **Create application**.
2. Вкладка **Pages** → **Import an existing Git repository** → **Connect
   to Git** → **GitHub** → авторизовать Cloudflare.
3. В списке репозиториев выбрать **billionsx/eyes** → **Begin setup**.
   Если репозитория нет в списке — **Add account / Configure** и дать
   Cloudflare доступ к `billionsx/eyes`.
4. Раздел **Set up builds and deployments** — вписать ровно так:

| поле | значение |
|---|---|
| Project name | `eyes` |
| Production branch | `main` |
| Framework preset | **None** |
| Build command | **оставить пустым** |
| Build output directory | `dashboard` |

5. **Save and Deploy**. Через минуту эфир жив на `https://eyes.pages.dev`.

Пустой build command — намеренно: страница уже собрана департаментом,
Cloudflare её только раздаёт. Ни npm, ни node, ни минут сборки.

В `dashboard/` каждым прогоном пишутся также `_headers` (кэш 5 минут,
`nosniff`, CORS на `data.json`) и `robots.txt` — Pages подхватывает их сам.
Числа эфира доступны машинам как `https://vrajs.com/data.json`.

---
## Шаг 3 · Домен на проект

1. В проекте Pages `eyes` → вкладка **Custom domains** → **Set up a
   custom domain**.
2. Ввести `vrajs.com` → **Continue** → **Activate domain**. Cloudflare сам
   создаст нужную DNS-запись в зоне — руками ничего вписывать не надо.
3. Повторить для `www.vrajs.com` (второй Custom domain) — чтобы адрес
   работал с `www` и без.

Через 1–3 минуты `https://vrajs.com` отдаёт эфир по TLS-сертификату
Cloudflare (выдаётся автоматически).

---
## Шаг 4 · Секреты департамента

**https://github.com/billionsx/eyes/settings/secrets/actions** → **New
repository secret**. Всё необязательно — департамент работает и без них:

| имя секрета | зачем | где взять |
|---|---|---|
| `EYES_PROJECTS_TOKEN` | забирать код **приватных** проектов | GitHub → Settings → Developer settings → Fine-grained tokens → `Contents: Read` на нужные репозитории |
| `SLACK_WEBHOOK_URL` | алерты монитора прода в Slack | Slack → Incoming Webhooks |
| `FIGMA_TOKEN` + `FIGMA_KIT_KEY` | рука Figma в органе «кит» | см. `KIT-UNLOCK.md` |

`GITHUB_TOKEN` выдаётся Actions автоматически — вносить не нужно.

---
## Шаг 5 · Кадротека — ИСПОЛНЕНО МЕХАНИЗМОМ 28.07.2026

Руками ничего не нужно. Воркфлоу `eyes-screens-import` перенёс архив кадров
(195 кадров приложений Apple) из релиза первого клиента в релиз
`eyes-screens-v1` ЭТОГО репозитория и подтвердил тождество sha256, скачав файл
из своего релиза снаружи. Отпечаток — `registry/screens/SOURCE.md`.

---
## Шаг 6 · Проверка, что всё дышит

| что | где смотреть | что должно быть |
|---|---|---|
| суд и прогон | https://github.com/billionsx/eyes/actions | воркфлоу `eyes` — зелёный |
| эфир в Markdown | `dashboard/DASHBOARD.md` в репозитории | свежая дата в заголовке |
| эфир на домене | https://vrajs.com | те же числа, тёмная страница |
| реестр проектов | локально `python3 bin/eyes.py projects` | твои проекты с `repo` и `prod` |

Если Pages показывает старую страницу — деплой ещё идёт: проект Pages →
**Deployments**, там видно текущую выкладку.

---
## Что дальше само

- пн и чт 05:43 UTC — полный обход департамента;
- дважды в сутки — урожай атласа, кита, живого взгляда;
- 1-го числа — пиксель-сертификаты проектов, 15-го — страж App Store;
- по понедельникам — Big7-бриф;
- каждые 6 часов (или сразу после деплоя проекта) — монитор прода;
- каждая хроника → новая выкладка на `vrajs.com`.

---
## Реестр службы · закрыть адрес политикой Access (5 кликов, необязательно)

Страница `https://vrajs.com/service/` не индексируется (`X-Robots-Tag` +
`robots.txt`), но Pages отдаёт её любому, кто знает адрес. Чтобы пускать только
себя:

1. https://one.dash.cloudflare.com → выбрать аккаунт → **Access** → **Applications**
2. **Add an application** → **Self-hosted**
3. Application name: `eyes service`, Session duration: по вкусу
4. Public hostname: домен `vrajs.com`, path `service`
5. **Add policy**: Policy name `founder`, Action **Allow**, Include →
   **Emails** → свой адрес → **Save**

После сохранения Cloudflare будет спрашивать одноразовый код на почту, а
публичное лицо `vrajs.com` останется открытым. Бесплатный план Zero Trust
покрывает до 50 пользователей.
