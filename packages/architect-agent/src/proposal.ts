import { ArchitectAgentError } from './errors.js';
import {
  OPERATION_TYPES,
  PROPOSAL_GOALS,
  type ModelOperation,
  type ModelProposal,
  type OperationType,
  type ProposalGoal,
} from './types.js';

export function parseModelProposal(value: unknown): ModelProposal {
  const record = requireRecord(value, 'Model output must be a JSON object');
  if (record.schemaVersion !== '1') {
    invalid('Unsupported proposal schema version');
  }
  if (!isProposalGoal(record.goal)) {
    invalid('Unsupported proposal goal');
  }
  if (!Array.isArray(record.operations)) {
    invalid('Proposal operations must be an array');
  }

  return {
    schemaVersion: '1',
    goal: record.goal,
    operations: record.operations.map((operation, index) => parseOperation(operation, index)),
  };
}

function parseOperation(value: unknown, index: number): ModelOperation {
  const record = requireRecord(value, `Operation ${index} must be an object`);
  const file = normalizeRelativePath(record.file, index);
  if (!isOperationType(record.type)) {
    invalid(`Operation ${index} has an unsupported type`);
  }

  if (record.type === 'delete') {
    if (record.content !== undefined && record.content !== null) {
      invalid(`Delete operation ${index} must not contain content`);
    }
    return { file, type: record.type, content: null };
  }

  if (typeof record.content !== 'string' || record.content.trim().length === 0) {
    invalid(`${record.type} operation ${index} requires non-empty content`);
  }
  return { file, type: record.type, content: record.content };
}

function normalizeRelativePath(value: unknown, index: number): string {
  if (typeof value !== 'string' || value.trim().length === 0) {
    invalid(`Operation ${index} requires a file path`);
  }
  const normalized = value.replaceAll('\\', '/');
  if (
    normalized.startsWith('/') ||
    /^[A-Za-z]:\//u.test(normalized) ||
    normalized.split('/').some((segment) => segment === '..')
  ) {
    invalid(`Operation ${index} file path must stay inside the workspace`);
  }
  return normalized;
}

function requireRecord(value: unknown, message: string): Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    invalid(message);
  }
  return value as Record<string, unknown>;
}

function isProposalGoal(value: unknown): value is ProposalGoal {
  return typeof value === 'string' && (PROPOSAL_GOALS as readonly string[]).includes(value);
}

function isOperationType(value: unknown): value is OperationType {
  return typeof value === 'string' && (OPERATION_TYPES as readonly string[]).includes(value);
}

function invalid(message: string): never {
  throw new ArchitectAgentError('INVALID_PROPOSAL', message);
}
