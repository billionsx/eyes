### 2026-07-28 · ЛИШНИЙ СЛОЙ УБРАН (поправка по слову основателя)
- реестр обслуживания был вынесен страницей `/service/` на домене, и к ней
  начала придумываться политика Cloudflare Access — то есть защита для того,
  что не обязано существовать. Основатель это и назвал: необходимости в
  сторонней панели нет, и делать руками он ничего не должен
- страница удалена. Реестр обслуживания стал файлом
  `registry/state/SERVICE.md` среди прочих реестров и в каталог `dashboard/`
  (его отдаёт домен) не попадает вообще
- правила `X-Robots-Tag` и `Disallow` для `/service/` удалены — охранять нечего
- ст. 54.1 переписана: «страницы, которой не существует, не нужно защищать;
  лишний слой защиты — признак лишнего слоя публикации»
- раздел про Access из docs/CLOUDFLARE.md убран: кнопок ноль

### 2026-07-28 · РАЗДЕЛЕНИЕ СВОДОВ (слово основателя)
- законы клиента остаются в репозитории клиента, инструмент стоит на СВОИХ:
  конституция редакции 7 объявила базовые законы департамента —
  ЗКН-Э001 «ноль выдумки» · ЗКН-Э002 «число несёт адрес» ·
  ЗКН-Э003 «свой свод суб-приложения»
- из конституции, мандата, реестров и всех органов убраны номера чужого свода
  (БТ001 · Д028 · Д029 · Д030) и имя продукта клиента в нормативном тексте;
  родословная законов записана словами один раз, в статье 1
- ст. 51 переписана: «Связь со сводом клиента» — чужой свод не становится
  частью департамента, департамент не вносит статьи в чужой свод
- ст. 53 (реестр поручений): продуктовые очереди клиентов здесь не живут —
  группа iskcon_product возвращена клиенту (docs/TASKS_PRODUCT.md)
- инструмент читается и применяется любым клиентом без чужого свода

### 2026-07-27 · ПЕРВЫЙ ПРОГОН В СВОЁМ РЕПОЗИТОРИИ
- пуш в `billionsx/eyes` прошёл; прогон `eyes` #30262202521 упал на шаге суда
- причина установлена воспроизведением среды (логи блобов Actions из песочницы
  недоступны): суд импортирует `fontTools` безусловно, а воркфлоу ставил только
  `pillow numpy` — в монорепо зависимость приходила из образа раннера молча
- ЗКН-Э007 (ст. 44.1): суд объявляет инструменты первым чеком и падает
  названной строкой с командой установки; зависимости объявлены в воркфлоу.
  Доказано в обе стороны, суд вырос до 62 проверок

### 2026-07-27 · СУВЕРЕНИТЕТ ДЕПАРТАМЕНТА
- департамент вынесен из монорепо `billionsx/iskcon` (каталог `bxad/`) в свой
  репозиторий `billionsx/eyes`; переименован в Billions X Eyes (BXE),
  точка входа `bin/eyes.py`, восемь воркфлоу `eyes-*.yml`
- конституция: редакция 6 · ст. 46 «Суверенитет» (вместо «Переносимости») ·
  ст. 57 «Паспорт проекта» · ст. 45.1 «Пустой обход» (ЗКН-Э006);
  мандат — 46 доменов
- автономность от проекта: `bin/projects.py` (реестр паспортов),
  `bin/fetch.py` (забор кода проектов в `_projects/`), хардкод `iskcon`
  вычищен из `certify.py`, `review.py`, `liveview.py`, `dashboard.py`
- ЗКН-Э006 обнаружен живьём при переносе: линт брал project_root из
  ROOT.parent, обход дал 0 файлов, храповик молча ужал долг iskcon 327 → 0.
  Починено (PROJECT_ROOT насквозь), храповик краснеет на пустом обходе,
  база восстановлена (327), суд вырос до 61 проверки
- эфир переписан под домен vrajs.com (Cloudflare Pages, output `dashboard`)
- подключение любого проекта: `templates/eyes-client.yml` (ревью PR),
  `templates/ping-eyes.yml` (пинг монитора), `docs/CONNECT.md`,
  `docs/CLOUDFLARE.md`

# BXE · ХРОНИКА РАЗВЕДКИ

Каждая запись — зафиксированное изменение официального источника Apple:
дата · источник · домены мандата · дифф заголовков. Пишет дозор, не человек.
Файл только растёт; правка задним числом запрещена уставом §3.

### 2026-07-23 08:46 UTC · `hig-index` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/
- домены мандата: hig, целостность

### 2026-07-23 08:46 UTC · `hig-whats-new` · первый снимок
- https://developer.apple.com/design/whats-new/
- домены мандата: hig, ios27

### 2026-07-23 08:46 UTC · `hig-materials` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/materials
- домены мандата: liquid-glass, размытие, полупрозрачность, многослойность

### 2026-07-23 08:46 UTC · `liquid-glass-adoption` · первый снимок
- https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass
- домены мандата: liquid-glass, свечение, стекло-движение

### 2026-07-23 08:46 UTC · `hig-color` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/color
- домены мандата: цвет, градиенты

### 2026-07-23 08:46 UTC · `hig-dark-mode` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/dark-mode
- домены мандата: цвет, тени

### 2026-07-23 08:46 UTC · `hig-typography` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/typography
- домены мандата: кернинг, шрифты

