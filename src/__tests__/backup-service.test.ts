import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { BackupService } from '../backup-service.js';
import { HarvestClient, HarvestAccount } from '../harvest-client.js';
import { promises as fs } from 'fs';
import path from 'path';
import { tmpdir } from 'os';

describe('BackupService', () => {
  let mockClient: HarvestClient;
  let backupService: BackupService;
  let testOutputDir: string;

  beforeEach(async () => {
    // Create a temporary directory for tests
    testOutputDir = path.join(tmpdir(), `harvest-backup-test-${Date.now()}`);
    await fs.mkdir(testOutputDir, { recursive: true });

    // Create a mock client
    mockClient = {
      getAccounts: vi.fn(),
      createAccountClient: vi.fn(),
      fetchEndpoint: vi.fn(),
    } as any;

    backupService = new BackupService(mockClient, testOutputDir);
  });

  afterEach(async () => {
    // Clean up test directory
    try {
      await fs.rm(testOutputDir, { recursive: true, force: true });
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  describe('backupAll', () => {
    it('should handle no accounts', async () => {
      vi.mocked(mockClient.getAccounts).mockResolvedValue([]);

      await backupService.backupAll();

      expect(mockClient.getAccounts).toHaveBeenCalledTimes(1);
      expect(mockClient.createAccountClient).not.toHaveBeenCalled();
    });

    it('should backup single account', async () => {
      const mockAccount: HarvestAccount = {
        id: 123,
        name: 'Test Account',
        product: 'harvest',
      };

      vi.mocked(mockClient.getAccounts).mockResolvedValue([mockAccount]);
      vi.mocked(mockClient.createAccountClient).mockReturnValue({} as any);
      vi.mocked(mockClient.fetchEndpoint).mockResolvedValue([]);

      await backupService.backupAll();

      expect(mockClient.getAccounts).toHaveBeenCalledTimes(1);
      expect(mockClient.createAccountClient).toHaveBeenCalledWith(123);

      // Verify account directory was created
      const accountDir = path.join(testOutputDir, '123-Test_Account');
      const accountDirExists = await fs.access(accountDir).then(() => true).catch(() => false);
      expect(accountDirExists).toBe(true);

      // Verify account.json was created
      const accountJsonPath = path.join(accountDir, 'account.json');
      const accountJson = await fs.readFile(accountJsonPath, 'utf-8');
      const savedAccount = JSON.parse(accountJson);
      expect(savedAccount).toEqual(mockAccount);
    });

    it('should backup multiple accounts', async () => {
      const mockAccounts: HarvestAccount[] = [
        { id: 1, name: 'Account 1', product: 'harvest' },
        { id: 2, name: 'Account 2', product: 'harvest' },
      ];

      vi.mocked(mockClient.getAccounts).mockResolvedValue(mockAccounts);
      vi.mocked(mockClient.createAccountClient).mockReturnValue({} as any);
      vi.mocked(mockClient.fetchEndpoint).mockResolvedValue([]);

      await backupService.backupAll();

      expect(mockClient.createAccountClient).toHaveBeenCalledTimes(2);
      expect(mockClient.createAccountClient).toHaveBeenCalledWith(1);
      expect(mockClient.createAccountClient).toHaveBeenCalledWith(2);

      // Verify both account directories exist
      const account1DirExists = await fs.access(path.join(testOutputDir, '1-Account_1')).then(() => true).catch(() => false);
      const account2DirExists = await fs.access(path.join(testOutputDir, '2-Account_2')).then(() => true).catch(() => false);
      expect(account1DirExists).toBe(true);
      expect(account2DirExists).toBe(true);
    });

    it('should backup endpoint data when available', async () => {
      const mockAccount: HarvestAccount = {
        id: 456,
        name: 'Data Account',
        product: 'harvest',
      };

      const mockUsers = [
        { id: 1, name: 'User 1' },
        { id: 2, name: 'User 2' },
      ];

      vi.mocked(mockClient.getAccounts).mockResolvedValue([mockAccount]);
      vi.mocked(mockClient.createAccountClient).mockReturnValue({} as any);
      
      // Mock fetchEndpoint to return data for 'users' and empty for others
      vi.mocked(mockClient.fetchEndpoint).mockImplementation(async (client, endpoint) => {
        if (endpoint === 'users') {
          return mockUsers;
        }
        return [];
      });

      await backupService.backupAll();

      // Verify users.json was created
      const usersJsonPath = path.join(testOutputDir, '456-Data_Account', 'users.json');
      const usersJson = await fs.readFile(usersJsonPath, 'utf-8');
      const savedUsers = JSON.parse(usersJson);
      expect(savedUsers).toEqual(mockUsers);
    });

    it('should handle endpoint errors gracefully', async () => {
      const mockAccount: HarvestAccount = {
        id: 789,
        name: 'Error Account',
        product: 'harvest',
      };

      vi.mocked(mockClient.getAccounts).mockResolvedValue([mockAccount]);
      vi.mocked(mockClient.createAccountClient).mockReturnValue({} as any);
      
      // Mock fetchEndpoint to throw error for first endpoint
      let callCount = 0;
      vi.mocked(mockClient.fetchEndpoint).mockImplementation(async () => {
        callCount++;
        if (callCount === 1) {
          throw new Error('API Error');
        }
        return [];
      });

      // Should not throw, just log and continue
      await expect(backupService.backupAll()).resolves.not.toThrow();

      // Verify account was still created
      const accountDirExists = await fs.access(path.join(testOutputDir, '789-Error_Account')).then(() => true).catch(() => false);
      expect(accountDirExists).toBe(true);
    });

    it('should sanitize account names for directories', async () => {
      const mockAccount: HarvestAccount = {
        id: 100,
        name: 'Test/Account:With*Special?Chars',
        product: 'harvest',
      };

      vi.mocked(mockClient.getAccounts).mockResolvedValue([mockAccount]);
      vi.mocked(mockClient.createAccountClient).mockReturnValue({} as any);
      vi.mocked(mockClient.fetchEndpoint).mockResolvedValue([]);

      await backupService.backupAll();

      // Verify sanitized directory was created
      const sanitizedDirExists = await fs.access(
        path.join(testOutputDir, '100-Test_Account_With_Special_Chars')
      ).then(() => true).catch(() => false);
      expect(sanitizedDirExists).toBe(true);
    });

    it('should handle nested endpoint paths', async () => {
      const mockAccount: HarvestAccount = {
        id: 200,
        name: 'Nested Account',
        product: 'harvest',
      };

      const mockData = [{ id: 1, data: 'test' }];

      vi.mocked(mockClient.getAccounts).mockResolvedValue([mockAccount]);
      vi.mocked(mockClient.createAccountClient).mockReturnValue({} as any);
      
      vi.mocked(mockClient.fetchEndpoint).mockImplementation(async (client, endpoint) => {
        if (endpoint === 'users/me') {
          return mockData;
        }
        return [];
      });

      await backupService.backupAll();

      // Verify nested endpoint file was created with sanitized name
      const nestedFilePath = path.join(testOutputDir, '200-Nested_Account', 'users_me.json');
      const fileExists = await fs.access(nestedFilePath).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);

      const fileContent = await fs.readFile(nestedFilePath, 'utf-8');
      const savedData = JSON.parse(fileContent);
      expect(savedData).toEqual(mockData);
    });
  });
});
