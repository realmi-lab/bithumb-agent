export const BITHUMB_AGENT_BRAND = "Bithumb Agent";
export const BITHUMB_AGENT_BRAND_SHORT = "B";

export const BITHUMB_AGENT_PROVIDER_IDS = [
  "openai-codex",
  "antigravity-cli",
] as const;

const BITHUMB_AGENT_PROVIDER_ID_SET = new Set<string>(BITHUMB_AGENT_PROVIDER_IDS);

export function isBithumbAgentProviderId(providerId: string): boolean {
  return BITHUMB_AGENT_PROVIDER_ID_SET.has(providerId.trim().toLowerCase());
}

export function filterBithumbAgentProviders<T extends { id?: string; slug?: string }>(
  providers: readonly T[],
): T[] {
  return providers.filter((provider) =>
    isBithumbAgentProviderId(provider.id ?? provider.slug ?? ""),
  );
}

/** Bithumb Agent inference is subscription OAuth-only. */
export const BITHUMB_AGENT_INFERENCE_API_KEYS_ENABLED = false;

/** Virtual multi-provider aggregators are outside the two-provider policy. */
export const BITHUMB_AGENT_MOA_ENABLED = false;
