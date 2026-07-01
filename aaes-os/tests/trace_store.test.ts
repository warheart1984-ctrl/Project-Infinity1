import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { SqliteTraceStoreStub } from "../src/index.js";
import type { AAESContext, AAESStep } from "../src/types.js";

const context: AAESContext = {
  traceId: "trace-stub",
  request: {
    actorId: "operator",
    scope: { name: "test" },
    prompt: "verify fail-closed storage",
  },
  session: {},
  steps: [],
  metadata: {},
};

const step: AAESStep = {
  stepId: "step-stub",
  stepType: "test",
  timestamp: "2026-07-01T00:00:00.000Z",
  summary: "verify fail-closed storage",
  status: "ok",
};

describe("SqliteTraceStoreStub", () => {
  it("fails closed for writes until durable storage is implemented", () => {
    const store = new SqliteTraceStoreStub();

    assert.throws(
      () => store.appendStep(context, step),
      /SqliteTraceStoreStub: not implemented in v1/,
    );
  });

  it("fails closed for reads until durable storage is implemented", () => {
    const store = new SqliteTraceStoreStub();

    assert.throws(
      () => store.getTrace(context.traceId),
      /SqliteTraceStoreStub: not implemented in v1/,
    );
  });
});