### 2026-07-23 08:46 UTC · `hig-layout` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/layout
- домены мандата: расстояния, минимализм, кроссплатформенность

### 2026-07-23 08:46 UTC · `hig-icons` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/icons
- домены мандата: иконки

### 2026-07-23 08:46 UTC · `hig-app-icons` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/app-icons
- домены мандата: иконки, динамические-иконки

### 2026-07-23 08:46 UTC · `sf-symbols` · первый снимок
- https://developer.apple.com/sf-symbols/
- домены мандата: иконки

### 2026-07-23 08:46 UTC · `fonts` · первый снимок
- https://developer.apple.com/fonts/
- домены мандата: шрифты, кернинг

### 2026-07-23 08:46 UTC · `hig-motion` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/motion
- домены мандата: анимация, кинетика, эффекты

### 2026-07-23 08:46 UTC · `hig-gestures` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/gestures
- домены мандата: жесты, надавливание

### 2026-07-23 08:46 UTC · `hig-haptics` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/playing-haptics
- домены мандата: вибрации

### 2026-07-23 08:46 UTC · `hig-buttons` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/buttons
- домены мандата: плашки, капсулы

### 2026-07-23 08:46 UTC · `hig-menus` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/menus
- домены мандата: динамичные-меню

### 2026-07-23 08:46 UTC · `hig-sliders` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/sliders
- домены мандата: ползунки

### 2026-07-23 08:46 UTC · `hig-sheets` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/sheets
- домены мандата: многослойность, popup

### 2026-07-23 08:46 UTC · `hig-popovers` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/popovers
- домены мандата: popup

### 2026-07-23 08:46 UTC · `hig-alerts` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/alerts
- домены мандата: popup

### 2026-07-23 08:46 UTC · `hig-tab-bars` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/tab-bars
- домены мандата: динамичные-меню, архитектура-приложений

### 2026-07-23 08:46 UTC · `hig-navigation-bars` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/navigation-bars
- домены мандата: архитектура-приложений

### 2026-07-23 08:47 UTC · `hig-live-activities` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/live-activities
- домены мандата: динамические-острова

### 2026-07-23 08:47 UTC · `hig-widgets` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/widgets
- домены мандата: динамические-острова, кроссплатформенность

### 2026-07-23 08:47 UTC · `hig-ratings-reviews` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/ratings-and-reviews
- домены мандата: рейтинги, отзывы

### 2026-07-23 08:47 UTC · `hig-game-center` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/game-center
- домены мандата: геймификация

### 2026-07-23 08:47 UTC · `hig-wallet` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/wallet
- домены мандата: apple-wallet

### 2026-07-23 08:47 UTC · `hig-apple-pay` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/apple-pay
- домены мандата: apple-pay

### 2026-07-23 08:47 UTC · `hig-designing-watchos` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/designing-for-watchos
- домены мандата: apple-watch, кроссплатформенность

### 2026-07-23 08:47 UTC · `hig-designing-visionos` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/designing-for-visionos
- домены мандата: пространственность, стекло-движение

### 2026-07-23 08:47 UTC · `design-resources` · первый снимок
- https://developer.apple.com/design/resources/
- домены мандата: hig, иконки, шрифты

### 2026-07-23 08:47 UTC · `ios-landing` · первый снимок
- https://developer.apple.com/ios/
- домены мандата: ios27

### 2026-07-23 08:47 UTC · `ipados-landing` · первый снимок
- https://developer.apple.com/ipados/
- домены мандата: ios27

### 2026-07-23 08:47 UTC · `ios-release-notes` · первый снимок
- https://developer.apple.com/documentation/ios-ipados-release-notes
- домены мандата: ios27

### 2026-07-23 08:47 UTC · `dev-news` · первый снимок
- https://developer.apple.com/news/
- домены мандата: ios27, hig

### 2026-07-23 08:47 UTC · `apple-newsroom-rss` · первый снимок
- https://www.apple.com/newsroom/rss-feed.rss
- домены мандата: ios27, маркетинг

### 2026-07-23 08:47 UTC · `doc-updates` · первый снимок
- https://developer.apple.com/documentation/updates/
- домены мандата: ios27, hig

### 2026-07-23 17:35 UTC · `hig-index` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/
- домены мандата: hig, целостность
- появились: Design fundamentals · Foundations of design · New and updated
- объём текста: 58 → 405 зн.

### 2026-07-23 17:35 UTC · `hig-materials` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/materials
- домены мандата: liquid-glass, размытие, полупрозрачность, многослойность
- появились: Liquid Glass · Standard materials · Platform considerations · iOS, iPadOS · macOS · tvOS · visionOS · watchOS · Resources · Related · Developer documentation · Videos
- объём текста: 41 → 9883 зн.

### 2026-07-23 17:35 UTC · `hig-color` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/color
- домены мандата: цвет, градиенты
- появились: Best practices · Inclusive color · System colors · Liquid Glass color · Color management · Platform considerations · iOS, iPadOS · macOS · App accent colors · tvOS · visionOS · watchOS
- объём текста: 37 → 14363 зн.

### 2026-07-23 17:36 UTC · `hig-dark-mode` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/dark-mode
- домены мандата: цвет, тени
- появились: Best practices · Dark Mode colors · Icons and images · Text · Platform considerations · iOS, iPadOS · macOS · Resources · Related · Videos · Change log
- объём текста: 41 → 6998 зн.

