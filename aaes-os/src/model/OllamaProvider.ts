import {
  OllamaProvider as ArchitectOllamaProvider,
  type ModelProposal,
  type ModelProvider,
  type OllamaProviderOptions,
} from '@aaes-os/architect-agent';

export class OllamaProvider implements ModelProvider {
  private readonly delegate: ArchitectOllamaProvider;

  constructor(options: OllamaProviderOptions = {}) {
    this.delegate = new ArchitectOllamaProvider(options);
  }

  generate(prompt: string): Promise<ModelProposal> {
    return this.delegate.generate(prompt);
  }
}

export type { OllamaProviderOptions };
