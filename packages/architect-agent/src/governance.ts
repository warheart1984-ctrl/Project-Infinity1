import { createHash } from 'node:crypto';

import type {
  AgentContract,
  AlaPlan,
  GovernanceEnvelope,
  ModelOperation,
  ModelProposal,
  ReplayResult,
  SafetyDecision,
  UcrDecision,
} from './types.js';

export function evaluateUcr(proposal: ModelProposal, contract: AgentContract): UcrDecision {
  const reasons: string[] = [];
  if (proposal.goal !== contract.goal) {
    reasons.push(`Goal mismatch: expected ${contract.goal}`);
  }

  for (const operation of proposal.operations) {
    if (!contract.allowedOps.includes(operation.type)) {
      reasons.push(`Operation not allowed: ${operation.type}`);
    }
    if (!contract.authorizedFiles.includes(operation.file)) {
      reasons.push(`Unauthorized file: ${operation.file}`);
    }
  }

  return { ok: reasons.length === 0, reasons };
}

export function normalizeOperations(proposal: ModelProposal): AlaPlan {
  return {
    operations: proposal.operations
      .map(cloneOperation)
      .sort(
        (left, right) =>
          left.file.localeCompare(right.file) || left.type.localeCompare(right.type),
      ),
  };
}

export function evaluateSafety(proposal: ModelProposal): SafetyDecision {
  const violations: string[] = [];
  for (const operation of proposal.operations) {
    if (
      (operation.type === 'insert' || operation.type === 'update') &&
      (typeof operation.content !== 'string' || operation.content.trim().length === 0)
    ) {
      violations.push(`${operation.type} requires non-empty content: ${operation.file}`);
    }
    if (pathEscapesWorkspace(operation.file)) {
      violations.push(`Operation path escapes workspace: ${operation.file}`);
    }
  }
  return { ok: violations.length === 0, violations };
}

export function buildEnvelope(
  proposal: ModelProposal,
  ucrDecision: UcrDecision,
  alaPlan: AlaPlan,
  safetyDecision: SafetyDecision,
  timestamp: string,
): GovernanceEnvelope {
  return {
    proposalHash: hashStable(proposal),
    proposal: cloneProposal(proposal),
    ucrDecision: { ok: ucrDecision.ok, reasons: [...ucrDecision.reasons] },
    alaPlan: { operations: alaPlan.operations.map(cloneOperation) },
    safetyDecision: {
      ok: safetyDecision.ok,
      violations: [...safetyDecision.violations],
    },
    timestamp,
  };
}

export function replayEnvelope(
  envelope: GovernanceEnvelope,
  contract: AgentContract,
): ReplayResult {
  const violations: string[] = [];
  if (hashStable(envelope.proposal) !== envelope.proposalHash) {
    violations.push('Proposal hash drift');
  }
  if (!sameJson(evaluateUcr(envelope.proposal, contract), envelope.ucrDecision)) {
    violations.push('UCR decision drift');
  }
  if (!sameJson(normalizeOperations(envelope.proposal), envelope.alaPlan)) {
    violations.push('ALA plan drift');
  }
  if (!sameJson(evaluateSafety(envelope.proposal), envelope.safetyDecision)) {
    violations.push('Safety decision drift');
  }
  if (Number.isNaN(Date.parse(envelope.timestamp))) {
    violations.push('Invalid envelope timestamp');
  }
  return { ok: violations.length === 0, violations };
}

export function hashStable(value: unknown): string {
  return createHash('sha256').update(stableStringify(value), 'utf8').digest('hex');
}

function pathEscapesWorkspace(file: string): boolean {
  const normalized = file.replaceAll('\\', '/');
  return (
    normalized.startsWith('/') ||
    /^[A-Za-z]:\//u.test(normalized) ||
    normalized.split('/').some((segment) => segment === '..')
  );
}

function cloneProposal(proposal: ModelProposal): ModelProposal {
  return {
    schemaVersion: proposal.schemaVersion,
    goal: proposal.goal,
    operations: proposal.operations.map(cloneOperation),
  };
}

function cloneOperation(operation: ModelOperation): ModelOperation {
  return {
    file: operation.file,
    type: operation.type,
    content: operation.content ?? null,
  };
}

function sameJson(left: unknown, right: unknown): boolean {
  return stableStringify(left) === stableStringify(right);
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`;
  }
  if (value !== null && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}
