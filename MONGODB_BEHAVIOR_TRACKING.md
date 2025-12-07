# MongoDB Behavior Tracking System

## Overview

The NEW Fridge backend now includes a comprehensive behavior tracking system using MongoDB to collect and analyze user interactions, API usage, and search patterns.

## What Was Implemented

### 1. MongoDB Collections

Seven collections have been created in the `newfridge` database:

- **`user_behavior`** - Tracks specific user actions (login, view_recipe, cook_recipe, create_order)
- **`api_usage`** - Automatically logs all API endpoint calls with performance metrics
- **`search_queries`** - Tracks search queries and results
- **`activity_logs`** - General activity logging (legacy)
- **`api_logs`** - API logging (legacy)
- **`analytics`** - Aggregated metrics storage
- **`error_logs`** - Error tracking

### 2. Automatic API Usage Tracking (Middleware)

**File:** `backend/middleware/behavior_tracking.py`

Every API request to `/api/*` endpoints is automatically logged with:
- Endpoint path
- HTTP method
- User ID (extracted from JWT token if authenticated)
- Status code
- Response time in milliseconds
- IP address
- User agent
- Timestamp

**Example logged data:**
```json
{
  "_id": ObjectId("69358ae594612f76607818de"),
  "endpoint": "/api/recipes/1",
  "method": "GET",
  "user_id": "402130ca-09d3-412d-a767-7e76961c36b9",
  "status_code": 200,
  "response_time_ms": 38.20,
  "timestamp": "2025-12-07T14:10:44.308963",
  "ip_address": "10.89.5.81",
  "user_agent": "curl/8.17.0"
}
```

### 3. User Behavior Tracking

**File:** `backend/services/behavior_service.py`

Specific user actions are tracked in the following endpoints:

#### Login Tracking
- **Endpoint:** `POST /api/auth/login`
- **Tracked:** User login events with username and roles

#### Recipe Viewing
- **Endpoint:** `GET /api/recipes/{recipe_id}`
- **Tracked:** Which recipes users view, including recipe name and cooking time

#### Recipe Cooking
- **Endpoint:** `POST /api/recipes/{recipe_id}/cook`
- **Tracked:** When users cook recipes, which fridge they use, number of ingredients consumed

#### Order Creation
- **Endpoint:** `POST /api/orders`
- **Tracked:** Order placements with partner info, total price, item count

#### Recipe Search
- **Endpoint:** `GET /api/recipes?search=...`
- **Tracked:** Search queries, search text, and number of results

**Example user behavior data:**
```json
{
  "_id": ObjectId("69358ae494612f76607818dd"),
  "user_id": "402130ca-09d3-412d-a767-7e76961c36b9",
  "action_type": "view_recipe",
  "resource_type": "recipe",
  "resource_id": "1",
  "timestamp": "2025-12-07T14:10:44.307472",
  "metadata": {
    "recipe_name": "Scrambled Eggs with Milk",
    "cooking_time": 10
  }
}
```

### 4. Analytics API Endpoints

**File:** `backend/routers/analytics.py`

Three analytics endpoints have been created:

#### GET /api/analytics/user/activity
Get aggregated user activity statistics.

**Query Parameters:**
- `days` (default: 30) - Number of days to analyze

**Returns:**
- Total actions count
- Actions broken down by type
- Most viewed recipes (top 10)
- Most cooked recipes (top 10)

#### GET /api/analytics/user/recent-actions
Get recent user actions.

**Query Parameters:**
- `limit` (default: 50, max: 200) - Number of actions to retrieve

**Returns:** List of recent actions

#### GET /api/analytics/api/endpoint-stats
Get performance statistics for a specific API endpoint.

**Query Parameters:**
- `endpoint` - API endpoint path (e.g., `/api/recipes`)
- `method` - HTTP method (GET, POST, etc.)
- `days` (default: 7) - Number of days to analyze

**Returns:**
- Total requests
- Average response time
- Success rate
- Status code distribution

#### GET /api/analytics/search/trends
Get search trends and popular queries.

**Query Parameters:**
- `days` (default: 30) - Number of days to analyze

**Returns:**
- Top 20 search queries
- Queries by type
- Average results per query

## Database Schema

### user_behavior Collection
```javascript
{
  user_id: UUID (optional),
  action_type: String,  // 'login', 'view_recipe', 'cook_recipe', 'create_order', etc.
  resource_type: String (optional),  // 'recipe', 'ingredient', 'order'
  resource_id: String (optional),
  timestamp: DateTime,
  metadata: Object  // Additional context data
}
```

**Indexes:**
- `user_id`
- `action_type`
- `timestamp`
- Compound: `(user_id, timestamp)` descending

### api_usage Collection
```javascript
{
  endpoint: String,
  method: String,
  user_id: UUID (optional),
  status_code: Integer,
  response_time_ms: Float,
  timestamp: DateTime,
  ip_address: String (optional),
  user_agent: String (optional),
  request_size: Integer (optional),
  response_size: Integer (optional)
}
```

**Indexes:**
- `endpoint`
- `user_id`
- `timestamp`
- Compound: `(endpoint, timestamp)` descending

