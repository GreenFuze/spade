import { execSync } from 'child_process';

export function buildAll() {
  execSync('npm run build --workspaces', { stdio: 'inherit' });
}
