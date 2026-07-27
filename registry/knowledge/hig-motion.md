# знание · `hig-motion`
Источник: https://developer.apple.com/design/human-interface-guidelines/motion
Домены мандата: анимация, кинетика, эффекты
Нормативных положений: 16 (детерминированная выжимка, не пересказ)


## без раздела
- Don’t add motion for the sake of adding motion.
- Not everyone can or wants to experience the motion in your app or game, so it’s essential to avoid using it as the only way to communicate important information.
- For example, if someone reveals a view by sliding it down from the top, they don’t expect to dismiss the view by sliding it to the side.
- In apps, generally avoid adding motion to UI interactions that occur frequently.
- For a custom element, you generally want to avoid making people spend extra time paying attention to unnecessary motion every time they interact with it.
- As much as possible, don’t make people wait for an animation to complete before they can do anything, especially if they have to experience the animation more than once.
- When you use SF Symbols 5 or later, you can apply animations to SF Symbols or custom symbols.
- Make sure your game’s motion looks great by default on each platform you support.
- For each platform you support, use the device’s graphics capabilities to enable default settings that let people enjoy your game without first having to change those settings.
- Because motion is likely to be a large part of your visionOS experience, it’s crucial to avoid causing distraction, confusion, or discomfort.
- As much as possible, avoid displaying motion at the edges of a person’s field of view.
- If you need to show an object moving in the periphery during an immersive experience, make sure the object’s brightness level is similar to the rest of the visible content.
- In general, avoid letting people rotate a virtual world.
- Avoid showing objects that oscillate in a sustained way.
- In particular, you want to avoid showing an oscillation that has a frequency of around 0.2 Hz because people can be very sensitive to this frequency.
- If you need to use WatchKit to animate layout and appearance changes — or create animated image sequences — see .
