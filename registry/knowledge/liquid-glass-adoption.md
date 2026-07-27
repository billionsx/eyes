# знание · `liquid-glass-adoption`
Источник: https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass
Домены мандата: liquid-glass, свечение, стекло-движение
Нормативных положений: 41 (детерминированная выжимка, не пересказ)


## без раздела
- As you review your app, use the following sections to understand the scope of changes and learn how you can adopt these best practices in your interface.
- Reduce your use of custom backgrounds in controls and navigation elements.
- Any custom backgrounds and appearances you use in these elements might overlay or interfere with Liquid Glass or other effects that the system provides, such as the scroll edge effect.
- Make sure to check any custom backgrounds in elements like split views, tab bars, and toolbars.
- Prefer to remove custom effects and let the system determine the background appearance, especially for the following elements: Test your interface with a variety of display and accessibility settings.
- For example, people can choose a preferred look for Liquid Glass in their device’s settings, or turn on accessibility settings that reduce transparency or motion in the interface.
- If you use standard components from system frameworks, this experience adapts automatically.
- Ensure you test your app’s custom elements, colors, and animations with different configurations of these settings.
- Avoid overusing Liquid Glass effects.
- Keep elements centered to avoid clipping.
- If you use standard controls from system frameworks and don’t hard-code their layout metrics, your app adopts changes to shapes and sizes automatically when you rebuild your app with the latest version of Xcode.
- Review changes to the following controls and any others and make sure they continue to look at home with the rest of your interface: Review your use of color in controls.
- Be judicious with your use of in controls and navigation so they stay legible.
- Prefer to use standard spacing metrics instead of overriding them, and avoid overcrowding or layering Liquid Glass elements on top of each other.
- If you use a custom bar with elements like controls, text, or icons that have content scrolling beneath them, you can register those views to use a scroll edge effect with these APIs: Consider aligning the shape of controls with other rounded elements throughout the interface.
- Ensure that you clearly separate your content from navigation elements, like tab bars and sidebars, to establish a distinct functional layer above the content layer.
- You can use the following standard system APIs for split views to build these types of layouts with minimal code: Check content safe areas for sidebars and inspectors.
- If you have these types of components in your app’s navigation structure, audit the safe area compatibility of content next to the sidebar and inspector to help make sure underlying content is peeking through appropriately.
- This effect is perfect for creating a full, edge-to-edge content experience in apps that use split views, such as for hero images on product pages.
- They adopt Liquid Glass, and menu items for common actions use icons to help people quickly scan and identify those actions.
- To adopt icons in those menu items with minimal code, make sure to use standard selectors.
- For consistency and predictability, make sure the actions you surface at the top of your contextual menu match the swipe actions you provide for the same item.
- This approach helps declutter the interface and increase the ease of use for common actions.
- For consistency, don’t mix text and icons across items that share a background.
- Regardless of what you show in the interface, always specify an accessibility label for each icon.
- This way, people who prefer a text label can opt into this information by turning on accessibility features like VoiceOver or Voice Control.
- Review anything custom you do to display items in your toolbars, like your use of fixed spacers or custom items, as these can appear inconsistent with system behavior.
- Instead of transitioning between specific preset sizes, windows resize fluidly down to a minimum size.
- Use split views to allow fluid resizing of columns.
- Make sure to use standard system APIs for split views to get these animations with minimal code: Use layout guides and safe areas.
- Make sure you specify safe areas for your content so the system can automatically adjust the window controls and title bar in relation to your content.
- Make sure to set the source view or item to indicate where to originate the action sheet and create the inline appearance.
- Make sure to update your section headers to title-style capitalization to match your app’s text to this systemwide convention.
- Use SwiftUI forms with the to automatically update your form layouts.
- Platform conventions for location and behavior of search optimize the experience for each device and use case.
- Test this experience in your app to make sure the search field moves consistently with other apps and system experiences.
- Use semantic search tabs.
- If your app’s search appears as part of a tab bar, make sure to use the standard system APIs for indicating which tab is the search tab.
- Liquid Glass changes are minimal in watchOS, so they appear automatically when you open your app on the latest release even if you don’t build against the latest SDK.
- However, to make sure your app picks up this appearance, adopt standard toolbar APIs and button styles from watchOS 10.
- If you apply these effects to custom elements, make sure to combine them using a , which helps optimize performance while fluidly morphing Liquid Glass shapes into each other.
