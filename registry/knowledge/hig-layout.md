# знание · `hig-layout`
Источник: https://developer.apple.com/design/human-interface-guidelines/layout
Домены мандата: расстояния, минимализм, кроссплатформенность
Нормативных положений: 42 (детерминированная выжимка, не пересказ)


## без раздела
- People expect familiar relationships between controls and content to help them use and discover your app’s features, and designing the layout to take advantage of this makes your app feel at home on the platform.
- For example, you might use negative space, background shapes, colors, materials, or separator lines to show when elements are related and to separate information into distinct areas.
- When you do so, ensure that content and controls remain clearly distinct.
- People want to view the most important information right away, so don’t obscure it by crowding it with nonessential details.
- Make sure backgrounds and full-screen artwork extend to the edges of the display.
- Also ensure that scrollable layouts continue all the way to the bottom and the sides of the device screen.
- When your content doesn’t span the full window, use a background extension view to provide the appearance of content behind the control layer on either side of the screen, such as beneath the sidebar or inspector.
- Instead of a background, use a scroll edge effect to provide a transition between content and the control area.
- Depending on the platform, you might use a , or display parts of items to hint that people can reveal additional content by interacting with the view, such as by scrolling.
- Make controls easier to use by providing enough space around them and grouping them in logical sections.
- If unrelated controls are too close together — or if other content crowds them — they can be difficult for people to tell apart or understand what they do, which can make your app or game hard to use.
- Using SwiftUI or Auto Layout can help you ensure that your interface adapts dynamically to these traits and other context changes; if you don’t use these tools, you need to use alternative methods to do the work.
- You can help ensure an adaptable interface by respecting system-defined safe areas, margins, and guides (where available) and specifying layout modifiers to fine-tune the placement of views in your interface.
- To support Dynamic Type in your Unity-based game, use Apple’s accessibility plug-in (for developer guidance, see ).
- You can streamline the testing process by first testing versions of your experience that use the largest and the smallest layouts.
- For example, if your iOS app or game supports landscape mode, you can use the simulator to make sure your layouts look great whether the device rotates left or right.
- If this happens, don’t change the aspect ratio of the artwork; instead, scale it so that important visual content remains visible.
- When an app or game doesn’t accommodate such features, it doesn’t feel at home in the platform and may be harder for people to use.
- In addition to helping you avoid display and system features, safe areas can also help you account for interactive components like bars, dynamically repositioning content when sizes change.
- If your app or game is landscape-only, make sure it runs equally well whether people rotate their device to the left or the right.
- Prefer a full-bleed interface for your game.
- Avoid full-width buttons.
- If you need to include a full-width button, make sure it harmonizes with the curvature of the hardware and aligns with adjacent safe areas.
- The status bar displays information people find useful and it occupies an area of the screen most apps don’t fully use, so it’s generally a good idea to keep it visible.
- People can freely resize windows down to a minimum width and height, similar to window behavior in macOS.
- For more complex layouts such as , prefer hiding tertiary columns such as inspectors as the view narrows.
- Be sure to minimize unexpected UI changes as people adjust down to the minimum and up to the maximum window size.
- For many apps, you don’t need to choose between a tab bar or sidebar for navigation; instead, you can adopt a style of tab bar that provides both.
- Avoid placing controls or critical information at the bottom of a window.
- Avoid displaying content within the camera housing at the top edge of the window.
- On Apple TV, layouts don’t automatically adapt to the size of the screen like they do on iPhone or iPad.
- When you use UIKit and the focus APIs, an element gets bigger when it comes into focus.
- Consider how elements look when they’re focused, and make sure you don’t let them overlap important information.
- Be sure to use appropriate spacing between unfocused rows and columns to prevent overlap when an item comes into focus.
- If you use the UIKit collection view flow element, the number of columns in a grid is automatically determined based on the width and spacing of your content.
- If a row has a title, provide enough spacing between the bottom of the previous unfocused row and the center of the title to avoid crowding.
- The guidance below can help you lay out content within the windows of your visionOS app or game, making it feel familiar and easy to use.
- Letting 2D or 3D content encroach on these areas can make the system-provided controls, especially those below the window, difficult for people to use.
- If you need to display additional controls that don’t belong within a window, use an ornament.
- For example, place buttons so their centers are at least 60 points apart.
- To avoid wasting valuable space, consider minimizing the padding between elements.
- Avoid placing more than two or three controls side by side in your interface.
