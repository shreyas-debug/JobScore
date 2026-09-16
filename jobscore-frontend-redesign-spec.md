# Jobscore frontend — redesign spec (minimal, beige, no dark mode)

Scanned the current repo (`JobScore/frontend`). This doc is instructions only — nothing in the repo was changed. Every section names the exact file(s) to edit. Feed this to Cursor section by section, or all at once.

---

## 0. Ground rules to apply everywhere

- **No dark mode.** Delete every dark-theme color value (`#090B10`, `#11141D`, `#1A1F2C`, etc.) — there should be one theme, not a light/dark toggle and not a dark default.
- **No em dashes ("—") anywhere** — not in UI copy, not in metadata, not in placeholder text. Straight sentences, or a period/colon instead. Exact locations found (search for `—` to catch anything added later, but these are the current ones):
  - `app/layout.tsx:13` — metadata description: `"...why you matched — no black boxes."` → rewrite without the dash.
  - `app/page.tsx:11` (`title`) and `:165`, `:280`, `:378` — hero/feature copy.
  - `app/(candidate)/onboarding/page.tsx:169` and `app/(candidate)/profile/page.tsx:192` — skill input placeholder text.
  - `app/(company)/dashboard/page.tsx:43` — fallback character for a missing average score (`"—"`); replace with `"N/A"` or `"–"` is still a dash, use `"Not enough data"` or similar plain text.
  - Also check every file's comments if you're doing a repo-wide pass, but comments aren't user-facing — prioritize the above, which are all real UI text.
- **Cut copy density everywhere**, not just the homepage — one clear sentence beats three. Apply this rule as you touch each file below.

---

## 1. Design tokens — `app/globals.css` (lines 1–41, the `:root` block)

Replace the entire dark palette with a warm, beige, light-mode-only system. Suggested concrete values (adjust to taste, but keep this structure — one accent, one warm neutral scale, no glow/neon effects):

```css
:root {
  /* Backgrounds — warm beige, not white */
  --color-bg: #F5F1E8;
  --color-surface: #FFFFFF;
  --color-surface-elevated: #FFFFFF;
  --color-border: rgba(43, 38, 32, 0.10);
  --color-border-hover: rgba(43, 38, 32, 0.20);

  /* Accent — pick one warm, muted tone instead of the current neon blue */
  --color-accent: #C1633D;        /* muted terracotta */
  --color-accent-light: #D68A67;
  --color-accent-subtle: rgba(193, 99, 61, 0.10);

  --color-success: #4A7C59;
  --color-danger: #B94A3D;
  --color-warning: #C08A2E;

  /* Text — warm dark brown, never pure black */
  --color-text: #2B2620;
  --color-text-muted: #6B6355;
  --color-text-dim: #A39A87;

  --font-display: var(--font-display), system-ui, sans-serif;
  --font-body: var(--font-body), system-ui, sans-serif;

  --radius-card: 14px;
  --radius-pill: 9999px;

  /* Soft, flat shadows — no glow effects, no colored box-shadows */
  --shadow-card: 0 1px 2px rgba(43, 38, 32, 0.04), 0 4px 16px rgba(43, 38, 32, 0.06);
  --shadow-sm: 0 1px 3px rgba(43, 38, 32, 0.06);
}
```

Delete `--shadow-glow`, `--color-accent-glow`, `--color-teal*`, `--color-gold` and every rule elsewhere in the file (and in `.tsx` files) that references them — grep for `glow` and `teal` across `app/` and `components/` and remove those effects; they belong to the old dark neon aesthetic, not a beige minimal one.

**Also add a shared transition token** so animation timing is consistent instead of ad hoc per-component values (see Section 6):
```css
:root {
  --ease-standard: cubic-bezier(0.2, 0.8, 0.2, 1);
  --duration-fast: 150ms;
  --duration-base: 250ms;
  --duration-slow: 400ms;
}
```

---

## 2. Fonts — `app/layout.tsx`

Fonts are already loaded correctly via `next/font/google` (Outfit for display, Inter for body) — don't touch that mechanism. What to change is the pairing itself, since Outfit/Inter reads as generic SaaS-dark-mode rather than warm/minimal/beige:

