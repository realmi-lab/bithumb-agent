import { describe, expect, it } from "vitest";
import {
  BITHUMB_AGENT_INFERENCE_API_KEYS_ENABLED,
  BITHUMB_AGENT_MOA_ENABLED,
  filterBithumbAgentProviders,
  isBithumbAgentProviderId,
} from "./bithumb-agent-policy";

describe("Bithumb Agent provider policy", () => {
  it("accepts only the two OAuth-backed inference providers", () => {
    expect(isBithumbAgentProviderId("openai-codex")).toBe(true);
    expect(isBithumbAgentProviderId("antigravity-cli")).toBe(true);
    expect(isBithumbAgentProviderId("openrouter")).toBe(false);
    expect(isBithumbAgentProviderId("gemini-api-key")).toBe(false);
  });

  it("filters provider payloads defensively", () => {
    expect(
      filterBithumbAgentProviders([
        { slug: "openrouter" },
        { slug: "antigravity-cli" },
        { slug: "openai-codex" },
      ]),
    ).toEqual([
      { slug: "antigravity-cli" },
      { slug: "openai-codex" },
    ]);
  });

  it("does not expose inference API-key setup", () => {
    expect(BITHUMB_AGENT_INFERENCE_API_KEYS_ENABLED).toBe(false);
    expect(BITHUMB_AGENT_MOA_ENABLED).toBe(false);
  });
});
