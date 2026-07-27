# знание · `hig-toolbars`
Источник: https://developer.apple.com/design/human-interface-guidelines/toolbars
Домены мандата: панели, меню
Нормативных положений: 34 (детерминированная выжимка, не пересказ)


## без раздела
- Choose items deliberately to avoid overcrowding.
- People need to be able to distinguish and activate each item, so you don’t want to put too many items in the toolbar.
- Don’t add an overflow menu manually, and avoid layouts that cause toolbar items to overflow by default.
- Toolbar customization is especially useful in apps that provide a lot of items — or that include advanced functionality that not everyone needs — and in apps that people tend to use for long periods of time.
- For example, it works well to make a range of editing actions available for toolbar customization, because people often use different types of editing commands based on their work style and their current project.
- Reduce the use of toolbar backgrounds and tinted controls.
- Any custom backgrounds and appearances you use might overlay or interfere with background effects that the system provides.
- Instead, use the content layer to inform the color and appearance of the toolbar, and use a when necessary to distinguish the toolbar area from the content area.
- Avoid applying a similar color to toolbar item labels and content layer backgrounds.
- If your app already has bright, colorful content in the content layer, prefer using the default monochromatic appearance of toolbars.
- Prefer using standard components in a toolbar.
- If you need to create a custom component, ensure that its corner radius is also concentric with the bar’s corners.
- Don’t title windows with your app name.
- Use the standard Back and Close buttons.
- Prefer the standard symbols for each, and don’t use a text label that says Back or Close .
- If you create a custom version of either, make sure it still looks the same, behaves as people expect, and matches the rest of your interface, and ensure you consistently implement it throughout your app or game.
- These commands are often the ones people use most frequently, but in some apps it might make sense to prioritize commands that map to the highest level or most important objects people work with.
- Make sure the meaning of each control is clear.
- Don’t make people guess or experiment to figure out what a toolbar item does.
- Prefer simple, recognizable symbols for items instead of text, except for actions like edit that aren’t well-represented by symbols.
- Prefer system-provided symbols without borders.
- Use the style for key actions such as Done or Submit.
- To ensure that these items are always available, items on the toolbar’s leading edge aren’t customizable.
- Group toolbar items logically by function and frequency of use.
- This helps people develop familiarity with your app and trust that it behaves similarly regardless of where they use it.
- In general, aim for a maximum of three.
- Use a large title to help people stay oriented as they navigate and scroll.
- Note that window titles can display inline with controls, and toolbar items don’t include a bezel.
- Prefer using a system-provided toolbar.
- Avoid creating a vertical toolbar.
- Be sure to reinstate the window’s standard toolbar controls when the app exits the modal state.
- Avoid using a pull-down menu in a toolbar.
- If you place these buttons above scrolling content, the buttons always remain visible, as the content scrolls under them.
- Use a scrolling toolbar button for an important action that isn’t a primary app function.