### 2026-07-23 17:36 UTC · `hig-typography` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/typography
- домены мандата: кернинг, шрифты
- появились: Ensuring legibility · Conveying hierarchy · Using system fonts · Using custom fonts · Supporting Dynamic Type · Platform considerations · iOS, iPadOS · macOS · tvOS · visionOS · watchOS · Specifications
- объём текста: 42 → 14572 зн.

### 2026-07-23 17:36 UTC · `hig-layout` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/layout
- домены мандата: расстояния, минимализм, кроссплатформенность
- появились: Best practices · Visual hierarchy · Adaptability · Guides and safe areas · Platform considerations · iOS · iPadOS · macOS · tvOS · Grids · visionOS · watchOS
- объём текста: 38 → 16757 зн.

### 2026-07-23 17:36 UTC · `hig-icons` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/icons
- домены мандата: иконки
- появились: Best practices · Standard icons · Editing · Selection · Text formatting · Search · Sharing and exporting · Users and accounts · Ratings · Layer ordering · Other · Platform considerations
- объём текста: 37 → 9329 зн.

### 2026-07-23 17:36 UTC · `hig-app-icons` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/app-icons
- домены мандата: иконки, динамические-иконки
- появились: Layer design · Icon shape · Design · Visual effects · Appearances · Platform considerations · tvOS · visionOS · watchOS · Specifications · Resources · Related
- объём текста: 41 → 12231 зн.

### 2026-07-23 17:36 UTC · `hig-motion` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/motion
- домены мандата: анимация, кинетика, эффекты
- появились: Best practices · Providing feedback · Leveraging platform capabilities · Platform considerations · visionOS · watchOS · Resources · Related · Developer documentation · Videos · Change log
- объём текста: 38 → 7038 зн.

### 2026-07-23 17:36 UTC · `hig-gestures` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/gestures
- домены мандата: жесты, надавливание
- появились: Best practices · Custom gestures · Platform considerations · iOS, iPadOS · macOS · tvOS · visionOS · Designing custom gestures in visionOS · Working with system overlays in visionOS · watchOS · Double tap · Specifications
- объём текста: 40 → 12141 зн.

### 2026-07-23 17:36 UTC · `hig-haptics` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/playing-haptics
- домены мандата: вибрации
- появились: Best practices · Custom haptics · Platform considerations · iOS · Notification · Impact · Selection · macOS · watchOS · Resources · Related · Developer documentation
- объём текста: 47 → 7039 зн.

### 2026-07-23 17:36 UTC · `hig-buttons` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/buttons
- домены мандата: плашки, капсулы
- появились: Best practices · Style · Content · Role · Platform considerations · iOS, iPadOS · macOS · Push buttons · Square buttons · Help buttons · Image buttons · visionOS
- объём текста: 39 → 14648 зн.

### 2026-07-23 17:36 UTC · `hig-menus` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/menus
- домены мандата: динамичные-меню
- появились: Labels · Icons · Organization · Submenus · Toggled items · In-game menus · Platform considerations · iOS, iPadOS · visionOS · Resources · Related · Developer documentation
- объём текста: 37 → 12762 зн.

### 2026-07-23 17:36 UTC · `hig-sliders` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/sliders
- домены мандата: ползунки
- появились: Best practices · Platform considerations · iOS, iPadOS · macOS · visionOS · watchOS · Resources · Related · Developer documentation · Change log
- объём текста: 39 → 4676 зн.

### 2026-07-23 17:36 UTC · `hig-sheets` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/sheets
- домены мандата: многослойность, popup
- появились: Anatomy · Best practices · Platform considerations · iOS, iPadOS · macOS · visionOS · watchOS · Resources · Related · Developer documentation · Change log
- объём текста: 38 → 8950 зн.

### 2026-07-23 17:36 UTC · `hig-popovers` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/popovers
- домены мандата: popup
- появились: Best practices · Platform considerations · iOS, iPadOS · macOS · Resources · Related · Developer documentation
- объём текста: 40 → 4172 зн.

### 2026-07-23 17:36 UTC · `hig-alerts` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/alerts
- домены мандата: popup
- появились: Best practices · Anatomy · Content · Buttons · Platform considerations · iOS, iPadOS · macOS · visionOS · Resources · Related · Developer documentation · Change log
- объём текста: 38 → 8617 зн.

### 2026-07-23 17:36 UTC · `hig-tab-bars` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/tab-bars
- домены мандата: динамичные-меню, архитектура-приложений
- появились: Best practices · Platform considerations · iOS · iPadOS · tvOS · visionOS · Resources · Related · Developer documentation · Videos · Change log
- объём текста: 40 → 7993 зн.

### 2026-07-23 17:36 UTC · `hig-navigation-bars` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/navigation-bars
- домены мандата: архитектура-приложений
- появились: Best practices · Titles · Navigation · Actions · Item groupings · Platform considerations · iOS · iPadOS · macOS · visionOS · watchOS · Resources
- объём текста: 40 → 13986 зн.

### 2026-07-23 17:36 UTC · `hig-live-activities` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/live-activities
- домены мандата: динамические-острова
- появились: Anatomy · Compact · Minimal · Expanded · Lock Screen · StandBy · Best practices · Creating Live Activity layouts · Choosing colors · Adding transitions and animating content updates · Offering interactivity · Starting, updating, and ending a Live Activity
- объём текста: 47 → 23698 зн.

