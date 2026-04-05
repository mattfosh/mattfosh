# Community Forum Platform — Implementation Plan

**Spec**: `docs/superpowers/specs/2026-04-02-community-forum-design.md`

## Context

We designed a community forum platform to be built as a Venus-native AstroJS product with a Venus BFF vertical. During design review, the stakeholder identified a critical insight: **before investing in the full Venus integration, we should prototype the UX with lightweight tools** (Supabase + Vercel) to validate the design and gather feedback. This plan reflects that phased approach.

Key constraints from design review:
- SEO is a big deal — best practices from day 1
- Moderation needs a proper admin tool (not just in-forum moderation)
- Search in mock phase should be a collector (track what users search for) not full-text
- Elasticsearch exists only for Graylog logging — not available for app search
- Backend team timeline is an open discussion — plan must work regardless of when they start
- Figma design system exists but may not have community-specific designs yet

---

## Phase 0: Rapid Prototype (Supabase + Vercel)

**Goal**: Get a working, clickable prototype in front of stakeholders and test users FAST. Validate the design, information architecture, and core UX before touching Venus or the BFF.

### Step 0.1 — Project Setup
- Create a new Next.js (or Astro) project
- Deploy to Vercel
- Connect Supabase as the backend (auth, database, real-time)
- Set up shadcn/ui + Tailwind (same design system target as Venus)

### Step 0.2 — Supabase Schema
Create tables in Supabase:
```sql
-- Categories
categories (id, name, slug, description, sort_order, icon, created_at)

-- Threads
threads (id, category_id, author_id, title, slug, body, is_pinned, is_locked, view_count, reply_count, last_reply_at, created_at, updated_at)

-- Replies
replies (id, thread_id, author_id, body, is_flagged, created_at, updated_at)

-- User profiles (extends Supabase auth)
profiles (id, username, display_name, avatar_url, bio, join_date, post_count)

-- Flags (moderation)
flags (id, flagged_by, content_type, content_id, reason, status, reviewed_by, created_at)

-- Search log (collector)
search_log (id, user_id, query, results_count, created_at)
```

### Step 0.3 — Core Pages (shadcn/ui)
Build using shadcn/ui components to match the target Venus design system:

| Page | Route | Description |
|---|---|---|
| Forum home | `/community` | Category list with thread counts, latest activity |
| Category view | `/community/:category` | Thread list with sorting (latest, popular, unanswered) |
| Thread view | `/community/:category/:thread` | Thread + replies, reply form, flag button |
| Create thread | `/community/new` | Title, category selector, rich text body |
| User profile | `/community/user/:username` | Activity history, post count, join date |
| Search | `/community/search` | Search input + results (logs all queries) |

### Step 0.4 — SEO Foundation
- Server-side rendering for all forum pages
- Proper meta tags (title, description, og:tags)
- Semantic HTML (`<article>`, `<nav>`, `<main>`, `<time>`)
- Structured data (JSON-LD for DiscussionForumPosting)
- Sitemap generation for categories and threads
- Canonical URLs
- Breadcrumb navigation

### Step 0.5 — Basic Moderation Admin
- Separate `/admin` section (or Supabase dashboard for MVP)
- View flagged content queue
- Actions: hide post, warn user, ban user
- Track: who flagged, reason, resolution

### Step 0.6 — User Testing & Feedback
- Deploy prototype to a staging URL
- Share with internal stakeholders and selected test users
- Collect feedback on:
  - Information architecture (are categories right?)
  - Navigation flow (can users find what they need?)
  - Posting experience (is creating a thread/reply intuitive?)
  - Search behavior (what do people try to search for? — log analysis)
  - Mobile experience
- Iterate on design based on feedback

### Step 0.7 — Extract Design Decisions
Capture what was learned:
- Final category structure
- Component inventory (which shadcn/ui components were used, any custom ones)
- UX patterns that worked / didn't work
- Search query patterns from the collector
- SEO baseline metrics
- Moderation workflow findings

**Exit criteria for Phase 0**: Stakeholder sign-off on the prototype UX. Design decisions documented. Ready to build in Venus.

---

## Phase 1: Venus BFF — Community Vertical (Mock Data)

**Goal**: Build the BFF service contracts and mock data layer so the Venus frontend team can develop against real WebSocket services.

**Repo**: Venus BFF

### Step 1.1 — ServiceMap & Entities

Update `src/shared/types/serviceMap.ts`:
```typescript
type ServiceMap = {
  // ... existing
  community:
    | 'forum/listCategories'
    | 'forum/getThreads'
    | 'forum/getThread'
    | 'forum/createThread'
    | 'forum/createReply'
    | 'forum/searchThreads'
    | 'moderation/flagPost'
    | 'moderation/getQueue'
    | 'moderation/reviewFlag'
    | 'user/getProfile'
    | 'user/getActivity';
};
```

