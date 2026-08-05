# ЧЕМ ЗАКРЫВАЮТСЯ ДЫРЫ БАЗЫ iOS 27

Дыр: **56** · кадров измерено: **11**

Дыра, не называющая своего сырья, хуже дыры: она выглядит закрываемой завтра. Здесь сказано, чем именно каждая закрывается — и чего департамент не получит, сколько бы кадров ему ни дали.

| вид сырья | дыр | чем закрывается |
|---|---|---|
| **КАДР** | 33 | статический кадр iOS 27 в тёмной теме |
| **ЗАПИСЬ** | 9 | запись экрана 60 fps: длительности на статическом кадре не существует |
| **ШРИФТ** | 7 | доля высоты прописной берётся из таблиц шрифта |
| **КАДР+СЛОЙ** | 5 | кадр, где известен цвет под стеклом: иначе прозрачность неотделима от фона |
| **НЕ КЛАССИФИЦИРОВАНО** | 1 | 🕳 вид сырья не назван — орган обязан быть дополнен, а не угадать |
| **СВОДКА** | 1 | не величина, а состояние базы: закроется само, когда закроются остальные |

## КАДР — 33

- `geometry.corner_form_required_above_pt`
- `geometry.superellipse_n`
- `geometry.radius_card_pt`
- `geometry.radius_card_full_pt`
- `geometry.radius_tile_pt`
- `geometry.button_height_pt`
- `geometry.button_hit_pad_pt`
- `geometry.chip_height_pt`
- `geometry.inset_card_pt`
- `geometry.card_width_pt`
- `geometry.tabbar_height_pt`
- `geometry.bottom_bar_with_safe_area_pt`
- `geometry.layer_axis_pt`
- `geometry.layer_span_pt`
- `geometry.layer_inset_pt`
- `geometry.layer_gap_pt`
- `geometry.radius_ladder_pt`
- `typography.role_sizes_pt`
- `typography.tracking_cap_px`
- `typography.line_height_families_pt`
- `rows.list_pt`
- `rows.note_pt`
- `rows.two_line_pt`
- `rows.wallet_two_line_pt`
- `rows.dense_pt`
- `rows.media_pitch_pt`
- `rows.media_cover_w_pt`
- `glyphs.menu_pt`
- `glyphs.tile_pt`
- `glyphs.stroke_pt`
- `glyphs.chevron`
- `glyphs.check`
- `empty.block_y_pt`

## ЗАПИСЬ — 9

- `motion.player_close_ms`
- `motion.view_change_ms`
- `motion.tab_crossfade_ms`
- `motion.press_response_ms_max`
- `motion.release_spring_ms`
- `motion.menu_exit_ms`
- `motion.pause_breath_scale`
- `motion.scrubber_grow`
- `motion.min_ms_for_curve`

## ШРИФТ — 7

- `typography.cap_height_fraction.caps_digits`
- `typography.cap_height_fraction.ascending`
- `typography.cap_height_fraction.descending`
- `typography.weights.regular`
- `typography.weights.medium`
- `typography.weights.semibold`
- `typography.weights.bold`

## КАДР+СЛОЙ — 5

- `glass.thin`
- `glass.regular`
- `glass.thick`
- `opacity_ladder.allow`
- `opacity_ladder.tolerance`

## НЕ КЛАССИФИЦИРОВАНО — 1

- `separator.width_pt`

## СВОДКА — 1

- `debts`

---

**Что это значит на деле.** Кадры поставляются разовым ручным импортом; автоматической поставки у департамента нет. Пока не появится новое сырьё нужного вида, соответствующие дыры не закрываются никаким усердием инструмента — и база iOS 27 не вступает в силу (Э002).
