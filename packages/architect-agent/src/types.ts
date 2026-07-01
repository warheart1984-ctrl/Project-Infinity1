export const PROPOSAL_GOALS = ['refactor', 'rewrite', 'fix', 'mutation'] as const;
export const OPERATION_TYPES = ['insert', 'update', 'delete'] as const;

export type ProposalGoal = (typeof PROPOSAL_GOALS)[number];
export type OperationType = (typeof OPERATION_TYPES)[number];

export interface ModelOperation {
  file: string;
  type: OperationType;
  content?: string | null;
}

export interface ModelProposal {
  schemaVersion: '1';
  goal: ProposalGoal;
  operations: ModelOperation[];
}

export interface ModelProvider {
  generate(prompt: string): Promise<ModelProposal>;
}

export interface AgentContract {
  goal: ProposalGoal;
  allowedOps: OperationType[];
  authorizedFiles: string[];
}

export interface UcrDecision {
  ok: boolean;
  reasons: string[];
}

export interface AlaPlan {
  operations: ModelOperation[];
}

export interface SafetyDecision {
  ok: boolean;
  violations: string[];
}

export interface GovernanceEnvelope {
  proposalHash: string;
  proposal: ModelProposal;
  ucrDecision: UcrDecision;
  alaPlan: AlaPlan;
  safetyDecision: SafetyDecision;
  timestamp: string;
}

export interface ReplayResult {
  ok: boolean;
  violations: string[];
}

export interface ArchitectReceipt {
  receiptId: string;
  proposalHash: string;
  accepted: boolean;
  issuedAt: string;
}

export interface ArchitectAgentResult {
  accepted: boolean;
  proposal: ModelProposal;
  envelope: GovernanceEnvelope;
  replay: ReplayResult;
  receipt: ArchitectReceipt;
}
