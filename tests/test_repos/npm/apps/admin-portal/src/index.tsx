import React from 'react';
import { Button } from '@monorepo/shared-ui';
import { Analytics } from '@monorepo/analytics';

export function AdminPortal() {
  const analytics = new Analytics();
  return (
    <div>
      <Button label="Admin" />
    </div>
  );
}
