import { Registry } from 'prom-client';
import { formatString } from '@monorepo/utils';

export const register = new Registry();

export function createCounter(name: string) {
  return new register.Counter({
    name: formatString(name),
    help: 'Counter metric'
  });
}
