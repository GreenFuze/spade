import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import { Core } from '@monorepo/core';
import { formatString } from '@monorepo/utils';

export function generateToken(payload: any): string {
  return jwt.sign(payload, 'secret');
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}
