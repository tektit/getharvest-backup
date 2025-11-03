import { describe, it, expect } from 'vitest';
import { API_CONFIG, HARVEST_ENDPOINTS } from '../config.js';

describe('Config', () => {
  describe('API_CONFIG', () => {
    it('should have correct API URLs', () => {
      expect(API_CONFIG.ID_BASE_URL).toBe('https://id.getharvest.com/api/v2');
      expect(API_CONFIG.HARVEST_BASE_URL).toBe('https://api.harvestapp.com/v2');
    });

    it('should have a user agent', () => {
      expect(API_CONFIG.USER_AGENT).toContain('Harvest Backup Tool');
    });

    it('should have rate limit configuration', () => {
      expect(API_CONFIG.RATE_LIMIT_DELAY).toBeGreaterThan(0);
      expect(API_CONFIG.PER_PAGE).toBeGreaterThan(0);
    });
  });

  describe('HARVEST_ENDPOINTS', () => {
    it('should include core endpoints', () => {
      expect(HARVEST_ENDPOINTS).toContain('users');
      expect(HARVEST_ENDPOINTS).toContain('projects');
      expect(HARVEST_ENDPOINTS).toContain('time_entries');
      expect(HARVEST_ENDPOINTS).toContain('invoices');
    });

    it('should be a non-empty array', () => {
      expect(Array.isArray(HARVEST_ENDPOINTS)).toBe(true);
      expect(HARVEST_ENDPOINTS.length).toBeGreaterThan(0);
    });
  });
});
