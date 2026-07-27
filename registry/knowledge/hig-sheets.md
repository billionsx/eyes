# знание · `hig-sheets`
Источник: https://developer.apple.com/design/human-interface-guidelines/sheets
Домены мандата: многослойность, popup
Нормативных положений: 19 (детерминированная выжимка, не пересказ)


## без раздела
- In macOS, tvOS, visionOS, and watchOS, a sheet is always modal .
- When a nonmodal sheet is onscreen, people use its functionality to affect the parent view without dismissing the sheet.
- Use a nonmodal view when you want to present supplementary items that affect the main task in the parent view.
- To give people access to information and actions they need while continuing to interact with the main window, consider using a in visionOS or a in macOS; in iOS and iPadOS, you can use a nonmodal sheet for this workflow.
- If you provide a Done button, always pair it with a Cancel button to give people a clear way to dismiss the sheet without confirming or saving their changes, or a Back button to move to a previous step in the sheet.
- Avoid showing all three buttons — Cancel, Done, and Back — together.
- If people have unsaved changes in the sheet when they begin swiping to dismiss it, use an action sheet to let them confirm their action.
- Prefer using the page or form sheet presentation styles in an iPadOS app.
- People don’t generally expect to resize sheets, so it’s important to use a size that’s appropriate for the content you display.
- When people want to interact with other windows in your app, make sure they can bring those windows forward even if they haven’t dismissed the sheet yet.
- Use a panel instead of a sheet if people need to repeatedly provide input and observe results.
- Avoid displaying a sheet that emerges from the bottom edge of a window.
- To help people view the sheet, prefer centering it in their .
- Avoid displaying a sheet that covers most or all of its window, but consider letting people resize the sheet if they want.
- Use a sheet only when your modal task requires a custom title or custom content presentation.
- Use a sheet only as a temporary interruption to the current workflow, and only to facilitate an important task.
- Avoid using a sheet to help people navigate your app’s content.
- If you change the default label, prefer using SF Symbols to represent the action.
- Avoid using a label that might mislead people into thinking that the sheet is part of a hierarchical navigation interface.
