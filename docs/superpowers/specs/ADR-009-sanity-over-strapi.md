# ADR-009 — Use Sanity for Editorial CMS (Replace Strapi Mention)

**Status**: Accepted
**Date**: 2026-04-12
**Supersedes**: Strapi references in `2026-04-02-community-forum-design.md` § Decision 2

## Context

The main design spec (`2026-04-02-community-forum-design.md`) referenced Strapi as the editorial CMS layer in the three-layer data architecture:

| Layer | Original plan |
|---|---|
| Community API (future) | UGC: threads, posts, replies, votes, badges |
| **Strapi CMS** | Editorial: guides, tutorials, announcements, FAQs |
| Venus BFF | Aggregation layer |

Strapi was suggested because the existing Venus platform already runs a Strapi instance ("Venus CMS") for other editorial content, so extending it for community editorial content was a natural reuse.

During Phase 0 prototype work (2026-04-12), the platform team decided to replace Strapi with **Sanity.io** as the editorial CMS for the community forum layer.

## Decision

**Use Sanity.io for editorial content in the community forum** (guides, tutorials, announcements, FAQs, category descriptions). The three-layer architecture is otherwise unchanged.

| Layer | New choice |
|---|---|
| Community API (future) | UGC: threads, posts, replies, votes, badges — unchanged |
| **Sanity.io** | Editorial: guides, tutorials, announcements, FAQs |
| Venus BFF | Aggregation layer — unchanged |

## Rationale

- **Portable & managed**: Sanity is hosted; no self-hosting/operational burden for a new CMS instance dedicated to community content.
- **Real-time live previews**: content editors get instant preview, which matters for editorial workflows around launches, promos, and event threads.
- **GROQ query language**: more flexible than REST for fetching related documents (e.g. "all guides in category X tagged with tournament-rules, sorted by publishedAt").
- **Portable Text**: structured rich-text format that renders cleanly in React/Astro without HTML-in-CMS fragility.
- **Cleaner separation**: keeps forum editorial content in its own Sanity dataset rather than crowding the existing Venus Strapi instance with a new content type family.

## Consequences

### Changes to upstream decisions in `2026-04-02-community-forum-design.md`
- **Decision 2** (Three-layer data architecture): replace "Strapi" with "Sanity" in the editorial layer.
- **Decision 6/7** (Frontend-Backend Separation / Mock Strategy): BFF repository layer adapter will call the Sanity client (`@sanity/client`) via GROQ instead of Strapi REST.

### No change
- Phase 0 prototype: no CMS connection, pure mock data — unaffected.
- Phase 1 BFF mock: schemas just need to match Sanity content shapes instead of Strapi.
- Phase 2/3: Venus AstroJS product and backend transition path both work the same way; only the adapter implementation differs.

### New items introduced
- Sanity project setup (new Sanity org/project under company account).
- Sanity schema definitions (starter schema in the Kimi chat output — should be formalized and versioned in this repo).
- Sanity Studio hosting decision (Sanity-hosted Studio vs embedded in Venus).
- Access control / role model for editorial team in Sanity.

## Open Questions

1. Does Foshtech already have a Sanity org, or is this the first project?
2. What's the licensing tier — free tier is fine for Phase 0 validation, but Year 1 volume needs costing.
3. Should Sanity Studio live inside the Venus monorepo, or be hosted separately?
4. Who owns Sanity schema evolution — backend, content, or a shared forum team?

## References

- Kimi chat session that triggered the swap: `~/Library/CloudStorage/Dropbox/Work/Foshtech/projects/2026 community & engagement platform/kimi-forum-prototype-2026-04-12/`
- Hosted prototype: https://ioqmsbxxmgypi.ok.kimi.link
- Sanity docs: https://www.sanity.io/docs
- GROQ reference: https://www.sanity.io/docs/groq
