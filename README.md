# getharvest-backup

Backup tool for Harvest Time Tracking data using the Harvest API v2. This tool automatically discovers all your Harvest accounts and backs up all data from all endpoints, including invoices, estimates, time entries, projects, clients, and more.

**Fully compliant with the Harvest API v2 OpenAPI specification** - All endpoints have been verified against the official OpenAPI spec to ensure complete data coverage.

## Features

- **Auto-discovery**: Automatically discovers all Harvest accounts using your Personal Access Token (PAT)
- **Comprehensive Backup**: Backs up all Harvest API v2 endpoints including:
  - Clients
  - Contacts
  - Projects and assignments
  - Tasks
  - Time entries
  - Users and assignments (including `/users/me`)
  - Expenses and expense categories
  - Invoices (with PDF downloads) and invoice item categories
  - Estimates (with PDF downloads) and estimate item categories
  - Roles
  - Company settings
- **Incremental Backup**: Binary artifacts (PDFs) are only downloaded if they don't already exist or have changed
- **Rate Limiting**: Automatically handles Harvest API rate limits (100 requests per 15 seconds)
- **Error Handling**: Robust error handling with retries and exponential backoff
- **Dry Run Mode**: Test without actually writing files
- **Docker Support**: Run in a containerized environment

## Requirements

