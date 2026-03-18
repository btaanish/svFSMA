#!/usr/bin/env python3
"""
Test harness: validates that agent_spec.md produces correct FSM outputs for all 9 SV codes.
Uses Claude API for extraction and LLM-as-judge comparison.
"""

import json
import os
import re
import sys
import time

import anthropic

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_PATH = os.path.join(REPO_ROOT, "spec.md")
AGENT_SPEC_PATH = os.path.join(REPO_ROOT, "agent_spec.md")
REFERENCES_DIR = os.path.join(REPO_ROOT, "tests", "references")
MODEL = "claude-haiku-4-5"  # claude-sonnet-4-6 unavailable with this token; haiku is accessible
SV_CODE_NUMBERS = [1, 2, 4, 5, 6, 7, 8, 9, 10]


def load_agent_spec() -> str:
    with open(AGENT_SPEC_PATH) as f:
        return f.read()


def parse_sv_codes(spec_text: str) -> dict[int, str]:
    """Parse SV code blocks from spec.md. Each block runs from 'Code N:' to the next 'Code M:' or EOF."""
    codes = {}
    # Find all code section positions
    pattern = re.compile(r"^Code (\d+):", re.MULTILINE)
    matches = list(pattern.finditer(spec_text))
    for i, match in enumerate(matches):
        code_num = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(spec_text)
        codes[code_num] = spec_text[start:end].strip()
    return codes


def load_reference(code_num: int) -> dict:
    ref_path = os.path.join(REFERENCES_DIR, f"code_{code_num}.json")
    with open(ref_path) as f:
        return json.load(f)


def extract_fsm(client: anthropic.Anthropic, agent_spec: str, sv_code: str, code_num: int) -> str:
    """Call Claude with agent_spec as system prompt to extract FSM from SV code."""
    user_message = (
        f"Please analyze the following SystemVerilog code (Code {code_num}) "
        f"and extract its FSM according to your instructions. "
        f"Produce a JSON object with the FSM structure including: "
        f"states (name, description, events), transitions (from, to, condition, timing), "
        f"outputs (state, signal, value), and interface (inputs, outputs, clock, reset).\n\n"
        f"```systemverilog\n{sv_code}\n```"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=agent_spec,
        messages=[{"role": "user", "content": user_message}],
        timeout=120,
    )
    return response.content[0].text


def judge_fsm(client: anthropic.Anthropic, extracted: str, reference: dict, code_num: int) -> tuple[bool, str]:
    """Use Claude as judge to compare extracted FSM against reference."""
    ref_json = json.dumps(reference, indent=2)
    judge_prompt = f"""You are a strict FSM validator. Compare the EXTRACTED FSM against the REFERENCE FSM for Code {code_num}.

REFERENCE FSM:
```json
{ref_json}
```

EXTRACTED FSM (agent output):
{extracted}

Evaluate whether the extracted FSM correctly captures the KEY STRUCTURAL ELEMENTS:
1. States: Are the same states present (by name or equivalent description)?
2. Transitions: Are the same state transitions present (from/to relationships and conditions)?
3. Outputs: Are the register assignments/outputs for each state correct?
4. Interface: Does the interface (inputs/outputs/clock/reset) match?

Be lenient on formatting and naming conventions — focus on semantic correctness.
A minor discrepancy (e.g., slightly different state naming) is OK if the structure is correct.
A FAIL requires a substantive structural difference.

Respond with EXACTLY this format:
VERDICT: PASS or FAIL
REASON: <one to three sentences explaining the verdict>
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": judge_prompt}],
        timeout=120,
    )
    text = response.content[0].text.strip()
    passed = "VERDICT: PASS" in text
    # Extract reason
    reason_match = re.search(r"REASON:\s*(.+)", text, re.DOTALL)
    reason = reason_match.group(1).strip() if reason_match else text
    return passed, reason


def run_tests() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN not set", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    agent_spec = load_agent_spec()

    spec_text = open(SPEC_PATH).read()
    sv_codes = parse_sv_codes(spec_text)

    results = {}
    all_passed = True

    print(f"Running FSM extraction tests for {len(SV_CODE_NUMBERS)} SV codes...\n")

    for code_num in SV_CODE_NUMBERS:
        print(f"--- Code {code_num} ---")
        if code_num not in sv_codes:
            print(f"  ERROR: Code {code_num} not found in spec.md")
            results[code_num] = (False, "Code not found in spec.md")
            all_passed = False
            continue

        try:
            reference = load_reference(code_num)
        except FileNotFoundError:
            print(f"  ERROR: Reference file tests/references/code_{code_num}.json not found")
            results[code_num] = (False, "Reference file missing")
            all_passed = False
            continue

        try:
            print(f"  Extracting FSM via Claude API...")
            extracted = extract_fsm(client, agent_spec, sv_codes[code_num], code_num)
        except Exception as e:
            print(f"  ERROR during extraction: {e}")
            results[code_num] = (False, f"Extraction error: {e}")
            all_passed = False
            continue

        try:
            print(f"  Judging extracted FSM...")
            passed, reason = judge_fsm(client, extracted, reference, code_num)
        except Exception as e:
            print(f"  ERROR during judging: {e}")
            results[code_num] = (False, f"Judge error: {e}")
            all_passed = False
            continue

        status = "PASS" if passed else "FAIL"
        print(f"  Result: {status}")
        print(f"  Reason: {reason}")
        results[code_num] = (passed, reason)
        if not passed:
            all_passed = False

        # Small delay to avoid rate limiting
        time.sleep(1)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for code_num in SV_CODE_NUMBERS:
        if code_num in results:
            passed, reason = results[code_num]
            status = "PASS" if passed else "FAIL"
            print(f"  Code {code_num:2d}: {status}  — {reason[:80]}")
        else:
            print(f"  Code {code_num:2d}: SKIP")

    print()
    if all_passed:
        print("ALL TESTS PASSED")
        return 0
    else:
        failed = [n for n in SV_CODE_NUMBERS if n in results and not results[n][0]]
        print(f"FAILED: {len(failed)} code(s) — {failed}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
