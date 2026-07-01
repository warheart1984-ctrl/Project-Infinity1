export type ArchitectAgentErrorCode =
  | 'INVALID_CONFIGURATION'
  | 'INVALID_PROPOSAL'
  | 'MODEL_RESPONSE_EMPTY'
  | 'MODEL_RESPONSE_INVALID'
  | 'OLLAMA_HTTP_ERROR'
  | 'OLLAMA_NETWORK_ERROR'
  | 'OLLAMA_TIMEOUT';

export class ArchitectAgentError extends Error {
  readonly code: ArchitectAgentErrorCode;
  readonly cause?: unknown;

  constructor(code: ArchitectAgentErrorCode, message: string, options: { cause?: unknown } = {}) {
    super(message);
    this.name = 'ArchitectAgentError';
    this.code = code;
    this.cause = options.cause;
  }
}
