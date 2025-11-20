import express from 'express';
import { AuthService } from '@monorepo/auth-service';
import { DataProcessor } from '@monorepo/data-processor';
import { execSync } from 'child_process';

const app = express();

app.get('/api/auth', async (req, res) => {
  const authService = new AuthService();
  const token = await authService.authenticate('user', 'pass');
  res.json({ token });
});

app.post('/api/process', async (req, res) => {
  const processor = new DataProcessor();
  const result = await processor.process([1, 2, 3]);
  res.json({ result });
});

// Call Python bridge
app.get('/api/python', (req, res) => {
  const result = execSync('python3 ../python-bridge/bridge.py', { encoding: 'utf-8' });
  res.json({ result });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