Create Zod schemas in `src/modules/community/entities/`:
- `category.schema.ts` — Category, CategoryList
- `thread.schema.ts` — Thread, ThreadList, CreateThreadParams
- `reply.schema.ts` — Reply, ReplyList, CreateReplyParams
- `flag.schema.ts` — Flag, FlagList, FlagPostParams, ReviewFlagParams
- `user-profile.schema.ts` — CommunityUserProfile, UserActivity
- `search.schema.ts` — SearchParams, SearchResults
- `pagination.schema.ts` — PaginationParams, PaginatedResponse

### Step 1.2 — Mock Data Repository

Create `src/repository/community/`:
- `mock-data/categories.json` — seeded from Phase 0 findings
- `mock-data/threads.json` — realistic sample threads
- `mock-data/replies.json` — sample replies
- `mock-data/profiles.json` — test user profiles
- `community-api.ts` — mock adapter that reads JSON, supports filtering/pagination/sorting in-memory
- `search-collector.ts` — logs search queries (writes to a file or in-memory array for analysis)

### Step 1.3 — Controllers

Create `src/controllers/community/` following BFF conventions:
- `forum/list-categories.ts` — `@community/forum/listCategories`
- `forum/get-threads.ts` — `@community/forum/getThreads` (params: categoryId, page, sort)
- `forum/get-thread.ts` — `@community/forum/getThread` (params: threadId)
- `forum/create-thread.ts` — `@community/forum/createThread` (params: categoryId, title, body)
- `forum/create-reply.ts` — `@community/forum/createReply` (params: threadId, body)
- `forum/search-threads.ts` — `@community/forum/searchThreads` (params: query, page)
- `moderation/flag-post.ts` — `@community/moderation/flagPost` (params: contentType, contentId, reason)
- `moderation/get-queue.ts` — `@community/moderation/getQueue` (params: status, page)
- `moderation/review-flag.ts` — `@community/moderation/reviewFlag` (params: flagId, action)
- `user/get-profile.ts` — `@community/user/getProfile` (params: userId)
- `user/get-activity.ts` — `@community/user/getActivity` (params: userId, page)

Each controller:
- Registers via `serviceFactory.createService()`
- Validates params with Zod schema via `validateParams()`
- Calls module service
- Returns via `buildResponse()`

### Step 1.4 — Module Services

Create `src/modules/community/services/`:
- `forum/list-categories.ts`
- `forum/get-threads.ts`
- `forum/get-thread.ts`
- `forum/create-thread.ts`
- `forum/create-reply.ts`
- `forum/search-threads.ts`
- `moderation/flag-post.ts`
- `moderation/get-queue.ts`
- `moderation/review-flag.ts`
- `user/get-profile.ts`
- `user/get-activity.ts`

Each service calls the repository mock adapter via `safeAsync()`.

### Step 1.5 — Service Registration & Config

- Export all controllers in `src/controllers/community/index.ts`
- Register in main `src/controllers/index.ts`
- Add to low-latency services array in CD config:
  ```yaml
  VENUS_BFF_LOW_LATENCY_SERVICES: '["@community/forum/listCategories", "@community/forum/getThreads", "@community/forum/getThread", "@community/forum/createThread", "@community/forum/createReply", "@community/forum/searchThreads", "@community/moderation/flagPost", "@community/moderation/getQueue", "@community/moderation/reviewFlag", "@community/user/getProfile", "@community/user/getActivity"]'
  ```

### Step 1.6 — Tests

Jest tests for all services (80%+ coverage):
- Schema validation tests (valid/invalid params)
- Service tests with mock repository
- Controller integration tests
- Response format verification (matches `ServiceResult` interface)

**Exit criteria for Phase 1**: All `@community/*` services respond over WebSocket with mock data. Tests pass at 80%+. BFF contracts documented.

---

## Phase 2: Venus Product — Community AstroJS App

**Goal**: Build the community as a new AstroJS product in the Venus monorepo, consuming the BFF services from Phase 1.

**Repo**: Venus (monorepo)

### Step 2.1 — Product Scaffolding

Create `products/community/` following existing Venus product patterns (copy structure from an existing product like `homepage` or `casino`):
- AstroJS config (server mode)
- Tailwind CSS + shadcn/ui setup
- Product Shell integration
- Config Manager integration (brand: betonline)
- Sceptor client setup (WebSocket connection to BFF)

### Step 2.2 — Brand Configuration

Create config files following Config Manager pattern:
- `config/default/community.json` — shared defaults (feature flags, pagination limits)
- `config/betonline/community.json` — BetOnline-specific (categories, branding tokens, enabled features)

### Step 2.3 — Pages & Routing

