---
name: IndicIntentGuard
description: A verification layer between Gnani Prisma and a voice agent, presented as a banknote's security print.
colors:
  ground: "#e6e3ee"
  note: "#f6f5fa"
  paper: "#ffffff"
  line: "#c9c3dc"
  line-2: "#a69dc6"
  ink: "#241d47"
  ink-2: "#463d6e"
  ink-3: "#5a5280"
  ink-hover: "#352b66"
  guilloche: "#7a6fb0"
  ochre: "#8a6410"
  ochre-ink: "#c8a24a"
  ochre-bg: "#f5ecd3"
  green: "#1b6a4e"
  green-bg: "#e1efe8"
  oxide: "#a63c2a"
  oxide-bg: "#f6e2dc"
  violet: "#5b3d93"
  violet-bg: "#ebe4f6"
  band-blank: "#ece9f4"
  focus: "#3a5bd9"
typography:
  display:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "clamp(42px, 4vw, 58px)"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "\"tnum\", \"lnum\""
  headline:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "clamp(24px, 2.5vw, 34px)"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 900
    letterSpacing: "-0.015em"
  section:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 900
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\", \"lnum\""
  label:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
  amount-words:
    fontFamily: "Hanken Grotesk, Noto Sans Telugu, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 800
    letterSpacing: "0.14em"
  microtext:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "6px"
    fontWeight: 600
    lineHeight: "9px"
    letterSpacing: "0.32em"
rounded:
  hairline: "2px"
  r: "4px"
  pill: "999px"
  round: "50%"
spacing:
  gap: "clamp(16px, 2.2vw, 28px)"
  note-inset: "6px"
  note-x: "22px"
  control-h: "48px"
  container: "min(1360px, 100% - 32px)"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "#f3f1fa"
    rounded: "{rounded.r}"
    padding: "0 18px"
    height: "48px"
    typography: "{typography.body}"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.r}"
    padding: "0 18px"
    height: "48px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.r}"
    padding: "0 18px"
    height: "48px"
  button-ok:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.green}"
    rounded: "{rounded.r}"
    padding: "0 18px"
    height: "44px"
  button-ok-hover:
    backgroundColor: "{colors.green-bg}"
  button-round:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.round}"
    size: "44px"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.r}"
    padding: "0 12px"
    height: "48px"
  note:
    backgroundColor: "{colors.note}"
    textColor: "{colors.ink}"
    rounded: "{rounded.r}"
    padding: "10px 22px 12px"
  band-wrong:
    backgroundColor: "{colors.oxide}"
    textColor: "#ffffff"
    padding: "12px 22px 11px"
  band-ok:
    backgroundColor: "{colors.green}"
    textColor: "#ffffff"
    padding: "12px 22px 11px"
  band-ask:
    backgroundColor: "{colors.ochre-ink}"
    textColor: "{colors.ink}"
    padding: "12px 22px 11px"
  band-refer:
    backgroundColor: "{colors.violet}"
    textColor: "#ffffff"
    padding: "12px 22px 11px"
  chip-accept:
    backgroundColor: "{colors.green-bg}"
    textColor: "{colors.green}"
    rounded: "{rounded.hairline}"
    padding: "2px 8px"
  chip-clarify:
    backgroundColor: "{colors.ochre-bg}"
    textColor: "{colors.ochre}"
    rounded: "{rounded.hairline}"
    padding: "2px 8px"
  chip-escalate:
    backgroundColor: "{colors.violet-bg}"
    textColor: "{colors.violet}"
    rounded: "{rounded.hairline}"
    padding: "2px 8px"
  chip-wrong:
    backgroundColor: "{colors.oxide-bg}"
    textColor: "{colors.oxide}"
    rounded: "{rounded.hairline}"
    padding: "2px 8px"
---

# Design System: IndicIntentGuard

## Overview

**Creative North Star: "Banknote Security Print"**

A rupee note is made so that a wrong number cannot get through: see-through register, microtext, intaglio, a seal nobody can fake. The interface runs the same kind of checks on a spoken instruction, and only a request that passes them earns the seal. The surface is a pale stone-lavender note ground printed in deep violet-navy intaglio ink. Information sits on "notes": framed panels with a double hairline border, each topped by a solid verdict band, a heavy tabular figure, and the amount spelled out in letterspaced words, the way a banknote prints its denomination.

