import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import nock from 'nock';
import { HarvestClient } from '../harvest-client.js';

describe('HarvestClient', () => {
  const mockPAT = 'test-token-123';
  let client: HarvestClient;

  beforeEach(() => {
    client = new HarvestClient(mockPAT);
    nock.cleanAll();
  });

  afterEach(() => {
    nock.cleanAll();
  });

  describe('getAccounts', () => {
    it('should fetch accounts successfully', async () => {
      const mockAccounts = {
        accounts: [
          { id: 1, name: 'Test Account 1', product: 'harvest' },
          { id: 2, name: 'Test Account 2', product: 'harvest' },
        ],
      };

      nock('https://id.getharvest.com')
        .get('/api/v2/accounts')
        .matchHeader('Authorization', `Bearer ${mockPAT}`)
        .reply(200, mockAccounts);

      const accounts = await client.getAccounts();

      expect(accounts).toHaveLength(2);
      expect(accounts[0]).toEqual({ id: 1, name: 'Test Account 1', product: 'harvest' });
      expect(accounts[1]).toEqual({ id: 2, name: 'Test Account 2', product: 'harvest' });
    });

    it('should throw error on 401 unauthorized', async () => {
      nock('https://id.getharvest.com')
        .get('/api/v2/accounts')
        .reply(401, { error: 'Unauthorized' });

      await expect(client.getAccounts()).rejects.toThrow('Failed to fetch accounts: 401 Unauthorized');
    });

    it('should throw error on network failure', async () => {
      nock('https://id.getharvest.com')
        .get('/api/v2/accounts')
        .replyWithError('Network error');

      await expect(client.getAccounts()).rejects.toThrow();
    });

    it('should return empty array when no accounts', async () => {
      nock('https://id.getharvest.com')
        .get('/api/v2/accounts')
        .reply(200, { accounts: [] });

      const accounts = await client.getAccounts();

      expect(accounts).toHaveLength(0);
    });
  });

  describe('createAccountClient', () => {
    it('should create account client with correct headers', () => {
      const accountId = 123;
      const accountClient = client.createAccountClient(accountId);

      expect(accountClient.defaults.baseURL).toBe('https://api.harvestapp.com/v2');
      expect(accountClient.defaults.headers['Authorization']).toBe(`Bearer ${mockPAT}`);
      expect(accountClient.defaults.headers['Harvest-Account-Id']).toBe('123');
    });
  });

  describe('fetchEndpoint', () => {
    it('should fetch single page of data', async () => {
      const accountClient = client.createAccountClient(123);
      
      const mockData = {
        users: [
          { id: 1, name: 'User 1' },
          { id: 2, name: 'User 2' },
        ],
        links: {},
      };

      nock('https://api.harvestapp.com')
        .get('/v2/users')
        .query({ page: 1, per_page: 100 })
        .reply(200, mockData);

      const results = await client.fetchEndpoint(accountClient, 'users');

      expect(results).toHaveLength(2);
      expect(results[0]).toEqual({ id: 1, name: 'User 1' });
    });

    it('should fetch multiple pages of data', async () => {
      const accountClient = client.createAccountClient(123);
      
      const page1Data = {
        users: [{ id: 1, name: 'User 1' }],
        links: { next: 'https://api.harvestapp.com/v2/users?page=2' },
      };

      const page2Data = {
        users: [{ id: 2, name: 'User 2' }],
        links: {},
      };

      nock('https://api.harvestapp.com')
        .get('/v2/users')
        .query({ page: 1, per_page: 100 })
        .reply(200, page1Data)
        .get('/v2/users')
        .query({ page: 2, per_page: 100 })
        .reply(200, page2Data);

      const results = await client.fetchEndpoint(accountClient, 'users');

      expect(results).toHaveLength(2);
      expect(results[0].id).toBe(1);
      expect(results[1].id).toBe(2);
    });

    it('should return empty array for 404 endpoint', async () => {
      const accountClient = client.createAccountClient(123);

      nock('https://api.harvestapp.com')
        .get('/v2/nonexistent')
        .query({ page: 1, per_page: 100 })
        .reply(404);

      const results = await client.fetchEndpoint(accountClient, 'nonexistent');

      expect(results).toHaveLength(0);
    });

    it('should throw error on 500 server error', async () => {
      const accountClient = client.createAccountClient(123);

      nock('https://api.harvestapp.com')
        .get('/v2/users')
        .query({ page: 1, per_page: 100 })
        .reply(500, { error: 'Internal Server Error' });

      await expect(client.fetchEndpoint(accountClient, 'users')).rejects.toThrow(
        'Failed to fetch users: 500 Internal Server Error'
      );
    });

    it('should handle data with different resource keys', async () => {
      const accountClient = client.createAccountClient(123);
      
      const mockData = {
        projects: [
          { id: 1, name: 'Project 1' },
          { id: 2, name: 'Project 2' },
        ],
        links: {},
      };

      nock('https://api.harvestapp.com')
        .get('/v2/projects')
        .query({ page: 1, per_page: 100 })
        .reply(200, mockData);

      const results = await client.fetchEndpoint(accountClient, 'projects');

      expect(results).toHaveLength(2);
      expect(results[0].name).toBe('Project 1');
    });
  });
});
