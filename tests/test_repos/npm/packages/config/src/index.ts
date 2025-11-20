import { formatString } from '@monorepo/utils';

export interface Config {
  apiUrl: string;
  timeout: number;
}

export function loadConfig(): Config {
  return {
    apiUrl: formatString('http://localhost:3000'),
    timeout: 5000
  };
}