### 2026-07-23 17:36 UTC · `hig-widgets` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/widgets
- домены мандата: динамические-острова, кроссплатформенность
- появились: Anatomy · System family widgets · Accessory widgets · Appearances · Best practices · Updating widget content · Adding interactivity · Choosing margins and padding · Displaying text in widgets · Using color · Rendering modes · Full-color
- объём текста: 39 → 30886 зн.

### 2026-07-23 17:36 UTC · `hig-ratings-reviews` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/ratings-and-reviews
- домены мандата: рейтинги, отзывы
- появились: Best practices · Platform considerations · Resources · Related · Developer documentation · Change log
- объём текста: 51 → 2918 зн.

### 2026-07-23 17:36 UTC · `hig-game-center` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/game-center
- домены мандата: геймификация
- появились: Accessing Game Center · Integrating the access point · Using custom UI · Achievements · Integrating achievements into your game · Creating achievement images · Leaderboards · Challenges · Multiplayer activities · Platform considerations · tvOS · watchOS
- объём текста: 43 → 13186 зн.

### 2026-07-23 17:36 UTC · `hig-wallet` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/wallet
- домены мандата: apple-wallet
- появились: Passes · Pass anatomy · Pass field types · Designing passes · Pass styles · Boarding passes · Coupons · Event tickets · Store cards · Poster generic passes · Generic passes · Pass images
- объём текста: 38 → 25768 зн.

### 2026-07-23 17:37 UTC · `hig-apple-pay` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/apple-pay
- домены мандата: apple-pay
- появились: Offering Apple Pay · Streamlining checkout · Customizing the payment sheet · Displaying a website icon · Handling problems · Data validation errors · Payment processing problems · Supporting subscriptions · Supporting donations · Using Apple Pay buttons · Button types · Apple Pay button
- объём текста: 41 → 22852 зн.

### 2026-07-23 17:37 UTC · `hig-designing-watchos` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/designing-for-watchos
- домены мандата: apple-watch, кроссплатформенность
- появились: Best practices · Resources · Related · Developer documentation · Videos · Change log
- объём текста: 53 → 3339 зн.

### 2026-07-23 17:37 UTC · `hig-designing-visionos` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/designing-for-visionos
- домены мандата: пространственность, стекло-движение
- появились: Best practices · Resources · Related · Developer documentation · Videos · Change log
- объём текста: 54 → 5724 зн.

### 2026-07-23 17:37 UTC · `apple-newsroom-rss` · ИЗМЕНЕНИЕ
- https://www.apple.com/newsroom/rss-feed.rss
- домены мандата: ios27, маркетинг
- объём текста: 1640 → 1631 зн.

### 2026-07-23 17:37 UTC · `app-store-marketing` · первый снимок
- https://developer.apple.com/app-store/marketing/guidelines/
- домены мандата: маркетинг, бейджи, реклама

### 2026-07-23 17:37 UTC · `hig-charting-data` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/charting-data
- домены мандата: графики, Fitness, геймификация

### 2026-07-23 17:37 UTC · `hig-toolbars` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/toolbars
- домены мандата: панели, меню

### 2026-07-23 17:37 UTC · `hig-toggles` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/toggles
- домены мандата: контролы, ползунки

### 2026-07-23 17:37 UTC · `hig-text-fields` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/text-fields
- домены мандата: контролы, формы

### 2026-07-23 17:37 UTC · `hig-pickers` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/pickers
- домены мандата: контролы, Calendar

### 2026-07-23 17:37 UTC · `hig-progress-indicators` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/progress-indicators
- домены мандата: контролы, анимация

### 2026-07-23 17:37 UTC · `hig-status-bars` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/status-bars
- домены мандата: хром, острова

### 2026-07-23 17:37 UTC · `hig-split-views` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/split-views
- домены мандата: архитектура, суб-приложения, кроссплатформенность

### 2026-07-23 17:37 UTC · `hig-designing-for-ipados` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/designing-for-ipados
- домены мандата: кроссплатформенность

### 2026-07-23 17:37 UTC · `hig-designing-for-macos` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/designing-for-macos
- домены мандата: кроссплатформенность

### 2026-07-23 17:38 UTC · `hig-designing-for-tvos` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/designing-for-tvos
- домены мандата: кроссплатформенность, TV

### 2026-07-23 17:38 UTC · пробы iOS 27
- ожили и завербованы в дозор: `ios27-landing` · `sf-symbols-8`

### 2026-07-23 18:00 UTC · храповик · осознанный подъём базы
- AE2 расширен на свечение (text-shadow / drop-shadow): вскрыто 1 скрытое нарушение в apps/web → база 54→55
- расширение зрения правила ≠ регресс кода; с этой точки AE2 снова только вниз

### 2026-07-23 18:08 UTC · `ios27-landing` · первый снимок
- https://developer.apple.com/ios/whats-new/
- домены мандата: ios27

### 2026-07-23 18:08 UTC · `sf-symbols-8` · первый снимок
- https://developer.apple.com/sf-symbols/
- домены мандата: ios27, иконки

### 2026-07-23 18:08 UTC · `app-review-guidelines` · первый снимок
- https://developer.apple.com/app-store/review/guidelines/
- домены мандата: маркетинг, рейтинги, отзывы, popup, геймификация

### 2026-07-23 18:09 UTC · `design-awards` · первый снимок
- https://developer.apple.com/design/awards/
- домены мандата: UI/UX, эталоны

### 2026-07-23 18:09 UTC · `wwdc-videos` · первый снимок
- https://developer.apple.com/videos/wwdc2026/
- домены мандата: ios27, анимация, Liquid Glass

