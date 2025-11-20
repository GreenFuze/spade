import { User } from '@monorepo/data-models';

export class NotificationService {
  send(user: User, message: string): void {
    console.log(`Sending to ${user.name}: ${message}`);
  }
}
