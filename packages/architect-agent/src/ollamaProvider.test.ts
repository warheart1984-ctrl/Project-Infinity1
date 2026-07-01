import { describe, expect, it, vi } from 'vitest';

import { ArchitectAgentError } from './errors.js';
import { OllamaProvider } from './ollamaProvider.js';

const VALID_PROPOSAL = {
  schemaVersion: '1',
  goal: 'fix',
  operations: [{ file: 'src/index.ts', type: 'update', content: 'export const fixed = true;' }],
};

describe('OllamaProvider', () => {
  it('uses deterministic 3B defaults and parses a valid proposal', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      jsonResponse({ response: JSON.stringify(VALID_PROPOSAL) }),
    );
    const provider = new OllamaProvider({ fetch });

    await expect(provider.generate('Fix src/index.ts')).resolves.toEqual(VALID_PROPOSAL);

    expect(fetch).toHaveBeenCalledOnce();
    const [url, init] = fetch.mock.calls[0]!;
    expect(url).toBe('http://127.0.0.1:11434/api/generate');
    expect(JSON.parse(String(init?.body))).toMatchObject({
      model: 'qwen2.5-coder:3b',
      stream: false,
      format: 'json',
      options: { temperature: 0, num_predict: 2048 },
    });
  });

  it('supports explicit 7B model selection', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      jsonResponse({ response: JSON.stringify(VALID_PROPOSAL) }),
    );
    const provider = new OllamaProvider({ model: 'qwen2.5-coder:7b', fetch });

    await provider.generate('Fix src/index.ts');

    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body)).model).toBe('qwen2.5-coder:7b');
  });

  it.each([
    ['empty model', { model: ' ' }],
    ['invalid timeout', { timeoutMs: 0 }],
    ['invalid temperature', { temperature: 3 }],
    ['invalid token limit', { maxTokens: -1 }],
  ])('rejects %s configuration', (_label, options) => {
    expect(() => new OllamaProvider(options)).toThrowError(ArchitectAgentError);
  });

  it('rejects non-success HTTP responses without exposing the prompt', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response('private provider body', { status: 500 }),
    );
    const provider = new OllamaProvider({ fetch });

    await expect(provider.generate('private prompt')).rejects.toMatchObject({
      code: 'OLLAMA_HTTP_ERROR',
    });
    await expect(provider.generate('private prompt')).rejects.not.toThrow(/private/u);
  });

  it('classifies network failures', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockRejectedValue(new Error('connection refused'));
    const provider = new OllamaProvider({ fetch });

    await expect(provider.generate('Fix it')).rejects.toMatchObject({
      code: 'OLLAMA_NETWORK_ERROR',
    });
  });

  it('classifies request timeouts', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockImplementation((_url, init) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
      });
    });
    const provider = new OllamaProvider({ fetch, timeoutMs: 5 });

    await expect(provider.generate('Fix it')).rejects.toMatchObject({
      code: 'OLLAMA_TIMEOUT',
    });
  });

  it.each([
    ['empty response', { response: '' }, 'MODEL_RESPONSE_EMPTY'],
    ['malformed JSON', { response: '{bad' }, 'MODEL_RESPONSE_INVALID'],
    ['invalid proposal', { response: JSON.stringify({ goal: 'fix' }) }, 'INVALID_PROPOSAL'],
  ])('rejects %s', async (_label, responseBody, code) => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(jsonResponse(responseBody));
    const provider = new OllamaProvider({ fetch });

    await expect(provider.generate('Fix it')).rejects.toMatchObject({ code });
  });
});

function jsonResponse(value: unknown): Response {
  return new Response(JSON.stringify(value), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
