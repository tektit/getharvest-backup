import { HarvestClient, HarvestAccount } from './harvest-client.js';
import { AxiosInstance } from 'axios';
import { promises as fs } from 'fs';
import path from 'path';
import { HARVEST_ENDPOINTS } from './config.js';
import { Logger } from './logger.js';

/**
 * Service for orchestrating backup of Harvest data
 */
export class BackupService {
  constructor(
    private readonly client: HarvestClient,
    private readonly outputDir: string
  ) {}

  /**
   * Backs up all accounts and their data
   */
  async backupAll(): Promise<void> {
    Logger.info('🔍 Discovering accounts...');
    const accounts = await this.client.getAccounts();
    
    if (accounts.length === 0) {
      Logger.warning('No accounts found');
      return;
    }

    Logger.success(`Found ${accounts.length} account(s)`);

    for (const account of accounts) {
      await this.backupAccount(account);
    }

    Logger.success('Backup completed successfully!');
  }

  /**
   * Backs up a single account's data
   */
  private async backupAccount(account: HarvestAccount): Promise<void> {
    Logger.info(`\n📦 Backing up account: ${account.name} (ID: ${account.id})`);
    
    const accountDir = this.getAccountDirectory(account);
    await fs.mkdir(accountDir, { recursive: true });

    // Save account metadata
    await this.saveJson(
      path.join(accountDir, 'account.json'),
      account
    );

    const accountClient = this.client.createAccountClient(account.id);

    for (const endpoint of HARVEST_ENDPOINTS) {
      await this.backupEndpoint(accountClient, accountDir, endpoint);
    }
  }

  /**
   * Backs up data from a single endpoint
   */
  private async backupEndpoint(
    accountClient: AxiosInstance,
    accountDir: string,
    endpoint: string
  ): Promise<void> {
    try {
      Logger.debug(`📄 Backing up ${endpoint}...`, 1);
      const data = await this.client.fetchEndpoint(accountClient, endpoint);
      
      if (data.length > 0) {
        const filename = this.getEndpointFilename(endpoint);
        await this.saveJson(path.join(accountDir, filename), data);
        Logger.debug(`✅ Saved ${data.length} record(s)`, 2);
      } else {
        Logger.debug('ℹ️  No data found', 2);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      Logger.debug(`⚠️  Skipped: ${message}`, 2);
    }
  }

  /**
   * Gets the directory path for an account
   */
  private getAccountDirectory(account: HarvestAccount): string {
    const sanitizedName = this.sanitizeFilename(`${account.id}-${account.name}`);
    return path.join(this.outputDir, sanitizedName);
  }

  /**
   * Gets the filename for an endpoint
   */
  private getEndpointFilename(endpoint: string): string {
    return `${endpoint.replace(/\//g, '_')}.json`;
  }

  /**
   * Saves data as JSON to a file
   */
  private async saveJson(filepath: string, data: any): Promise<void> {
    await fs.writeFile(
      filepath,
      JSON.stringify(data, null, 2),
      'utf-8'
    );
  }

  /**
   * Sanitizes a string for use as a filename
   */
  private sanitizeFilename(filename: string): string {
    return filename.replace(/[^a-z0-9_\-]/gi, '_');
  }
}
