# знание · `hig-toggles`
Источник: https://developer.apple.com/design/human-interface-guidelines/toggles
Домены мандата: контролы, ползунки
Нормативных положений: 27 (детерминированная выжимка, не пересказ)


## без раздела
- A toggle can have various styles, such as switch and checkbox, and different platforms can use these styles in different ways.
- Use a toggle to help people choose between two opposing values that affect the state of content or a view.
- A toggle always lets people manage the state of something, so if you need to support other types of actions — such as choosing from a list of items — use a different component, like a .
- If you use a button that behaves like a toggle, you generally use an interface icon that communicates its purpose, and you update its appearance — typically by changing the background — based on the current state.
- Make sure the visual differences in a toggle’s state are obvious.
- Avoid relying solely on different colors to communicate state, because not everyone can perceive the differences.
- Use the switch toggle style only in a list row.
- You don’t need to supply a label in this situation because the content in the row provides the context for the state the switch controls.
- The default green color tends to work well in most cases, but you might want to use your app’s accent color instead.
- Be sure to use a color that provides enough contrast with the uncolored appearance to be perceptible.
- Outside of a list, use a button that behaves like a toggle, not a switch.
- Avoid supplying a label that explains the button’s purpose.
- Use switches, checkboxes, and radio buttons in the window body, not the window frame.
- In particular, avoid using these components in a toolbar or status bar.
- Prefer a switch for settings that you want to emphasize.
- For example, you might use a switch to let people turn on or off a group of settings, instead of just one setting.
- If you need to present a hierarchy of settings within a grouped form, you can use a regular switch for the primary setting and mini switches for the subordinate settings.
- In general, don’t replace a checkbox with a switch.
- Use a checkbox instead of a switch if you need to present a hierarchy of settings.
- If you use a checkbox to globally turn on and off multiple subordinate checkboxes, show a mixed state when the subordinate checkboxes have different states.
- Prefer a set of radio buttons to present mutually exclusive options.
- If you need to let people choose multiple options in a set, use checkboxes instead.
- Avoid listing too many radio buttons in a set.
- To present a single setting that can be on or off, prefer a checkbox.
- In rare cases where a single checkbox doesn’t clearly communicate the opposing states, you can use a pair of radio buttons, each with a label that specifies the state it controls.
- Use consistent spacing when you display radio buttons horizontally.
- Measure the space needed to accommodate the longest button label, and use that measurement consistently.