Mount as Express middleware at `/community`:
- `/community` — Forum home (category list)
- `/community/:category` — Category view (thread list)
- `/community/:category/:thread` — Thread view (thread + replies)
- `/community/new` — Create thread form
- `/community/user/:username` — User profile
- `/community/search` — Search with query collector
- `/community/admin/moderation` — Moderation queue (auth-gated)

### Step 2.4 — React Components (shadcn/ui)

Build community-specific components using shadcn/ui:
- `CategoryCard` — card with icon, name, thread count, latest activity
- `CategoryList` — grid/list of CategoryCards
- `ThreadListItem` — thread title, author, reply count, last activity
- `ThreadList` — sortable list with pagination
- `ThreadView` — full thread with body, metadata, actions
- `ReplyCard` — individual reply with author, timestamp, flag button
- `ReplyList` — chronological list of replies
- `ReplyForm` — rich text editor for posting replies
- `CreateThreadForm` — title input, category selector, body editor
- `UserProfileCard` — avatar, username, stats, join date
- `UserActivityFeed` — list of user's posts and replies
- `SearchBar` — search input with results dropdown
- `SearchResults` — full search results page
- `ModerationQueue` — flagged content list with actions
- `ForumBreadcrumbs` — navigation breadcrumbs
- `Pagination` — reusable pagination component

### Step 2.5 — SEO Implementation

Carry forward SEO patterns from Phase 0 prototype:
- Server-side rendering (Astro SSR mode)
- Meta tags via Astro `<head>` management
- JSON-LD structured data for `DiscussionForumPosting`
- Sitemap integration with Venus prerender service (Varnish)
- Canonical URLs with proper slugs
- Breadcrumbs with Schema.org markup
- OpenGraph tags for social sharing

### Step 2.6 — Moderation Admin Panel

Dedicated admin section at `/community/admin/`:
- Auth-gated (Keycloak roles — require moderator/admin role)
- Moderation queue: flagged posts/replies with context
- Actions: hide, warn, ban, dismiss flag
- Activity log: moderation actions taken
- Brand-scoped: admin sees only their brand's content (Config Manager)

### Step 2.7 — Integration Testing

- End-to-end flow: browse categories → open thread → post reply
- Auth flow: login → create thread → see it in profile
- Moderation flow: flag post → appears in admin queue → take action
- SEO validation: check meta tags, structured data, sitemap
- Multi-brand: verify Config Manager loads correct brand config

**Exit criteria for Phase 2**: Community product running in Venus dev environment, consuming BFF mock data. All core flows working. SEO validated. Moderation admin functional.

---

## Phase 3: Backend Transition (When Community API is Ready)

**Goal**: Swap mock data for real API in the BFF repository layer.

### Step 3.1 — Hand Off BFF Contracts

Provide backend team with:
- All Zod schemas (these ARE the API contract)
- Mock data samples (expected response shapes)
- Service list with params and response types
- Pagination convention
- Error code expectations

### Step 3.2 — Swap Repository Layer

In `src/repository/community/community-api.ts`:
- Replace mock data reads with `httpService.get/post()` calls to the real Community API
- Validate responses with existing Zod schemas via `safeAsync()`
- Error handling via `buildResponse()` — no changes needed

### Step 3.3 — Verification

- Run all existing BFF tests — should pass with real API
- Verify response shapes match the schemas
- Performance testing: response times under load
- Frontend verification: no changes needed, just confirm it works

---

## Verification Plan

### Phase 0 Verification
- Deploy prototype to Vercel staging URL
- Manual testing of all flows on desktop + mobile
- Lighthouse audit for SEO score
- Review search collector logs
- Stakeholder demo and feedback session

### Phase 1 Verification
- `npm run test` — all community service tests pass
- `npm run coverage` — 80%+ coverage on community modules
- `npm run typecheck` — no TypeScript errors
- `npm run lint` — no lint errors
- Manual WebSocket testing: connect and call each `@community/*` service

### Phase 2 Verification
- `yarn test` — product tests pass
- `yarn build` — builds without errors
- Dev server: navigate all routes, verify data loads from BFF
- Lighthouse SEO audit: score 90+
- Structured data testing tool: validate JSON-LD
- Auth flow: verify Keycloak integration
- Config Manager: verify brand-specific config loads
- Cross-browser: Chrome, Firefox, Safari, mobile

---

## Summary

| Phase | What | Where | Depends On |
|---|---|---|---|
| **0: Prototype** | Supabase + Vercel + shadcn/ui rapid prototype | New standalone repo | Nothing — start immediately |
| **1: BFF Vertical** | `@community/*` services with mock data | Venus BFF repo | Phase 0 learnings (category structure, data shapes) |
| **2: Venus Product** | AstroJS community product with shadcn/ui | Venus monorepo | Phase 1 (BFF services available) |
| **3: Backend Swap** | Replace mock repository with real API calls | Venus BFF repo | Backend team delivers Community API |
