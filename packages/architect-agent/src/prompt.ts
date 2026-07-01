export function buildStructuredProposalPrompt(userPrompt: string): string {
  return [
    'You are a deterministic coding proposal engine.',
    'Return only valid JSON with this exact shape:',
    '{"schemaVersion":"1","goal":"refactor|rewrite|fix|mutation","operations":[{"file":"relative/path","type":"insert|update|delete","content":"string or null"}]}',
    'Use workspace-relative paths. Never include markdown, prose, or code fences.',
    'Insert and update operations require non-empty content. Delete operations use null content.',
    '',
    'Task:',
    userPrompt,
  ].join('\n');
}
