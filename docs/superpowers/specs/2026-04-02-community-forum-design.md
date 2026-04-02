# Community Forum Platform — Design & Decision Record

## Context

A request was made to add a community engagement platform to the company's existing betting/casino website, inspired by stake.com's community features. The initiative aims to improve retention (+75%), engagement (3x with gamification), and customer success through a value-first, community-led strategy.

The existing frontend platform is **Venus** — a monorepo powering multiple betting brands (BetOnline, Wild Casino, etc.) built on Express.js + AstroJS + React. The component library is currently MUI but is being migrated to **shadcn/ui** (Radix primitives + Tailwind CSS). The backend ecosystem includes Keycloak (auth), Strapi (CMS), a WebSocket-based BFF (Venus BFF via Sceptor v5), and multiple domain APIs (Gamint, Cashier, Bocato, etc.) deployed on Kubernetes via ArgoCD.

This document captures the brainstorming session, decisions made, and the recommended architecture for the MVP.

---

## 1. Original Request Summary

The original request described a comprehensive community platform with:

- **Forum** with 6 category groups (Welcome, Education, Support, Events, Discussion, Showcase)
- **Content framework** with 4 pillars: Educational (40%), Discussion (25%), Community (20%), Entertainment (15%)
- **Editorial calendar** with weekly schedules, monthly themes, and quarterly events
- **3-layer moderation** system: Automated, Community (trust levels), Human
- **Gamification**: points, badges (50+), levels (25), leaderboards
- **Community culture** guidelines with tiered enforcement
- **12-month rollout** across 3 phases: Foundation, Growth, Maturity
- **Staffing plan**: scaling from 3 FTE to 12 FTE + volunteers
- **Technology**: Discourse recommended ($300/mo), with integrations to Discord, Slack, Analytics, SendGrid
- **Year 1 targets**: 50,000 MAU, 12-15 min avg session, 45%+ 30-day retention, NPS >50

---

## 2. Discovery & Context Gathering

### 2.1 Existing Platform: Venus

Venus is a monorepo that powers multiple web apps representing different brands.

**Architecture (from C4 diagrams):**

- **App Shell** (Express.js): Entry point handling routing, config management, auth
- **Product Shell** (Astro, React, JS): Shared UI logic (layout, navigation)
- **Products** (AstroJS apps mounted as middleware):
  - Homepage
  - Casino
  - Sportsbook
  - My Account
  - VIP Rewards
  - SUP (Sportsbook Unified Platform)
- **Packages**: Component Catalog (MUI React), Config Manager, BEAT Integration (tracking), i18n client, Auth Service, Data Collections
- **External services**: Keycloak (auth), Forge (content BFF/reverse proxy), Venus CMS (Strapi), Prerender (Varnish), Venus BFF (Sceptor)
- **Backend APIs**: Bocato (campaigns), Cashier, Gamint (casino), Pulsar (messaging/streaming), Sportsbook APIs, RDD Diffusion (real-time), Customer API, Wallet API, Report API
- **Infrastructure**: CDN/WAF/WAAP (Cloudflare/Imperva), Kubernetes, ArgoCD, Jenkins, Nexus

**Tech stack**: Node 20.x, Yarn 4.x, Turborepo, AstroJS 4.x, React, MUI, Storybook

### 2.2 Venus BFF Architecture

The Venus BFF uses **Hexagonal Architecture** (Ports and Adapters) with Sceptor v5 WebSocket framework:

- **Controllers**: Service registration via `serviceFactory.createService()`. Named as `@<vertical>/<apiName>/<endpoint>`
- **Modules**: Business logic, entities (Zod schemas), helpers, services
- **Repository**: API calls via `httpService` (REST), validated with `safeAsync` + Zod schemas
- **Response format**: Standardized via `buildResponse()` — returns `{ clientSessionId, referenceId, result?, warning?, error? }`
- **Service types**: `RequestService` (request/response) and `LiveSubscription` (real-time polling)
- **Validation**: All params validated with Zod schemas via `validateParams()`
- **Service classification**: High-latency vs. low-latency, configured per brand in CD repo
- **Testing**: Jest, minimum 80% coverage

