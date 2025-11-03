import { describe, it, expect, beforeEach, afterEach, vi, type Mock } from 'vitest';
import { Logger } from '../logger.js';

describe('Logger', () => {
  let logSpy: Mock;
  let errorSpy: Mock;

  beforeEach(() => {
    logSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    logSpy.mockRestore();
    errorSpy.mockRestore();
  });

  describe('info', () => {
    it('should log info messages', () => {
      Logger.info('Test message');
      expect(logSpy).toHaveBeenCalledWith('Test message');
    });
  });

  describe('success', () => {
    it('should log success messages with checkmark', () => {
      Logger.success('Operation complete');
      expect(logSpy).toHaveBeenCalledWith('✅ Operation complete');
    });
  });

  describe('warning', () => {
    it('should log warning messages with icon', () => {
      Logger.warning('Warning message');
      expect(logSpy).toHaveBeenCalledWith('⚠️  Warning message');
    });
  });

  describe('error', () => {
    it('should log error messages with icon', () => {
      Logger.error('Error message');
      expect(errorSpy).toHaveBeenCalledWith('❌ Error message');
    });
  });

  describe('debug', () => {
    it('should log debug messages without indent', () => {
      Logger.debug('Debug message');
      expect(logSpy).toHaveBeenCalledWith('Debug message');
    });

    it('should log debug messages with indent', () => {
      Logger.debug('Indented message', 2);
      expect(logSpy).toHaveBeenCalledWith('    Indented message');
    });

    it('should support multiple indent levels', () => {
      Logger.debug('Level 1', 1);
      expect(logSpy).toHaveBeenCalledWith('  Level 1');
      
      Logger.debug('Level 3', 3);
      expect(logSpy).toHaveBeenCalledWith('      Level 3');
    });
  });
});