```tsx
import { Fraunces, Inter } from "next/font/google";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-display",
});
const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-body" });
```

Fraunces (a warm serif) for headings + Inter for body is a common, well-tested pairing for exactly this beige/editorial/minimal look. Update the `className` on `<html>` to use `fraunces.variable` instead of `outfit.variable`. Also fix the em-dash in `metadata.title` / `metadata.description` on lines 11–13 per Section 0.

---

## 3. Homepage — `app/page.tsx` (currently 503 lines)

This file is the single biggest offender for "too much text" and "not minimal": 5 sections (hero, rotating-role hero copy, a stats row, a "how it works" section, a "why Jobscore" feature grid, and a closing CTA banner), almost every element styled with a one-off inline `style={{...}}` object instead of shared classes, plus decorative radial-gradient glow blobs (lines 57–84) that belong to the old dark theme.

**Cut, don't just restyle:**
- Delete the `STATS` array (lines 14–18) entirely — `"93% Recruiter response rate"`, `"4.1× Faster time-to-offer"`, `"0 Spam applications"` are fabricated numbers with no backing data anywhere in the codebase. Don't replace them with new invented numbers; either drop the stats row completely or replace it with 2–3 short factual product statements (e.g. "Every match shows its score breakdown", "One swipe cap per day, no spam applying").
- Cut the "how it works" and "why Jobscore" sections down to 3 short items each, one line of copy per item, no paragraph-length descriptions (current `desc` strings run 20+ words each — cut to under 10).
- Remove the two decorative radial-gradient blobs (lines 57–84) — on a flat beige background these read as dark-theme leftovers, not minimal.
- Remove the closing CTA gradient banner's colored background (`linear-gradient(135deg, rgba(59,130,246,...)`) — use a flat `--color-surface` card instead, consistent with the rest of the page.

**Structural fix:** move all the inline `style={{...}}` objects into `globals.css` as real classes (`.hero`, `.hero__eyebrow`, `.hero__stats`, `.how-it-works`, `.feature-grid`, `.cta-banner`) following the same naming convention the rest of the app already uses (`.swipe-card`, `.dashboard-grid`). This isn't just cosmetic — it's what makes "minimal" maintainable instead of 500 lines of one-off objects.

Target: under 200 lines total once the copy is cut and the styling is moved to CSS classes.

---

## 4. Feed cards — `components/swipe/SwipeCard.tsx`

Current card crams in: a company-avatar row, title + seniority badge, a location row with an inline "Remote OK" badge, a boxed salary callout, the *full* job description text, up to 6 skill tags, and a bottom hint row — all separately inline-styled. That's a lot of visual weight for a card meant to be scanned in 2–3 seconds.

**Cut for minimalism:**
- **Truncate the description** to ~2 lines with `-webkit-line-clamp: 2; overflow: hidden;` instead of showing the full text (lines 140–144) — full detail belongs on a "view details" expand, not the swipe card itself.
- **Merge the salary box into the header row** instead of a separate bordered callout box (lines 132–137) — one line, not a whole section: `$120k – $150k · Remote OK` next to the title, not a separate boxed element.
- **Cap skill tags at 4, not 6** (line 153), and drop the "+N more" tag styling flourish — just `+3` in muted text.
- **Drop the bottom "← Pass / Express Interest →" hint row** (lines 168–182) once the swipe gesture and the on-screen buttons already communicate this — redundant text on every single card adds up over a long swipe session.
- Replace every inline `style={{...}}` in this file with classes in `globals.css` (`.swipe-card__company-row`, `.swipe-card__meta`, etc.) — same reasoning as Section 3.

