import React from 'react';
import { Button } from '@monorepo/shared-ui';
import { AuthService } from '@monorepo/auth-service';
import { ApiClient } from '@monorepo/api-client';

export function App() {
  return (
    <div>
      <Button label="Click me" />
    </div>
  );
}
