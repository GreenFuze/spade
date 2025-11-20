import { Core } from '@monorepo/core';

export function formatString(value: string): string {
  return `[${value}]`;
}

export function processCore(core: Core): string {
  return formatString(core.getValue());
}