### 2026-07-23 18:34 UTC · `liquid-glass-adoption` · ИЗМЕНЕНИЕ
- https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass
- домены мандата: liquid-glass, свечение, стекло-движение
- появились: Overview · See your app with Liquid Glass · Visual refresh · App icons · Controls · Navigation · Menus and toolbars · Windows and modals · Organization and layout · Search · Platform considerations
- объём текста: 53 → 17716 зн.

### 2026-07-23 18:36 UTC · `ios-release-notes` · ИЗМЕНЕНИЕ
- https://developer.apple.com/documentation/ios-ipados-release-notes
- домены мандата: ios27
- появились: Overview · Bug Reporting · iOS & iPadOS 27 · iOS & iPadOS 26 · iOS & iPadOS 18 · iOS & iPadOS 17 · iOS & iPadOS 16 · iOS & iPadOS 15 · iOS & iPadOS 14 · iOS & iPadOS 13 · iOS 12
- объём текста: 58 → 2588 зн.

### 2026-07-23 18:36 UTC · `doc-updates` · ИЗМЕНЕНИЕ
- https://developer.apple.com/documentation/updates/
- домены мандата: ios27, hig
- появились: The 27 platform releases – June 2026 · Xcode 27 · Performance and analysis · Apple Intelligence and Machine Learning · Siri, Intents, and Spotlight · Foundation Models · Core AI · Evaluations · SwiftUI · UIKit · AppKit · SwiftData
- объём текста: 39 → 13629 зн.

### 2026-07-23 18:47 UTC · `hig-accessibility` · первый снимок
- https://developer.apple.com/design/human-interface-guidelines/accessibility
- домены мандата: динамика, эффекты, анимация, доступность

### 2026-07-23 18:47 UTC · `swiftui-animation` · первый снимок
- https://developer.apple.com/documentation/swiftui/animation
- домены мандата: динамика, анимация, спринги

### 2026-07-24 16:51 UTC · `swiftui-spring` · первый снимок
- https://developer.apple.com/documentation/swiftui/spring
- домены мандата: динамика, спринги, анимация

### 2026-07-24 17:43 UTC · `asc-help` · первый снимок
- https://developer.apple.com/help/app-store-connect/
- домены мандата: App Store Connect, публикация, маркетинг

### 2026-07-24 17:43 UTC · `upcoming-requirements` · первый снимок
- https://developer.apple.com/news/upcoming-requirements/
- домены мандата: требования, релиз-ноты, маркетинг

### 2026-07-24 17:43 UTC · `icon-composer` · первый снимок
- https://developer.apple.com/icon-composer/
- домены мандата: иконки, инструменты

### 2026-07-24 17:43 UTC · `pass-designer` · первый снимок
- https://developer.apple.com/pass-designer/
- домены мандата: Wallet, инструменты

### 2026-07-24 17:43 UTC · `reality-composer-pro` · первый снимок
- https://developer.apple.com/reality-composer-pro/
- домены мандата: visionOS, инструменты, 3D

### 2026-07-24 17:43 UTC · `videos-design` · первый снимок
- https://developer.apple.com/videos/design/
- домены мандата: UI/UX, видео, Liquid Glass

### 2026-07-24 17:43 UTC · `dev-programs` · первый снимок
- https://developer.apple.com/programs/
- домены мандата: программа разработчика, правила

### 2026-07-24 17:43 UTC · `appstore-whats-new` · первый снимок
- https://developer.apple.com/app-store/whats-new/
- домены мандата: App Store, маркетинг

### 2026-07-24 17:43 UTC · `technologies` · первый снимок
- https://developer.apple.com/technologies/
- домены мандата: технологии, кроссплатформенность

### 2026-07-24 17:43 UTC · `dev-community` · первый снимок
- https://developer.apple.com/community/
- домены мандата: сообщество

### 2026-07-24 17:43 UTC · `dev-download` · первый снимок
- https://developer.apple.com/download/
- домены мандата: загрузки, инструменты, iOS 27

### 2026-07-24 17:43 UTC · `dev-help` · первый снимок
- https://developer.apple.com/help/
- домены мандата: справка, правила

### 2026-07-24 17:58 UTC · атлас · шаг дня
- пройдено 700 · в очередь 6900 · законов добыто 2460 · изменилось 0
- фронтир 6201 · всего пройдено 700 · библиотека 2460 законов / 123 фреймворков

### 2026-07-24 17:58 UTC · кит
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch

### 2026-07-25 03:51 UTC · macOS-плечо
- Xcode зафиксирован · SF Symbols установлен · символов выгружено: 9184

### 2026-07-25 04:24 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 2893 · законов добыто 322 · изменилось 1
- фронтир 7594 · всего пройдено 2200 · библиотека 5894 законов / 316 фреймворков
- закон изменился: /documentation/RealityComposerPro · «Reality Composer Pro»

### · веб-атлас лендингов
- страниц 85 · секций-видов 13 · модулей-видов 528 · новых типографических законов 145

### 2026-07-25 04:29 UTC · кит
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0

### 2026-07-25 18:35 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 16940 · законов добыто 3121 · изменилось 0
- фронтир 23034 · всего пройдено 3700 · библиотека 9160 законов / 323 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 13 · модулей-видов 528 · новых типографических законов 0

### 2026-07-25 18:40 UTC · кит
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0

