"""Tool schemas and dispatcher.

Seven tools, registered with Anthropic tool-use shape. The dispatcher returns
serialized JSON strings to be wrapped as `tool_result` content. Errors follow
the Playbook "Graceful Tool Failure" shape:

    {"is_error": true,
     "error_category": "transient"|"permanent",
     "is_retryable": bool,
     "message": "..."}

Errors are never raised to the loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claims_intake.session import ClaimSession

CLAIM_TYPES = ["property_damage", "theft", "liability", "auto"]
SEVERITIES = ["low", "medium", "high"]

# ----------------------------------------------------------------------------
# Schemas — passed verbatim to the Anthropic Messages API as the `tools` arg.
# ----------------------------------------------------------------------------

# TODO:Populate TOOL_SCHEMAS with the first four tool schemas. Each schema
# is a dict with "name", "description", and "input_schema". Tool descriptions are read by
# the model on every turn — write them as if you were teaching the model what each tool is
# for and *when* to call it. Categorical fields ("claim_type", "severity") must use
# Anthropic's tool-use `enum` shape against CLAIM_TYPES and SEVERITIES.
#
#   - lookup_policy(policy_id: str)
#     Returns the policy record. Used early in the conversation.
#   - record_claim_fact(field: str, value: str)
#     Records one normalized fact (incident_date, location, items_lost, ...).
#   - classify_claim(claim_type: enum CLAIM_TYPES, confidence: number in [0,1], rationale: str)
#     Commits the model to a claim type with a confidence score.
#   - assess_severity(severity: enum SEVERITIES, rationale: str)
#     Commits the model to a severity bucket.
#
# Later tools (request_clarification, route_to_adjuster, escalate_to_human) extend this list.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "lookup_policy",
        "description": (
            "Look up a policyholder's coverage record. Use this early in the "
            "conversation to confirm the policy exists, what is covered, and the "
            "deductible. Returns coverage, deductible, status, and policy_holder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "Policy identifier, e.g. POL-1001"}
            },
            "required": ["policy_id"],
        },
    },
    # ... record_claim_fact, classify_claim, assess_severity follow the same structure.
]

# ----------------------------------------------------------------------------
# Errors — Graceful Tool Failure shape
# ----------------------------------------------------------------------------


def _err(category: str, retryable: bool, message: str) -> str:
    return json.dumps({
        "is_error": True,
        "error_category": category,
        "is_retryable": retryable,
        "message": message,
    })

def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


def _ok(payload: dict[str, Any]) -> str:
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "lookup_policy",
        "description": (
            "Look up a policyholder's coverage record. Use this early in the "
            "conversation to confirm the policy exists, what is covered, and the "
            "deductible. Returns coverage, deductible, status, and policy_holder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "Policy identifier, e.g. POL-1001"}
            },
            "required": ["policy_id"],
        },
    },
    {
    "name": "request_clarification",
    "description": (
        "Ask the claimant ONE clarifying question to disambiguate the claim "
        "type or fill a critical missing fact. Use only when the claim type "
        "is genuinely ambiguous between two or more types. Returns the "
        "claimant's reply, or NO_RESPONSE if the claimant cannot answer."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "ambiguity_between": {
                "type": "array",
                "items": {"type": "string", "enum": CLAIM_TYPES},
                "minItems": 2,
            },
        },
        "required": ["question", "ambiguity_between"],
    },
},
    # ... record_claim_fact, classify_claim, assess_severity follow the same structure.
]
    return "{}"


# ----------------------------------------------------------------------------
# Tool implementations
# ----------------------------------------------------------------------------


def _t_lookup_policy(session: ClaimSession, inp: dict[str, Any]) -> str:
    # TODO:Read inp["policy_id"]; if not a string, return a permanent error.
    # Look it up in session.policies; if missing, return a permanent error naming the id.
    # Otherwise return the policy dict via _ok(...).
    return _err("permanent", False, "TODO: _t_lookup_policy not implemented yet")


def _t_record_claim_fact(session: ClaimSession, inp: dict[str, Any]) -> str:
    # TODO:Validate inp["field"] and inp["value"] are both strings; store
    # session.case_facts[field] = value; return _ok with {"recorded": True, "field": field,
    # "case_facts_count": len(session.case_facts)}.
    return _err("permanent", False, "TODO: _t_record_claim_fact not implemented yet")


def _t_classify_claim(session: ClaimSession, inp: dict[str, Any]) -> str:
    # TODO:Validate claim_type (in CLAIM_TYPES), confidence (number in [0,1]),
    # rationale (string). Store session.classification = {claim_type, confidence, rationale}
    # and return _ok with the recorded values plus {"recorded": True}.
    return _err("permanent", False, "TODO: _t_classify_claim not implemented yet")


def _t_assess_severity(session: ClaimSession, inp: dict[str, Any]) -> str:
    # TODO:Validate severity (in SEVERITIES) and rationale (string).
    # Store session.severity = {severity, rationale} and return _ok with the recorded
    # values plus {"recorded": True}.
    return _err("permanent", False, "TODO: _t_assess_severity not implemented yet")


def _t_request_clarification(session, inp):
    question = inp.get("question")
    candidates = inp.get("ambiguity_between")
    if not isinstance(question, str):
        return _err("permanent", False, "question must be a string")
    if not isinstance(candidates, list) or len(candidates) < 2:
        return _err("permanent", False, "ambiguity_between must list at least two candidate types")
    session.clarifications_asked.append({"question": question, "candidates": list(candidates)})
    qlow = question.lower()
    for pattern, reply in session.clarification_responses.items():
        if pattern.lower() in qlow:
            return _ok({"claimant_reply": reply})
    return _ok({"claimant_reply": "NO_RESPONSE"})

def _t_route_to_adjuster(session, inp):
    if session.terminal_called:
        return _err("permanent", False, "terminal tool already called this claim")
    # validation, build record, _append_jsonl, set session.routing, return _ok(...)

def _t_escalate_to_human(session, inp):
    if session.terminal_called:
        return _err("permanent", False, "terminal tool already called this claim")
    # validation, missing-field check, build record, _append_jsonl, set session.escalation

# ----------------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------------


_DISPATCH = {
    "lookup_policy": _t_lookup_policy,
    "record_claim_fact": _t_record_claim_fact,
    "classify_claim": _t_classify_claim,
    "assess_severity": _t_assess_severity,
    "request_clarification": _t_request_clarification,
    "route_to_adjuster": _t_route_to_adjuster,
    "escalate_to_human": _t_escalate_to_human,
}
def _t_classify_claim(session: ClaimSession, inp: dict[str, Any]) -> str:
    claim_type = inp.get("claim_type")
    confidence = inp.get("confidence")
    rationale = inp.get("rationale")
    if claim_type not in CLAIM_TYPES:
        return _err("permanent", False, f"claim_type must be one of {CLAIM_TYPES}")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        return _err("permanent", False, "confidence must be a number in [0,1]")
    if not isinstance(rationale, str):
        return _err("permanent", False, "rationale must be a string")
    session.classification = {
        "claim_type": claim_type,
        "confidence": float(confidence),
        "rationale": rationale,
    }
    return _ok({"recorded": True, **session.classification})

def make_executor(session: ClaimSession) -> Executor:
    """Return a ToolExecutor callable bound to this session."""

    def execute(name: str, tool_input: dict[str, Any]) -> str:
        handler = _DISPATCH.get(name)
        if handler is None:
            return _err("permanent", False, f"unknown tool: {name}")
        try:
            return handler(session, tool_input)
        except Exception as exc:
            # Defensive: anything raised inside a handler becomes a graceful error,
            # never crashes the loop.
            return _err("transient", True, f"{type(exc).__name__}: {exc}")

    return execute


# Type alias for clarity; the loop only sees a Callable.
Executor = Any


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
