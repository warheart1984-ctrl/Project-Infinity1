import { describe, expect, it, vi } from 'vitest';

import { ArchitectAgent } from './architectAgent.js';
import type { AgentContract, ModelProvider, ModelProposal } from './types.js';

const PROPOSAL: ModelProposal = {
  schemaVersion: '1',
  goal: 'fix',
  operations: [{ file: 'src/index.ts', type: 'update', content: 'export const fixed = true;' }],
};

const CONTRACT: AgentContract = {
  goal: 'fix',
  allowedOps: ['update'],
  authorizedFiles: ['src/index.ts'],
};

describe('ArchitectAgent', () => {
  it('generates and evaluates a governed proposal without applying it', async () => {
    const generate = vi.fn<ModelProvider['generate']>().mockResolvedValue(PROPOSAL);
    const agent = new ArchitectAgent({
      provider: { generate },
      now: () => new Date('2026-07-01T00:00:00.000Z'),
    });

    const result = await agent.run('Fix src/index.ts', CONTRACT);

    expect(generate).toHaveBeenCalledWith('Fix src/index.ts');
    expect(result.accepted).toBe(true);
    expect(result.envelope.ucrDecision.ok).toBe(true);
    expect(result.envelope.safetyDecision.ok).toBe(true);
    expect(result.replay.ok).toBe(true);
    expect(result.receipt.receiptId).toMatch(/^architect:/u);
    expect(result).not.toHaveProperty('applied');
  });

  it('returns a governed rejection for unauthorized model output', async () => {
    const agent = new ArchitectAgent({
      provider: { generate: async () => PROPOSAL },
      now: () => new Date('2026-07-01T00:00:00.000Z'),
    });

    const result = await agent.run('Fix src/index.ts', {
      ...CONTRACT,
      authorizedFiles: [],
    });

    expect(result.accepted).toBe(false);
    expect(result.envelope.ucrDecision.reasons).toEqual(['Unauthorized file: src/index.ts']);
    expect(result.replay.ok).toBe(true);
  });
});
