# знание · `hig-menus`
Источник: https://developer.apple.com/design/human-interface-guidelines/menus
Домены мандата: динамичные-меню
Нормативных положений: 32 (детерминированная выжимка, не пересказ)


## без раздела
- Menus are ubiquitous in apps and games, so most people already know how to use them.
- Whether you use system-provided components or custom ones, people expect menus to behave in familiar ways.
- Several system-provided components also include menus that support specific use cases.
- Depending on menu layout, an iOS, iPadOS, or visionOS app can display a few unlabeled menu items that use only symbols or icons to identify them.
- To be consistent with platform experiences, use title-style capitalization.
- Although a game might have a different writing style, generally prefer using title-style capitalization, which capitalizes every word except articles, coordinating conjunctions, and short prepositions, and capitalizes the last word in the label, regardless of the part of speech.
- In English, articles always lengthen labels, but rarely enhance understanding.
- Append an ellipsis to a menu item’s label when the action requires more information before it can complete.
- Using standard icons makes your app easier to use and more familiar.
- Use menu item icons sparingly and with purpose.
- Use an icon to highlight the most common actions and key features of your app, file system locations, connected devices, visual concepts like rotating or flipping an image, and user-generated content like folders and documents.
- Don’t display an icon if you can’t find one that clearly represents the menu item.
- Organizing menu items in ways that reflect how people use your app or game can make your experience feel straightforward and easy to use.
- Prefer listing important or frequently used menu items first.
- To help people visually distinguish such groups, use a separator.
- Prefer keeping all logically related commands in the same group, even if the commands don’t all have the same importance.
- For example, people generally use Paste and Match Style much less often than they use Paste, but they expect to find both commands in the same group that contains more frequently used editing commands like Copy and Cut.
- Alternatively, you might be able to use a submenu to shorten the list, such as listing difficulty levels in a submenu of a New Game menu item.
- It generally works well to use the repeated term — in this case, Sort by — in the menu item’s label to help people predict the contents of the submenu.
- Make sure a submenu remains available even when its nested menu items are unavailable.
- Prefer using a submenu to indenting menu items.
- Menu items often represent attributes or objects that people can turn on or off.
- If you want to avoid listing a separate menu item for each state, it can be efficient to create a single, toggled menu item that communicates the current state and lets people change it.
- People expect to use the same interactions to navigate your menus as they use for navigating other menus on the device.
- Make sure your menus remain easy to open and read on all platforms you support.
- Use the small layout only for closely related actions that typically appear as a group, such as Bold, Italic, Underline, and Strikethrough.
- For each action, use a recognizable symbol that helps people identify the action without a label.
- To ensure that your menu is always visible to people, even when other content occludes it, you can apply a .
- Prefer displaying a menu near the content it controls.
- Prefer the subtle breakthrough effect in most cases.
- You can use if it’s important to display a menu prominently over the entire scene in your app or game, but this can disrupt the experience for people and potentially cause discomfort.
- Alternatively, you can use to fully occlude your menu behind other 3D content — for example, in a puzzle game that requires people to navigate around barriers — but this may make it difficult for people to see and access the menu.
