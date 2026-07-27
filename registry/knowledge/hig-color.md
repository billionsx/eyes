# знание · `hig-color`
Источник: https://developer.apple.com/design/human-interface-guidelines/color
Домены мандата: цвет, градиенты
Нормативных положений: 48 (детерминированная выжимка, не пересказ)


## без раздела
- You may also want to use custom colors to enhance the visual experience of your app or game and express its unique personality.
- The following guidelines can help you use color in ways that people appreciate, regardless of whether you use system-defined or custom colors.
- Avoid using the same color to mean different things.
- Use color consistently throughout your interface, especially when you use it to help communicate information like status or interactivity.
- For example, if you use your brand color to indicate that a borderless button is interactive, using the same or similar color to stylize noninteractive text is confusing.
- Make sure all your app’s colors work well in light, dark, and increased contrast contexts.
- vary subtly depending on the system appearance, adjusting to ensure proper color differentiation and contrast for text, symbols, and other elements.
- When possible, use system colors, which already define variants for all these contexts.
- If you define a custom color, make sure to supply light and dark variants, and an increased contrast option for each variant that provides a significantly higher amount of visual differentiation.
- Adjust app colors to provide an optimal viewing experience in the majority of use cases.
- If your app lets people choose colors, prefer system-provided color controls where available.
- Avoid relying solely on color to differentiate between objects, indicate interactivity, or communicate essential information.
- When you use color to convey information, be sure to provide the same information in alternative ways so people with color blindness or other visual disabilities can understand it.
- For example, you can use text labels or glyph shapes to identify objects or states.
- Avoid using colors that make it hard to perceive content in your app.
- Consider how the colors you use might be perceived in other countries and cultures.
- Make sure the colors in your app send the message you intend.
- Avoid hard-coding system color values in your app.
- Use APIs like to apply system colors.
- Avoid redefining the semantic meanings of dynamic system colors.
- To ensure a consistent experience and ensure your interface looks great when the appearance of the platform changes, use dynamic system colors as intended.
- For example, don’t use the color as a text color, or color as a background color.
- Avoid using similar colors in control labels if your app has a colorful background.
- If your app features colorful backgrounds or visually rich content, prefer a monochromatic appearance for toolbars and tab bars, or choose an accent color with sufficient visual differentiation.
- Make sure your interface maintains sufficient contrast by avoiding overlap of similar colors in the content layer and controls when possible.
- Although colorful content might intermittently scroll underneath controls, make sure its default or resting state — like the top of a screen of scrollable content — maintains clear legibility.
- Color profiles help ensure that your app’s colors appear as intended on different displays.
- Use wide color to enhance the visual experience on compatible displays.
- As a result, photos and videos that use wide color are more lifelike, and visual data and status indicators that use wide color can be more meaningful.
- When appropriate, use the Display P3 color profile at 16 bits per pixel (per channel) and export images in PNG format.
- Note that you need to use a wide color display to design wide color images and select P3 colors.
- Gradients that use P3 colors can also sometimes appear clipped on sRGB displays.
- To avoid these issues and to ensure visual fidelity on both wide color and sRGB displays, you can use the asset catalog of your Xcode project to provide different versions of images and colors for each color space.
- In general, use the grouped background colors ( , , and ) when you have a grouped table view; otherwise, use the system set of background colors ( , , and ).
- Subtle use of color can help you communicate your brand while deferring to the content.
- Avoid using only color to indicate focus.
- Use color sparingly, especially on glass.
- Standard visionOS windows typically use the system-defined glass , which lets light and objects from people’s physical surroundings and their space show through.
- Prefer using color in places where it can help call attention to important information or show the relationship between parts of the interface.
- Prefer using color in bold text and large areas.
- For example, avoid displaying a bright object on a very dark or black background, especially if the object flashes or moves.
- Use background color to support existing content or supply additional information.
- Use background color when you have something to communicate, rather than as a solely visual flourish.
- Avoid using full-screen background color in views that are likely to remain onscreen for long periods of time, such as in a workout or audio-playing app.
- Recognize that people might prefer graphic complications to use tinted mode instead of full color.
- The system can use a single color that’s based on the wearer’s selected color in a graphic complication’s images, gauges, and text.
- visionOS system colors use the default dark color values.
- Judicious use of color can enhance communication, evoke your brand, provide visual continuity, communicate status and feedback, and help people understand information.