Density is set for a screen recording: large figures, high contrast, one thing moving at a time. Colour is mostly ink on paper. The four verdict hues appear only when a decision exists, so the first glance answers "what will happen to the money". Ornament is limited to devices a banknote actually uses: microtext rules, the guilloché seal, register, and a ruled scale. The system rejects the card-grid dashboard and the dark, glowing AI console.

**Key Characteristics:**
- Light stone-lavender ground; violet-navy ink for text, primary actions and the masthead.
- Four verdict colours with fixed meanings: ochre asks, green clears, oxide marks unchecked execution, violet refers.
- Double-hairline note panels with a solid verdict band across the top.
- One sans family (Hanken Grotesk) from 6px microtext to the 900-weight figure, with Noto Sans Telugu and Devanagari as script fallbacks.
- Security-print devices with a job: microtext section rules, see-through register, guilloché seal, transit-line route.
- Motion that shows a check happening, never ambient. All of it collapses under reduced motion.

## Colors

Intaglio ink on a lavender note, with four verdict hues that appear only when a decision has been made.

### Primary
- **Intaglio Violet-Navy** (ink): body text, headings, the masthead ground, the primary button, lit route segments, the figure. Hover darkens to **Pressed Ink** (ink-hover).
- **Second Impression** (ink-2) and **Third Impression** (ink-3): secondary copy, sub-labels, table headers, empty states. These are the only ways to step text down. Do not use opacity.

### Secondary: verdict hues
Each hue has a strong value (bands, strokes, button text) and a pale tint (chips, ledger flash).
- **Note Green** (green / green-bg): cleared, executed safely, the confirm button, the "Bank" route branch, a check that passed.
- **Ochre** (ochre-ink / ochre / ochre-bg): the guard is asking. ochre-ink fills the ask band and colours the Timbre route branch, the seal's ask stroke, the threshold line and the register ghost. The darker ochre is the text form, used for seal and threshold labels and chip text. Use ochre-ink for fills and strokes, and ochre for words.
- **Oxide Red** (oxide / oxide-bg): an action that ran without a check. Used for the naive agent's band, its figure when wrong, the misregistered ghost, struck-through retracted amounts, the recording state, and error status.
- **Refer Violet** (violet / violet-bg): escalation to a human desk.

### Tertiary
- **Guilloché Violet** (guilloche): the seal's fine-line default only. No other element uses it.

### Neutral
- **Stone-Lavender Ground** (ground): page background, and the halo ring around the scale marker.
- **Note** (note): note panels and the route plate.
- **Paper** (paper): fields, secondary buttons, the settings popover, the ledger table.
- **Hairline** (line): inner note border, row rules, dividers, the seal's unengraved plate.
- **Plate Line** (line-2): outer note border, control borders, microtext, idle route stations.
- **Blank Band** (band-blank): the verdict band before any request.
- **Focus Blue** (focus): the 2.5px focus outline and the caret. This is the one hue outside the world, kept so focus is never confused with a verdict.

### Named Rules
**The Four Verdicts Rule.** Ochre = ask, green = cleared, oxide = executed unchecked, violet = refer. A verdict hue never decorates. If an element is not reporting one of these four outcomes, it is ink.

**The Fill and Word Rule.** ochre-ink is too light for text on paper, so it fills and strokes. Ochre text is always the darker ochre, or ink set on an ochre-ink band.

## Typography

**Display Font:** Hanken Grotesk (with system-ui, sans-serif)
**Body Font:** Hanken Grotesk
**Indic scripts:** Noto Sans Telugu, Noto Sans Devanagari (in the same stack, 400 and 600)

**Character:** A single grotesk that runs from hairline microtext up to a black-weight figure. Numerals are tabular and lining throughout (set on body), so amounts line up in place and flip digit by digit without reflowing.

