import axios, { AxiosInstance } from 'axios';
import { API_CONFIG } from './config.js';

export interface HarvestAccount {
  id: number;
  name: string;
  product: string;
}

export interface AccountsResponse {
  accounts: HarvestAccount[];
}

/**
 * Client for interacting with the Harvest API
 */
export class HarvestClient {
  private readonly idClient: AxiosInstance;

  constructor(private readonly pat: string) {
    this.idClient = this.createIdClient();
  }

  /**
   * Creates an Axios client for the Harvest ID API
   */
  private createIdClient(): AxiosInstance {
    return axios.create({
      baseURL: API_CONFIG.ID_BASE_URL,
      headers: {
        'Authorization': `Bearer ${this.pat}`,
        'User-Agent': API_CONFIG.USER_AGENT,
      },
    });
  }

  /**
   * Fetches all accounts associated with the PAT
   */
  async getAccounts(): Promise<HarvestAccount[]> {
    try {
      const response = await this.idClient.get<AccountsResponse>('/accounts');
      return response.data.accounts;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`Failed to fetch accounts: ${error.response?.status} ${error.response?.statusText}`);
      }
      throw error;
    }
  }

  /**
   * Creates an Axios client for a specific Harvest account
   */
  createAccountClient(accountId: number): AxiosInstance {
    return axios.create({
      baseURL: API_CONFIG.HARVEST_BASE_URL,
      headers: {
        'Authorization': `Bearer ${this.pat}`,
        'Harvest-Account-Id': accountId.toString(),
        'User-Agent': API_CONFIG.USER_AGENT,
      },
    });
  }

  /**
   * Fetches all data from a paginated endpoint
   * @param accountClient - Axios client configured for the account
   * @param endpoint - API endpoint to fetch from
   * @returns Array of all records from all pages
   */
  async fetchEndpoint(accountClient: AxiosInstance, endpoint: string): Promise<any[]> {
    const results: any[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      try {
        const response = await accountClient.get(endpoint, {
          params: { 
            page, 
            per_page: API_CONFIG.PER_PAGE,
          },
        });

        const data = response.data;
        
        // Extract resource data - Harvest API returns data with a key matching the resource name
        const resourceKey = this.findResourceKey(data);
        if (resourceKey && Array.isArray(data[resourceKey])) {
          results.push(...data[resourceKey]);
        }

        // Check if there are more pages
        hasMore = this.hasNextPage(data);
        page++;

        // Respect rate limits
        await this.delay(API_CONFIG.RATE_LIMIT_DELAY);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 404) {
            // Endpoint doesn't exist for this account - not an error
            break;
          }
          throw new Error(`Failed to fetch ${endpoint}: ${error.response?.status} ${error.response?.statusText}`);
        }
        throw error;
      }
    }

    return results;
  }

  /**
   * Finds the resource key in the API response
   * (the key containing the array of data items)
   */
  private findResourceKey(data: any): string | undefined {
    return Object.keys(data).find(key => 
      Array.isArray(data[key]) && key !== 'links'
    );
  }

  /**
   * Checks if there's a next page in the pagination
   */
  private hasNextPage(data: any): boolean {
    return data.links?.next !== undefined && data.links?.next !== null;
  }

  /**
   * Delays execution for the specified milliseconds
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