**Key pattern — the flow:**
```
WebSocket Message → Controller → Module (business logic) → Repository → Backend API
```

### 2.3 Figma Design System & Component Migration

The company maintains a design system in Figma. UI components are currently implemented in the Component Catalog package (MUI React) with Storybook for visualization and testing.

**Important**: The team is actively migrating from MUI to **shadcn/ui** (Radix primitives + Tailwind CSS). This means:
- Existing products (Casino, Sportsbook, etc.) are on MUI
- New products should be built on shadcn/ui where possible
- The community product is an opportunity to be one of the first products on the new design system, avoiding MUI debt

---

## 3. Decisions Made

### Decision 1: Integration Strategy

**Question**: Should the community be a separate service (e.g., Discourse), built natively within Venus, or a hybrid?

**Decision**: **Option B (Venus-native) or C (Hybrid)**, with a strong lean toward Venus-native.

**Rationale (from stakeholder)**:
> "I don't think forum software is that complicated. We will already need it deeply integrated and quite frankly, there are so many amazing tools that have come out in the last year, I think it changes things significantly."

The existing platform already solves auth (Keycloak), components (MUI), CMS (Strapi), real-time (Pulsar), and deployment (K8s/ArgoCD) — the typical "long tail" of building from scratch is already handled.

---

### Decision 2: Data Architecture — Three-Layer Split

**Question**: Where does community data live? New API, extend BFF, or use Strapi?

**Decision**: **All three, with clear responsibilities:**

| Layer | Responsibility |
|---|---|
| **New Community API** (future) | Source of truth for all UGC: threads, posts, replies, votes, user points/badges, moderation actions. Purpose-built schema, optimized queries |
| **Strapi CMS** | Editorial content: official guides, tutorials, announcements, FAQs, challenge descriptions — things the content team authors |
| **Venus BFF** | Aggregation layer: combines Community API data + Strapi content + user profile data from Customer API into unified responses for the frontend |

**Rationale**: This mirrors existing patterns — Casino doesn't store game data in Strapi, it uses Gamint API. Strapi is a headless CMS designed for editorial content, not high-volume user-generated content with complex relationships.

---

### Decision 3: Real-Time Strategy

**Question**: How important is real-time interaction?

**Decision**: **Progressive approach** — launch as a traditional forum, add real-time features later.

**Context**: There is a separate request/workstream to build a chat feature. Real-time infrastructure (Pulsar, Sceptor LiveSubscription) is available when needed, but the community forum MVP does not require it.

---

### Decision 4: Multi-Brand Strategy

**Question**: Should the community be available across all brands from day one?

**Decision**: **Start with one brand (BetOnline), but architect for multi-brand from the start.**

**Rationale**: Venus already handles multi-brand via Config Manager. The community product will follow the same pattern — brand-specific configuration for categories, branding, and user segmentation, with shared code.

---

### Decision 5: MVP Scope

**Question**: What's the scope for the first design?

**Decision**: **Forum core** — categories, threads, posts, replies, user profiles, basic moderation. Designed with extensibility for gamification, events, and real-time features in future phases.

---

### Decision 6: Frontend-Backend Separation

**Question**: Full-stack design or frontend-focused?

**Decision**: **Frontend-focused with strong BFF contracts.**

**Stakeholder input on separation philosophy**:
> "We are trying to push the use of the BFF as a solid layer to separate the frontend visual and presentation from the backend. We could build out the frontend with a BFF layer, contracts and mocked APIs that would be replaced by the BFF at some later point."

**Implementation approach**: The BFF repository layer returns mock data (in-memory/JSON) initially. When the backend team builds the real Community API, the repository layer swaps from mock to real HTTP calls — zero frontend changes required.

