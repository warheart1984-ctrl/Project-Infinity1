"""Continuity governance stack: CCS, Proof, CVR, and substrate."""

from src.continuity.ccs import (
    CCSStore,
    ContinuityTrace,
    build_store_from_scenario,
    continuity_trace_fingerprint,
    load_scenario,
    replay_trace_from_store,
    trace_from_object,
)
from src.continuity.pipeline import run_proof_pipeline
from src.continuity.pod import PODDecision
from src.continuity.proof import Proof, ProofStatus, create_proof, revoke_proof, valid_proof
from src.continuity.reputation import (
    ContinuityReputation,
    ContinuityValidatedReputation,
    compute_cvr,
    compute_derived_score,
    ReputationWeights,
    DEFAULT_REPUTATION_WEIGHTS,
    EXAMPLE_REPUTATION_WEIGHTS,
)
from src.continuity.trace_v1 import ContinuityMetrics, ContinuityTraceV1, project_trace_v1
from src.continuity.substrate import ContinuitySubstrate, substrate_from_store, validate_substrate
from src.continuity.ugr_trace import evaluate_trace_ugr_invariants, valid_continuity_trace

__all__ = [
    "CCSStore",
    "ContinuityReputation",
    "ContinuitySubstrate",
    "ContinuityTrace",
    "ContinuityValidatedReputation",
    "PODDecision",
    "Proof",
    "ProofStatus",
    "build_store_from_scenario",
    "compute_cvr",
    "compute_derived_score",
    "ContinuityMetrics",
    "ContinuityTraceV1",
    "ReputationWeights",
    "DEFAULT_REPUTATION_WEIGHTS",
    "EXAMPLE_REPUTATION_WEIGHTS",
    "project_trace_v1",
    "continuity_trace_fingerprint",
    "create_proof",
    "evaluate_trace_ugr_invariants",
    "load_scenario",
    "replay_trace_from_store",
    "revoke_proof",
    "run_proof_pipeline",
    "substrate_from_store",
    "trace_from_object",
    "valid_continuity_trace",
    "valid_proof",
    "validate_substrate",
]