### Hierarchy
- **Display** (900, clamp(42px, 4vw, 58px), line-height 1, -0.03em): the amount on a note. One per note.
- **Headline** (700, clamp(24px, 2.5vw, 34px), 1.3, balanced wrap): what Prisma heard. Drops to ink-3 at 500 when empty.
- **Title** (900, 22px): note column titles. **Section** (900, 20px) titles the checks and tables blocks.
- **Body** (400, 16px, 1.5): running copy. Note lines and sign lists run at 14.5px (600 for signs, 500 for hypotheticals). The confirmation prompt is 700, 18px, 1.3.
- **Label** (700, 12.5px, ink-3): fact keys, table headers, the signs title. Sentence case.
- **Amount in words** (800, 13px, 0.14em, uppercase, ink-2): the denomination printed under the figure. Uppercase tracking is reserved for this, the seal label (900, 11.5px, 0.14em) and chips (800, 12.5px, 0.04em).
- **Microtext** (600, 6px/9px, 0.32em, line-2, aria-hidden): a repeating "INDICINTENTGUARD · SPEECH TO ACTION VERIFIED · PRISMA · TIMBRE" line used as a rule. It is texture and is never read as content.

### Named Rules
**The Denomination Rule.** Amounts are always shown twice: as the heavy tabular figure and as words underneath. The figure is for the eye, and the words are the proof.

**The Weight Not Size Rule.** Weight separates levels (900 / 800 / 700 / 500). Text is stepped down with ink-2 and ink-3, never with opacity.

## Layout

A single centred column (min(1360px, 100% - 32px)) read top to bottom in the order a request travels: masthead, route diagram, intake row, what Prisma heard, the two notes side by side, then the checks and the tables. Sections are separated by microtext rules (6px top margin), not ink bars. The notes and the tables are two equal columns separated by the fluid gap (clamp(16px, 2.2vw, 28px)). The checks block is a 220-300px heading column beside a two-column list.

Spacing is tight so the guard's confirmation fits in the first viewport at 1440x900: masthead 64px, route plate with no vertical padding, note body padding 10px 22px 12px, confirmation leaf 10px 16px 12px.

Breakpoints: at 1100px the check list becomes one column. At 980px the notes, tables and checks stack. At 560px the route map is replaced by pill steps, the intake controls go full width or pair at 50%, the seal shrinks to 96px, note padding drops to 14px, and some table columns are hidden.

## Elevation & Depth

The system is flat paper. Depth comes from printing: the double hairline and tone. Two soft, low shadows exist, and both lift paper off the ground.

### Shadow Vocabulary
- **Note frame** (`box-shadow: inset 0 0 0 5px var(--note), inset 0 0 0 6px var(--line), 0 12px 26px -20px rgb(36 29 71 / .5)`): the two inset rings draw the inner hairline 5px inside the outer border, and the drop is a faint lift under the note.
- **Popover** (`box-shadow: 0 14px 30px -14px rgb(36 29 71 / .35)`): the account and language settings panel only.

### Named Rules
**The Double Hairline Rule.** A note is framed by a 1px line-2 border plus an inset 1px line hairline 5px inside it. Other surfaces (route plate, confirmation, fields) use a single border.

## Shapes

