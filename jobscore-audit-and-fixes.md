# Jobscore — code audit: problems, fixes applied, and what's still open

Scope: full review of the uploaded `JobScore` codebase (backend FastAPI + frontend Next.js). Each item below is a real bug or inconsistency found by reading the actual code, not a generic checklist. Items are grouped by severity. **FIXED** items were changed directly in the codebase during this session. **OPEN** items are described in enough detail to fix without re-auditing.

---

## 1. Critical — correctness bugs

### 1.1 "It's a match" didn't work reliably — FIXED
**File:** `backend/app/api/v1/candidate/swipe.py`, `backend/app/schemas/__init__.py`, `backend/app/services/application_service.py`

**What was wrong:** `POST /candidate/swipe` creates the `Match` + `Application` server-side when a right-swipe clears the threshold, but the response (`SwipeResponse`) only ever contained `id`, `direction`, `created_at` — nothing about whether a match happened. The frontend had no way to know, so it made a *second*, separate call to `GET /candidate/matches` after every right-swipe and guessed by scanning the list for the job ID (`frontend/app/(candidate)/feed/page.tsx`, old `handleSwipe`). This was slow (extra round trip on every swipe), racy (fired in the background via `.then()`, not awaited, so the modal could pop up while the user was already looking at the next card), and wasteful (fetches the candidate's *entire* match history on every single swipe).

**Fix applied:**
- `SwipeResponse` now includes `matched: bool`, `match_id`, `application_id`, `score`, `score_breakdown`.
- `application_service.create_application_on_match` returns `(match, application)` instead of just `match`.
- The swipe endpoint populates these fields directly in the same response, in the same transaction.
- Frontend `apiClient.swipe()` return type updated to `SwipeResponse`; `feed/page.tsx` now reads `res.matched` / `res.score` straight off the swipe response — no follow-up call, no polling.

**If revisiting:** don't reintroduce a second round trip to detect a match. Any UI that needs to show match state should get it from the action that caused it (the swipe response), not a subsequent list fetch.

---

### 1.2 Company/recruiter sessions silently downgraded on token refresh — FIXED
**File:** `backend/app/api/v1/auth.py`

**What was wrong:** `POST /auth/refresh` decoded the refresh token (which only carries `sub`, the user ID) and re-issued a new access token with **hardcoded `role="candidate"` and no `tenant_id`** — regardless of whether the original user was a candidate or a recruiter. The code's own comment admitted this: *"In production, look up the user to get fresh role/tenant claims"* — but never did it. Practical effect: any recruiter whose 30-minute access token expired and got refreshed would silently become an unauthenticated-for-company-routes "candidate," and every subsequent `/company/*` call would 403 until they logged out and back in. This is very likely the source of "backend doesn't work properly" complaints on the company side.

**Fix applied:** `/auth/refresh` now looks up the subject ID against both `Candidate` and `Recruiter` tables (same logic as `/login`) and reissues an access token with the **current, correct** role and tenant, not a guess. Also returns a clean 401 if the account no longer exists.

**If revisiting:** never encode role/tenant into a long-lived refresh token and never assume a default role when reissuing — always re-derive from the database so a permission change (e.g., recruiter removed from a company) takes effect on the very next refresh.

---

### 1.3 Frontend never actually called the refresh endpoint — FIXED
**File:** `frontend/lib/api-client.ts`

**What was wrong:** `apiClient.refreshToken()` existed but was **never called anywhere in the app** (confirmed via grep — zero call sites outside its own definition). Combined with 1.2, this meant every session — candidate or company — hard-died with 401s after 30 minutes with no recovery path. The only way out was a manual logout/login.

**Fix applied:** `request()` in `api-client.ts` now catches a 401, calls the refresh endpoint once, retries the original request with the new token, and only redirects to `/login` if the refresh itself fails. Concurrent 401s share a single in-flight refresh call (via a module-level promise) instead of each firing their own refresh and racing.

**If revisiting:** keep the single-in-flight-refresh guard — without it, five simultaneous 401s trigger five refresh calls, and whichever token lands last silently invalidates the others (most refresh-token schemes rotate the refresh token on use).

---

### 1.4 Swiped cards could reappear in the deck — FIXED
**File:** `frontend/components/swipe/SwipeDeck.tsx`, `frontend/app/(candidate)/feed/page.tsx`

**What was wrong:** `SwipeDeck` kept its own local `deck` state, initialized from the `jobs` prop and re-synced via `useEffect(() => setDeck(initialJobs), [initialJobs])`. Meanwhile the parent `FeedPage` also held its own `jobs` state, sliced it independently on swipe, and mutated it again for prefetching (`loadFeed(nextCursor)` appends more items, which is a new array reference). Every time the parent's `jobs` array changed reference — including on prefetch, which happens automatically once fewer than 4 cards remain — the effect fired and **overwrote the child's already-swiped-down deck with the full, unsliced list again**, resurfacing cards the user had already swiped on. There was also a second, parallel swipe path: the on-screen buttons and keyboard shortcuts called the parent's `handleSwipe` directly and sliced `jobs` themselves, bypassing `SwipeDeck`'s own slicing logic entirely — two different code paths mutating overlapping state.

**Fix applied:** `SwipeDeck` is now a fully controlled component with no local state — `jobs` from the parent is the only source of truth, and the parent removes a swiped card from `jobs` exactly once, in exactly one function (`handleSwipe`), used identically by drag gesture, buttons, and keyboard.

**If revisiting:** don't give a child component its own copy of state that's also owned by a parent and synced via `useEffect` on a prop — pick one owner. If a child needs local UI-only state (e.g., drag position), that's fine; list membership isn't UI-only state.

---

### 1.5 Feed had no relationship to the matching algorithm — FIXED
**File:** `backend/app/api/v1/candidate/feed.py`

**What was wrong:** `GET /candidate/feed` returned active, unswiped listings in plain chronological order (`ORDER BY created_at ASC`). It never ran `passes_hard_filters` or `compute_match_score`. Practical effect: a candidate in NYC with an on-site-only job requirement would see, and could right-swipe on, a fully remote-incompatible on-site role in a different city — burning one of their capped daily swipes on a card that was *always* going to fail Stage 1 the instant the swipe landed. The homepage's own copy calls this a "curated deck" — it wasn't curated at all.

**Fix applied:** the feed endpoint now loads the candidate, pulls a bounded window of active unswiped listings, runs `passes_hard_filters` on each, scores the survivors with `compute_match_score`, and returns them sorted by predicted score (highest first). Pagination changed from a timestamp cursor to an offset-into-the-ranked-list cursor, since ranked order isn't stable against `created_at`.

**Known limitation (documented, not fixed):** scoring happens in-memory per-request against up to 500 listings (`MAX_CANDIDATES_TO_RANK`). Fine for portfolio-scale data; at real scale this needs to move to precomputed scores (the existing Celery `recompute_matches_for_candidate`/`recompute_matches_for_job` tasks are a start, but they only update *existing* matches — they'd need to write a `predicted_score` onto a candidate/listing pair table so the feed query can `ORDER BY` it in SQL instead of scoring on the fly).

---

## 2. High — data quality / matching integrity

### 2.1 Resume parser fabricated data on failure — FIXED (removed)
**File:** `frontend/lib/resume-parser.ts` (deleted), `frontend/app/(candidate)/onboarding/page.tsx` (rewritten)

**What was wrong:** the "resume parser" was a from-scratch regex-based PDF text extractor — no real PDF library, just regex hunting for `Tj`/`TJ` PDF text-drawing operators and a printable-ASCII fallback. This is fragile against any PDF that isn't a very simple, uncompressed, text-based layout (most PDFs from Word/Google Docs/LaTeX export use compressed streams this regex approach can't decode at all). Worse: **on any extraction failure or empty skill match, it silently defaulted to `skills: ["React", "TypeScript", "Node.js"]`** and a fabricated summary sentence, then wrote that straight into the candidate's profile and embedding — with no indication to the candidate that their real skills weren't captured. Since embedding similarity is 50% of the match score, this alone could explain a meaningful share of "the matching algorithm is not working properly": a candidate with a design or backend-only background could silently get profiled as a generic React/TypeScript/Node candidate and matched against completely wrong listings.

**Fix applied:** `resume-parser.ts` deleted entirely. The onboarding page is now a plain preference form — summary, skills (tag input), years of experience, salary range, location, remote toggle — all typed in directly by the candidate, all validated before submit (non-empty summary of meaningful length, at least one skill, non-negative experience, salary-min ≤ salary-max, location-or-remote required), with **no pre-filled fake defaults**. Every field is empty until the candidate fills it in, and each field's comment in the code notes exactly which term of the matching score it feeds.

**If revisiting resume upload later:** if you want it back, do it server-side with a real PDF text-extraction library (e.g. `pdfplumber` or `pypdf` in Python) and always show the candidate the extracted fields for **manual review and correction** before saving — never auto-save unreviewed extracted data, and never fall back to a fabricated default skill set on failure. Show "we couldn't extract this — please fill it in" instead.

---

### 2.2 Company job-posting form pre-fills fake default values — OPEN
**File:** `frontend/app/(company)/jobs/new/page.tsx`

**What's wrong:** the new-job form initializes `skills` to `["TypeScript", "React", "Node.js"]`, `location` to `"San Francisco, CA"`, `salaryMin`/`salaryMax` to `130000`/`170000`, etc. These are meant as UI placeholders but are actually **live form state** — if a recruiter clicks "Publish" without touching those fields (easy to do, since they look like real values, not placeholder text), the listing gets created with fabricated requirements that don't reflect the actual job. This directly pollutes the matching algorithm from the company side, the same failure mode as 2.1 but on the other side of the marketplace.

**How to fix:** initialize `skills` to `[]`, and text/number fields to empty strings, exactly the same pattern used in the candidate onboarding rewrite (2.1). Use the `placeholder` attribute for example text ("e.g. San Francisco, CA") instead of a real initial value. Add the same category of validation as 2.1: at least one required skill, `salaryMin <= salaryMax`, and don't allow submit with default/unedited values.

---

### 2.3 Embedding-failure comment is misleading — OPEN
**File:** `backend/app/api/v1/candidate/profile.py` (line ~50–53), `backend/app/api/v1/company/jobs.py` (line ~50–52)

**What's wrong:** both places catch `(TimeoutError, RuntimeError)` around the embedding `encode()` call and silently `pass`, with a comment claiming *"embedding retry queued"* (`profile.py`) or *"embedding computed later by worker"* (`jobs.py`). **Nothing queues a retry.** If encoding fails, `profile_embedding`/`listing_embedding` stays `None` permanently — nothing else in the codebase ever revisits it. A candidate or job whose embedding failed to compute once will have `embedding_similarity` silently treated as `0.0` (or fall into the keyword-overlap fallback path in `matching_service.compute_match_score`) forever, with no visible error and no retry.

**How to fix:** either (a) fix the comment to be honest — "embedding failed; profile saved without one, matches for this candidate/listing will use the skill-overlap fallback until profile is edited again" — or (b) actually queue a retry: on catch, call a new Celery task (e.g. `retry_embedding_for_candidate.delay(candidate.id)` / `retry_embedding_for_job.delay(job.id)`) that retries `encode()` with backoff and writes the result once it succeeds. Option (b) is the real fix; option (a) is the minimum honesty fix if there's no time for (b) right now.

---

### 2.4 `/candidate/matches` has no pagination — OPEN
**File:** `backend/app/api/v1/candidate/swipe.py`, `get_matches` endpoint

**What's wrong:** returns the candidate's *entire* match history with an unfiltered `select(Match).where(Match.candidate_id == candidate_id)` — no `limit`, no cursor. The project's own design doc (Section 10, non-functional requirements) explicitly calls for cursor-based pagination on this exact endpoint. As a candidate accumulates matches over time this becomes a slow, unbounded response.

**How to fix:** add the same offset/cursor pattern used in the rewritten feed endpoint (or a `created_at`-based cursor, since match list order doesn't need re-ranking the way the feed does — chronological is fine here). Default `limit=20`, cap at 100, same as feed.

---

## 3. Medium — UI, homepage, fonts

### 3.1 Google Fonts loaded via manual `<link>` tags instead of `next/font` — OPEN
**File:** `frontend/app/layout.tsx`

**What's wrong:** fonts (Sora + DM Sans) are loaded via `<link rel="preconnect">` / `<link rel="stylesheet" href="https://fonts.googleapis.com/...">` tags in `<head>`. This is the pre-Next.js-13 way of loading fonts and has real costs: it's a render-blocking external request (extra DNS lookup + connection + download before text can render in the right typeface), causes flash-of-unstyled-text/layout shift, and doesn't get Next's automatic self-hosting/subsetting/`font-display` optimization.

**How to fix:**
```tsx
// app/layout.tsx
import { Sora, DM_Sans } from "next/font/google";

const sora = Sora({ subsets: ["latin"], weight: ["400","500","600","700","800"], variable: "--font-display" });
const dmSans = DM_Sans({ subsets: ["latin"], weight: ["300","400","500","600"], variable: "--font-body" });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sora.variable} ${dmSans.variable}`}>
      <body>...</body>
    </html>
  );
}
```
Remove the manual `<link>` tags entirely — the `--font-display` / `--font-body` CSS variables already used throughout `globals.css` don't need to change, since `next/font` outputs the same variable names via `.variable`.

---

### 3.2 Homepage is fabricated marketing copy + unmaintainable inline styles — OPEN
**File:** `frontend/app/page.tsx`

**What's wrong, two separate issues:**

1. **Fabricated stats.** The `STATS` array hardcodes `"93% Recruiter response rate"`, `"4.1× Faster time-to-offer"`, `"0 Spam applications"` as if they were real, measured numbers. There is no backing data anywhere in the codebase for these — they're invented placeholder copy that shipped as if real. For a portfolio piece this reads as dishonest the moment anyone asks "where's that 93% from?" — remove them or replace with something true and unverifiable-claim-free, e.g. product principles instead of fake metrics ("Every match shows its score breakdown," "Daily swipe cap, not unlimited spam").
2. **Every section uses `style={{ ... }}` inline**, despite Tailwind being installed in `package.json` and available project-wide. This is ~450 lines of one-off inline styles duplicating what should be a handful of reusable Tailwind utility classes or `globals.css` classes (the rest of the app, e.g. `.btn`, `.card`, `.swipe-card`, already uses a proper class-based design system — the homepage is the outlier). Inline styles here mean: no responsive breakpoints without manual media-query juggling, no hover states without separate `onMouseEnter` handlers (several are already missing), and any future design-token change (e.g. adjusting `--radius-card`) has to be hunted down across scattered inline objects instead of one CSS rule.

**How to fix:** rewrite `page.tsx` using the existing `globals.css` class system (extend it with a few new classes — `.hero`, `.hero__stats`, `.how-it-works`, `.feature-grid` — following the same naming convention already used for `.swipe-card`, `.dashboard-grid`, etc.) or migrate to Tailwind utility classes directly in JSX, but pick one approach and use it consistently — not per-element inline style objects. Also update the copy that still says *"Upload your resume in under 60 seconds"* and *"Drop a PDF. We semantically parse every skill…"* in the "How it works" section — this describes the resume parser that no longer exists (removed in 2.1); update the three "How it works" steps to describe the new preference-form flow instead.

---

### 3.3 Company `candidate_feed.py` filename is a leftover from an earlier design — OPEN
**File:** `backend/app/api/v1/company/candidate_feed.py`

**What's wrong:** this file correctly implements the *current* auto-match/no-company-swipe model (`list_applications`, `update_application_status`) — the logic is right. But the filename and module name are a holdover from an earlier design where the company browsed and swiped on a feed of candidates. This is purely a naming inconsistency, not a functional bug, but it's confusing for anyone navigating the codebase (a new contributor would reasonably expect this file to contain a candidate-swiping feed, not an applications list).

**How to fix:** rename `backend/app/api/v1/company/candidate_feed.py` → `backend/app/api/v1/company/applications.py`, and update the import in `backend/app/api/v1/__init__.py` (wherever the router is registered) accordingly. No route paths or logic need to change — only the filename and its import.

---

## 4. Lower priority — worth doing, not urgent

### 4.1 JWTs stored in `localStorage`
**File:** `frontend/lib/api-client.ts`

Access and refresh tokens are stored in `localStorage`, which is readable by any JS running on the page — an XSS vulnerability anywhere in the app (including a third-party script) can exfiltrate both tokens. The more defensible pattern is an httpOnly cookie set by the backend, which JS can't read at all. This is a bigger structural change (cookie-based auth needs CORS/`SameSite`/CSRF handling on the backend) — reasonable to defer for a portfolio project, but worth a one-line note if this ever handles real user data.

### 4.2 `passes_hard_filters` location matching is a brittle exact string match
**File:** `backend/app/services/matching_service.py`

Location hard-filtering does `c_loc.lower().strip() != j_loc.lower().strip()` — so a candidate who typed `"NYC"` will never match a listing that says `"New York, NY"`, even though they mean the same place. Fine as a first pass, but worth normalizing against a small metro-alias table or geocoding lookup if location mismatches keep silently filtering out otherwise-good matches.

### 4.3 `application_service.create_application_on_match` uses `datetime.now(...).isoformat()` for a column that could be a real timestamp type
**File:** `backend/app/models/match.py`, `backend/app/services/application_service.py`

`Match.matched_at` is stored as a plain string column (`mapped_column(nullable=True)` with no type = defaults to inferred string), populated with an ISO-formatted string, instead of a proper `DateTime` column. Works, but loses the ability to do date-range queries/sorting at the SQL level without string comparison tricks. Worth switching to `DateTime(timezone=True)` in a future migration if `matched_at` needs to be queried or sorted on later.

---

## Summary table

| # | Issue | Severity | Status |
|---|---|---|---|
| 1.1 | Swipe response didn't report match result | Critical | **Fixed** |
| 1.2 | Token refresh reset role/tenant to defaults | Critical | **Fixed** |
| 1.3 | Frontend never called refresh endpoint | Critical | **Fixed** |
| 1.4 | Swiped cards could reappear (deck state desync) | Critical | **Fixed** |
| 1.5 | Feed ignored the matching algorithm entirely | Critical | **Fixed** |
| 2.1 | Resume parser fabricated skills on failure | High | **Fixed (removed)** |
| 2.2 | Job-post form pre-fills fake values | High | Open |
| 2.3 | Embedding-failure comment is false ("retry queued") | High | Open |
| 2.4 | `/candidate/matches` has no pagination | High | Open |
| 3.1 | Fonts loaded via manual `<link>` instead of `next/font` | Medium | Open |
| 3.2 | Homepage: fabricated stats + inline-style sprawl + stale copy | Medium | Open |
| 3.3 | `candidate_feed.py` filename stale vs. current design | Medium | Open |
| 4.1 | JWTs in localStorage (XSS exposure) | Low | Open |
| 4.2 | Location hard filter is brittle exact-match | Low | Open |
| 4.3 | `matched_at` stored as string, not `DateTime` | Low | Open |
