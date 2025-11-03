#!/usr/bin/env node

import { Command } from 'commander';
import { HarvestClient } from './harvest-client.js';
import { BackupService } from './backup-service.js';
import { promises as fs } from 'fs';
import path from 'path';

const program = new Command();

program
  .name('harvest-backup')
  .description('Backup tool for Harvest Time Tracking data')
  .version('1.0.0')
  .requiredOption('-t, --token <token>', 'Harvest Personal Access Token (PAT)')
  .option('-o, --output <directory>', 'Output directory for backups', './backups')
  .action(async (options) => {
    try {
      console.log('🚀 Starting Harvest backup...\n');
      
      const { token, output } = options;

      // Ensure output directory exists
      await fs.mkdir(output, { recursive: true });

      const client = new HarvestClient(token);
      const backupService = new BackupService(client, output);

      await backupService.backupAll();

      console.log(`\n✅ All backups saved to: ${path.resolve(output)}`);
    } catch (error) {
      if (error instanceof Error) {
        console.error(`\n❌ Error: ${error.message}`);
      } else {
        console.error('\n❌ An unknown error occurred');
      }
      process.exit(1);
    }
  });

program.parse();