Corners are nearly square: 4px on notes, buttons, fields and the route plate, and 2px on chips and the focus ring. Round forms are only for things that are physically round: route stations, the seal, evidence dots, the scale marker and the play button (50%). Pills (999px) appear only as the phone version of the route steps. Lines carry meaning. Dashed marks something provisional (the confirmation leaf's top edge, the threshold on the scale, a route segment waiting on Prisma). Strikethrough in oxide marks a retracted amount.

## Components

### Buttons
- **Shape:** lightly squared (4px), 48px tall, 0 18px padding, 700 16px, 20px stroke icon with a 10px gap.
- **Primary:** ink fill with near-white text. Used for Record and Answer by voice. While recording it turns oxide and the icon breathes.
- **Secondary / Quiet:** paper or transparent with a 1.5px line-2 border.
- **Confirm (ok):** green border and text, and fills with green-bg on hover.
- **Hover / Focus / Active:** the border darkens to ink-2 (primary fills ink-hover), active shifts down 1px, and focus is the 2.5px focus-blue outline offset 2px. Disabled is 45% opacity.
- **Round:** 44px circle for the play control.

### Chips
- **Style:** 2px corners, 800 12.5px uppercase with 0.04em tracking, verdict text on its pale tint. Used for decisions in the systems table: accept (green), clarify (ochre), escalate (violet), and wrong execution (oxide).

### Inputs / Fields
- **Style:** paper fill, 1.5px line-2 border, 4px corners, 48px tall, 500 15px. Hover darkens the border to ink-2. Placeholder is ink-3.
- **Focus:** the global focus-blue outline.

### Navigation
The masthead is an ink band: a 900-weight wordmark with a one-line purpose, a meter strip (label 12px over a 700 16px value) on the right, and a microtext rule on a darker underlay (#1d1740) at the bottom. There is no other navigation.

### Note (signature component)
A double-hairline panel on the note colour. From top to bottom: the **verdict band** (solid verdict fill, 800 15px title on the left, 600 13px reason on the right; blank and void bands use band-blank and ink-3), the **figure** (₹ at clamp(26px, 2.6vw, 36px) 700 beside the display amount), the **amount in words**, a **note line** (intent · account, with retracted amounts struck through in oxide) above a hairline, and the **signs** list. Each sign is a coloured dot plus a sentence. The confirmation lives inside the guard's note as its lower leaf, separated by a dashed hairline and set flush.

### Verification Seal (signature component)
A guilloché rosette drawn by code from hypotrochoid and epitrochoid curves (0.8px strokes, 2px ring) in two layers: an unengraved plate in line, and an inked copy revealed by a conic mask whose angle is the registered `--sweep` property (1.6s). The sweep angle follows the state: ask 216deg (60%) in ochre-ink, cleared 360deg in green, refer 108deg in violet, void 54deg in ink-3. The open wedge is the point, showing how much of the check is still owed. A letterspaced label below it takes the verdict colour. Size is clamp(108px, 9vw, 128px), or 96px on phones.

### See-through Register
A ghost copy of the figure in ochre-ink (multiply, 55%) sits 10px right and 6px up. When Prisma's words and digits agree, it slides into place and fades (0.9s). When they disagree, it stays offset and turns oxide.

### Evidence Dots
Dot diameter encodes evidence weight and nothing else. In the note's signs it runs from 10 to 24px (6 + 6w, clamped) in the decision's colour. In the checks list it is 9, 13 or 18px in ink, and passed checks show a green check icon. Hypothetical consequences take a uniform 8px dot and 500-weight ink-2 text so they never read as evidence.

### Route Diagram
A transit-line map on the note plate: 8px round-capped tracks in #ddd8ea, stations as 11px paper rings (17px interchange with an ink core at Decision). Segments light up in sequence (stroke-dashoffset, 0.7s). Branches take verdict colours (Bank green, Timbre ochre-ink, Human desk violet), the live station pings, and a segment waiting on Prisma marches with a dash. Below 560px it becomes a row of pill steps that fill with the same colours.

### Scale
A ruled log-percent scale (2px ink baseline, line-2 ticks every 2.5%), a dashed ochre-ink threshold labelled in ochre, and a 16px ink marker with a 3px ground halo that slides to the error estimate (0.9s).

### Motion
All motion uses one curve (`cubic-bezier(.16, 1, .3, 1)`) and each piece shows a check taking place: route trace (0.7s per segment), transcript words un-blur from 6px (0.6s), verdict band wipes in from the left (clip-path, 0.5s), changed digits flip on X (0.38s, staggered 90ms), register settles (0.9s), seal sweeps (1.6s), confirmation leaf drops 8px (0.5s), signs and checks rise 6px with stagger, new ledger rows flash ochre-bg (1.4s). `prefers-reduced-motion` reduces every animation and transition to 0.01ms, and app.js sets all pacing delays to zero.

## Do's and Don'ts

### Do:
- **Do** give every amount a 900-weight tabular figure with its value in letterspaced words underneath.
- **Do** keep verdict colours to the four meanings: ochre asks, green clears, oxide executed unchecked, violet refers.
- **Do** fill and stroke with ochre-ink, and set ochre text in the darker ochre (or ink on an ochre-ink band).
- **Do** frame note panels with the double hairline (1px line-2 plus an inset line 5px inside).
- **Do** separate major sections with a microtext rule, not a solid bar.
- **Do** use dot size only for evidence weight, with a uniform 8px mark for hypotheticals.
- **Do** make every motion show a check happening, and make sure it collapses under reduced motion.

### Don't:
- **Don't** use guilloché violet anywhere outside the seal.
- **Don't** use a verdict hue for decoration, branding or emphasis.
- **Don't** round containers beyond 4px. Round forms are for round objects, and pills only for the phone route steps.
- **Don't** add dark glowing panels, gradient glows, or a card grid. The world is printed paper.
- **Don't** treat microtext as readable content. It stays aria-hidden texture.
- **Don't** fade text with opacity to make it secondary. Step down through ink-2 and ink-3.
