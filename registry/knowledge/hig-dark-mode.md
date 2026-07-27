# знание · `hig-dark-mode`
Источник: https://developer.apple.com/design/human-interface-guidelines/dark-mode
Домены мандата: цвет, тени
Нормативных положений: 19 (детерминированная выжимка, не пересказ)


## без раздела
- In Dark Mode, the system uses a dark color palette for all screens, views, menus, and controls, and may also use greater perceptual contrast to make foreground content stand out against the darker backgrounds.
- Avoid offering an app-specific appearance setting.
- Ensure that your app looks good in both appearance modes.
- Test your content to make sure that it remains comfortably legible in both appearance modes.
- For example, it can make sense for an app that supports immersive media viewing to use a permanently dark appearance that lets the UI recede and helps people focus on the media.
- Avoid using hard-coded color values or colors that don’t adapt.
- At a minimum, make sure the contrast ratio between colors is no lower than 4.5:1.
- This ratio ensures that your foreground content stands out from the background, and helps your content meet recommended accessibility guidelines.
- Use SF Symbols wherever possible.
- Symbols work well in both appearance modes when you use dynamic colors to tint them or when you add vibrancy.
- Make sure full-color images and icons look good in both appearances.
- Use the same asset if it looks good in both the light and dark appearances.
- Use asset catalogs to combine your assets into a single named image.
- Use the system-provided label colors for labels.
- Use system views to draw text fields and text views.
- When possible, use a system-provided view to display text instead of drawing the text yourself.
- Prefer the system background colors.
- To help achieve this harmony, add transparency only to a custom component that has a visible background or bezel, and only when the component is in a neutral state, such as state that doesn’t use color.
- You don’t want to add transparency when the component is in a state that uses color, because doing so can cause the component’s color to fluctuate when the window background adjusts to a different location on the desktop or when the desktop picture changes.
