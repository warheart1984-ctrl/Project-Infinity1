import { describe, expect, it } from 'vitest';

import {
  buildEnvelope,
  evaluateSafety,
  evaluateUcr,
  normalizeOperations,
  replayEnvelope,
} from './governance.js';
import type { AgentContract, ModelProposal } from './types.js';

const PROPOSAL: ModelProposal = {
  schemaVersion: '1',
  goal: 'refactor',
  operations: [
    { file: 'src/z.ts', type: 'update', content: 'z' },
    { file: 'src/a.ts', type: 'insert', content: 'a' },
  ],
};

const CONTRACT: AgentContract = {
  goal: 'refactor',
  allowedOps: ['insert', 'update'],
  authorizedFiles: ['src/a.ts', 'src/z.ts'],
};

describe('governance pipeline', () => {
  it('authorizes matching goals, operations, and files', () => {
    expect(evaluateUcr(PROPOSAL, CONTRACT)).toEqual({ ok: true, reasons: [] });
  });

  it('fails closed for goal, operation, and file violations', () => {
    const decision = evaluateUcr(PROPOSAL, {
      goal: 'fix',
      allowedOps: ['insert'],
      authorizedFiles: ['src/a.ts'],
    });

    expect(decision.ok).toBe(false);
    expect(decision.reasons).toEqual([
      'Goal mismatch: expected fix',
      'Operation not allowed: update',
      'Unauthorized file: src/z.ts',
    ]);
  });

  it('normalizes operations without mutating the proposal', () => {
    const plan = normalizeOperations(PROPOSAL);

    expect(plan.operations.map((operation) => operation.file)).toEqual(['src/a.ts', 'src/z.ts']);
    expect(PROPOSAL.operations.map((operation) => operation.file)).toEqual(['src/z.ts', 'src/a.ts']);
  });

  it('rejects unsafe content and workspace traversal', () => {
    const decision = evaluateSafety({
      schemaVersion: '1',
      goal: 'fix',
      operations: [
        { file: 'src/empty.ts', type: 'update', content: '' },
        { file: '../outside.ts', type: 'delete', content: null },
      ],
    });

    expect(decision.ok).toBe(false);
    expect(decision.violations).toEqual([
      'update requires non-empty content: src/empty.ts',
      'Operation path escapes workspace: ../outside.ts',
    ]);
  });

  it('builds stable proposal hashes for equivalent object key order', () => {
    const first = buildEnvelope(
      PROPOSAL,
      evaluateUcr(PROPOSAL, CONTRACT),
      normalizeOperations(PROPOSAL),
      evaluateSafety(PROPOSAL),
      '2026-07-01T00:00:00.000Z',
    );
    const reordered = {
      operations: PROPOSAL.operations.map(({ file, type, content }) => ({ content, type, file })),
      goal: PROPOSAL.goal,
      schemaVersion: PROPOSAL.schemaVersion,
    } as ModelProposal;
    const second = buildEnvelope(
      reordered,
      evaluateUcr(reordered, CONTRACT),
      normalizeOperations(reordered),
      evaluateSafety(reordered),
      '2026-07-01T00:00:00.000Z',
    );

    expect(first.proposalHash).toBe(second.proposalHash);
  });

  it('detects proposal and plan drift during replay', () => {
    const envelope = buildEnvelope(
      PROPOSAL,
      evaluateUcr(PROPOSAL, CONTRACT),
      normalizeOperations(PROPOSAL),
      evaluateSafety(PROPOSAL),
      '2026-07-01T00:00:00.000Z',
    );
    const tampered = {
      ...envelope,
      alaPlan: { operations: [] },
    };

    expect(replayEnvelope(envelope, CONTRACT)).toEqual({ ok: true, violations: [] });
    expect(replayEnvelope(tampered, CONTRACT)).toEqual({
      ok: false,
      violations: ['ALA plan drift'],
    });
  });
});
