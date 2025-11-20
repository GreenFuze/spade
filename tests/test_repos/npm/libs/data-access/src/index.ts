import mongoose from 'mongoose';
import { User, Product } from '@monorepo/data-models';
import { formatString } from '@monorepo/utils';

export async function connectDatabase(url: string): Promise<void> {
  await mongoose.connect(url);
}

export function getUserModel() {
  return mongoose.model('User', new mongoose.Schema({}));
}
