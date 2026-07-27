# знание · `hig-accessibility`
Источник: https://developer.apple.com/design/human-interface-guidelines/accessibility
Домены мандата: динамика, эффекты, анимация, доступность
Нормативных положений: 53 (детерминированная выжимка, не пересказ)


## без раздела
- An accessible interface allows people to experience your app or game regardless of their capabilities or how they use their devices.
- People can access and interact with your content, whether they use sight, hearing, speech, or touch.
- Your interface adapts to how people want to use their device, whether by supporting system accessibility features or letting people personalize settings.
- Use to highlight accessibility issues with your interface and to understand how your app represents itself to people using system accessibility features.
- The people who use your interface may be blind, color blind, or have low vision or light sensitivity.
- Make sure people can adjust the size of your text or icons to make them more legible, visible, and comfortable to read.
- Ideally, give people the option to enlarge text by at least 200 percent (or 140 percent in watchOS apps).
- Use recommended defaults for custom type sizes.
- Each platform has different default and minimum sizes for system-defined type styles to promote readability.
- If you’re using custom type styles, follow the recommended defaults.
- If you’re using a custom font with a thin weight, aim for larger than the recommended sizes to increase legibility.
- Strive to meet color contrast minimum standards.
- To ensure all information in your app is legible, it’s important that there’s enough contrast between foreground text and icons and background colors.
- Use standard contrast calculators to ensure your UI meets acceptable levels.
- If your app doesn’t provide this minimum contrast by default, ensure it at least provides a higher contrast color scheme when the system setting Increase Contrast is turned on.
- If your app supports , make sure to check the minimum contrast in both light and dark appearances.
- Prefer system-defined colors.
- The people who use your interface may be deaf or hard of hearing.
- Use haptics in addition to audio cues.
- In iOS and iPadOS, you can also use and to let people experience music and infographics through vibration and texture.
- Ensure your interface offers a comfortable experience for people with limited dexterity or mobility.
- Strive to meet the recommended minimum control size for each platform to ensure controls and menus are comfortable for all when tapping and clicking.
- For interactions people do frequently in your app or game, use the simplest gesture possible — avoid custom multifinger and multihand gestures — so repetitive actions are both comfortable and easy to remember.
- Make sure your UI’s core functionality is accessible through more than one type of physical interaction.
- For example, if you use a swipe gesture to dismiss a view, also make a button available so people can tap or use an assistive device.
- Let people use Voice Control to give guidance and enter information verbally.
- To ensure a smooth experience, label interface elements appropriately.
- Conduct testing and verify that your app or game supports these technologies, and that your interface elements are appropriately labeled to ensure a great experience.
- Apple’s accessibility features help people with speech disabilities and people who prefer text-based interactions to communicate effectively using their devices.
- Let people use the keyboard alone to navigate and interact with your app.
- People can turn on Full Keyboard Access to navigate apps using their physical keyboard.
- The system also defines accessibility keyboard shortcuts and a wide range of other that many people use all the time.
- Avoid overriding system-defined keyboard shortcuts and evaluate your app to ensure it works well with Full Keyboard Access.
- Ensure that people can navigate your interface using easy-to-remember and consistent interactions.
- Prefer system gestures and behaviors people are already familiar with over creating custom gestures people must learn and retain.
- Minimize use of time-boxed interface elements.
- Views and controls that auto-dismiss on a timer can be problematic for people who need longer to process information, and for people who use assistive technologies that require more time to traverse the interface.
- Prefer dismissing views with an explicit action.
- Avoid autoplaying audio and video content without also providing controls to start and stop it.
- Make sure these controls are discoverable and easy to act upon, and consider global settings that let people opt out of auto-playing all audio and video.
- People might want to avoid bright, frequent flashes of light in the media they consume.
- If your app supports video playback, ensure that it responds appropriately to the Dim Flashing Lights setting.
- When you use these effects in excess, it can be distracting, cause dizziness, and in some cases even result in epileptic episodes.
- People who are prone to these effects can turn on the Reduce Motion accessibility setting.
- When this setting is active, ensure your app or game responds by reducing automatic and repetitive animations, including zooming, scaling, and peripheral motion.
- Assistive Access is an accessibility feature in iOS and iPadOS that allows people with cognitive disabilities to use a streamlined version of your app.
- To optimize your app for this mode, use the following guidelines when Assistive Access is turned on: Identify the core functionality of your app and consider removing noncritical workflows and UI elements.
- Always ask for confirmation twice whenever people perform an action that’s difficult to recover from, such a deleting a file.
- visionOS offers a variety of accessibility features people can use to interact with their surroundings in ways that are comfortable and work best for them, including head and hand Pointer Control, and a Zoom feature.
- To ensure the most comfortable experience, consider these tips: Keep interface elements within a person’s field of view.
- Prefer horizontal layouts to vertical ones that might cause neck strain, and avoid demanding the viewer’s attention in different locations in quick succession.
- Be gentle with camera and video motion, and avoid situations where someone may feel like the world around them is moving without their control.
- Avoid anchoring content to the wearer’s head, which may make them feel stuck and confined, and also prevent them from using assistive technologies like Pointer Control.
