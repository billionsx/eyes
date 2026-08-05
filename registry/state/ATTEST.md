# ДВОЙНОЕ СВИДЕТЕЛЬСТВО · замер против свода

Каждая строка сшивает число, снятое с кадров операционной системы, с нормой, написанной Apple словами. Совпадение усиливает правило вдвое; расхождение — самостоятельная находка и предъявляется, а не прячется (ст. 7.4: разрешает основатель).

| вердикт | предмет | замер | свод говорит | адрес нормы |
|---|---|---|---|---|
| ПОДТВЕРЖДЕНО | `contrast.min_ratio` | 4.5 :1 | 4.5 :1 | /design/human-interface-guidelines/dark-mode |
| ПОДТВЕРЖДЕНО | `tap_target.min_pt` | 44 pt | 44.0 pt | /design/human-interface-guidelines/game-controls |
| ПОДТВЕРЖДЕНО | `tap_target.secondary_min_pt` | 28 pt | 28.0 pt | /design/human-interface-guidelines/game-controls |
| ПРОТИВОРЕЧИЕ | `geometry.inset_card_pt` | 16 pt | 20.0 pt | /documentation/WidgetKit/DynamicIsland/contentMargins(_:_:for:) |
| НЕМО | `geometry.corner_form_required_above_pt` | 12 pt | — | — |
| НЕМО | `geometry.radius_card_pt` | 24 pt | — | — |
| НЕМО | `geometry.tabbar_height_pt` | 62 pt | — | — |
| НЕМО | `motion.min_ms_for_curve` | 200 ms | — | — |
| НЕМО | `motion.press_response_ms_max` | 120 ms | — | — |
| НЕМО | `typography.tracking_cap_px` | 0.4 px | — | — |

## Счёт

- ПОДТВЕРЖДЕНО: 3
- ПРОТИВОРЕЧИЕ: 1
- НЕМО: 6

## Расхождения написанного с отгруженным

Ниже — места, где свод Apple называет одно число, а кадры операционной системы дают другое. Ни одна сторона не объявляется правой автоматически.

**`geometry.inset_card_pt`** — замер 16 pt, свод 20.0 pt
> The following example results in a margin of 8 points for the trailing edge and 20 points for all other edges when the Live Activity appears in the expanded presentation: Overrides default content margins for the provided content modes in the Dynamic Island.
> адрес: /documentation/WidgetKit/DynamicIsland/contentMargins(_:_:for:)