- Python 3.13 or higher
- Personal Access Token (PAT) from [Harvest ID](https://id.getharvest.com/developers)

## Installation

### From Source

```bash
git clone https://github.com/tektit/getharvest-backup.git
cd getharvest-backup
pip install -r requirements.txt
```

### Using Docker

```bash
docker build -t getharvest-backup .
```

## Usage

### Command Line

```bash
# Using environment variable for PAT
export HARVEST_PAT=your_personal_access_token
python -m harvest_backup.cli --output ./backup

# Or specify PAT directly
python -m harvest_backup.cli --pat your_personal_access_token --output ./backup

# Dry run mode (test without writing files)
python -m harvest_backup.cli --pat your_pat --dry-run

# Verbose logging
python -m harvest_backup.cli --pat your_pat --verbose
```

### Docker

```bash
# Build and run
docker build -t getharvest-backup .
docker run --rm \
  -e HARVEST_PAT=your_personal_access_token \
  -v $(pwd)/backup:/backup \
  getharvest-backup \
  --output /backup
```

### Docker Compose

```bash
# Set PAT in environment or .env file
export HARVEST_PAT=your_personal_access_token

# Run backup
docker-compose up
```

The backup will be stored in the `./backup` directory by default.

## Backup Output Structure

```
backup/
├── accounts.json                    # List of all discovered accounts
├── harvest_account_12345/
│   ├── clients/
│   │   ├── list.json               # All clients
│   │   └── 123.json                # Individual client detail
│   ├── contacts/
│   │   ├── list.json               # All contacts
│   │   └── 456.json                # Individual contact detail
│   ├── projects/
│   │   ├── list.json
│   │   ├── 456.json
│   │   ├── 456_user_assignments.json
│   │   ├── 456_task_assignments.json
│   │   └── artifacts/             # Project receipts (incremental)
│   ├── tasks/
│   │   ├── list.json
│   │   └── 789.json
│   ├── time_entries/
│   │   ├── list.json
│   │   └── 100.json
│   ├── users/
│   │   ├── list.json
│   │   ├── 1.json
│   │   ├── 1_billable_rates.json
│   │   ├── 1_cost_rates.json
│   │   ├── 1_project_assignments.json
│   │   └── 1_teammates.json
│   ├── users_me/
│   │   └── data.json               # Current user info
│   ├── users_me_project_assignments/
│   │   └── list.json               # Current user project assignments
│   ├── expenses/
│   │   ├── list.json
│   │   └── 200.json
│   ├── expense_categories/
│   │   ├── list.json
│   │   └── 300.json
│   ├── invoices/
│   │   ├── list.json
│   │   ├── 300.json
│   │   └── artifacts/
│   │       └── 300.pdf            # Invoice PDF (incremental)
│   ├── invoice_item_categories/
│   │   ├── list.json
│   │   └── 400.json
│   ├── estimates/
│   │   ├── list.json
│   │   ├── 400.json
│   │   └── artifacts/
│   │       └── 400.pdf            # Estimate PDF (incremental)
│   ├── estimate_item_categories/
│   │   ├── list.json
│   │   └── 500.json
│   ├── roles/
│   │   ├── list.json
│   │   └── 500.json
│   └── company/
│       └── data.json
└── harvest_account_67890/
    └── ...
```

## Incremental Backup

The tool uses incremental backup for binary artifacts (PDFs):

- **JSON files**: Always written (overwritten) to ensure data is up-to-date
- **PDF files**: Only downloaded if:
  - The file doesn't exist, or
  - The file exists but has a different hash (content changed)

Artifact manifests are stored in `.artifacts_manifest.json` in the backup root directory.

## API Endpoint Coverage

The tool backs up all Harvest API v2 data endpoints as defined in the official OpenAPI specification:

### Core Data Endpoints

- **Clients**: `/v2/clients` - All clients with full details
- **Contacts**: `/v2/contacts` - All client contacts (standalone endpoint)
- **Projects**: `/v2/projects` - All projects with user and task assignments
- **Tasks**: `/v2/tasks` - All tasks
- **Time Entries**: `/v2/time_entries` - All time entries
- **Users**: `/v2/users` - All users with nested resources:
  - Billable rates (`/v2/users/{id}/billable_rates`)
  - Cost rates (`/v2/users/{id}/cost_rates`)
  - Project assignments (`/v2/users/{id}/project_assignments`)
  - Teammates (`/v2/users/{id}/teammates`)
- **Current User**: 
  - `/v2/users/me` - Authenticated user information
  - `/v2/users/me/project_assignments` - Current user's project assignments
- **Expenses**: 
  - `/v2/expenses` - All expenses
  - `/v2/expense_categories` - All expense categories
- **Invoices**: 
  - `/v2/invoices` - All invoices with PDF downloads
  - `/v2/invoice_item_categories` - All invoice item categories
- **Estimates**: 
  - `/v2/estimates` - All estimates with PDF downloads
  - `/v2/estimate_item_categories` - All estimate item categories
- **Roles**: `/v2/roles` - All roles
- **Company**: `/v2/company` - Company settings (single resource)

### What's Not Included

- **Report endpoints** (`/v2/reports/*`): These require date range parameters and are analytical rather than raw data. They can be added as a future enhancement if needed.

All endpoints are backed up with full pagination support, ensuring complete data coverage even for accounts with thousands of records.

## Rate Limiting and Pagination

The tool automatically handles Harvest API rate limits and pagination:
- **Rate limit**: 100 requests per 15 seconds
- **Pagination**: Automatically handles pagination with up to 2000 items per page (maximum per Harvest API)
- **Pagination detection**: Supports both `next_page` (number) and `links.next` (URL) for maximum compatibility
- **Automatic retry**: Exponential backoff on rate limit errors (429)
- **Network retry**: Automatic retry on network errors
- **No retry**: Authentication errors (401, 403) are not retried

## Testing

The tool includes comprehensive test coverage (22 tests) covering:
- API client functionality (rate limiting, pagination, retries)
- Account discovery
- Backup executor
- File writer with incremental backup
- Error handling

Run tests with pytest:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .

# Run tests
pytest

# Run with coverage
pytest --cov=harvest_backup --cov-report=html
```

## Configuration

### Environment Variables

- `HARVEST_PAT`: Personal Access Token (can also be provided via `--pat` argument)

### Command Line Options

- `--pat`: Personal Access Token (overrides `HARVEST_PAT` env var)
- `--output`, `-o`: Output directory (default: `./backup`)
- `--user-agent`: User-Agent header value (default: `HarvestBackupTool/0.1.0`)
- `--dry-run`: Don't write files, just show what would be done
- `--verbose`, `-v`: Enable verbose logging

## Error Handling

The tool handles various error scenarios:

- **Rate limit errors (429)**: Automatic retry with backoff based on `Retry-After` header
- **Network errors**: Retry with exponential backoff
- **Authentication errors**: Clear error message, no retry
- **Missing accounts**: Skip and log warning
- **File write errors**: Log and continue with other endpoints

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:
- Code follows Python 3.13 best practices
- All tests pass
- Type hints are used throughout
- Code is formatted with black (line length 100)

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
