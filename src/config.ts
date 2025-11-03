/**
 * Configuration constants for the Harvest backup tool
 */

export const API_CONFIG = {
  /** Base URL for Harvest ID API */
  ID_BASE_URL: 'https://id.getharvest.com/api/v2',
  
  /** Base URL for Harvest API */
  HARVEST_BASE_URL: 'https://api.harvestapp.com/v2',
  
  /** User agent string for API requests */
  USER_AGENT: 'Harvest Backup Tool (https://github.com/tektit/getharvest-backup)',
  
  /** Rate limit delay between requests (milliseconds) */
  RATE_LIMIT_DELAY: 100,
  
  /** Items per page for paginated requests */
  PER_PAGE: 100,
} as const;

/**
 * Harvest API endpoints to backup
 * Based on the official Harvest OpenAPI specification
 * 
 * Note: Report endpoints that require date range parameters (from/to) are excluded
 * as they are designed for generating reports for specific time periods rather than
 * complete data backups. These include:
 * - reports/time/clients
 * - reports/time/projects  
 * - reports/time/tasks
 * - reports/time/team
 * - reports/expenses/categories
 * - reports/expenses/clients
 * - reports/expenses/projects
 * - reports/expenses/team
 * - reports/uninvoiced
 */
export const HARVEST_ENDPOINTS = [
  'company',
  'users',
  'users/me',
  'users/me/project_assignments',
  'clients',
  'contacts',
  'projects',
  'tasks',
  'task_assignments',
  'user_assignments',
  'time_entries',
  'expenses',
  'expense_categories',
  'invoices',
  'invoice_item_categories',
  'estimates',
  'estimate_item_categories',
  'roles',
  // Only include reports that don't require date parameters
  'reports/project_budget',
] as const;