---

### Decision 7: Mock API Strategy

**Question**: How to mock the backend during frontend development?

**Decision**: **BFF with in-memory/JSON data** — the BFF repository layer itself returns mock data.

**Rationale**: This fits the hexagonal architecture perfectly. The mock lives in the repository layer (the adapter), and the rest of the stack (controllers, modules, validation) runs exactly as it would in production. When the real API is ready, only the repository adapter changes.

---

## 4. Proposed Approach: Full Venus-Native Product

### 4.1 Overview

Build `community` as a new AstroJS product in Venus, with a new `@community/*` vertical in the Venus BFF. Mock the backend API in the BFF repository layer.

**Reuses existing infrastructure:**
- Auth Service (Keycloak) — user identity, session management
- Product Shell — shared layout, navigation
- Config Manager — brand-specific configuration
- Venus BFF (Sceptor v5) — WebSocket transport, service framework
- Strapi CMS — editorial content (guides, announcements)
- Customer API — user profile data
- Jenkins/ArgoCD — CI/CD pipeline
- Cloudflare/Imperva — CDN/WAF

**New in this product:**
- shadcn/ui (Radix + Tailwind CSS) — first Venus product on the new design system

### 4.2 New Components

**Venus Monorepo — New Product:**
```
products/community/          # New AstroJS product
├── src/
│   ├── pages/              # Forum routes (/community, /community/thread/:id, etc.)
│   ├── components/         # Community-specific React components (shadcn/ui)
│   ├── layouts/            # Community layouts (uses Product Shell)
│   └── ...
```

**Venus BFF — New Vertical:**
```
src/
├── controllers/community/          # @community/* service controllers
│   ├── forum/
│   │   ├── list-categories.ts     # @community/forum/listCategories
│   │   ├── get-threads.ts         # @community/forum/getThreads
│   │   ├── get-thread.ts          # @community/forum/getThread
│   │   ├── create-thread.ts       # @community/forum/createThread
│   │   ├── create-reply.ts        # @community/forum/createReply
│   │   └── index.ts
│   ├── moderation/
│   │   ├── flag-post.ts           # @community/moderation/flagPost
│   │   ├── get-queue.ts           # @community/moderation/getQueue
│   │   └── index.ts
│   ├── user/
│   │   ├── get-profile.ts         # @community/user/getProfile
│   │   ├── get-activity.ts        # @community/user/getActivity
│   │   └── index.ts
│   └── index.ts
├── modules/community/              # Business logic
│   ├── entities/                   # Zod schemas
│   ├── helpers/
│   └── services/
│       ├── forum/
│       ├── moderation/
│       └── user/
└── repository/community/           # Mock data (swap for real API later)
    ├── mock-data/                  # JSON fixtures
    └── community-api.ts            # httpService calls (mocked initially)
```

### 4.3 BFF Service Map

```typescript
type ServiceMap = {
  // ... existing services
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

### 4.4 Multi-Brand Architecture

Follows Venus Config Manager pattern:
```
config/
├── betonline/
│   └── community.json         # BetOnline-specific: categories, branding, feature flags
├── wildcasino/
│   └── community.json         # Wild Casino config (future)
└── default/
    └── community.json         # Shared defaults
