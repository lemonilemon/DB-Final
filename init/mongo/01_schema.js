// ============================================================================
// NEW Fridge - MongoDB Schema & Indexes
// ============================================================================
// Version: 1.0.0
// Date: December 10, 2025
// Description: Analytics and behavior tracking collections
// ============================================================================

// Connect to database
db = db.getSiblingDB('newfridge');

print('Creating MongoDB collections and indexes...');

// ============================================================================
// User Behavior Tracking
// ============================================================================

// Collection: activity_logs (user actions and interactions)
db.createCollection('activity_logs');

// Indexes for activity_logs
db.activity_logs.createIndex({ user_id: 1, timestamp: -1 });
db.activity_logs.createIndex({ action_type: 1, timestamp: -1 });
db.activity_logs.createIndex({ timestamp: -1 });
db.activity_logs.createIndex({ resource_type: 1, resource_id: 1 });

// Sample document structure
db.activity_logs.insertOne({
    _id: ObjectId(),
    user_id: "123e4567-e89b-12d3-a456-426614174000",
    action_type: "cook_recipe",           // login, search_recipe, view_recipe, cook_recipe, create_order, view_fridge
    resource_type: "recipe",              // recipe, ingredient, order, fridge
    resource_id: "42",
    timestamp: new Date(),
    metadata: {
        recipe_name: "Pasta Carbonara",
        fridge_id: "987e4567-e89b-12d3-a456-426614174000",
        ingredients_consumed: 5
    }
});

// Remove sample document
db.activity_logs.deleteMany({});

print('✓ Created activity_logs collection with indexes');

// ============================================================================
// Search Query Tracking
// ============================================================================

// Collection: search_queries (recipe/ingredient searches)
db.createCollection('search_queries');

// Indexes for search_queries
db.search_queries.createIndex({ user_id: 1, timestamp: -1 });
db.search_queries.createIndex({ query_type: 1, query_text: 1 });
db.search_queries.createIndex({ timestamp: -1 });
db.search_queries.createIndex({ query_text: "text" });  // Full-text search

// Sample document structure
db.search_queries.insertOne({
    _id: ObjectId(),
    user_id: "123e4567-e89b-12d3-a456-426614174000",
    query_type: "recipe",                 // recipe, ingredient
    query_text: "pasta",
    results_count: 15,
    timestamp: new Date(),
    filters: {
        cooking_time_max: 30,
        difficulty: "easy"
    }
});

// Remove sample document
db.search_queries.deleteMany({});

print('✓ Created search_queries collection with indexes');

// ============================================================================
// API Usage Tracking
// ============================================================================

// Collection: api_usage (endpoint performance monitoring)
db.createCollection('api_usage');

// Indexes for api_usage
db.api_usage.createIndex({ endpoint: 1, method: 1, timestamp: -1 });
db.api_usage.createIndex({ user_id: 1, timestamp: -1 });
db.api_usage.createIndex({ timestamp: -1 });
db.api_usage.createIndex({ status_code: 1, timestamp: -1 });

// Sample document structure
db.api_usage.insertOne({
    _id: ObjectId(),
    endpoint: "/api/recipes/42",
    method: "GET",
    user_id: "123e4567-e89b-12d3-a456-426614174000",
    status_code: 200,
    response_time_ms: 45.2,
    timestamp: new Date(),
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0...",
    request_size: 256,
    response_size: 1024
});

// Remove sample document
db.api_usage.deleteMany({});

print('✓ Created api_usage collection with indexes');

// ============================================================================
// Collection Metadata
// ============================================================================

// Add validation schemas for data quality
db.runCommand({
    collMod: "activity_logs",
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["action_type", "timestamp"],
            properties: {
                user_id: {
                    bsonType: "string",
                    description: "UUID of user performing action (optional for anonymous)"
                },
                action_type: {
                    bsonType: "string",
                    description: "Type of action performed"
                },
                resource_type: {
                    bsonType: "string",
                    description: "Type of resource (recipe, ingredient, etc.)"
                },
                resource_id: {
                    bsonType: "string",
                    description: "ID of the resource"
                },
                timestamp: {
                    bsonType: "date",
                    description: "When the action occurred"
                },
                metadata: {
                    bsonType: "object",
                    description: "Additional context data"
                }
            }
        }
    },
    validationLevel: "moderate"
});

db.runCommand({
    collMod: "search_queries",
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["query_type", "query_text", "results_count", "timestamp"],
            properties: {
                user_id: {
                    bsonType: "string"
                },
                query_type: {
                    bsonType: "string",
                    enum: ["recipe", "ingredient"]
                },
                query_text: {
                    bsonType: "string"
                },
                results_count: {
                    bsonType: "int",
                    minimum: 0
                },
                timestamp: {
                    bsonType: "date"
                },
                filters: {
                    bsonType: "object"
                }
            }
        }
    },
    validationLevel: "moderate"
});

db.runCommand({
    collMod: "api_usage",
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["endpoint", "method", "status_code", "response_time_ms", "timestamp"],
            properties: {
                endpoint: {
                    bsonType: "string"
                },
                method: {
                    bsonType: "string",
                    enum: ["GET", "POST", "PUT", "PATCH", "DELETE"]
                },
                user_id: {
                    bsonType: "string"
                },
                status_code: {
                    bsonType: "int",
                    minimum: 100,
                    maximum: 599
                },
                response_time_ms: {
                    bsonType: "double",
                    minimum: 0
                },
                timestamp: {
                    bsonType: "date"
                }
            }
        }
    },
    validationLevel: "moderate"
});

print('✓ Added validation schemas to collections');

// ============================================================================
// Collection Statistics
// ============================================================================

print('\n📊 Collection Summary:');
print('  - activity_logs: User behavior tracking');
print('  - search_queries: Search analytics');
print('  - api_usage: API performance monitoring');

print('\n✅ MongoDB schema initialization complete!');

// ============================================================================
// Common Analytics Queries
// ============================================================================

/*
// Get top search queries (last 30 days)
db.search_queries.aggregate([
    { $match: { timestamp: { $gte: new Date(Date.now() - 30*24*60*60*1000) } } },
    { $group: {
        _id: { query_type: "$query_type", query_text: "$query_text" },
        count: { $sum: 1 },
        avg_results: { $avg: "$results_count" }
    }},
    { $sort: { count: -1 } },
    { $limit: 20 }
]);

// Get user activity summary
db.activity_logs.aggregate([
    { $match: { user_id: "YOUR_USER_ID" } },
    { $group: { _id: "$action_type", count: { $sum: 1 } } },
    { $sort: { count: -1 } }
]);

// Get API endpoint performance
db.api_usage.aggregate([
    { $match: { endpoint: "/api/recipes", method: "GET" } },
    { $group: {
        _id: null,
        total_requests: { $sum: 1 },
        avg_response_time: { $avg: "$response_time_ms" },
        success_count: {
            $sum: { $cond: [{ $lt: ["$status_code", 400] }, 1, 0] }
        }
    }}
]);
*/
