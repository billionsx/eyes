# знание · `hig-haptics`
Источник: https://developer.apple.com/design/human-interface-guidelines/playing-haptics
Домены мандата: вибрации
Нормативных положений: 18 (детерминированная выжимка, не пересказ)


## без раздела
- Use system-provided haptic patterns according to their documented meanings.
- If the documented use case for a pattern doesn’t make sense in your app or game, avoid using the pattern to mean something else.
- Instead, use a generic pattern or create your own, where supported.
- Use haptics consistently throughout your app or game.
- If you use the same haptic pattern for a positive outcome like a level completion, people will be confused.
- Prefer using haptics to complement other feedback in your app or game.
- In most apps, prefer playing short haptics that complement discrete events.
- On Apple Pencil Pro, for example, continuous or long-lasting haptics don’t tend to clarify the writing or drawing experience and can even make holding the pencil less pleasant.
- Let people turn off or mute haptics, and make sure people can still enjoy your app or game without them.
- Ensure that haptic vibrations don’t disrupt experiences involving device features like the camera, gyroscope, or microphone.
- Games often use custom haptics to enhance gameplay.
- Although it’s less common, nongame apps might also use custom haptics to provide a richer, more delightful experience.
- There are two basic building blocks you can use to generate custom haptic patterns.
- Regardless of the type of haptic event you use to generate a custom haptic, you can also control its sharpness and intensity .
- For example, you might use sharpness values to convey an experience that’s soft, rounded, or organic, or one that’s crisp, precise, or mechanical.
- On supported iPhone models, you can add haptics to your experience in the following ways: Use standard UI components — like , , and — that play Apple-designed system haptics by default.
- When it makes sense, use a feedback generator to play one of several predefined haptic patterns in the categories of , , and (for developer guidance, see ).
- Impact haptics provide a physical metaphor you can use to complement a visual experience.
