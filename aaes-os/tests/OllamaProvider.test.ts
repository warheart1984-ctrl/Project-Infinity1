import assert from 'node:assert/strict';
import test from 'node:test';

import { OllamaProvider } from '../src/model/OllamaProvider.js';

test('root OllamaProvider returns the validated proposal shape', async () => {
  const fetchImplementation: typeof globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        response: JSON.stringify({
          schemaVersion: '1',
          goal: 'fix',
          operations: [
            {
              file: 'src/index.ts',
              type: 'update',
              content: 'export const fixed = true;',
            },
          ],
        }),
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    );
  const provider = new OllamaProvider({ fetch: fetchImplementation });

  const proposal = await provider.generate('Fix src/index.ts');

  assert.equal(proposal.goal, 'fix');
  assert.equal(proposal.operations[0]?.file, 'src/index.ts');
  assert.equal('raw' in proposal, false);
});
