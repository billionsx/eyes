# знание · `hig-typography`
Источник: https://developer.apple.com/design/human-interface-guidelines/typography
Домены мандата: кернинг, шрифты
Нормативных положений: 54 (детерминированная выжимка, не пересказ)


## без раздела
- Use font sizes that most people can read easily.
- Follow the recommended default and minimum text sizes for each platform — for both custom and system fonts — to ensure your text is legible on all devices.
- If you use a custom font with a thin weight, aim for larger than the recommended sizes to increase legibility.
- In general, avoid light font weights.
- For example, if you’re using system-provided fonts, prefer Regular, Medium, Semibold, or Bold font weights, and avoid Ultralight, Thin, and Light font weights, which can be difficult to see, especially when text is small.
- Be sure to maintain the relative hierarchy and visual distinction of text elements when people adjust text sizes.
- Minimize the number of typefaces you use, even in a highly customized interface.
- When someone chooses a larger text size, they typically want to make the content they care about easier to read; they don’t always want to increase the size of every word on the screen.
- For example, when people increase text size to read the content in a tabbed window, they don’t expect the tab titles to increase in size.
- The system also offers SF Pro, SF Compact, SF Arabic, SF Armenian, SF Georgian, and SF Hebrew in rounded variants you can use to coordinate text with the appearance of soft or rounded UI elements, or to provide an alternative typographic voice.
- With dynamic optical sizes, you don’t need to use discrete optical sizes unless you’re working with a design tool that doesn’t support all the features of the variable font format.
- Because SF Symbols use equivalent weights, you can achieve precise weight matching between symbols and adjacent text, regardless of the size or style you choose.
- Taken together, the text styles form a typographic hierarchy you can use to express the different levels of importance in your content.
- You can also use symbolic traits to adjust leading if you need to improve readability or conserve space.
- If you need to display three or more lines of text, avoid tight leading even in areas where height is limited.
- You can use the constants defined in to access all system fonts — don’t embed system fonts in your app or game.
- For example, use to get the system font on all platforms; use to get the New York font.
- To produce an accurate interface mockup of an interface that uses the variable system fonts, you don’t have to choose a discrete optical size at certain point sizes, but you might need to adjust the tracking.
- Make sure custom fonts are legible.
- While using a custom font, be guided by the recommended minimum font sizes for various styles and weights in .
- System fonts automatically support Dynamic Type (where available) and respond when people turn on accessibility features, such as Bold Text.
- If you use a custom font, make sure it implements the same behaviors.
- In a Unity-based game, you can use to support Dynamic Type.
- If the plug-in isn’t appropriate for your game, be sure to let players adjust text size in other ways.
- Dynamic Type is a system-level feature in iOS, iPadOS, tvOS, visionOS, and watchOS that lets people adjust the size of visible text on their device to ensure readability and comfort.
- To support Dynamic Type in Unity-based games, use .
- Make sure your app’s layout adapts to all font sizes.
- On iPhone or iPad, turn on Larger Accessibility Text Sizes in Settings > Accessibility > Display & Text Size > Larger Text, and confirm that your app remains comfortably readable.
- If you use interface icons to communicate important information, make sure they’re easy to view at larger font sizes too.
- When you use , you get icons that scale automatically with Dynamic Type size changes.
- Keep text truncation to a minimum as font size increases.
- Avoid truncating text in scrollable regions unless people can open a separate view to read the rest of the content.
- You can prevent text truncation in a label by configuring it to use as many lines as needed to display a useful amount of text.
- Reduce the number of columns when the font size increases to avoid truncation and enhance readability.
- For example, keep primary elements toward the top of a view even when the font size is very large, so that people don’t lose track of these elements.
- iOS and iPadOS apps can also use NY.
- When necessary, use dynamic system font variants to match the text in standard controls.
- Use the variants listed below to achieve a look that’s consistent with other apps on the platform.
- SF Pro is the system font in tvOS, and apps can also use NY.
- If you use NY, you need to specify the type styles you want.
- In general, prefer 2D text.
- Although a small amount of 3D text can provide a fun visual element that draws people’s attention, if you’re going to display content that people need to read and understand, prefer using text that has little or no visual depth.
- Make sure text looks good and remains legible when people scale it.
- Use a text style that makes the text look good at full scale, then test it for legibility at different scales.
- If you want to use a different text color, be sure to test it in a variety of contexts.
- In this situation, you generally want to avoid adding shadows to increase text contrast.
- If you display text that’s associated with a point in space, such as a label for a 3D object, you generally want to use billboarding — that is, you want the text to face the wearer regardless of how they or the object move.
- If you don’t rotate text to remain facing the wearer, the text can become impossible to read because people may view it from the side or a highly oblique angle.
- SF Compact is the system font in watchOS, and apps can also use NY.
- In SwiftUI, use the modifier; in UIKit, use in the API.
- Point size based on image resolution of 144 ppi for @2x designs.
- Point size based on image resolution of 72 ppi for @1x and 144 ppi for @2x designs.
- Point size based on image resolution of 144 ppi for @2x and 216 ppi for @3x designs.
- Point size based on image resolution of 144 ppi for @2x and 216 ppi for @3x designs.
