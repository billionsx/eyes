# знание · `hig-split-views`
Источник: https://developer.apple.com/design/human-interface-guidelines/split-views
Домены мандата: архитектура, суб-приложения, кроссплатформенность
Нормативных положений: 18 (детерминированная выжимка, не пересказ)


## без раздела
- Typically, you use a split view to show multiple levels of your app’s hierarchy at once and support navigation between them.
- It’s common to use a split view to display a for navigation, where the leading pane lists the top-level items or collections in an app, and the secondary and optional tertiary panes can present child collections and item details.
- Rarely, you might also use a split view to provide groups of functionality that supplement the primary view — for example, Keynote in macOS uses split view panes to present the slide navigator, the presenter notes, and the inspector pane in areas that surround the main slide canvas.
- Prefer using a split view in a regular — not a compact — environment.
- In particular, ensure that it’s possible to navigate between the various panes in a logical way.
- Set reasonable defaults for minimum and maximum pane sizes.
- If people can resize the panes in your app’s split view, make sure to use sizes that keep the divider visible.
- If a pane gets too small, the divider can seem to disappear, becoming difficult to use.
- For example, you might provide a toolbar button or a menu command — including a keyboard shortcut — that people can use to restore a hidden pane.
- Prefer the thin divider style.
- The thin divider measures one point in width, giving you maximum space for content while remaining easy for people to use.
- Avoid using thicker divider styles unless you have a specific need.
- For example, if both sides of a divider present table rows that use strong linear elements that might make a thin divider hard to distinguish, it might work to use a thicker divider.
- People already know how to use a split view to navigate and filter content; they don’t need titles that describe what each pane contains.
- To display supplementary information, prefer a split view instead of a new window.
- Opening more windows also requires you to carefully manage the relationship between views in your app or game.
- If you need to request a small amount of information or present a simple task that someone must complete before returning to their main task, use a .
- People can then use the Digital Crown to scroll between the detail view’s tabs.