### 2026-07-25 23:27 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 13470 · законов добыто 2901 · изменилось 0
- фронтир 35004 · всего пройдено 5200 · библиотека 12061 законов / 326 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 253 · модулей-видов 528 · новых типографических законов 12

### 2026-07-25 23:32 UTC · кит
- tvOS-18-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 4 · символов 7
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- шрифты: SF-Pro.dmg: лиц 0 · крышка None 
- шрифты: SF-Compact.dmg: лиц 0 · крышка None 
- шрифты: SF-Mono.dmg: лиц 0 · крышка None 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0
- https://brajs.com/katha: элементов 0 · находок 0
- https://brajs.com/library: элементов 0 · находок 0

### 2026-07-26 00:34 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 10842 · законов добыто 3209 · изменилось 0
- фронтир 44346 · всего пройдено 6700 · библиотека 15282 законов / 329 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 253 · модулей-видов 528 · новых типографических законов 0

### · большая семёрка
- страниц 50 · новых положений 63 · рамок в карте 6

### 2026-07-26 00:59 UTC · кит
- tvOS-18-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 4 · символов 7
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0
- https://brajs.com/katha: элементов 0 · находок 0
- https://brajs.com/library: элементов 0 · находок 0

### 2026-07-26 06:17 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 5882 · законов добыто 1639 · изменилось 0
- фронтир 48728 · всего пройдено 8200 · библиотека 16984 законов / 334 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 253 · модулей-видов 528 · новых типографических законов 0

### · большая семёрка
- страниц 50 · новых положений 89 · рамок в карте 7

### 2026-07-26 06:23 UTC · кит
- tvOS-18-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 4 · символов 7
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0
- https://brajs.com/katha: элементов 0 · находок 0
- https://brajs.com/library: элементов 0 · находок 0

### 2026-07-26 12:19 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 5028 · законов добыто 755 · изменилось 0
- фронтир 52256 · всего пройдено 9700 · библиотека 17828 законов / 335 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 253 · модулей-видов 528 · новых типографических законов 0

### · большая семёрка
- страниц 50 · новых положений 100 · рамок в карте 7

### 2026-07-26 12:26 UTC · кит
- tvOS-18-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 4 · символов 7
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0
- https://brajs.com/katha: элементов 0 · находок 0
- https://brajs.com/library: элементов 0 · находок 0

### 2026-07-26 18:39 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 4105 · законов добыто 1084 · изменилось 0
- фронтир 54861 · всего пройдено 11200 · библиотека 19012 законов / 335 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 253 · модулей-видов 528 · новых типографических законов 0

### 2026-07-26 18:56 UTC · кит
- tvOS-18-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 4 · символов 7
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 39 · находок 12
- https://brajs.com/katha: элементов 34 · находок 12
- https://brajs.com/library: элементов 39 · находок 12

### живой взгляд
- https://brajs.com/: элементов 37 · находок 3
- https://brajs.com/katha: элементов 32 · находок 3
- https://brajs.com/library: элементов 37 · находок 3

### 2026-07-26 20:12 UTC · монитор прода
- сейчас 9 · новых 9 · закрыто 0 · алерт: эфир

### 2026-07-26 20:52 UTC · сертификация
- iskcon: скор 0.0 · грейд D (strict 0 · report 327 · live 9 · сверка 0)

### 2026-07-26 20:53 UTC · сертификация
- iskcon: скор 81.5 · грейд C (strict 0 · report 327 · live 9 · сверка 0)

### 2026-07-26 20:55 UTC · сертификация
- iskcon: скор 81.5 · грейд C (strict 0 · report 327 · live 9 · сверка 0)

### 2026-07-27 06:37 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 240 · законов добыто 1067 · изменилось 0
- фронтир 53601 · всего пройдено 12700 · библиотека 20079 законов / 335 фреймворков

### · веб-атлас лендингов
- страниц 85 · секций-видов 253 · модулей-видов 528 · новых типографических законов 0

### 2026-07-27 06:55 UTC · кит
- tvOS-18-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 4 · символов 7
- ОШИБКА руки: iOS-27-Icon-Templates-Photoshop-Illustrator.dmg: RuntimeError: в контейнере нет .sketch
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 37 · находок 3
- https://brajs.com/katha: элементов 32 · находок 3
- https://brajs.com/library: элементов 37 · находок 3

### · big7-бриф 2026-W31
- положений в брифе 40 · рамок выросло 7

### · big7-бриф 2026-W31
- положений в брифе 40 · рамок выросло 0

### 2026-07-27 07:48 UTC · страж App Store
- пунктов 0 · privacy НЕТ · support ok

### 2026-07-27 07:53 UTC · страж App Store
- пунктов 55 · privacy НЕТ · support ok

### 2026-07-27 08:05 UTC · страж App Store
- пунктов 55 · privacy ok · support ok

### живой взгляд
- https://brajs.com/: элементов 37 · находок 3
- https://brajs.com/katha: элементов 32 · находок 3
- https://brajs.com/library: элементов 37 · находок 3

### 2026-07-27 08:21 UTC · монитор прода
- сейчас 9 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 37 · находок 3
- https://brajs.com/katha: элементов 32 · находок 3
- https://brajs.com/library: элементов 37 · находок 3

### 2026-07-27 08:32 UTC · монитор прода
- сейчас 9 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 37 · находок 0
- https://brajs.com/katha: элементов 32 · находок 0
- https://brajs.com/library: элементов 37 · находок 0

