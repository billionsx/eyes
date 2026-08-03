# ГРАДУИРОВКА БИБЛИОТЕКИ

Честная мера того, чем департамент владеет. Число «строк в библиотеке» не есть число законов: правдоподобное хуже отсутствующего (ЗКН-Э001).

| ступень | строк | доля |
|---|---|---|
| СВЯЗЫВАЕМАЯ | 29 | 0.1% |
| ЧИСЛОВАЯ | 68 | 0.2% |
| НОРМАТИВНАЯ | 10840 | 35.8% |
| ПРОЗА | 19127 | 63.2% |
| ОБВЯЗКА | 194 | 0.6% |
| БЕЗАДРЕСНАЯ | 0 | 0.0% |

**Связываемых в правило: 29 из 30258.** Это и есть настоящий надзорный запас библиотеки.

## Обвязка страницы — мусор обходчика

Куки-баннеры, навигация и кнопки, прошедшие извлечение. Опаснее прозы: выглядит как текст источника и раздувает счёт.

- `big7` — 52
- `authenticationservices` — 14
- `signinwithapple` — 12
- `xcode` — 10
- `human-interface-guidelines` — 7
- `appclip` — 6
- `appstoreconnectapi` — 6
- `arkit` — 6
- `swiftui` — 6
- `combine` — 5
- `applemapsserverapi` — 4
- `healthkit` — 4
- `watchkit` — 4
- `accelerate` — 3
- `accessibility` — 3
- `applemusicapi` — 3
- `cloudkit` — 3
- `realitykit` — 3
- `security` — 3
- `technotes` — 3
- `tvservices` — 3
- `wifiaware` — 3
- `avfoundation` — 2
- `bundleresources` — 2
- `corelocation` — 2
- `fileprovider` — 2
- `gamekit` — 2
- `metalperformanceshadersgraph` — 2
- `signinwithapplerestapi` — 2
- `storekit` — 2
- `updates` — 2
- `activitykit` — 1
- `appkit` — 1
- `classkit` — 1
- `coretelephony` — 1
- `devicediscoveryui` — 1
- `endpointsecurity` — 1
- `metalperformanceshaders` — 1
- `proximityreader` — 1
- `safariservices` — 1
- `servicemanagement` — 1
- `technologyoverviews` — 1
- `tipkit` — 1
- `uikit` — 1

## Связываемые нормы

- `/documentation/appkit/nscollectionlayoutdimension`  
  Use an absolute value to specify exact dimensions, like a 44 x 44 point square: Use an estimated value if the size of your content might change at runtime, such as when data is loaded or in response t
- `/documentation/callkit/cxproviderconfiguration/icontemplateimagedata`  
  The icon image should be a square with side length of 40 points.
