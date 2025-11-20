import { formatString, processCore } from './index';
import { Core } from '@monorepo/core';

describe('Utils', () => {
  it('should format string', () => {
    expect(formatString('test')).toBe('[test]');
  });

  it('should process core', () => {
    const core = new Core('test');
    expect(processCore(core)).toBe('[test]');
  });
});
