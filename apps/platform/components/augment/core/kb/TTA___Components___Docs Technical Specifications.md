---
title: TTA Technical Specifications
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/technical-specifications.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/TTA Technical Specifications]]

## Overview
This document provides authoritative technical specifications for the TTA (Therapeutic Text Adventure) system, validated against the demonstrated system capabilities and aligned with resolved documentation conflicts.

## System Architecture

### **High-Level Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   React/TS      │◄──►│   FastAPI       │◄──►│   Neo4j + Redis │
│   Port: 3000    │    │   Port: 8080    │    │   Ports: 7474,  │
│                 │    │                 │    │   7687, 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   AI Services   │◄─────────────┘
                        │   OpenRouter    │
                        │   Integration   │
                        └─────────────────┘
```

### **Component Breakdown**

#### **Frontend Layer**
- **Technology**: React 18+ with TypeScript
- **State Management**: Redux Toolkit
- **Styling**: Tailwind CSS
- **Build Tool**: Create React App
- **Port**: 3000 (development), 80/443 (production)
- **Authentication**: JWT token-based with automatic refresh

#### **Backend Layer**
- **Technology**: Python 3.11+ with FastAPI
- **API Framework**: RESTful API with OpenAPI documentation
- **Authentication**: JWT with role-based access control
- **Port**: 8080 (all environments)
- **CORS**: Configured for frontend communication

#### **Database Layer**
- **Primary Database**: Neo4j 5.x (Graph database)
  - **Purpose**: Characters, worlds, relationships, therapeutic data
  - **Ports**: 7474 (HTTP), 7687 (Bolt)
  - **Authentication**: Username/password with role-based access
- **Cache/Session Store**: Redis 7.x
  - **Purpose**: Session management, caching, real-time data
  - **Port**: 6379
  - **Configuration**: Persistence enabled, memory optimization

#### **AI Integration Layer**
- **Provider**: OpenRouter API
- **Authentication**: API key or OAuth
- **Models**: Multiple AI models for therapeutic content generation
- **Fallback**: Local model support for offline scenarios

## API Specifications

### **Authentication Endpoints**
```yaml
Base URL: http://localhost:8080/api/v1

POST /auth/register
  Description: User registration
  Request Body:
    username: string (required, 3-50 chars)
    email: string (required, valid email)
    password: string (required, 8+ chars)
  Response: 200 OK with user data and JWT token
  Status: ✅ Implemented and Validated

POST /auth/login
  Description: User authentication
  Request Body:
    username: string (required)
    password: string (required)
  Response: 200 OK with JWT token
  Status: ✅ Implemented and Validated

POST /auth/logout
  Description: User logout and token invalidation
  Headers: Authorization: Bearer <token>
  Response: 200 OK
  Status: ✅ Implemented, Needs Validation

GET /auth/verify
  Description: Token verification
  Headers: Authorization: Bearer <token>
  Response: 200 OK with user data
  Status: ✅ Implemented, Needs Validation
```

### **Character Management Endpoints**
```yaml
GET /characters
  Description: List user's characters
  Headers: Authorization: Bearer <token>
  Response: 200 OK with character array
  Status: 🔶 Partial - Returns empty array

POST /characters
  Description: Create new character
  Headers: Authorization: Bearer <token>
  Request Body:
    name: string (required, max 50 chars)
    appearance: string (required)
    background: string (required)
    personality_traits: array of strings
    character_goals: array of strings
    comfort_level: integer (1-10)
    therapeutic_intensity: enum [LOW, MEDIUM, HIGH]
    therapeutic_goals: array of strings
  Response: 201 Created with character data
  Status: ❌ Not Implemented - Form submission fails

GET /characters/{id}
  Description: Get specific character
  Headers: Authorization: Bearer <token>
  Response: 200 OK with character data
  Status: ❌ Not Implemented

PUT /characters/{id}
  Description: Update character
  Headers: Authorization: Bearer <token>
  Request Body: Character update data
  Response: 200 OK with updated character
  Status: ❌ Not Implemented
```

### **Settings Management Endpoints**
```yaml
GET /settings
  Description: Get user settings
  Headers: Authorization: Bearer <token>
  Response: 200 OK with settings data
  Status: ✅ Implemented and Validated

