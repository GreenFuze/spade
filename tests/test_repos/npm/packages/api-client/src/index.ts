import axios from 'axios';
import { Core } from '@monorepo/core';
import { formatString } from '@monorepo/utils';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get(endpoint: string): Promise<any> {
    const response = await axios.get(`${this.baseUrl}${endpoint}`);
    return response.data;
  }
}
