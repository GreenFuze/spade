import { execSync } from 'child_process';
import { generateToken } from '@monorepo/auth-lib';
import { User } from '@monorepo/data-models';

export class AuthService {
  async authenticate(username: string, password: string): Promise<string> {
    // Call Python script for advanced validation
    const result = execSync(`python3 scripts/validate.py ${username}`, { encoding: 'utf-8' });
    if (result.trim() === 'valid') {
      return generateToken({ username });
    }
    throw new Error('Invalid credentials');
  }
}
