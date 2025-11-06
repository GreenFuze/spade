import express from 'express';

const app = express();
app.get('/health', (_req, res) => res.json({ ok: true }));

export function start() {
  return app.listen(3000, () => console.log('api-server up'));
}

