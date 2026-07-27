# знание · `hig-icons`
Источник: https://developer.apple.com/design/human-interface-guidelines/icons
Домены мандата: иконки
Нормативных положений: 28 (детерминированная выжимка, не пересказ)


## без раздела
- Apps and games use a variety of simple icons to help people understand the items, actions, and modes they can choose.
- Unlike , which can use rich visual details like shading, texturing, and highlighting to evoke the app’s personality, an interface icon typically uses streamlined shapes and touches of color to communicate a straightforward idea.
- Both interface icons and symbols use black and clear colors to define their shapes; the system can apply other colors to the black areas in each image.
- In general, icons work best when they use familiar visual metaphors that are directly related to the actions they initiate or content they represent.
- Whether you use only custom icons or mix custom and system-provided ones, all interface icons in your app need to use a consistent size, level of detail, stroke thickness (or weight), and perspective.
- Depending on the visual weight of an icon, you may need to adjust its dimensions to ensure that it appears visually consistent with other icons.
- You don’t need to provide selected and unselected appearances for an icon that’s used in standard system components such as toolbars, tab bars, and buttons.
- Prefer depicting gender-neutral human figures and avoid images that might be hard to recognize across different cultures or languages.
- If you need to display individual characters in your icon, be sure to localize them.
- If you need to suggest a passage of text, design an abstract representation of it, and include a flipped version of the icon to use when the context is right-to-left.
- If you create a custom interface icon, use a vector format like PDF or SVG.
- The system automatically scales a vector-based interface icon for high-resolution displays, so you don’t need to provide high-resolution versions of it.
- Avoid using replicas of Apple hardware products.
- If you must display Apple hardware, use only the images available in or the SF Symbols that represent various Apple products.
- For icons to represent common actions in , , , and other places in interfaces across Apple platforms, you can use these .
- If your macOS app can use a custom document type, you can create a document icon to represent it.
- If you don’t supply a document icon for a file type you support, macOS creates one for you by compositing your app icon and the file’s extension onto the canvas.
- provides a template you can use to create a custom background fill and center image for a document icon.
- As you use this template, follow the guidelines below.
- Whether you use a background fill, a center image, or both, prefer uncomplicated shapes and a reduced palette of distinct colors.
- For example, Xcode and TextEdit both use rich background images that don’t include a center image.
- For example, to ensure that the grid lines in the custom heart document icon remain clear in intermediate sizes, you might use fewer lines and thicken them by aligning them to the reduced pixel grid.
- Avoid placing important content in the top-right corner of your background fill.
- 512x512 px @1x, 1024x1024 px @2x 256x256 px @1x, 512x512 px @2x 128x128 px @1x, 256x256 px @2x 32x32 px @1x, 64x64 px @2x 16x16 px @1x, 32x32 px @2x If a familiar object can convey a document’s type or its connection with your app, consider creating a center image that depicts it.
- For example, to create a center image for a 32x32 px document icon, use an image canvas that measures 16x16 px.
- You can provide center images in the following sizes: 256x256 px @1x, 512x512 px @2x 128x128 px @1x, 256x256 px @2x 32x32 px @1x, 64x64 px @2x 16x16 px @1x, 32x32 px @2x Define a margin that measures about 10% of the image canvas and keep most of the image within it.
- Although parts of the image can extend into this margin for optical alignment, it’s best when the image occupies about 80% of the image canvas.
- The system automatically scales the extension text to fit in the document icon, so be sure to use a term that’s short enough to be legible at small sizes.
