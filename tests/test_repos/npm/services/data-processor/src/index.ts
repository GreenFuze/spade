import init, { process_data } from '@monorepo/wasm-module';

export class DataProcessor {
  private wasmReady: Promise<void>;

  constructor() {
    this.wasmReady = init();
  }

  async process(data: number[]): Promise<number[]> {
    await this.wasmReady;
    return process_data(data);
  }
}
