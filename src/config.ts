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
 * Based on https://help.getharvest.com/api-v2/
 */
export const HARVEST_ENDPOINTS = [
  'company',
  'users',
  'users/me',
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
  'invoice_messages',
  'invoice_payments',
  'estimates',
  'estimate_item_categories',
  'estimate_messages',
  'roles',
  'project_assignments',
] as const;
