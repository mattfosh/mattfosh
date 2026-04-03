# Competing Plans Analysis — Community Forum Platform

**Date**: 2026-04-03
**Context**: Two external documents were provided as alternative approaches to building the community forum. This analysis compares them against our adopted plan (`docs/superpowers/plans/2026-04-02-community-forum-plan.md`) and spec (`docs/superpowers/specs/2026-04-02-community-forum-design.md`).

---

## Documents Compared

| Document | Focus | File |
|---|---|---|
| **Our Plan** | Product delivery strategy (4 phases, prototype-first) | `plans/2026-04-02-community-forum-plan.md` |
| **Competing Plan 1** | Frontend + BFF integration with Strapi | `reference/competing-plan-1-venus-forum-integration-strategy.md` |
| **Competing Plan 2** | Backend database, gamification, moderation, scaling | `reference/competing-plan-2-forum-technical-architecture.md` |

---

## Why Neither Competing Plan Was Adopted

Both competing plans share the same fundamental problems:

1. **No prototype/validation phase.** Both jump straight to production infrastructure. The stakeholder explicitly asked for a Phase 0 rapid prototype (Supabase + Vercel) to validate UX before building.

2. **Strapi as the forum backend.** Our spec (section 5.2) explicitly rejected this: "Strapi is designed for editorial content, not high-volume UGC. Would hit performance and scaling walls."

3. **Don't fit Venus BFF architecture.** Both use generic REST/Express patterns instead of Sceptor WebSocket services with `serviceFactory.createService()`, `validateParams()`, `buildResponse()`, and `safeAsync()`.

4. **No multi-brand support.** Neither mentions Config Manager or brand-scoped configuration. Our spec (ADR-003) architects for multi-brand from day 1.

5. **Assume Elasticsearch is available.** Stakeholder confirmed Elasticsearch is only for Graylog logging — not in the application stack.

6. **Over-scoped for MVP.** Both include gamification, real-time notifications, typing indicators, presence tracking, and reputation systems from early phases. Our spec defers all of this to Phase 2+.

---

## What IS Relevant — Steal List

### From Competing Plan 1 (Integration Strategy)

| Item | Relevance | When to Use | Notes |
|---|---|---|---|
| **Keycloak role definitions** (forum-user, forum-moderator, forum-admin) | HIGH | Phase 2 (Venus product) | Good role taxonomy. Need to verify if these should be created in Keycloak or reuse existing roles — this is still an open question in our spec. |
| **Keycloak user attributes** (forum_nickname, forum_avatar) | MEDIUM | Phase 2 | Consider whether forum profile data should live in Keycloak attributes or in the Community API. Keycloak attributes are simpler but less flexible. |
| **Cache TTL strategy** (categories: 5min, topics: 2min) | HIGH | Phase 1 (BFF mock) | Even with mock data, establishing cache patterns early means the BFF behaves realistically. |
| **Pulsar topic design** (forum.content.created, forum.notifications, forum.moderation.actions) | MEDIUM | Phase 3+ (real-time, future) | Good topic naming and partitioning strategy. Not needed until real-time features are in scope. |
| **SEO Astro component** (ForumSEO.astro with JSON-LD) | HIGH | Phase 0 (prototype) and Phase 2 | The JSON-LD DiscussionForumPosting pattern and breadcrumb schema are directly usable. |
| **Sitemap generation approach** | HIGH | Phase 2 | The `/sitemap-forum.xml` endpoint pattern with cache headers is clean. |
| **WebSocket room pattern** (forum:{id}, topic:{id}, user:{id}) | LOW | Phase 3+ (future) | Not needed until real-time is in scope. |
| **Zustand store for drafts** | LOW | Phase 2 (maybe) | Draft persistence is a nice-to-have, not MVP. |
| **Separate Strapi instance** | NOT RELEVANT | Never | Contradicts our decision to extend existing Venus CMS Strapi. |
| **Express-based Forum BFF** | NOT RELEVANT | Never | Contradicts Venus BFF architecture (Sceptor). |
| **keycloak-js in browser** | NOT RELEVANT | Never | Venus handles auth through Product Shell + BFF, not direct Keycloak JS. |

### From Competing Plan 2 (Technical Architecture)

