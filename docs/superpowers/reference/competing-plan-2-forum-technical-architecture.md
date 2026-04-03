# Forum Technical Architecture Specification
## Customer Forum for Online Betting Platform

> **Source**: External competing plan, not authored by this team.
> **Status**: Reference only — not adopted. See analysis in `competing-plans-analysis.md`.

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Strapi Content Type Schema Design](#1-strapi-content-type-schema-design)
3. [Database Schema Design](#2-database-schema-design)
4. [API Design](#3-api-design)
5. [Gamification System Architecture](#4-gamification-system-architecture)
6. [Moderation System Design](#5-moderation-system-design)
7. [Real-time Features Architecture](#6-real-time-features-architecture)
8. [Performance & Scaling Strategies](#7-performance--scaling-strategies)
9. [Security Considerations](#8-security-considerations)
10. [Implementation Roadmap](#9-implementation-roadmap)

---

## Executive Summary

This document provides a comprehensive technical architecture for a customer forum integrated into an online betting website, designed to support 50K Monthly Active Users (MAU) by Year 1.

### Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Hybrid Database** | PostgreSQL for transactional data, Redis for caching/sessions, Elasticsearch for search |
| **Event-Driven Architecture** | Apache Pulsar for real-time updates, notifications, and gamification events |
| **BFF Pattern** | Venus BFF layer to aggregate CMS data and provide optimized frontend APIs |
| **Strapi CMS** | Leverage existing Venus CMS for content management and user-generated content |
| **3-Layer Moderation** | AI + Community + Human for scalable content moderation |

---

## 1. Strapi Content Type Schema Design

### 1.1 Category Content Type

```javascript
// src/api/category/content-types/category/schema.json
{
  "kind": "collectionType",
  "collectionName": "categories",
  "info": {
    "name": "Category",
    "description": "Forum categories and subcategories"
  },
  "attributes": {
    "name": { "type": "string", "required": true, "maxLength": 100 },
    "slug": { "type": "uid", "targetField": "name", "required": true },
    "description": { "type": "text", "maxLength": 500 },
    "icon": { "type": "media", "multiple": false },
    "color": { "type": "string", "regex": "^#[0-9A-Fa-f]{6}$" },
    "displayOrder": { "type": "integer", "default": 0 },
    "isActive": { "type": "boolean", "default": true },
    "isPrivate": { "type": "boolean", "default": false },
    "requiredTrustLevel": { "type": "integer", "default": 0, "min": 0, "max": 4 },
    "parentCategory": {
      "type": "relation", "relation": "manyToOne",
      "target": "api::category.category", "inversedBy": "subcategories"
    },
    "subcategories": {
      "type": "relation", "relation": "oneToMany",
      "target": "api::category.category", "mappedBy": "parentCategory"
    },
    "topics": {
      "type": "relation", "relation": "oneToMany",
      "target": "api::topic.topic", "mappedBy": "category"
    },
    "topicCount": { "type": "integer", "default": 0 },
    "postCount": { "type": "integer", "default": 0 },
    "lastActivityAt": { "type": "datetime" },
    "seo": { "type": "component", "component": "shared.seo-meta" }
  }
}
```

### 1.2 Topic Content Type

```javascript
// src/api/topic/content-types/topic/schema.json
{
  "kind": "collectionType",
  "collectionName": "topics",
  "info": { "name": "Topic", "description": "Forum topics/threads" },
  "options": { "draftAndPublish": true },
  "attributes": {
    "title": { "type": "string", "required": true, "maxLength": 200 },
    "slug": { "type": "uid", "targetField": "title" },
    "content": { "type": "richtext", "required": true },
    "excerpt": { "type": "text", "maxLength": 300 },
    "category": {
      "type": "relation", "relation": "manyToOne",
      "target": "api::category.category", "inversedBy": "topics"
    },
    "author": {
      "type": "relation", "relation": "manyToOne",
      "target": "plugin::users-permissions.user", "inversedBy": "topics"
    },
    "posts": {
      "type": "relation", "relation": "oneToMany",
      "target": "api::post.post", "mappedBy": "topic"
    },
    "tags": {
      "type": "relation", "relation": "manyToMany",
      "target": "api::tag.tag", "inversedBy": "topics"
    },
    "status": {
      "type": "enumeration",
      "enum": ["draft", "pending", "published", "locked", "archived", "deleted"],
      "default": "pending"
    },
    "topicType": {
      "type": "enumeration",
      "enum": ["discussion", "question", "poll", "announcement", "guide"],
      "default": "discussion"
    },
    "isPinned": { "type": "boolean", "default": false },
    "isFeatured": { "type": "boolean", "default": false },
    "viewCount": { "type": "integer", "default": 0 },
    "replyCount": { "type": "integer", "default": 0 },
    "likeCount": { "type": "integer", "default": 0 },
    "lastPostAt": { "type": "datetime" },
    "lastPostBy": {
      "type": "relation", "relation": "manyToOne",
      "target": "plugin::users-permissions.user"
    },
    "moderationStatus": { "type": "component", "component": "moderation.moderation-status" },
    "poll": { "type": "component", "component": "forum.poll" },
    "seo": { "type": "component", "component": "shared.seo-meta" }
  }
}
```

### 1.3 Post Content Type

```javascript
// src/api/post/content-types/post/schema.json
{
  "kind": "collectionType",
  "collectionName": "posts",
  "info": { "name": "Post", "description": "Forum posts and replies" },
  "attributes": {
    "content": { "type": "richtext", "required": true },
    "rawContent": { "type": "text" },
    "topic": {
      "type": "relation", "relation": "manyToOne",
      "target": "api::topic.topic", "inversedBy": "posts"
    },
    "author": {
      "type": "relation", "relation": "manyToOne",
      "target": "plugin::users-permissions.user", "inversedBy": "posts"
    },
    "parentPost": {
      "type": "relation", "relation": "manyToOne",
      "target": "api::post.post", "inversedBy": "replies"
    },
    "replies": {
      "type": "relation", "relation": "oneToMany",
      "target": "api::post.post", "mappedBy": "parentPost"
    },
    "status": {
      "type": "enumeration",
      "enum": ["pending", "approved", "rejected", "hidden", "deleted"],
      "default": "pending"
    },
    "postNumber": { "type": "integer" },
    "likeCount": { "type": "integer", "default": 0 },
    "editCount": { "type": "integer", "default": 0 },
    "editedAt": { "type": "datetime" },
    "editReason": { "type": "string", "maxLength": 200 },
    "isSolution": { "type": "boolean", "default": false },
    "moderationStatus": { "type": "component", "component": "moderation.moderation-status" },
    "attachments": { "type": "component", "component": "forum.attachments", "repeatable": true },
    "reactions": { "type": "component", "component": "forum.reactions", "repeatable": true }
  }
}
```

### 1.4 User Profile Extension

```javascript
// src/extensions/users-permissions/content-types/user/schema.json
// Extends Strapi user with forum-specific fields:
// displayName, avatar, bio, signature, location, website,
// trustLevel (0-4), reputation component, preferences component,
// topics/posts relations, badges, achievements, notifications,
// following/followers, mutedUsers, moderationFlags
```

### 1.5 Badge Content Type

```javascript
// src/api/badge/content-types/badge/schema.json
// Badge fields: name, slug, description, icon, iconAnimated,
// badgeType (bronze/silver/gold/platinum/special),
// category (community/posting/engagement/milestone/expertise/special/moderation),
// pointsAwarded, isHidden, displayOrder, requirement component,
// users relation, earnedCount, isActive
```

### 1.6 Components

#### Reputation Component
```javascript
// src/components/gamification/reputation.json
// Fields: totalPoints, level (1-25), levelName, pointsToNextLevel,
// dailyPoints, weeklyPoints, monthlyPoints, allTimeRank, categoryPoints (JSON)
```

#### Moderation Status Component
```javascript
// src/components/moderation/moderation-status.json
// Fields: aiScore (0-1), aiFlags (JSON), reviewedAt, reviewedBy,
// communityFlags, flaggedBy, heldForReview, reviewReason
```

---

## 2. Database Schema Design

### 2.1 PostgreSQL Core Schema

```sql
-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon_url VARCHAR(500),
    color CHAR(7),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_private BOOLEAN DEFAULT false,
    required_trust_level INTEGER DEFAULT 0 CHECK (required_trust_level BETWEEN 0 AND 4),
    parent_category_id INTEGER REFERENCES categories(id),
    topic_count INTEGER DEFAULT 0,
    post_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_parent ON categories(parent_category_id);
CREATE INDEX idx_categories_active ON categories(is_active, display_order);
CREATE INDEX idx_categories_slug ON categories(slug);

-- Topics
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    excerpt VARCHAR(300),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    author_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    topic_type VARCHAR(20) DEFAULT 'discussion',
    is_pinned BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    view_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    last_post_at TIMESTAMP,
    last_post_by INTEGER REFERENCES users(id),
    published_at TIMESTAMP,
    -- Moderation fields
    ai_score DECIMAL(3,2),
    ai_flags JSONB,
    held_for_review BOOLEAN DEFAULT false,
    review_reason VARCHAR(50),
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id),
    community_flags INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, slug)
);

CREATE INDEX idx_topics_category ON topics(category_id, status, is_pinned, last_post_at DESC);
CREATE INDEX idx_topics_author ON topics(author_id, created_at DESC);
CREATE INDEX idx_topics_status ON topics(status, created_at DESC);
CREATE INDEX idx_topics_featured ON topics(is_featured, created_at DESC) WHERE is_featured = true;
CREATE INDEX idx_topics_search ON topics USING gin(to_tsvector('english', title || ' ' || COALESCE(content, '')));

-- Posts
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    raw_content TEXT,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id),
    parent_post_id INTEGER REFERENCES posts(id),
    status VARCHAR(20) DEFAULT 'pending',
    post_number INTEGER NOT NULL,
    like_count INTEGER DEFAULT 0,
    edit_count INTEGER DEFAULT 0,
    edited_at TIMESTAMP,
    edit_reason VARCHAR(200),
    is_solution BOOLEAN DEFAULT false,
    -- Moderation fields
    ai_score DECIMAL(3,2),
    ai_flags JSONB,
    held_for_review BOOLEAN DEFAULT false,
    community_flags INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(topic_id, post_number)
);

CREATE INDEX idx_posts_topic ON posts(topic_id, status, created_at);
CREATE INDEX idx_posts_author ON posts(author_id, created_at DESC);

-- User Profiles
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    display_name VARCHAR(50) UNIQUE,
    avatar_url VARCHAR(500),
    bio VARCHAR(500),
    signature VARCHAR(200),
    trust_level INTEGER DEFAULT 0 CHECK (trust_level BETWEEN 0 AND 4),
    -- Reputation
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1 CHECK (level BETWEEN 1 AND 25),
    level_name VARCHAR(50) DEFAULT 'New Member',
    daily_points INTEGER DEFAULT 0,
    weekly_points INTEGER DEFAULT 0,
    monthly_points INTEGER DEFAULT 0,
    all_time_rank INTEGER,
    -- Activity
    last_active_at TIMESTAMP,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Moderation
    warning_count INTEGER DEFAULT 0,
    suspension_count INTEGER DEFAULT 0,
    suspended_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_trust ON user_profiles(trust_level, total_points DESC);
CREATE INDEX idx_user_profiles_rank ON user_profiles(all_time_rank) WHERE all_time_rank IS NOT NULL;

-- Badges
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon_url VARCHAR(500) NOT NULL,
    badge_type VARCHAR(20) DEFAULT 'bronze',
    category VARCHAR(20) DEFAULT 'community',
    points_awarded INTEGER DEFAULT 0,
    is_hidden BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    earned_count INTEGER DEFAULT 0,
    requirement_type VARCHAR(50),
    target_value INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Badges (Many-to-Many)
CREATE TABLE user_badges (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, badge_id)
);

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    notification_type VARCHAR(30) NOT NULL,
    title VARCHAR(200),
    message TEXT,
    data JSONB,
    actor_id INTEGER REFERENCES user_profiles(id),
    topic_id INTEGER REFERENCES topics(id),
    post_id INTEGER REFERENCES posts(id),
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);

-- Likes
CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK ((topic_id IS NOT NULL AND post_id IS NULL) OR (topic_id IS NULL AND post_id IS NOT NULL)),
    UNIQUE(user_id, topic_id),
    UNIQUE(user_id, post_id)
);

-- Moderation Actions
CREATE TABLE moderation_actions (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(20) NOT NULL,
    reason TEXT,
    moderator_id INTEGER REFERENCES user_profiles(id),
    target_user_id INTEGER REFERENCES user_profiles(id),
    topic_id INTEGER REFERENCES topics(id),
    post_id INTEGER REFERENCES posts(id),
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    is_automated BOOLEAN DEFAULT false,
    ai_confidence DECIMAL(3,2),
    appealable BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES user_profiles(id),
    reported_user_id INTEGER REFERENCES user_profiles(id),
    topic_id INTEGER REFERENCES topics(id),
    post_id INTEGER REFERENCES posts(id),
    report_type VARCHAR(30) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(10) DEFAULT 'medium',
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Point Transactions
CREATE TABLE point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materialized view for leaderboards
CREATE MATERIALIZED VIEW leaderboard_alltime AS
SELECT 
  user_id,
  total_points,
  ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank
FROM user_profiles
WHERE total_points > 0;

-- Table partitioning for posts
CREATE TABLE posts_2024_q1 PARTITION OF posts
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

### 2.2 Redis Schema

```
# User Sessions
session:{sessionId} -> Hash { userId, expiresAt, ... }

# User Online Status
user:online:{userId} -> String (timestamp)
online:users -> Sorted Set (score: timestamp, member: userId)

# Rate Limiting
rate_limit:{action}:{userId} -> String (count)

# Caching
cache:categories:all -> JSON
cache:topics:category:{categoryId}:{page} -> JSON
cache:topic:{topicId} -> JSON
cache:user:{userId} -> JSON
cache:leaderboard:{period}:{page} -> JSON

# Real-time counters
topic:{topicId}:view_count -> Integer
post:{postId}:like_count -> Integer

# Moderation Queue
moderation:queue:pending -> List (topic/post IDs)
```

---

## 3. API Design

### 3.1 REST API Endpoints

```yaml
# Categories
GET    /api/v1/categories
GET    /api/v1/categories/:slug
GET    /api/v1/categories/:slug/topics

# Topics
GET    /api/v1/topics
GET    /api/v1/topics/:slug
POST   /api/v1/topics
PUT    /api/v1/topics/:id
DELETE /api/v1/topics/:id
POST   /api/v1/topics/:id/like
GET    /api/v1/topics/:id/posts

# Posts
GET    /api/v1/posts/:id
POST   /api/v1/posts
PUT    /api/v1/posts/:id
DELETE /api/v1/posts/:id
POST   /api/v1/posts/:id/like

# Users
GET    /api/v1/users/:username
GET    /api/v1/users/me
PUT    /api/v1/users/me
GET    /api/v1/users/me/notifications
GET    /api/v1/users/leaderboard

# Badges
GET    /api/v1/badges
GET    /api/v1/users/me/badges

# Search
GET    /api/v1/search?q=query
```

### 3.2 BFF Service Integration

```javascript
class ForumService {
  async getCategories() {
    const cacheKey = 'cache:categories:all';
    let categories = await this.redis.get(cacheKey);
    if (!categories) {
      categories = await this.strapi.find('categories', {
        populate: ['subcategories'],
        filters: { isActive: true },
        sort: ['displayOrder:asc']
      });
      await this.redis.setex(cacheKey, 300, JSON.stringify(categories));
    }
    return JSON.parse(categories);
  }

  async createTopic(data, userId) {
    const rateKey = `rate_limit:post:${userId}`;
    const postCount = await this.redis.incr(rateKey);
    if (postCount === 1) await this.redis.expire(rateKey, 60);
    if (postCount > 5) throw new Error('Rate limit exceeded');

    const topic = await this.strapi.create('topics', {
      ...data, author: userId, status: 'pending'
    });

    await this.pulsar.send('forum.topic.created', {
      topicId: topic.id, userId, timestamp: new Date().toISOString()
    });

    await this.redis.del(`cache:topics:category:${data.categoryId}:*`);
    return topic;
  }
}
```

---

## 4. Gamification System Architecture

### 4.1 Points Configuration

```javascript
const POINTS_CONFIG = {
  CREATE_TOPIC: { points: 10, dailyLimit: 50 },
  CREATE_POST: { points: 5, dailyLimit: 100 },
  RECEIVE_LIKE: { points: 2, dailyLimit: 500 },
  GIVE_LIKE: { points: 1, dailyLimit: 100 },
  MARK_SOLUTION: { points: 50, dailyLimit: 200 },
  DAILY_VISIT: { points: 5, streakBonus: true },
  TRUST_LEVEL_UP: { points: 100, oneTime: true }
};

const LEVELS = [
  { level: 1, name: 'New Member', minPoints: 0 },
  { level: 2, name: 'Explorer', minPoints: 100 },
  { level: 3, name: 'Learner', minPoints: 250 },
  { level: 4, name: 'Contributor', minPoints: 500 },
  { level: 5, name: 'Regular', minPoints: 1000 },
  { level: 6, name: 'Enthusiast', minPoints: 2000 },
  { level: 7, name: 'Helper', minPoints: 3500 },
  { level: 8, name: 'Advisor', minPoints: 5500 },
  { level: 9, name: 'Expert', minPoints: 8000 },
  { level: 10, name: 'Specialist', minPoints: 11000 },
  // ... levels 11-25 up to 212,000 points
  { level: 25, name: 'Ultimate', minPoints: 212000 }
];
```

### 4.2 Points Engine

```javascript
class PointsEngine {
  async awardPoints(userId, actionType, metadata = {}) {
    const config = POINTS_CONFIG[actionType];
    if (!config) return null;
    if (config.oneTime && await this.checkOneTimeAction(userId, actionType)) return null;

    let points = config.points;
    if (config.streakBonus && metadata.streak) {
      points += Math.min(metadata.streak * 2, 20);
    }

    const transaction = await this.strapi.create('point-transactions', {
      user: userId, points, transactionType: actionType,
      referenceType: metadata.referenceType, referenceId: metadata.referenceId
    });

    await this.updateUserReputation(userId, points);
    await this.pulsar.send('gamification.points.awarded', {
      userId, points, actionType, transactionId: transaction.id
    });

    return transaction;
  }
}
```

---

## 5. Moderation System Design

### 5.1 Three-Layer Architecture

```
LAYER 1: AUTOMATED (AI)
- Content filtering, spam detection, toxicity scoring, keyword filtering

LAYER 2: COMMUNITY (Trust-based)
- User flagging, community voting, trust level moderation

LAYER 3: HUMAN (Staff)
- Manual review, appeal handling, policy enforcement
```

### 5.2 AI Moderation Service

```javascript
class AIModerationService {
  async moderateContent(content, metadata = {}) {
    const results = { passed: true, score: 0, flags: [], actions: [] };

    // Keyword filtering
    const keywordResult = this.checkKeywords(content);
    if (keywordResult.found) {
      results.passed = false;
      results.flags.push(...keywordResult.flags);
      results.actions.push('block');
    }

    // AI toxicity analysis
    if (this.config.aiServiceUrl) {
      const aiResult = await this.callAIModeration(content);
      results.score = aiResult.score;
      if (aiResult.score >= this.config.toxicityThreshold) {
        results.passed = false;
        results.actions.push('hold_for_review');
      }
    }

    return results;
  }
}
```

---

## 6. Real-time Features Architecture

### 6.1 Pulsar Integration

```javascript
class ForumRealtimeService {
  async initializeConsumers() {
    await this.pulsar.subscribe('forum.topic.*', async (message) => {
      const event = JSON.parse(message.data);
      await this.handleTopicEvent(event);
    });

    await this.pulsar.subscribe('forum.post.*', async (message) => {
      const event = JSON.parse(message.data);
      await this.handlePostEvent(event);
    });

    await this.pulsar.subscribe('gamification.*', async (message) => {
      const event = JSON.parse(message.data);
      await this.handleGamificationEvent(event);
    });
  }
}
```

---

## 7. Performance & Scaling Strategies

### 7.1 Caching Strategy

```javascript
const CACHE_STRATEGY = {
  categories: { ttl: 300, key: 'cache:categories:all' },
  badges: { ttl: 600, key: 'cache:badges:all' },
  topics: { ttl: 60, key: 'cache:topics:{categoryId}:{page}' },
  topic: { ttl: 30, key: 'cache:topic:{topicId}' },
  posts: { ttl: 30, key: 'cache:topic:{topicId}:posts:{page}' },
  user: { ttl: 300, key: 'cache:user:{userId}' },
  leaderboard: { ttl: 300, key: 'cache:leaderboard:{period}:{page}' },
  search: { ttl: 30, key: 'cache:search:{query_hash}:{page}' }
};
```

### 7.2 Database Optimization

- Connection pooling via PgBouncer (100 connections per instance, transaction mode)
- Read replicas (1 primary + 3 replicas)
- Table partitioning by quarter for posts
- Materialized views for leaderboards

---

## 8. Security Considerations

### 8.1 Rate Limiting

```javascript
const RATE_LIMITS = {
  createTopic: { window: 60, max: 5 },
  createPost: { window: 60, max: 10 },
  like: { window: 60, max: 30 },
  search: { window: 60, max: 20 },
  report: { window: 3600, max: 10 }
};
```

### 8.2 Content Security

```javascript
const DOMPurify = require('isomorphic-dompurify');

function sanitizeContent(content) {
  return DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
    FORBID_ATTR: ['style', 'class']
  });
}
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- Set up Strapi content types
- Implement core database schema
- Basic CRUD APIs for categories, topics, posts
- User authentication integration with Keycloak

### Phase 2: Core Features (Weeks 5-8)
- Topic and post creation
- User profiles and following
- Search functionality with Elasticsearch
- Basic notifications

### Phase 3: Gamification (Weeks 9-12)
- Points system implementation
- Badge engine
- Trust levels
- Leaderboards

### Phase 4: Moderation (Weeks 13-16)
- AI moderation integration
- Community flagging
- Moderation dashboard
- Reporting system

### Phase 5: Real-time & Polish (Weeks 17-20)
- WebSocket implementation
- Real-time notifications
- Performance optimization
- Load testing

---

*Document Version: 1.0*
*Last Updated: 2024*
