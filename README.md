# getharvest-backup

A TypeScript-based backup tool for Harvest Time Tracking data that creates a complete backup of all data exposed via the Harvest API v2.

## Features

- 🔍 Auto-discovers all accounts from your Harvest Personal Access Token (PAT)
- 📦 Backs up all available data types from the Harvest API
- 🗂️ Organizes backups in a clear folder structure by account and data type
- 🐳 Runs in Docker for easy deployment
- 🚀 Modern TypeScript CLI application

## Prerequisites

- Node.js 20+ (for local development)
- Docker (for containerized execution)
- Harvest Personal Access Token (PAT)

## Getting Your Harvest PAT

1. Log in to your Harvest account
2. Go to Settings → Developers
3. Create a new Personal Access Token
4. Copy the token for use with this tool

## Installation & Usage

### Building the Application

Before using Docker, you need to build the application:

```bash
# Build TypeScript and prepare for Docker
npm install
npm run build
npm install --production

# Then build Docker image
docker build -t harvest-backup .
```

Or use the provided build script:

```bash
./build.sh
```

### Option 1: Using Docker (Recommended)

1. Build the Docker image:
```bash
docker build -t harvest-backup .
```

2. Run the backup:
```bash
docker run -v $(pwd)/backups:/app/backups harvest-backup -t YOUR_HARVEST_PAT -o /app/backups
```

### Option 2: Using Docker Compose

1. Create a `.env` file with your token:
```bash
echo "HARVEST_TOKEN=your_harvest_pat_here" > .env
```

2. Run with docker-compose:
```bash
docker-compose up
```

### Option 3: Local Development

1. Install dependencies:
```bash
npm install
```

2. Run the backup:
```bash
npm run dev -- -t YOUR_HARVEST_PAT -o ./backups
```

Or build and run:
```bash
npm run build
npm start -- -t YOUR_HARVEST_PAT -o ./backups
```

## CLI Options

```
Usage: harvest-backup [options]

Backup tool for Harvest Time Tracking data

Options:
  -V, --version          output the version number
  -t, --token <token>    Harvest Personal Access Token (PAT) (required)
  -o, --output <directory>  Output directory for backups (default: "./backups")
  -h, --help             display help for command
```

## Backup Structure

The tool creates the following directory structure:

```
backups/
├── {account_id}-{account_name}/
│   ├── account.json
│   ├── company.json
│   ├── users.json
│   ├── clients.json
│   ├── projects.json
│   ├── tasks.json
│   ├── time_entries.json
│   ├── expenses.json
│   ├── invoices.json
│   └── ... (other data types)
```

## Backed Up Data Types

The tool backs up the following data from each account based on the [official Harvest API specification](https://help.getharvest.com/api-v2/):

**Core Data**
- Company information
- Users (including current user details and project assignments)
- Clients and contacts
- Projects (including task and user assignments)
- Tasks
- Time entries
- Expenses and expense categories
- Invoices and invoice item categories
- Estimates and estimate item categories
- Roles

**Reports**
- Project budget report

**Note on Reports**: Time-based and expense reports (e.g., time by client, expenses by project) require specific date range parameters and are designed for ad-hoc reporting rather than full data backups. These are not included in the automatic backup. The underlying data is captured through the time entries and expenses endpoints.

**Note on Nested Resources**: Resources like invoice messages, invoice payments, and estimate messages are accessible only through their parent resources (e.g., `/invoices/{id}/messages`) and are not available as standalone list endpoints. These may be added in a future version by iterating through parent resources.

## How It Works

1. **Account Discovery**: Connects to `https://id.getharvest.com/api/v2/accounts` to discover all accounts associated with your PAT
2. **Data Fetching**: For each account, iterates through all Harvest API endpoints
3. **Pagination Handling**: Automatically handles pagination to fetch all records
4. **Rate Limiting**: Includes delays to respect Harvest API rate limits
5. **File Organization**: Saves data as JSON files organized by account and data type

## Development

### Running Tests

The project includes comprehensive test coverage using Vitest:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Project Structure

```
src/
├── index.ts           # CLI entry point
├── harvest-client.ts  # Harvest API client
└── backup-service.ts  # Backup orchestration logic
```

### Technologies Used

- **TypeScript**: Type-safe development
- **tsx**: Fast TypeScript execution
- **Commander**: CLI framework
- **Axios**: HTTP client for API calls

## License

Apache-2.0