**Card shape:** on the beige theme, give the card a plain white surface (`--color-surface`), a hairline border (`--color-border`), and the flat `--shadow-card` from Section 1 — no gradient avatar badges (line 81 uses `linear-gradient(135deg, var(--color-accent), var(--color-teal))`, which won't exist anymore once `--color-teal` is removed). Use a flat, single-color avatar background instead.

---

## 5. Animation pass — apply across the app, not just the feed

Current animation exists in exactly one place (`SwipeCard`'s drag/spring physics) and nowhere else — buttons, page loads, and modals have zero transition. For "better animations across everywhere":

- **Buttons**: add a `transition: transform var(--duration-fast) var(--ease-standard), opacity var(--duration-fast)` to `.btn` in `globals.css`, plus a `:active { transform: scale(0.97); }` — every button press should have a tiny bit of give.
- **Cards entering a list** (matches list, jobs list, dashboard funnel): wrap list items in `framer-motion`'s `<motion.div initial={{opacity:0, y:8}} animate={{opacity:1, y:0}} transition={{duration:0.25, ease:[0.2,0.8,0.2,1]}}>` so they fade/slide in instead of popping in instantly — apply to `app/(candidate)/matches/page.tsx`, `app/(company)/jobs/page.tsx`, `app/(company)/jobs/[id]/candidates/page.tsx`.
- **Modals** (match popup, any future dialog): wrap in `<AnimatePresence>` + `<motion.div>` with a scale+fade entrance (`initial={{opacity:0, scale:0.95}}`, `animate={{opacity:1, scale:1}}`) instead of the current instant-appear `.modal-overlay` / `.modal-content` divs in `feed/page.tsx` (lines 220+).
- **Page-level transitions**: consider a shared `<motion.main>` wrapper (fade-in on mount) at the layout level in `app/layout.tsx` so every route transition has a consistent, subtle fade rather than a hard cut.
- Keep every animation duration inside 150–400ms (use the tokens from Section 1) — minimal design reads as sluggish fast if animations run long.

---

## 6. "It's a match" popup — `app/(candidate)/feed/page.tsx` (lines ~220–250)

Current modal shows: a bouncing emoji, an "It's a Match!" heading, a full sentence naming the job title and stating the application was auto-submitted, plus two buttons ("Keep Swiping" / "View Match Breakdown"). Simplify drastically per the ask — **the popup should say only that it's a match**, nothing else:

- Strip the modal down to: a checkmark or heart icon, and the words **"It's a match"** (or "It's a match!" if you want the exclamation) — no job title, no score, no explanatory sentence.
- Auto-dismiss it after ~1.2–1.5 seconds (`setTimeout(() => setMatchCelebration(null), 1300)`) instead of requiring a click, since there's nothing left to read or decide — this also means you can drop both buttons.
- Keep it small and centered, not a large full card — this is a toast/confirmation, not a page.
- The detail that used to live in this popup (job title, score, "why") now belongs entirely in the Matches tab (Section 7) — that's where someone goes to actually look at it, not in a popup they'll see for a second and dismiss.

---

## 7. Matches tab — `app/(candidate)/matches/page.tsx` + `components/match/MatchScoreBreakdown.tsx`

Current behavior: a flat list of match cards showing score % and job title (with a raw `Listing ID: xxxxxxxx…` line as filler — replace with the company name, which is already available on `job.company_name` per `lib/types.ts`'s `JobCard` interface). Clicking "See Why" **replaces the entire view** with the breakdown component and a "back" button.

**Change to an inline expand, company-first:**
- Each row's primary line should be the **company name** (`m.job?.company_name` — verify this matches whatever field name the actual `/candidate/matches` response uses; the type in `lib/types.ts` currently has both `job?: JobCard` and a looser `job_listing?: any` for the same data — pick one field consistently across the codebase instead of keeping both), with the job title as a secondary line underneath, not the other way around.
- Remove the `Listing ID: {slice}…` line (line 136) entirely — it's internal debugging text, not something a candidate needs to see.
- Replace the current full-page-replace pattern (the `selected ? <MatchScoreBreakdown /> : <list>` ternary, lines 82–151) with an **inline accordion**: clicking a row expands `<MatchScoreBreakdown>` directly underneath that row (animate the expand/collapse with `framer-motion`'s `<motion.div animate={{height: expanded ? "auto" : 0}}>` or a simple `AnimatePresence`), while the rest of the list stays visible and scrollable. Track expanded state as `expandedId: string | null` instead of a single `selected` breakdown object, so switching between which match is expanded doesn't require a full "back" navigation.
- Keep `MatchScoreBreakdown.tsx` itself largely as-is (the score-bar breakdown by component is good content) — just restyle it to the beige palette (it currently has no hardcoded dark colors, so this should mostly flow through once `globals.css` tokens change) and make sure it fits visually inside a collapsed row rather than as a standalone full-width page section.

---

## 8. Login & signup — `app/login/page.tsx`, `app/register/candidate/page.tsx`, `app/register/company/page.tsx`

All three currently share the same pattern: a centered card on the dark background, a gradient icon badge with a box-shadow glow (login page lines 38–53), heavy inline styling throughout. To match the new beige/minimal system:

- Replace the glowing gradient icon badge with a flat, simple mark — either just the wordmark text (`Job` + accent-colored `score`, matching the navbar logo treatment) or a plain single-color icon container with no `boxShadow` glow.
- Card surface: white (`--color-surface`) on the beige page background, hairline border, flat `--shadow-card` — remove any dark-theme-specific `boxShadow` values.
- Error states (e.g. login page lines 67–81, invalid-credentials banner) should use `--color-danger` at a light background tint consistent with the new palette, not the current `rgba(239, 68, 68, 0.12)` hardcoded dark-theme value.
- Apply the same entrance animation as Section 5 (fade + slight upward motion on mount) to the card so the auth pages don't feel static compared to the rest of the redesigned app.
- Move the inline `style={{}}` objects in all three files into shared classes (`.auth-card`, `.auth-icon`, `.auth-footer-links`) — they're nearly identical between the three pages, so one shared CSS block covers all of them instead of three copies of inline styles.

---

## 9. Loading performance

A few concrete, low-risk wins:

- **Feed page** (`app/(candidate)/feed/page.tsx`): the initial loading state is a full-page centered spinner/text block that blocks everything until the first `getFeed()` call resolves. Replace with a **skeleton card** (a gray/beige placeholder shaped like `SwipeCard`) rendered immediately, swapped for the real card once data arrives — this doesn't make the network call faster, but it removes the blank-screen perception of slowness, which is most of what "loading time should be faster" is actually about for a swipe UI.
- **Matches / jobs / dashboard pages**: same pattern — replace `<p>Loading…</p>` placeholders with skeleton rows matching the eventual layout.
- **Framer Motion import weight**: confirm `framer-motion` is only imported where actually used (`SwipeCard.tsx`, and wherever Section 5's animations get added) — don't import it in files that don't animate anything, since it's one of the heavier client-side dependencies in this app.
- **Font weights**: the current `next/font` config pulls multiple weights per family; only request the weights actually used in the CSS (check `globals.css` for every `font-weight` value used and trim the `weight: [...]` array in `layout.tsx` to match — fewer weights means a smaller font payload).
- **Images**: if any company logos or avatars get added later, use `next/image`, not a plain `<img>`, so they're automatically sized/optimized.

---

## Summary checklist

- [ ] `globals.css`: replace dark palette with beige/terracotta tokens, add transition tokens, remove glow/teal remnants
- [ ] `layout.tsx`: swap Outfit → Fraunces for display font, fix em-dash in metadata
- [ ] `page.tsx`: cut fabricated stats, shorten all section copy, remove dark-theme gradient decoration, move inline styles to classes
- [ ] `SwipeCard.tsx`: truncate description, merge salary into header, cap skills at 4, drop bottom hint row, move inline styles to classes
- [ ] Add entrance/exit animation to buttons, list items, modals, and auth cards via shared `--duration`/`--ease` tokens
- [ ] `feed/page.tsx`: simplify match modal to "It's a match" only, auto-dismiss, no extra text/buttons
- [ ] `matches/page.tsx`: company name as primary line, inline accordion expand instead of full-view replace, drop the raw listing-ID line
- [ ] `login/page.tsx`, `register/*/page.tsx`: flat beige card styling, no glow effects, shared auth classes
- [ ] Replace blocking full-page loading states with skeleton placeholders on feed/matches/jobs/dashboard
- [ ] Repo-wide: remove every em dash in user-facing copy (see Section 0 for exact locations found)
