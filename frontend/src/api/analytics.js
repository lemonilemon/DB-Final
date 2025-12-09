// src/api/analytics.js
import api from "./client";

// 1) User activity analytics
export const getUserActivity = async (days = 30) => {
  const res = await api.get("/analytics/user/activity", {
    params: { days },
  });
  return res.data;
};

// 2) Recent user actions
export const getRecentActions = async (limit = 50) => {
  const res = await api.get("/analytics/user/recent-actions", {
    params: { limit },
  });
  return res.data;
};

// 3) API endpoint statistics
export const getEndpointStats = async (endpoint, method, days = 7) => {
  const res = await api.get("/analytics/api/endpoint-stats", {
    params: { endpoint, method, days },
  });
  return res.data;
};

// 4) Search trends
export const getSearchTrends = async (days = 30) => {
  const res = await api.get("/analytics/search/trends", {
    params: { days },
  });
  return res.data;
};
