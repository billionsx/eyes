# знание · `hig-alerts`
Источник: https://developer.apple.com/design/human-interface-guidelines/alerts
Домены мандата: popup
Нормативных положений: 31 (детерминированная выжимка, не пересказ)


## без раздела
- Avoid using an alert merely to provide information.
- People don’t appreciate an interruption from an alert that’s informative, but not actionable.
- If you need to provide only information, prefer finding an alternative way to communicate it within the relevant context.
- Avoid displaying alerts for common, undoable actions, even when they’re destructive.
- For example, you don’t need to alert people about data loss every time they delete an email or file because they do so with the intention of discarding data, and they can undo the action.
- Avoid showing an alert when your app starts.
- In all alert copy, be direct, and use a neutral, approachable tone.
- Alerts often describe problems and serious situations, so avoid being oblique or accusatory, or masking the severity of the issue.
- Avoid writing a title that doesn’t convey useful information — like “Error” or “Error 329347 occurred” — but also avoid overly long titles that wrap to more than two lines.
- If the title is a complete sentence, use and appropriate ending punctuation.
- If the title is a sentence fragment, use title-style capitalization, and don’t add ending punctuation.
- Avoid explaining alert buttons.
- If your alert text and button titles are clear, you don’t need to explain what the buttons do.
- In rare cases where you need to provide guidance on choosing a button, use a term like choose to account for people’s current device and interaction method, and refer to a button using its exact title without quotes.
- Prefer verbs and verb phrases that relate directly to the alert text — for example, “View All,” “Reply,” or “Ignore.” In informational alerts only, you can use “OK” for acceptance, avoiding “Yes” and “No.” Always use “Cancel” to title a button that cancels the alert’s action.
- As with all button titles, use and no ending punctuation.
- Avoid using OK as the default button title unless the alert is purely informational.
- Always place the default button on the trailing side of a row or at the top of a stack.
- Use the destructive style to identify a button that performs a destructive action people didn’t deliberately choose.
- If there’s a destructive action, include a Cancel button to give people a clear, safe way to avoid the action.
- Always use the title “Cancel” for a button that cancels an alert’s action.
- Note that you don’t want to make a Cancel button the default button.
- If you want to encourage people to read an alert and not just automatically press Return to dismiss it, avoid making any button the default button.
- Similarly, if you must display an alert with a single button that’s also the default, use a Done button, not a Cancel button.
- Use an action sheet — not an alert — to offer choices related to an intentional action.
- When possible, avoid displaying an alert that scrolls.
- Although an alert might scroll if the text size is large enough, be sure to minimize the potential for scrolling by keeping alert titles short and including a brief message only when necessary.
- Use a caution symbol sparingly.
- Use the symbol only when extra attention is really needed, as when confirming an action that might result in unexpected loss of data.
- Don’t use the symbol for tasks whose only purpose is to overwrite or remove data, such as a save or empty trash.
- If you need to display an accessory view in a visionOS alert, create a view that has a maximum height of 154 pt and a 16-pt corner radius.
