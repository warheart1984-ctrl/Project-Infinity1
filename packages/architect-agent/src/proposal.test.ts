import { describe, expect, it } from 'vitest';

import { ArchitectAgentError } from './errors.js';
import { parseModelProposal } from './proposal.js';

describe('parseModelProposal', () => {
  it('accepts and normalizes supported operations', () => {
    expect(
      parseModelProposal({
        schemaVersion: '1',
        goal: 'refactor',
        operations: [
          { file: 'src\\index.ts', type: 'update', content: 'export {};' },
          { file: 'src/new.ts', type: 'insert', content: 'export const value = 1;' },
          { file: 'src/old.ts', type: 'delete' },
        ],
      }),
    ).toEqual({
      schemaVersion: '1',
      goal: 'refactor',
      operations: [
        { file: 'src/index.ts', type: 'update', content: 'export {};' },
        { file: 'src/new.ts', type: 'insert', content: 'export const value = 1;' },
        { file: 'src/old.ts', type: 'delete', content: null },
      ],
    });
  });

  it.each([
    ['non-object output', null],
    ['unknown schema', { schemaVersion: '2', goal: 'fix', operations: [] }],
    ['unknown goal', { schemaVersion: '1', goal: 'deploy', operations: [] }],
    [
      'absolute path',
      {
        schemaVersion: '1',
        goal: 'fix',
        operations: [{ file: 'C:\\secret.txt', type: 'update', content: 'x' }],
      },
    ],
    [
      'parent traversal',
      {
        schemaVersion: '1',
        goal: 'fix',
        operations: [{ file: '../secret.txt', type: 'update', content: 'x' }],
      },
    ],
    [
      'unsupported operation',
      {
        schemaVersion: '1',
        goal: 'fix',
        operations: [{ file: 'src/index.ts', type: 'execute', content: 'x' }],
      },
    ],
    [
      'empty update',
      {
        schemaVersion: '1',
        goal: 'fix',
        operations: [{ file: 'src/index.ts', type: 'update', content: '   ' }],
      },
    ],
  ])('rejects %s', (_label, value) => {
    expect(() => parseModelProposal(value)).toThrowError(ArchitectAgentError);
  });
});
