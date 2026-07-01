import { ArchitectAgentError } from './errors.js';
import { buildStructuredProposalPrompt } from './prompt.js';
import { parseModelProposal } from './proposal.js';
import type { ModelProposal, ModelProvider } from './types.js';

const DEFAULT_BASE_URL = 'http://127.0.0.1:11434';
const DEFAULT_MODEL = 'qwen2.5-coder:3b';
const DEFAULT_TIMEOUT_MS = 120_000;
const DEFAULT_TEMPERATURE = 0;
const DEFAULT_MAX_TOKENS = 2048;

export interface OllamaProviderOptions {
  baseUrl?: string;
  model?: string;
  timeoutMs?: number;
  temperature?: number;
  maxTokens?: number;
  fetch?: typeof globalThis.fetch;
}

interface OllamaGenerateResponse {
  response?: unknown;
}

export class OllamaProvider implements ModelProvider {
  readonly baseUrl: string;
  readonly model: string;
  readonly timeoutMs: number;
  readonly temperature: number;
  readonly maxTokens: number;

  private readonly fetchImplementation: typeof globalThis.fetch;

  constructor(options: OllamaProviderOptions = {}) {
    this.baseUrl = validateBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
    this.model = validateModel(options.model ?? DEFAULT_MODEL);
    this.timeoutMs = validatePositiveInteger(options.timeoutMs ?? DEFAULT_TIMEOUT_MS, 'timeoutMs');
    this.temperature = validateTemperature(options.temperature ?? DEFAULT_TEMPERATURE);
    this.maxTokens = validatePositiveInteger(options.maxTokens ?? DEFAULT_MAX_TOKENS, 'maxTokens');
    this.fetchImplementation = options.fetch ?? globalThis.fetch;
  }

  async generate(prompt: string): Promise<ModelProposal> {
    if (typeof prompt !== 'string' || prompt.trim().length === 0) {
      throw new ArchitectAgentError('INVALID_CONFIGURATION', 'Prompt must be a non-empty string');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await this.fetchImplementation(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.model,
          prompt: buildStructuredProposalPrompt(prompt),
          stream: false,
          format: 'json',
          options: {
            temperature: this.temperature,
            num_predict: this.maxTokens,
          },
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new ArchitectAgentError(
          'OLLAMA_HTTP_ERROR',
          `Ollama request failed with HTTP ${response.status}`,
        );
      }

      const data = await parseResponseEnvelope(response);
      if (typeof data.response !== 'string' || data.response.trim().length === 0) {
        throw new ArchitectAgentError('MODEL_RESPONSE_EMPTY', 'Ollama returned an empty response');
      }

      let proposal: unknown;
      try {
        proposal = JSON.parse(data.response);
      } catch (error) {
        throw new ArchitectAgentError(
          'MODEL_RESPONSE_INVALID',
          'Ollama returned malformed JSON',
          { cause: error },
        );
      }
      return parseModelProposal(proposal);
    } catch (error) {
      if (error instanceof ArchitectAgentError) {
        throw error;
      }
      if (controller.signal.aborted || isAbortError(error)) {
        throw new ArchitectAgentError('OLLAMA_TIMEOUT', 'Ollama request timed out', { cause: error });
      }
      throw new ArchitectAgentError('OLLAMA_NETWORK_ERROR', 'Ollama request failed', {
        cause: error,
      });
    } finally {
      clearTimeout(timeout);
    }
  }
}

async function parseResponseEnvelope(response: Response): Promise<OllamaGenerateResponse> {
  try {
    const value: unknown = await response.json();
    if (value === null || typeof value !== 'object' || Array.isArray(value)) {
      throw new Error('Response envelope must be an object');
    }
    return value as OllamaGenerateResponse;
  } catch (error) {
    throw new ArchitectAgentError(
      'MODEL_RESPONSE_INVALID',
      'Ollama returned an invalid response envelope',
      { cause: error },
    );
  }
}

function validateBaseUrl(value: string): string {
  try {
    const parsed = new URL(value);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error('Unsupported protocol');
    }
    return parsed.toString().replace(/\/$/u, '');
  } catch (error) {
    throw new ArchitectAgentError(
      'INVALID_CONFIGURATION',
      'baseUrl must be a valid HTTP URL',
      { cause: error },
    );
  }
}

function validateModel(value: string): string {
  if (typeof value !== 'string' || value.trim().length === 0) {
    throw new ArchitectAgentError('INVALID_CONFIGURATION', 'model must be a non-empty string');
  }
  return value.trim();
}

function validatePositiveInteger(value: number, name: string): number {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new ArchitectAgentError(
      'INVALID_CONFIGURATION',
      `${name} must be a positive integer`,
    );
  }
  return value;
}

function validateTemperature(value: number): number {
  if (!Number.isFinite(value) || value < 0 || value > 2) {
    throw new ArchitectAgentError(
      'INVALID_CONFIGURATION',
      'temperature must be between 0 and 2',
    );
  }
  return value;
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === 'AbortError';
}
