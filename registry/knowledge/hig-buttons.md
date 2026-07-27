# знание · `hig-buttons`
Источник: https://developer.apple.com/design/human-interface-guidelines/buttons
Домены мандата: плашки, капсулы
Нормативных положений: 58 (детерминированная выжимка, не пересказ)


## без раздела
- There are also many button-like components that have distinct appearances and behaviors for specific use cases, like , , and .
- Make buttons easy for people to use.
- Giving a button enough space is also critical for helping people select or activate it, regardless of the method of input they use.
- As a general rule, a button needs a hit region of at least 44x44 pt — in visionOS, 60x60 pt — to ensure that people can select it easily, whether they use a fingertip, a pointer, their eyes, or a remote.
- Always include a press state for a custom button.
- In general, use a button that has a prominent visual style for the most likely action in a view.
- To draw people’s attention to a specific button, use a prominent button style so the system can apply an accent color to the button’s background.
- Buttons that use color tend to be the most visually distinctive, helping people quickly identify the actions they’re most likely to use.
- Use style — not size — to visually distinguish the preferred choice among multiple options.
- When you use buttons of the same size to offer two or more options, you signal that the options form a coherent set of choices.
- If you want to highlight the preferred or most likely option in a set, use a more prominent button style for that option and a less prominent style for the remaining ones.
- Avoid applying a similar color to button labels and content layer backgrounds.
- If your app already has bright, colorful content in the content layer, prefer using the default monochromatic appearance of button labels.
- Ensure that each button clearly communicates its purpose.
- If it makes sense to use an icon in your button, consider using an existing or customized .
- To use text, write a few words that succinctly describe what the button does.
- Using , consider starting the label with a verb to help convey the button’s action — for example, a button that lets people add items to their shopping cart might use the label “Add to Cart.”
- Don’t assign the primary role to a button that performs a destructive action, even if that action is the most likely choice.
- Help people avoid losing content by assigning the primary role to nondestructive buttons.
- Use a flexible-height push button only when you need to display tall or variable height content.
- Flexible-height buttons support the same configurations as regular push buttons — and they use the same corner radius and content padding — so they look consistent with other buttons in your interface.
- If you need to present a button that contains two lines of text or a tall icon, use a flexible-height button; otherwise, use a standard push button.
- Use square buttons in a view, not in the window frame.
- Square buttons aren’t intended for use in toolbars or status bars.
- If you need a button in a , use a toolbar item.
- Prefer using a symbol in a square button.
- Avoid using labels to introduce square buttons.
- Use the system-provided help button to display your help documentation.
- Use the following locations for guidance.
- Use a help button within a view, not in the window frame.
- For example, avoid placing a help button in a toolbar or status bar.
- Avoid displaying text that introduces a help button.
- People know what a help button does, so they don’t need additional descriptive text.
- Use an image button in a view, not in the window frame.
- For example, avoid placing an image button in a toolbar or status bar.
- If you need to use an image as a button in a toolbar, use a toolbar item.
- In general, avoid including a system-provided border in an image button; for developer guidance, see .
- visionOS buttons use different visual styles to communicate four different interaction states.
- In visionOS, buttons don’t support custom hover effects.
- In general, buttons that contain text don’t need to display a tooltip because the button’s descriptive label communicates what it does.
- Prefer buttons that have a discernible background shape and fill.
- The following guidelines can help you ensure that a button looks good in different contexts: When a button appears on top of a glass , use the material as the button’s background.
- When a button appears floating in space, use the for its background.
- Avoid creating a custom button that uses a white background fill and black text or icons.
- In general, prefer circular or capsule-shape buttons.
- When you need to display a button by itself, prefer a capsule-shape button.
- Aim to place buttons so their centers are always at least 60 pts apart.
- If your buttons measure 60 pts or larger, add 4 pts of padding around them to keep the hover effect from overlapping.
- Also, it’s usually best to avoid displaying small or mini buttons in a vertical stack or horizontal row.
- Specifically, prefer the rounded-rectangle shape in a vertical stack of buttons and prefer the capsule shape in a horizontal row of buttons.
- Use standard controls to take advantage of the audible feedback sounds people already know.
- When you place a button inline with content, it gains a material effect that contrasts with the background to ensure legibility.
- Use a toolbar to place buttons in the corners.
- Prefer buttons that span the width of the screen for primary actions in your app.
- If two buttons must share the same horizontal space, use the same height for both, and use images or short text titles for each button’s content.
- Use toolbar buttons to provide either navigation to related areas or contextual actions for the view’s content.
- Use the same height for vertical stacks of one- and two-line text buttons.
- As much as possible, use identical button heights for visual consistency.