### 2026-07-27 08:38 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 9 · алерт: эфир

### 2026-07-27 08:44 UTC · сертификация
- iskcon: скор 95.0 · грейд A (strict 0 · report 327 · live 0 · сверка 0)

### живой взгляд
- https://brajs.com/: элементов 37 · находок 0
- https://brajs.com/katha: элементов 32 · находок 0
- https://brajs.com/library: элементов 37 · находок 0

### 2026-07-27 09:26 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-27 10:48 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-27 15:18 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-27 19:13 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 2914 · законов добыто 905 · изменилось 0
- фронтир 55015 · всего пройдено 14200 · библиотека 20829 законов / 336 фреймворков

### · веб-атлас лендингов
- страниц 87 · секций-видов 254 · модулей-видов 529 · новых типографических законов 107

### · большая семёрка
- страниц 58 · новых положений 31 · рамок в карте 7

### 2026-07-27 19:20 UTC · кит
- tvOS-18-Production-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 0 · символов 0
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-27 19:59 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-28 03:41 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-28 06:04 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1773 · законов добыто 1147 · изменилось 0
- фронтир 55288 · всего пройдено 15700 · библиотека 22114 законов / 336 фреймворков

### · веб-атлас лендингов
- страниц 87 · секций-видов 254 · модулей-видов 529 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 30 · рамок в карте 8

### 2026-07-28 06:12 UTC · кит
- visionOS-2-Design-Templates-Sketch.dmg: цветов 0 · текст-стилей 0 · радиусов 3 · символов 0
- шрифты: SF-Pro.dmg: лиц 47 · крышка 0.7046 
- шрифты: SF-Compact.dmg: лиц 38 · крышка 0.6665 
- шрифты: SF-Mono.dmg: лиц 12 · крышка 0.7046 
- все ссылки страницы: Bezel-Apple-TV.dmg · Bezel-Apple-Watch-Series-11-2025.dmg · Bezel-Apple-Watch-Ultra-2-2024.dmg · Bezel-Apple-Watch-Ultra-3-2025.dmg · Bezel-MacBook-Air-M5.dmg · Bezel-MacBook-Neo.dmg · Bezel-MacBook-Pro-M5.dmg · Bezel-Studio-Displays.dmg · Bezel-iMac-M4.dmg · Bezel-iPad-(A16).dmg · Bezel-iPad-Air-(M4).dmg · Bezel-iPad-Pro-(M5).dmg · Bezel-iPad-mini-(A17-Pro).dmg · Bezel-iPhone-16.dmg · Bezel-iPhone-17.dmg · Glyph-ARKit.dmg · Glyph-Add-Apple-Watch-Face.dmg · Glyph-AirPlay.dmg · Icon-Apple-Health.dmg · Icon-Game-Center.dmg · Icon-HomeKit.dmg · Icon-Siri.dmg · Keynote-Live-Video-Product-Bezel.dmg · Logo-Sign-in-with-Apple.dmg · NY.dmg · Parallax%20Previewer.dmg · Parallax%20Previewer_1_0.dmg · ParallaxExporter_Apps.zip · ParallaxExporter_Windows.zip · SF-Arabic.dmg · SF-Armenian.dmg · SF-Compact.dmg · SF-Georgian.dmg · SF-Hebrew.dmg · SF-Mono.dmg · SF-Pro.dmg · iOS-27-Icon-Templates-Photoshop-Illustrator.dmg · tvOS-18-Design-Templates-Sketch.dmg · tvOS-18-Production-Templates-Photoshop.dmg · tvOS-18-Production-Templates-Sketch.dmg · visionOS-2-Design-Templates-Sketch.dmg

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-28 06:32 UTC · `hig-index` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/
- домены мандата: hig, целостность
- объём текста: 405 → 479 зн.

### 2026-07-28 06:33 UTC · `hig-app-icons` · ИЗМЕНЕНИЕ
- https://developer.apple.com/design/human-interface-guidelines/app-icons
- домены мандата: иконки, динамические-иконки
- объём текста: 12231 → 12347 зн.

### 2026-07-28 08:20 UTC · сертификация
- iskcon: скор 95.0 · грейд A (strict 0 · report 327 · live 0 · сверка 0)

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-28 09:09 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-28 09:10 UTC · macOS-плечо
- Xcode зафиксирован · SF Symbols установлен · символов выгружено: 9184

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-28 14:43 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-28 19:10 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 4895 · законов добыто 1266 · изменилось 0
- фронтир 58683 · всего пройдено 17200 · библиотека 23410 законов / 336 фреймворков

### · веб-атлас лендингов
- страниц 87 · секций-видов 255 · модулей-видов 530 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 38 · рамок в карте 8

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-28 19:55 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 03:45 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-29 06:09 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 3474 · законов добыто 1234 · изменилось 0
- фронтир 60657 · всего пройдено 18700 · библиотека 24682 законов / 338 фреймворков

### · веб-атлас лендингов
- страниц 87 · секций-видов 255 · модулей-видов 530 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 32 · рамок в карте 8

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 06:18 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 0 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 06:46 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 06:54 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 35 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 07:39 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 07:51 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 08:05 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 08:57 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 09:13 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 11:24 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 11:46 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 12:05 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 14:34 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 14:36 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-29 18:44 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 2933 · законов добыто 872 · изменилось 0
- фронтир 62090 · всего пройдено 20200 · библиотека 25586 законов / 338 фреймворков
- копилка фреймворков собрана из пройденного: 404
- отбор: отсеяно не по предмету 3604 · в очереди изученных и пустых фреймворков 2505 из 62090 (было 2499)

