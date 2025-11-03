import axios, { AxiosInstance } from 'axios';

export interface HarvestAccount {
  id: number;
  name: string;
  product: string;
}

export interface AccountsResponse {
  accounts: HarvestAccount[];
}

export class HarvestClient {
  private client: AxiosInstance;

  constructor(private pat: string) {
    this.client = axios.create({
      baseURL: 'https://id.getharvest.com/api/v2',
      headers: {
        'Authorization': `Bearer ${pat}`,
        'User-Agent': 'Harvest Backup Tool (https://github.com/tektit/getharvest-backup)',
      },
    });
  }

  async getAccounts(): Promise<HarvestAccount[]> {
    try {
      const response = await this.client.get<AccountsResponse>('/accounts');
      return response.data.accounts;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`Failed to fetch accounts: ${error.response?.status} ${error.response?.statusText}`);
      }
      throw error;
    }
  }

  createAccountClient(accountId: number): AxiosInstance {
    return axios.create({
      baseURL: `https://api.harvestapp.com/v2`,
      headers: {
        'Authorization': `Bearer ${this.pat}`,
        'Harvest-Account-Id': accountId.toString(),
        'User-Agent': 'Harvest Backup Tool (https://github.com/tektit/getharvest-backup)',
      },
    });
  }

  async fetchEndpoint(accountClient: AxiosInstance, endpoint: string): Promise<any[]> {
    const results: any[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      try {
        const response = await accountClient.get(endpoint, {
          params: { page, per_page: 100 },
        });

        const data = response.data;
        
        // Harvest API returns data in different formats
        // Most endpoints have a key matching the resource name
        const resourceKey = Object.keys(data).find(key => 
          Array.isArray(data[key]) && key !== 'links'
        );

        if (resourceKey && Array.isArray(data[resourceKey])) {
          results.push(...data[resourceKey]);
        }

        // Check pagination
        hasMore = data.links?.next !== undefined && data.links?.next !== null;
        page++;

        // Add a small delay to respect rate limits
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 404) {
            // Endpoint doesn't exist for this account
            break;
          }
          throw new Error(`Failed to fetch ${endpoint}: ${error.response?.status} ${error.response?.statusText}`);
        }
        throw error;
      }
    }

    return results;
  }
}
