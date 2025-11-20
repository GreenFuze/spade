import { createCounter } from '@monorepo/metrics-lib';
import nativeAddon from '@monorepo/native-addon';

export class Analytics {
  private counter = createCounter('analytics_events');

  track(event: string): void {
    this.counter.inc();
    nativeAddon.processEvent(event);
  }
}