### · веб-атлас лендингов
- страниц 87 · секций-видов 255 · модулей-видов 530 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 30 · рамок в карте 8

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-29 19:48 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-30 05:55 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1876 · законов добыто 388 · изменилось 0
- фронтир 62466 · всего пройдено 21700 · библиотека 26004 законов / 338 фреймворков
- отбор: отсеяно не по предмету 1107 · в очереди изученных и пустых фреймворков 2510 из 62466 (было 2505)

### · веб-атлас лендингов
- страниц 87 · секций-видов 255 · модулей-видов 530 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 34 · рамок в карте 8

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 09:07 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 09:38 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 14:36 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-30 15:54 UTC · `ios-release-notes` · ИЗМЕНЕНИЕ
- https://developer.apple.com/documentation/ios-ipados-release-notes
- домены мандата: ios27
- объём текста: 2588 → 2585 зн.

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 15:58 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-30 16:44 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 2642 · законов добыто 459 · изменилось 0
- фронтир 63610 · всего пройдено 23200 · библиотека 26497 законов / 338 фреймворков
- отбор: отсеяно не по предмету 1405 · в очереди изученных и пустых фреймворков 2510 из 63610 (было 2510)

### · веб-атлас лендингов
- страниц 87 · секций-видов 255 · модулей-видов 530 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 32 · рамок в карте 9

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 16:44 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 16:53 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 17:12 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 17:27 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-30 19:13 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1664 · законов добыто 480 · изменилось 0
- фронтир 63774 · всего пройдено 24700 · библиотека 27009 законов / 339 фреймворков
- отбор: отсеяно не по предмету 927 · в очереди изученных и пустых фреймворков 2510 из 63774 (было 2510)

### · веб-атлас лендингов
- страниц 87 · секций-видов 255 · модулей-видов 530 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 48 · рамок в карте 9

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-30 19:56 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-31 03:55 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-31 06:22 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1948 · законов добыто 1015 · изменилось 0
- фронтир 64222 · всего пройдено 26200 · библиотека 28072 законов / 339 фреймворков
- отбор: отсеяно не по предмету 2035 · в очереди изученных и пустых фреймворков 2510 из 64222 (было 2510)

### · веб-атлас лендингов
- страниц 87 · секций-видов 253 · модулей-видов 527 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 56 · рамок в карте 9

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-31 07:01 UTC · `apple-newsroom-rss` · ИЗМЕНЕНИЕ
- https://www.apple.com/newsroom/rss-feed.rss
- домены мандата: ios27, маркетинг
- объём текста: 1621 → 1585 зн.

### 2026-07-31 07:42 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1582 · законов добыто 542 · изменилось 0
- фронтир 64304 · всего пройдено 27700 · библиотека 28670 законов / 339 фреймворков
- отбор: отсеяно не по предмету 1268 · в очереди изученных и пустых фреймворков 2510 из 64304 (было 2510)

### · веб-атлас лендингов
- страниц 87 · секций-видов 253 · модулей-видов 527 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 37 · рамок в карте 9

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-31 09:20 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-31 14:40 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-07-31 19:11 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1709 · законов добыто 438 · изменилось 0
- фронтир 64513 · всего пройдено 29200 · библиотека 29145 законов / 339 фреймворков
- отбор: отсеяно не по предмету 1434 · в очереди изученных и пустых фреймворков 2510 из 64513 (было 2510)

### · веб-атлас лендингов
- страниц 87 · секций-видов 253 · модулей-видов 527 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 38 · рамок в карте 10

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-07-31 19:56 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-08-01 03:54 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-08-01 06:11 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 845 · законов добыто 214 · изменилось 0
- фронтир 63858 · всего пройдено 30700 · библиотека 29397 законов / 339 фреймворков
- отбор: отсеяно не по предмету 695 · в очереди изученных и пустых фреймворков 2512 из 63858 (было 2510)

### · веб-атлас лендингов
- страниц 87 · секций-видов 253 · модулей-видов 527 · новых типографических законов 39

### · большая семёрка
- страниц 58 · новых положений 38 · рамок в карте 10

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-08-01 08:36 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-08-01 09:28 UTC · сертификация
- iskcon: скор 89.6 · грейд B (strict 0 · report 208 · live 0 · сверка 0)

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-08-01 13:59 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

### 2026-08-01 18:39 UTC · атлас · шаг дня
- пройдено 1500 · в очередь 1021 · законов добыто 389 · изменилось 0
- фронтир 63379 · всего пройдено 32200 · библиотека 29863 законов / 339 фреймворков
- отбор: отсеяно не по предмету 710 · в очереди изученных и пустых фреймворков 2512 из 63379 (было 2512)

### · веб-атлас лендингов
- страниц 87 · секций-видов 253 · модулей-видов 527 · новых типографических законов 0

### · большая семёрка
- страниц 58 · новых положений 20 · рамок в карте 10

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### живой взгляд
- https://brajs.com/: элементов 38 · находок 0
- https://brajs.com/katha: элементов 33 · находок 0
- https://brajs.com/library: элементов 38 · находок 0

### 2026-08-01 19:37 UTC · монитор прода
- сейчас 0 · новых 0 · закрыто 0 · алерт: эфир

