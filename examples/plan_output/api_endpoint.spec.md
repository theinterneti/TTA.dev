# Feature: Add User Profile API Endpoint

## Overview

Add RESTful API endpoint for user profile management.

## Requirements

- GET /api/users/{id} - Retrieve user profile
- PUT /api/users/{id} - Update user profile
- POST /api/users/{id}/avatar - Upload avatar
- Authentication required for all endpoints
- Rate limiting: 100 requests/minute per user

## Database

- User table with id, email, name, avatar_url, created_at, updated_at
- Indexed on email for fast lookups

## Integration

- Integrate with existing auth service
- Store avatars in S3-compatible storage