- `/design/human-interface-guidelines/complications`  
  A SwiftUI view that implements an extra-large circular layout uses the following default text values: Style: Rounded Weight: Medium Text size: 34.5 pt (40mm), 36.5 pt (41mm), 36.5 pt (44mm), 41 pt (45
- `/design/human-interface-guidelines/widgets`  
  Use the standard margin width for widgets — 16 points for most widgets — to avoid crowding their edges and creating a cluttered appearance.
- `/design/human-interface-guidelines/eyes`  
  You can help ensure that there’s enough space between interactive items by using a margin of at least 16 points around the bounds of each item or by placing items so that their centers are always at l
- `/design/human-interface-guidelines/playing-video`  
  To improve performance, supply a set of thumbnails that each measure 160 px in width.
- `/design/human-interface-guidelines/mac-catalyst`  
  For example, the system scales text that uses the iPadOS baseline font size of 17pt down to 13pt in macOS.
- `/design/human-interface-guidelines/maps`  
  For example, it works well to use 7 points of padding on the sides of the elements and 10 points above and below them.
- `/documentation/realitykit/imagepresentationcomponent/spatial3dimage/generate()`  
  Also throws an error if the image size does not meet the following requirements: At least 320 pixels on its shortest side At most 16,384 pixels on its largest side Aspect ratio between 1:3 and 3:1 Cre
- `/documentation/swiftui/creating-performant-scrollable-stacks`  
  If the in the example code above has an intrinsic content size of 200 x 200 points, the maximum width of 500 points that the view modifier applies to the causes the stack to scroll inside it.
- `/documentation/swiftui/fitting-images-into-available-space`  
  The following example loads the image directly into an view, and then places it in a 300 x 400 point frame, with a blue border: As seen in the following screenshot, the image data loads at full size i
- `/documentation/swiftui/font/system(size:weight:design:)`  
  The following example styles the text as 17 point system font using design, while its weight can depend on the current context: Specifies a system font to use, along with the style, weight, and any de
- `/documentation/swiftui/font/system(size:weight:design:)-697b2`  
  The following example styles the text as 17 point system font using design, while its weight can depend on the current context: Specifies a system font to use, along with the style, weight, and any de
- `/documentation/swiftui/font/system(size:weight:design:)-73a88`  
  The following styles the system font as 17 point, text: While the following styles the text as 17 point , and applies a to the system font: If you want to use the default ( ), you don’t need to specif
- `/documentation/swiftui/font/system(size:weight:design:)-73a88`  
  The following example styles the text as 17 point , and uses a system font: Specifies a system font to use, along with the style, weight, and any design parameters you want applied to the text.
- `/documentation/tvservices/tvtopshelfinsetcontent/imagesize`  
  The standard image size for inset items is 1740 x 560 points.
- `/documentation/uikit/uiimage/alignmentrectinsets`  
  For example, if you have a 20 x 20 pixel icon that includes a glow effect, you might set the insets to {{2, 2}, {16, 16}} to indicate the position of the underlying icon without the glow effect.
- `/documentation/uikit/nscollectionlayoutdimension`  
  Use an absolute value to specify exact dimensions, like a 44 x 44 point square: Use an estimated value if the size of your content might change at runtime, such as when data is loaded or in response t
- `/documentation/watchkit/wkinterfacegroup/setcornerradius(_:)`  
  The default corner radius for groups is 6 points.
- `/documentation/Xcode/creating-your-app-icon-using-icon-composer`  
  Otherwise, change the canvas size to match the size that you use in Icon Composer, such as 1024 x 1024 pixels for iPhone, iPad, and Mac, and 1088 x 1088 pixels for Apple Watch.
- `/documentation/xcode/configuring-your-app-icon`  
  Variations of your app icon appear throughout the system in places like the Home View, Settings, and search results: iOS, iPadOS, tvOS, and watchOS apps can auto-generate all icon variations from a si
- `/documentation/xcode/creating-your-app-icon-using-icon-composer`  
  Otherwise, change the canvas size to match the size that you use in Icon Composer, such as 1024 x 1024 pixels for iPhone, iPad, and Mac, and 1088 x 1088 pixels for Apple Watch.
- `/documentation/Xcode/Analyzing-the-performance-of-your-Metal-app`  
  In contrast, the following screenshot shows an app that maintained a consistent frame rate: A duration of 16.67 ms is one 60 fps frame, and because all other frames consistently achieve this frame dur
- `/documentation/Xcode/Analyzing-the-performance-of-your-Metal-app`  
  Because the combined duration of the vertex and the fragment shader is more than the duration of a 60 fps frame interval (16.67 ms), the app skipped a frame.
- `/documentation/xcode/analyzing-the-performance-of-your-metal-app`  
  In contrast, the following screenshot shows an app that maintained a consistent frame rate: A duration of 16.67 ms is one 60 fps frame, and because all other frames consistently achieve this frame dur
- `/documentation/xcode/analyzing-the-performance-of-your-metal-app`  
  Because the combined duration of the vertex and the fragment shader is more than the duration of a 60 fps frame interval (16.67 ms), the app skipped a frame.
- `/documentation/xcode/analyzing-the-performance-of-your-metal-app`  
  To identify whether your app is overutilizing the CPU, and to determine the reason, perform the following steps: Observe a stutter, as identified by a display duration longer than 16.67 ms.
- `/documentation/Xcode/configuring-your-app-icon`  
  Variations of your app icon appear throughout the system in places like the Home View, Settings, and search results: iOS, iPadOS, tvOS, and watchOS apps can auto-generate all icon variations from a si
- `/documentation/xcode/understanding-hitches-in-your-app`  
  So in the illustration below, the hitch duration is one vsync interval, or 16.7 ms for a 60 Hz refresh rate.
