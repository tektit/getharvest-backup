/**
 * Simple logger utility for consistent console output
 */
export class Logger {
  static info(message: string): void {
    console.log(message);
  }

  static success(message: string): void {
    console.log(`✅ ${message}`);
  }

  static warning(message: string): void {
    console.log(`⚠️  ${message}`);
  }

  static error(message: string): void {
    console.error(`❌ ${message}`);
  }

  static debug(message: string, indent: number = 0): void {
    const spacing = '  '.repeat(indent);
    console.log(`${spacing}${message}`);
  }
}
