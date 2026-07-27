# КИТ iOS 27 · разблокировка Figma-руки (1 минута, любой бесплатный аккаунт)
Community-hub без сессии ключ не отдаёт; MCP требует edit-доступ. Путь:
1. Любой бесплатный аккаунт Figma → открыть
   https://www.figma.com/community/file/1651309003795292092 → «Open in Figma»
   (дубликат в drafts). Из URL дубликата взять KEY (…/design/<KEY>/…).
2. Figma → Settings → Personal access tokens → создать токен.
3. В репо: Settings → Secrets → Actions: FIGMA_TOKEN=<токен>,
   FIGMA_KIT_KEY=<KEY>. Следующий прогон: рука проснётся сама
   (`bin/figkit.py::run_figma_arm`) и снимет стили/компоненты кита.
Пока ключей нет — кит идёт кадротекой (ст. 36.2) и macOS-символами (ст. 49.1).