| Item | Relevance | When to Use | Notes |
|---|---|---|---|
| **PostgreSQL schema with indexes** | HIGH | Phase 3 (backend handoff) | The composite indexes (e.g., `idx_topics_category` on `(category_id, status, is_pinned, last_post_at DESC)`) show good query optimization. Hand this to the backend team as a starting point. |
| **Three-layer moderation** (AI → Community → Human) | HIGH | Phase 2+ | Our spec only addresses layers 2 (community flagging) and 3 (admin panel). The AI layer (toxicity scoring, keyword filtering) should be noted as a target architecture for scale. |
| **Rate limiting per action** | HIGH | Phase 1 (BFF) | `createTopic: 5/min, createPost: 10/min, like: 30/min, search: 20/min, report: 10/hour`. Implement in BFF services. |
| **Content sanitization** (DOMPurify allowlist) | HIGH | Phase 0 (prototype) and Phase 2 | Essential for any UGC platform. The allowlist (`p, br, strong, em, u, a, ul, ol, li, blockquote, code, pre`) is sensible. |
| **Gamification design** (25 levels, points config, badge engine) | MEDIUM | Phase 2 (gamification, future) | When gamification scope begins, this is a solid starting point. Don't build any of it now. |
| **Materialized views for leaderboards** | MEDIUM | Phase 2 (gamification, future) | Good PostgreSQL pattern for leaderboard performance. |
| **Redis caching schema** | HIGH | Phase 1/2 | The key naming convention (`cache:categories:all`, `cache:topics:category:{id}:{page}`) and TTL matrix are directly usable. |
| **Trust level system** (0-4) | LOW | Phase 2+ (future) | Interesting Discourse-inspired concept but way beyond MVP. |
| **Table partitioning by quarter** | LOW | Phase 3+ (scale) | Only relevant if/when post volume justifies it. Premature for launch. |
| **PgBouncer connection pooling** | LOW | Phase 3 (backend) | Backend infrastructure decision, not frontend/BFF concern. |
| **Strapi content types** | NOT RELEVANT | Never | Strapi-as-forum-backend was rejected. |
| **Elasticsearch search** | NOT RELEVANT | Never | Not in the app stack. |
| **50K MAU scaling targets** | LOW | Future | Useful context but premature to optimize for before we have users. |

---

## Summary: Relevance Tiers

### Tier 1: Use Now or Soon (Phase 0-2)
- Cache TTL strategy (categories 5min, topics 2min, posts 30s)
- Rate limiting per action type
- Content sanitization (DOMPurify + allowlist)
- SEO patterns (JSON-LD DiscussionForumPosting, breadcrumb schema, sitemap)
- Keycloak role definitions (forum-user, forum-moderator, forum-admin)
- Redis key naming convention

### Tier 2: Use Later (Phase 2-3)
- Three-layer moderation architecture (add AI layer to roadmap)
- PostgreSQL schema with indexes (hand to backend team)
- Gamification design (25 levels, points, badges)
- Materialized views for leaderboards
- Pulsar topic naming and partitioning

### Tier 3: Probably Not Relevant
- Separate Strapi instance (rejected)
- Express-based BFF (doesn't fit Venus)
- keycloak-js browser integration (Venus uses Product Shell)
- Elasticsearch search (not in app stack)
- Strapi content types for UGC (rejected approach)
- Table partitioning (premature optimization)
- Trust level system (beyond MVP scope)
- WebSocket typing indicators / presence (beyond MVP scope)

---

## Architectural Conflicts to Watch

1. **Auth pattern**: Competing plans use direct Keycloak JS in browser. Venus uses Product Shell + BFF for auth. Do not mix these patterns.

2. **BFF pattern**: Competing plans use REST Express routes. Venus uses Sceptor WebSocket services. All community services must follow the `serviceFactory.createService()` pattern.

3. **Data source**: Competing plans assume Strapi stores UGC. Our plan uses a purpose-built Community API (Phase 3) with BFF mock data until then.

4. **Search**: Competing plans assume Elasticsearch. We use a search query collector in mock phase, with production search solution TBD.

5. **Scope**: Competing plans build everything at once. Our plan validates with a prototype first, then builds incrementally.
