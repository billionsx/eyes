# ЭФИР НА ДОМЕНЕ vrajs.com · CLOUDFLARE, ПО ШАГАМ

Что получится: `https://vrajs.com` — живой эфир департамента, который сам
пересобирается каждым прогоном (каждая хроника в репозиторий → Cloudflare
Pages перевыкладывает страницу автоматически). Ни сервера, ни билда, ни
платы: страница уже лежит готовой в `dashboard/`.

Проверено 27.07.2026: `vrajs.com` **занят** — то есть уже зарегистрирован
(домен не продаётся). Если регистратор твой — идёшь по шагам как есть.

---
## Шаг 1 · Зона домена в Cloudflare

Открыть **https://dash.cloudflare.com** → выбрать аккаунт.

**Если `vrajs.com` уже в списке сайтов** — пропустить шаг, идти на шаг 2.

Если нет:
1. **Add a domain** (кнопка справа сверху или на главной аккаунта).
2. Ввести `vrajs.com` → **Continue**.
3. План — **Free** → **Continue**.
4. Cloudflare покажет найденные DNS-записи → **Continue**.
5. Cloudflare выдаст **два своих nameserver'а** вида
   `xxx.ns.cloudflare.com` — их нужно вписать у регистратора домена
   (там, где домен куплен: раздел NS / DNS-серверы / «Управление
   DNS-серверами»), заменив текущие.
6. Вернуться в Cloudflare → **Check nameservers now**. Активация занимает
   от 5 минут до нескольких часов; статус зоны станет **Active**.

---
## Шаг 2 · Проект Pages из репозитория

1. В меню слева — **Workers & Pages** → кнопка **Create application**.
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
## Шаг 5 · Кадротека в релиз (1 минута, необязательно)

Архив кадров приложений Apple (195 кадров, 10 приложений) лежит в релизе
монорепо. Перенести:

1. Скачать `Apple_Apps_iOS27.zip` из
   https://github.com/billionsx/iskcon/releases/tag/bxad-screens-v1
2. **https://github.com/billionsx/eyes/releases** → **Draft a new release**
   → tag `eyes-screens-v1` → прикрепить файл → **Publish release**.

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