PUT /settings/therapeutic
  Description: Update therapeutic preferences
  Headers: Authorization: Bearer <token>
  Request Body:
    intensity_level: enum [LOW, MEDIUM, HIGH]
    therapeutic_approaches: array of enums
    trigger_warnings: array of strings
    comfort_topics: array of strings
    topics_to_avoid: array of strings
  Response: 200 OK
  Status: ✅ Implemented and Validated

GET /models/status
  Description: Get AI model configuration status
  Headers: Authorization: Bearer <token>
  Response: 200 OK with model status
  Status: 🔶 Partial - Returns connection errors
```

### **World Management Endpoints**
```yaml
GET /worlds
  Description: List available worlds
  Headers: Authorization: Bearer <token>
  Query Parameters:
    theme: string (optional)
    difficulty: enum [EASY, MEDIUM, HARD] (optional)
    duration: enum [SHORT, MEDIUM, LONG] (optional)
  Response: 200 OK with world array
  Status: ❌ Not Implemented - Returns empty array

GET /worlds/{id}
  Description: Get world details
  Headers: Authorization: Bearer <token>
  Response: 200 OK with world data
  Status: ❌ Not Implemented

GET /worlds/compatibility
  Description: Check character-world compatibility
  Headers: Authorization: Bearer <token>
  Query Parameters:
    character_id: string (required)
    world_id: string (required)
  Response: 200 OK with compatibility score
  Status: ❌ Not Implemented
```

### **Session Management Endpoints**
```yaml
POST /sessions
  Description: Create therapeutic session
  Headers: Authorization: Bearer <token>
  Request Body:
    character_id: string (required)
    world_id: string (required)
  Response: 201 Created with session data
  Status: ❌ Not Implemented

GET /sessions/{id}
  Description: Get session details
  Headers: Authorization: Bearer <token>
  Response: 200 OK with session data
  Status: ❌ Not Implemented

POST /sessions/{id}/progress
  Description: Update session progress
  Headers: Authorization: Bearer <token>
  Request Body: Progress data
  Response: 200 OK
  Status: ❌ Not Implemented
```

## Database Schemas

### **Neo4j Graph Schema**

#### **User Node**
```cypher
CREATE CONSTRAINT user_id_unique FOR (u:User) REQUIRE u.id IS UNIQUE;

(:User {
  id: string (UUID),
  username: string (unique),
  email: string (unique),
  password_hash: string,
  user_type: enum [PLAYER, PATIENT, CLINICAL_STAFF, ADMIN, DEVELOPER],
  created_at: datetime,
  updated_at: datetime,
  is_active: boolean
})
```

#### **Character Node**
```cypher
CREATE CONSTRAINT character_id_unique FOR (c:Character) REQUIRE c.id IS UNIQUE;

(:Character {
  id: string (UUID),
  name: string,
  appearance: string,
  background: string,
  personality_traits: array of strings,
  character_goals: array of strings,
  comfort_level: integer (1-10),
  therapeutic_intensity: enum [LOW, MEDIUM, HIGH],
  therapeutic_goals: array of strings,
  created_at: datetime,
  updated_at: datetime,
  is_active: boolean
})

// Relationship
(:User)-[:OWNS]->(:Character)
```

#### **World Node**
```cypher
CREATE CONSTRAINT world_id_unique FOR (w:World) REQUIRE w.id IS UNIQUE;

(:World {
  id: string (UUID),
  name: string,
  description: string,
  theme: string,
  difficulty: enum [EASY, MEDIUM, HARD],
  duration: enum [SHORT, MEDIUM, LONG],
  therapeutic_approaches: array of enums,
  content: text,
  created_at: datetime,
  updated_at: datetime,
  is_active: boolean
})
```

#### **Session Node**
```cypher
CREATE CONSTRAINT session_id_unique FOR (s:Session) REQUIRE s.id IS UNIQUE;

(:Session {
  id: string (UUID),
  session_state: text (JSON),
  progress_data: text (JSON),
  start_time: datetime,
  end_time: datetime,
  status: enum [ACTIVE, PAUSED, COMPLETED, TERMINATED],
  created_at: datetime,
  updated_at: datetime
})

// Relationships
(:User)-[:PARTICIPATES_IN]->(:Session)
(:Character)-[:ACTS_IN]->(:Session)
(:World)-[:HOSTS]->(:Session)
```

### **Redis Data Structures**

#### **Session Management**
```redis
# User sessions (JWT token storage)
SET user_session:{user_id} "{jwt_token}" EX 86400

