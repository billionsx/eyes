# знание · `hig-gestures`
Источник: https://developer.apple.com/design/human-interface-guidelines/gestures
Домены мандата: жесты, надавливание
Нормативных положений: 39 (детерминированная выжимка, не пересказ)


## без раздела
- Although the precise movements that make up basic gestures can vary per platform and input device, people are familiar with the underlying functionality of these gestures and expect to use them everywhere.
- People commonly prefer or need to use other inputs — such as their voice, keyboard, or Switch Control — to interact with their devices.
- Don’t assume that people can use a specific gesture to perform a given task.
- Avoid using a familiar gesture like tap or swipe to perform an action that’s unique to your app; similarly, avoid creating a unique gesture to perform a standard action like activating a button or scrolling a long view.
- As people perform a gesture in your app, provide feedback that helps them predict its results and, if necessary, communicates the extent and type of movement required to complete the action.
- If you don’t clearly communicate why a gesture doesn’t work, people might think your app has frozen or they aren’t performing the gesture correctly, leading to frustration.
- If you decide to implement a custom gesture, make sure it’s: Discoverable Straightforward to perform Distinct from other gestures Not the only way to perform an important action in your app or game Make custom gestures easy to learn.
- Offer moments in your app to help people quickly learn and perform custom gestures, and make sure to test your interactions in real use scenarios.
- If you’re finding it difficult to use simple language and graphics to describe a gesture, it may mean people will find the gesture difficult to learn and perform.
- Use shortcut gestures to supplement standard gestures, not replace them.
- Avoid conflicting with gestures that access system UI.
- It’s important to avoid defining custom gestures that might conflict with these interactions, as people expect these controls to work consistently.
- People expect to use to navigate tvOS apps and games with a compatible remote, Siri Remote, or that includes a touch surface.
- People use an indirect gesture by looking at an object to target it, and then manipulating that object from a distance — indirectly — with their hands.
- People use a direct gesture to physically touch an interactive object.
- Because people may find it tiring to keep their arms raised for extended periods, direct gestures are best for infrequent use.
- Here are the standard direct gestures people use in visionOS; see for a list of standard indirect gestures.
- Prefer indirect gestures for UI and common components like buttons.
- Avoid requiring specific body movements or positions for input.
- If your experience requires movement, consider supporting alternative inputs to let people choose the interaction method that works best for them.
- To offer this type of interaction, your app needs to be running in a Full Space, and you must request people’s permission to access information about their hands.
- Continually test ergonomics of all interactions that require custom gestures.
- A custom interaction that requires people to keep their arms raised for even a little while can be physically tiring, and repeating very similar movements many times in succession can stress people’s muscles and joints.
- People may not always have both hands available when using your app or game.
- If you require a more complex gesture for your experience, consider also offering an alternative that requires less movement.
- Avoid custom gestures that require using a specific hand.
- It can increase someone’s cognitive load if they need to remember which hand to use to trigger a custom gesture.
- In visionOS 2 and later, people can look at the palm of one hand and use gestures to quickly access system overlays for Home and Control Center.
- When designing apps and games that use custom gestures or anchor content to a person’s hands, it’s important to take interactions with the system overlays into consideration.
- If possible, don’t anchor content to a person’s hands or wrists.
- If you’re designing a game that involves hand-anchored content, place it outside of the immediate area of someone’s hand to avoid colliding with the Home indicator.
- In such cases, when your app is running in a Full Space, you can choose to require a tap to reveal the Home indicator instead.
- Use caution when designing custom gestures that involve a rolling motion of the hand, wrist, and forearm.
- Since system overlays always display on top of app content and your app isn’t aware of when they’re visible, it’s important to test any custom gestures or content that might conflict.
- In watchOS 11 and later, people can use the double-tap gesture to scroll through lists and scroll views, and to advance between vertical tab views.
- Avoid setting a primary action in views with lists, scroll views, or vertical tabs.
- Choose the button that people use most commonly as the primary action in a view.
- Double tap is helpful in a nonscrolling view when it performs the action that people use the most.
- The system provides APIs that support the familiar gestures people use with their devices, whether they use a touchscreen, an indirect gesture in visionOS, or an input device like a trackpad, mouse, remote, or game controller.
