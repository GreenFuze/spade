import winston from 'winston';
import { Core } from '@monorepo/core';

export const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});