# Active user tracking
SADD active_users {user_id}

# Session state caching
HSET session:{session_id}
  state "{session_state_json}"
  last_activity "{timestamp}"
  user_id "{user_id}"
```

#### **Caching Layer**
```redis
# User settings cache
HSET user_settings:{user_id}
  therapeutic_preferences "{json_data}"
  ai_model_config "{json_data}"
  privacy_settings "{json_data}"

# Character cache
HSET character:{character_id}
  data "{character_json}"
  last_accessed "{timestamp}"

# World cache
HSET world:{world_id}
  data "{world_json}"
  access_count "{integer}"
```

## Security Specifications

### **Authentication & Authorization**
- **JWT Token Expiration**: 24 hours
- **Token Refresh**: Automatic refresh 1 hour before expiration
- **Password Requirements**: Minimum 8 characters, complexity validation
- **Session Management**: Redis-based with automatic cleanup
- **Role-Based Access Control**: Six user types with defined permissions

### **Data Protection**
- **Encryption in Transit**: TLS 1.3 for all API communications
- **Encryption at Rest**: Database-level encryption for sensitive data
- **Password Storage**: bcrypt hashing with salt
- **API Key Management**: Secure storage and rotation for external services

### **Privacy Compliance**
- **HIPAA Compliance**: Required for clinical data handling
- **GDPR Compliance**: User data protection and right to deletion
- **Audit Logging**: Complete audit trail for all user actions
- **Data Retention**: Configurable retention policies by data type

## Performance Specifications

### **Response Time Targets**
- **Page Load**: < 2 seconds for initial page load
- **API Responses**: < 500ms for standard operations
- **Character Creation**: < 3 seconds for complete workflow
- **Session Initiation**: < 1 second for session start

### **Scalability Requirements (Solo Development Targets)**
- **Concurrent Users**: Support 10-50 simultaneous active users initially
- **Database Performance**: < 500ms query response time (acceptable for small user base)
- **Memory Usage**: < 1GB per application instance (suitable for basic hosting)
- **Storage**: Scalable to 10GB+ user-generated content initially

### **Availability Targets (Realistic for Solo Development)**
- **Uptime**: 95%+ availability (reasonable for solo-maintained system)
- **Recovery Time**: < 1 hour for system recovery (manual intervention acceptable)
- **Backup Frequency**: Weekly automated backups (daily when user base grows)
- **Monitoring**: Basic error logging and health checks

## Integration Specifications

### **AI Model Integration**
- **Primary Provider**: OpenRouter API
- **Authentication**: API key or OAuth 2.0
- **Model Selection**: User-configurable with fallback options
- **Rate Limiting**: Configurable limits per user type
- **Error Handling**: Graceful degradation with offline capabilities

### **External System Integration**
- **Healthcare Systems**: HL7 FHIR compatibility for clinical data exchange
- **Single Sign-On**: SAML 2.0 and OAuth 2.0 support
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Logging**: Structured logging with ELK stack integration

## Deployment Specifications

### **Development Environment (Solo Setup)**
- **Docker Compose**: Simple multi-container development setup (already working)
- **Hot Reload**: Automatic code reloading for development
- **Database Seeding**: Basic test data population scripts
- **Environment Variables**: Configuration through .env files

### **Production Environment (Solo-Friendly)**
- **Simple Hosting**: Single server deployment (DigitalOcean, Heroku, etc.)
- **Basic Load Balancing**: Simple reverse proxy setup
- **Database**: Single Neo4j instance with Redis (clustering when needed)
- **Monitoring**: Basic health checks and error logging

### **Configuration Management**
- **Environment-Specific**: Separate configurations for dev/staging/production
- **Secret Management**: Secure handling of API keys and credentials
- **Feature Flags**: Runtime feature toggling capabilities
- **Version Control**: All configurations tracked in version control

---

**Validation Status**: ✅ **Validated Against Demonstrated System**
**Implementation Alignment**: ✅ **Specifications Match Working Components**
**Gap Identification**: ✅ **Missing Components Clearly Identified**
**Authority Level**: **PRIMARY** - This document serves as the authoritative technical reference

**Last Updated**: 2025-01-23
**Version**: 2.0
**Status**: ✅ Complete and Authoritative


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs technical specifications]]