```

### 4.5 Development Phases

**Phase 1 — MVP (This Design)**
- Forum core: categories, threads, posts, replies
- User profiles (read-only, from existing Customer API)
- Basic moderation: flag/hide/escalate
- BFF with mock data
- BetOnline brand only
- Built on shadcn/ui (new design system)

**Phase 2 — Gamification (Future)**
- Points, badges, levels, leaderboards
- New BFF services: `@community/gamification/*`
- Likely needs real Community API backend

**Phase 3 — Events & Real-Time (Future)**
- Challenges, AMAs, contests
- LiveSubscription for live threads
- Integration with chat workstream
- Multi-brand rollout

**Phase 4 — Community-Led (Future)**
- Member-created content and events
- Ambassador program
- Advanced moderation (trust levels, weighted flags)

### 4.6 Backend Transition Plan

The mock-to-real transition happens entirely in the BFF repository layer:

```
Phase 1 (Mock):
  Controller → Module → Repository → In-memory JSON data

Phase 2 (Real):
  Controller → Module → Repository → httpService.get('https://community-api/...') → Community API
```

The controller, module, and Zod schema layers remain unchanged. The `safeAsync` + `buildResponse` pattern ensures the same error handling and response format regardless of data source.

---

## 5. Approaches Considered But Not Selected

### 5.1 Headless Forum Engine + Venus Frontend (Approach B)

Use an open-source forum engine (Discourse, NodeBB, Flarum) as the backend, with Venus frontend.

**Why not selected**: Creates vendor lock-in on the data model, adds translation complexity in the BFF, and doesn't map cleanly to future gamification/events plans. Extra infrastructure (PostgreSQL, Redis, Sidekiq for Discourse) adds operational burden.

### 5.2 Strapi-Backed MVP (Approach C)

Model forum data as Strapi collections, accessed through the BFF.

**Why not selected**: Strapi is designed for editorial content, not high-volume UGC. Would hit performance and scaling walls. Moderation, search, and real-time features become difficult. Would likely require migration to a purpose-built backend.

---

## ADR-001: Build Community as Venus-Native Product

**Status**: Proposed

**Context**: The business requires a community engagement platform to improve retention and customer success. The existing Venus platform provides auth, components, CMS, deployment, and real-time infrastructure.

**Decision**: Build the community forum as a new AstroJS product within the Venus monorepo, with a new `@community/*` vertical in the Venus BFF. Use mock data in the BFF repository layer initially, transitioning to a real Community API backend when available.

**Consequences**:
- (+) Full integration with existing auth, design system, config, and deployment
- (+) Frontend can ship independently of backend timeline
- (+) Clean multi-brand support from day one
- (+) No vendor lock-in on data model
- (+) Future gamification/events/real-time integrate naturally
- (+) Opportunity to pioneer shadcn/ui adoption — avoids accumulating MUI debt
- (-) More upfront frontend dev work than off-the-shelf forum
- (-) Forum UI components built from scratch (mitigated by Figma design system + shadcn/ui primitives)
- (-) Backend Community API still needs to be built eventually

---

## ADR-002: BFF-First Development with Mock Repository Layer

**Status**: Proposed

**Context**: The frontend and backend teams operate on different timelines. The frontend team needs to build and validate the community UI without waiting for a backend API.

**Decision**: The Venus BFF repository layer will return mock data (in-memory/JSON) for all community services. The entire BFF stack (controllers, modules, Zod validation, buildResponse) runs as production code. When the real Community API is built, only the repository adapter layer changes.

**Consequences**:
- (+) Frontend and backend development fully decoupled
- (+) BFF contracts serve as the API specification for the backend team
- (+) All validation, error handling, and response formatting tested with real code paths
- (+) Zero frontend changes when backend goes live
- (-) Mock data may not capture all edge cases of a real database
- (-) Search and pagination behavior harder to simulate realistically in mocks

---

## ADR-003: Start Single-Brand, Architect Multi-Brand

**Status**: Proposed

**Context**: Venus supports multiple brands (BetOnline, Wild Casino, etc.) via Config Manager. The community platform needs to work across brands eventually, but launching across all brands simultaneously adds risk.

**Decision**: Pilot on BetOnline only. Use Config Manager from day one so that brand-specific categories, branding, and feature flags are configuration — not code. Expanding to additional brands is a config change, not a code change.

**Consequences**:
- (+) Reduced launch risk — validate with one audience first
- (+) Multi-brand is a configuration exercise, not a re-architecture
- (+) Follows established Venus pattern for brand management
- (-) Other brands wait for community features

---

## ADR-004: Build Community Product on shadcn/ui (New Design System)

**Status**: Proposed

**Context**: Venus is migrating from MUI to shadcn/ui (Radix + Tailwind CSS). Existing products (Casino, Sportsbook) are on MUI. New products face a choice: build on MUI for consistency with existing products, or build on shadcn/ui to align with the future direction.

**Decision**: Build the community product on shadcn/ui. It will be one of the first Venus products on the new design system.

**Consequences**:
- (+) No MUI debt to migrate later
- (+) Establishes patterns and conventions for shadcn/ui usage in Venus that other products can follow
- (+) shadcn/ui components are copy-paste (owned by the project), giving full control over customization
- (+) Tailwind CSS aligns with modern tooling and reduces CSS-in-JS overhead
- (-) Cannot reuse existing MUI Component Catalog components directly — community-specific components need to be built
- (-) Team needs to be comfortable with shadcn/ui + Tailwind (learning curve if this is the first product)
- (-) Product Shell integration may need adaptation if Product Shell still assumes MUI

---

## 6. Open Questions (Resolved)

1. **Backend team timeline**: Remains an open discussion. Plan is designed to work regardless — Phase 0 (prototype) and Phase 1 (BFF mock) proceed without backend. Phase 3 (swap) happens when ready.
2. **Content team readiness**: Team exists, details unknown. Content seeding is part of prototype validation in Phase 0.
3. **Moderation tooling**: **Resolved — needs a proper admin tool.** Given multi-brand approach, moderators need a dedicated admin panel, not just in-forum moderation. Admin panel is brand-scoped via Config Manager.
4. **Search**: **Resolved — Elasticsearch is only used for Graylog logging, not in the app stack.** Mock phase implements a search query collector (logs what users try to search for) rather than full-text search. Production search solution TBD based on collector findings.
5. **SEO**: **Resolved — SEO is a big deal.** Best practices from day 1: SSR, structured data (JSON-LD DiscussionForumPosting), meta tags, sitemaps, canonical URLs, breadcrumbs, Varnish prerender integration.
6. **Figma designs**: Some design system exists, may not have community-specific designs. **Resolved by Phase 0** — the rapid prototype (Supabase + Vercel + shadcn/ui) serves as the design exploration and validation phase.
7. **shadcn/ui readiness**: Still open — team should confirm shared Tailwind configs and conventions before Phase 2 (Venus product build).

## 7. Open Questions (Remaining)

1. **shadcn/ui conventions**: Are there shared Tailwind configs, tokens, or conventions established yet that the community product should follow?
2. **Production search**: What will power full-text search in production? (Elasticsearch, Typesense, Meilisearch, or database-level search?)
3. **Moderation roles in Keycloak**: Do community moderator/admin roles need to be created in Keycloak, or can existing admin roles be reused?

---

## 8. Updated Approach: Phase 0 Prototype

### Decision 8: Prototype Before Venus Integration

**Stakeholder input:**
> "I think we should have a first phase where we put up a prototype that does not need BFF mocks. We can use vibe coding favorites like Supabase or Airtable and Vercel. Get the designs and prototype the main look and feel before going too far."

**Decision**: Add a **Phase 0** using Supabase + Vercel + shadcn/ui to rapidly prototype the community UX. This validates the design, information architecture, and core flows before investing in Venus/BFF integration.

**Rationale**: Catches design mistakes early. The prototype uses shadcn/ui (same target as Venus), so components and patterns transfer directly. Supabase provides instant auth + database + real-time, removing all infrastructure friction for prototyping.

---

## 9. Next Steps

1. **Phase 0: Rapid Prototype** — Supabase + Vercel + shadcn/ui (start immediately)
2. **Phase 1: BFF Vertical** — `@community/*` services with mock data (after Phase 0 learnings)
3. **Phase 2: Venus Product** — AstroJS community product (after Phase 1 BFF is ready)
4. **Phase 3: Backend Swap** — replace mock repository with real Community API (when backend team delivers)
