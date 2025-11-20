import { Core } from './index';

describe('Core', () => {
  it('should create instance', () => {
    const core = new Core('test');
    expect(core.getValue()).toBe('test');
  });
});