### search_queries Collection
```javascript
{
  user_id: UUID (optional),
  query_type: String,  // 'recipe', 'ingredient', etc.
  query_text: String,
  results_count: Integer,
  timestamp: DateTime,
  filters: Object  // Applied filters
}
```

**Indexes:**
- `user_id`
- `query_type`
- `timestamp`

## Testing the System

### 1. Verify MongoDB Connection
```bash
curl http://localhost:8000/health/mongo
```

Expected response:
```json
{
  "status": "success",
  "database": "MongoDB",
  "message": "Connection successful",
  "activity_log_count": 0
}
```

### 2. View Logged Data

**Check API usage:**
```bash
docker compose exec mongodb mongosh -u root -p password \
  --authenticationDatabase admin newfridge \
  --eval "db.api_usage.find().limit(5).toArray()" --quiet
```

**Check user behavior:**
```bash
docker compose exec mongodb mongosh -u root -p password \
  --authenticationDatabase admin newfridge \
  --eval "db.user_behavior.find().sort({timestamp:-1}).limit(5).toArray()" --quiet
```

**Check search queries:**
```bash
docker compose exec mongodb mongosh -u root -p password \
  --authenticationDatabase admin newfridge \
  --eval "db.search_queries.find().limit(5).toArray()" --quiet
```

### 3. Test Behavior Tracking

**Register and login:**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"user_name":"testuser","email":"test@example.com","password":"password123"}'

# Login (tracks login action)
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_name":"testuser","password":"password123"}'
```

**View a recipe (tracks view_recipe action):**
```bash
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/recipes/1
```

**Search recipes (tracks search query):**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/recipes?search=eggs
```

## Performance Considerations

### Automatic Cleanup
The `BehaviorService` includes a cleanup method to remove old logs:

```python
await BehaviorService.clear_old_logs(days_to_keep=90)
```

This can be scheduled as a maintenance task to keep MongoDB storage manageable.

### Indexes
All collections have been indexed for common query patterns:
- Single field indexes on frequently queried fields
- Compound indexes for common queries (e.g., user + timestamp)

### Async Operations
All MongoDB operations are asynchronous and won't block API requests.

### Error Handling
Logging failures are caught and logged to console but don't affect the main API response.

## Use Cases for Final Project Demo

### 1. User Engagement Analysis
- Track which recipes are most popular
- Identify power users
- Analyze user session patterns

### 2. Performance Monitoring
- Track API response times
- Identify slow endpoints
- Monitor error rates

### 3. Search Optimization
- Analyze what users search for
- Identify queries with poor results
- Optimize recipe recommendations

### 4. Business Intelligence
- Track order patterns
- Analyze procurement behavior
- Monitor system usage trends

## Files Created/Modified

### New Files:
- `backend/database/mongodb.py` - MongoDB connection manager (originally `backend/mongodb.py` was updated)
- `backend/schemas/behavior.py` - Pydantic schemas for behavior data
- `backend/services/behavior_service.py` - Service for logging and analytics
- `backend/middleware/behavior_tracking.py` - Automatic API tracking middleware
- `backend/routers/analytics.py` - Analytics API endpoints

### Modified Files:
- `backend/main.py` - Added middleware and analytics router
- `backend/mongodb.py` - Added indexes for behavior tracking collections
- `backend/services/recipe_service.py` - Added behavior tracking for recipe actions
- `backend/routers/recipe.py` - Added search tracking
- `backend/routers/auth.py` - Added login tracking
- `backend/routers/procurement.py` - Added order creation tracking

## MongoDB Collections Summary

| Collection | Purpose | Auto-logged | Indexed Fields |
|------------|---------|-------------|----------------|
| user_behavior | User actions (login, view, cook, order) | Partially | user_id, action_type, timestamp |
| api_usage | All API endpoint calls | Yes (middleware) | endpoint, user_id, timestamp |
| search_queries | Search queries and results | Yes (on search) | user_id, query_type, timestamp |
| activity_logs | General activities | Manual | user_id, action_type, timestamp |
| api_logs | Legacy API logging | Manual | timestamp, endpoint |
| analytics | Aggregated metrics | Manual | metric_type, date |
| error_logs | Error tracking | Manual | timestamp, error_type |

## Next Steps

1. **Add More Tracking Points** - Track other important actions like:
   - Fridge item additions/removals
   - Shopping list modifications
   - Meal plan creations

2. **Create Dashboard** - Build a frontend dashboard to visualize:
   - User activity trends
   - Popular recipes
   - API performance graphs

3. **Scheduled Analytics** - Create background jobs to:
   - Pre-compute daily/weekly statistics
   - Clean up old logs
   - Generate reports

4. **Alerts** - Set up monitoring for:
   - Slow API endpoints
   - High error rates
   - Unusual user behavior

## Verification

MongoDB behavior tracking is fully operational and tested:

✅ MongoDB connection established
✅ Collections created with indexes
✅ API usage middleware logging all requests
✅ User actions tracked (login, view_recipe, etc.)
✅ Search queries logged
✅ Analytics endpoints available
✅ Tested with real user data

The system is ready for use and can collect valuable behavioral data for your final project presentation!
