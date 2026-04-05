# Competing Plans Analysis — Community Forum Platform

**Date**: 2026-04-03 (updated 2026-04-04)
**Context**: Three external documents were provided as alternative approaches to building the community forum. All three originate from the same Strapi-based architecture. This analysis compares them against our adopted plan (`docs/superpowers/plans/2026-04-02-community-forum-plan.md`) and spec (`docs/superpowers/specs/2026-04-02-community-forum-design.md`).

---

## Documents Compared

| Document | Focus | File |
|---|---|---|
| **Our Plan** | Product delivery strategy (4 phases, prototype-first) | `plans/2026-04-02-community-forum-plan.md` |
| **Competing Plan 1** | Frontend + BFF integration with Strapi | `reference/competing-plan-1-venus-forum-integration-strategy.md` |
| **Competing Plan 2** | Backend database, gamification, moderation, scaling | `reference/competing-plan-2-forum-technical-architecture.md` |
| **Competing Plan 3** | Infrastructure config (Docker, K8s, Nginx, Keycloak, Pulsar, env vars) | `reference/competing-plan-3-configuration-reference.md` |

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

---

## Analysis: Competing Plan 3 (Configuration Reference)

This document is an infrastructure/ops companion to Plans 1 and 2. It contains Docker Compose, Kubernetes manifests, Nginx Ingress, Keycloak realm config, Pulsar topic setup scripts, and environment variable templates. It's built entirely around the Strapi-based separate-BFF architecture that we rejected.

### From Competing Plan 3 (Configuration Reference)

| Item | Relevance | When to Use | Notes |
|---|---|---|---|
| **Keycloak realm config (full JSON)** | HIGH | Phase 2 | Most complete Keycloak reference across all three docs. Includes brute force protection settings, protocol mappers for `forum_nickname` and `forum_roles` claims, user profile attribute definitions with validation patterns. This is the template to adapt when creating forum roles in Keycloak. The `forum-banned` role is a useful addition not seen in Plans 1/2. |
| **Keycloak protocol mappers** | HIGH | Phase 2 | Shows how to map `forum_nickname` as a custom claim into ID/access/userinfo tokens via `oidc-usermodel-attribute-mapper`. Also maps realm roles into a `forum_roles` claim. These are the exact Keycloak config steps needed to expose forum-specific data in JWTs. |
| **Keycloak user profile validation** | MEDIUM | Phase 2 | Nickname validation pattern (`^[a-zA-Z0-9_]+$`, 3-30 chars) with permission scoping (admins can edit reputation, users cannot). Good template for user attribute governance. |
| **Cache TTL env vars** | HIGH | Phase 1 | `DEFAULT_CACHE_TTL=300`, `FORUM_LIST_CACHE_TTL=300`, `TOPIC_LIST_CACHE_TTL=120`, `TOPIC_DETAIL_CACHE_TTL=60`. Confirms the TTL strategy from Plans 1/2 and shows how to make it configurable via env vars rather than hardcoded. |
| **Pulsar topic setup script** | MEDIUM | Phase 3+ | Ready-to-run bash script for creating topics, setting retention policies, enabling compaction, and creating subscriptions. Good ops reference for when real-time features are in scope. |
| **Pulsar retention policies** | MEDIUM | Phase 3+ | `content.created: 30d/10G`, `notifications: 3d/5G`, `moderation.actions: 90d/20G`. Sensible retention defaults. Moderation at 90d is important for audit trails. |
| **K8s resource limits** | LOW | Phase 3+ (production) | BFF: 256Mi-512Mi RAM, 100m-300m CPU. Strapi: 512Mi-1Gi RAM, 250m-500m CPU. Reference sizing for capacity planning. |
| **K8s HPA config** | LOW | Phase 3+ (production) | Scale BFF 3-10 replicas at 70% CPU / 80% memory. Not needed until production. |
| **Nginx WebSocket ingress** | LOW | Phase 3+ | Shows the exact annotations for WebSocket upgrade (`proxy-read-timeout: 3600`, `connection-proxy-header: upgrade`, `upstream-hash-by: $binary_remote_addr` for sticky sessions). Reference for when real-time features are deployed. |
| **Nginx rate limiting** | MEDIUM | Phase 2 | Ingress-level rate limit: 100 req/min. This is a defense-in-depth layer on top of application-level rate limiting from Plan 2. |
| **Docker Compose for local dev** | LOW | Maybe never | Built around the separate Strapi instance architecture. Would need significant rework to match our approach. The Pulsar standalone config (`-Xms512m -Xmx512m`) might be useful if local Pulsar dev is needed. |
| **Env var templates** | MEDIUM | Phase 1-2 | The variable naming conventions and groupings are clean. Useful as a checklist when setting up BFF and frontend env configs, even though some vars (STRAPI_URL, STRAPI_API_TOKEN) won't apply to our architecture. |
| **Separate forum-strapi container** | NOT RELEVANT | Never | We extend existing Venus CMS Strapi, not a separate instance. |
| **Separate forum-bff container** | NOT RELEVANT | Never | Community services live in the existing Venus BFF, not a separate Express app. |
| **Separate forum-ws container** | NOT RELEVANT | Never (Phase 3 at earliest) | Venus already has WebSocket via Sceptor. A separate WS server is redundant. |

### Updated Tier Summary (Including Plan 3)

**Added to Tier 1 (use now/soon):**
- Keycloak realm config with protocol mappers (adapt for Phase 2)
- Cache TTLs as configurable env vars (Phase 1)

**Added to Tier 2 (use later):**
- Pulsar topic setup script with retention policies
- Nginx ingress-level rate limiting
- K8s resource sizing reference

**Added to Tier 3 (not relevant):**
- Separate Docker containers for forum-strapi, forum-bff, forum-ws
- Docker Compose stack (wrong architecture)
