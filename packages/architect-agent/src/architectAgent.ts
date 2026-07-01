import { hashStable, buildEnvelope, evaluateSafety, evaluateUcr, normalizeOperations, replayEnvelope } from './governance.js';
import { OllamaProvider, type OllamaProviderOptions } from './ollamaProvider.js';
import type {
  AgentContract,
  ArchitectAgentResult,
  ModelProvider,
} from './types.js';

export interface ArchitectAgentOptions {
  provider?: ModelProvider;
  ollama?: OllamaProviderOptions;
  now?: () => Date;
}

export class ArchitectAgent {
  private readonly provider: ModelProvider;
  private readonly now: () => Date;

  constructor(options: ArchitectAgentOptions = {}) {
    this.provider = options.provider ?? new OllamaProvider(options.ollama);
    this.now = options.now ?? (() => new Date());
  }

  async run(prompt: string, contract: AgentContract): Promise<ArchitectAgentResult> {
    const proposal = await this.provider.generate(prompt);
    const ucrDecision = evaluateUcr(proposal, contract);
    const alaPlan = normalizeOperations(proposal);
    const safetyDecision = evaluateSafety(proposal);
    const issuedAt = this.now().toISOString();
    const envelope = buildEnvelope(
      proposal,
      ucrDecision,
      alaPlan,
      safetyDecision,
      issuedAt,
    );
    const accepted = ucrDecision.ok && safetyDecision.ok;

    return {
      accepted,
      proposal,
      envelope,
      replay: replayEnvelope(envelope, contract),
      receipt: {
        receiptId: `architect:${hashStable({ envelope, accepted })}`,
        proposalHash: envelope.proposalHash,
        accepted,
        issuedAt,
      },
    };
  }
}
