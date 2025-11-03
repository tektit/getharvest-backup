import { HarvestClient, HarvestAccount } from './harvest-client.js';
import { AxiosInstance } from 'axios';
import { promises as fs } from 'fs';
import path from 'path';

export class BackupService {
  // Common Harvest API endpoints based on https://help.getharvest.com/api-v2/
  private endpoints = [
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
  ];

  constructor(
    private client: HarvestClient,
    private outputDir: string
  ) {}

  async backupAll(): Promise<void> {
    console.log('🔍 Discovering accounts...');
    const accounts = await this.client.getAccounts();
    
    if (accounts.length === 0) {
      console.log('⚠️  No accounts found');
      return;
    }

    console.log(`✅ Found ${accounts.length} account(s)`);

    for (const account of accounts) {
      await this.backupAccount(account);
    }

    console.log('✅ Backup completed successfully!');
  }

  private async backupAccount(account: HarvestAccount): Promise<void> {
    console.log(`\n📦 Backing up account: ${account.name} (ID: ${account.id})`);
    
    const accountDir = path.join(
      this.outputDir,
      this.sanitizeFilename(`${account.id}-${account.name}`)
    );
    
    await fs.mkdir(accountDir, { recursive: true });

    // Save account metadata
    await this.saveJson(
      path.join(accountDir, 'account.json'),
      account
    );

    const accountClient = this.client.createAccountClient(account.id);

    for (const endpoint of this.endpoints) {
      await this.backupEndpoint(accountClient, accountDir, endpoint);
    }
  }

  private async backupEndpoint(
    accountClient: AxiosInstance,
    accountDir: string,
    endpoint: string
  ): Promise<void> {
    try {
      console.log(`  📄 Backing up ${endpoint}...`);
      const data = await this.client.fetchEndpoint(accountClient, endpoint);
      
      if (data.length > 0) {
        const filename = `${endpoint.replace(/\//g, '_')}.json`;
        await this.saveJson(path.join(accountDir, filename), data);
        console.log(`    ✅ Saved ${data.length} record(s)`);
      } else {
        console.log(`    ℹ️  No data found`);
      }
    } catch (error) {
      if (error instanceof Error) {
        console.log(`    ⚠️  Skipped: ${error.message}`);
      } else {
        console.log(`    ⚠️  Skipped: Unknown error`);
      }
    }
  }

  private async saveJson(filepath: string, data: any): Promise<void> {
    await fs.writeFile(
      filepath,
      JSON.stringify(data, null, 2),
      'utf-8'
    );
  }

  private sanitizeFilename(filename: string): string {
    return filename.replace(/[^a-z0-9_\-]/gi, '_');
  }
}
