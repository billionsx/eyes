# знание · `hig-materials`
Источник: https://developer.apple.com/design/human-interface-guidelines/materials
Домены мандата: liquid-glass, размытие, полупрозрачность, многослойность
Нормативных положений: 32 (детерминированная выжимка, не пересказ)


## без раздела
- Don’t use Liquid Glass in the content layer.
- Instead, use for elements in the content layer, such as app backgrounds.
- Use Liquid Glass effects sparingly.
- Only use clear Liquid Glass for components that appear over visually rich backgrounds.
- The appearance of these variants can differ in response to certain system settings, like if people choose a preferred look for Liquid Glass in their device’s settings, or turn on accessibility settings that reduce transparency or increase contrast in the interface.
- Most system components use this variant.
- Use the regular variant when background content might create legibility issues, or when components have a significant amount of text, such as alerts, sidebars, or popovers.
- Use this variant for components that float above media backgrounds — such as photos and videos — to create a more immersive content experience.
- For optimal contrast and legibility, determine whether to add a dimming layer behind components with clear Liquid Glass: If the underlying content is bright, consider adding a dark dimming layer of 35% opacity.
- If the underlying content is sufficiently dark, or if you use standard media playback controls from AVKit that provide their own dimming layer, you don’t need to apply a dimming layer.
- For guidance about the use of color, see .
- Use standard materials and effects — such as , , and — to convey a sense of structure in the content beneath Liquid Glass.
- Choose materials and effects based on semantic meaning and recommended usage.
- Avoid selecting a material or effect based on the apparent color it imparts to your interface, because system settings can change its appearance and behavior.
- Instead, match the material or vibrancy style to your specific use case.
- Help ensure legibility by using vibrant colors on top of materials.
- When you use system-defined vibrant colors, you don’t need to worry about colors seeming too dark, bright, saturated, or low contrast in different contexts.
- Regardless of the material you choose, use vibrant colors on top of it.
- In addition to Liquid Glass, iOS and iPadOS continue to provide four standard materials — ultra-thin, thin, regular (default), and thick — which you can use in the content layer to help create visual distinction.
- Except for quaternary, you can use the following vibrancy values for labels on any material.
- In general, avoid using quaternary on top of the and materials, because the contrast is too low.
- (default) You can use the following vibrancy values for fills on all materials.
- Depending on configuration and system settings, system views and controls use vibrancy to make foreground content stand out against any background.
- In addition to Liquid Glass, tvOS continues to provide standard materials, which you can use to help define structure in the content layer.
- In visionOS, windows generally use an unmodifiable system-defined material called glass that helps people stay grounded by letting light, the current Environment, virtual content, and objects in people’s surroundings show through.
- Prefer translucency to opaque colors in windows.
- Use the following examples for guidance.
- To ensure foreground content remains legible when it displays on top of a material, visionOS applies vibrancy to text, symbols, and fills.
- Use for descriptive text like footnotes and subtitles.
- Use for inactive elements, and only when text doesn’t need high legibility.
- Use materials to provide context in a full-screen modal view.
- Avoid removing or replacing material backgrounds for modal sheets when they’re provided by default.
