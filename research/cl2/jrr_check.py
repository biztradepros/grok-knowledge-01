#!/usr/bin/env python3
"""Justified Result Record (JRR) v0.1 — stale-dependency rule and one self-test.

Standard library only. Run:  python3 research/cl2/jrr_check.py
Exit code 0 = PASS, 1 = FAIL.
"""
import copy
import hashlib
import json
import sys

REQUIRED = ("task_id", "result_id", "produced_by", "consumes",
            "evidence_refs", "rule_version", "result_hash", "created_at")

OK, INVALID, STALE, UNRESOLVED = "OK", "INVALID", "STALE_DEPENDENCY", "UNRESOLVED"


def sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def evaluate(records):
    """Return {result_id: (status, reason_chain)} for every record.

    A record is INVALID if some record lists its result_hash in `rejects`.
    A record is STALE_DEPENDENCY if anything it consumes is INVALID or STALE_DEPENDENCY.
    The rule reads no timestamps, so the verdict does not depend on arrival order.
    """
    for r in records:
        missing = [k for k in REQUIRED if k not in r]
        if missing:
            raise ValueError("%s: missing fields %s" % (r.get("result_id", "?"), missing))
    by_hash = {r["result_hash"]: r for r in records}
    rejected_by = {h: r["result_id"] for r in records for h in r.get("rejects", [])}
    memo = {}

    def name(h):
        return by_hash[h]["result_id"] if h in by_hash else h[:19] + "..."

    def judge(r, path):
        rid = r["result_id"]
        if rid in memo:
            return memo[rid]
        if r["result_hash"] in rejected_by:
            out = (INVALID, ["%s rejected by %s" % (rid, rejected_by[r["result_hash"]])])
        else:
            out = (OK, [])
            for h in r["consumes"]:
                if h in rejected_by:
                    out = (STALE, ["%s consumed %s" % (rid, name(h)),
                                   "%s rejected by %s" % (name(h), rejected_by[h])])
                    break
                dep = by_hash.get(h)
                if dep is None or dep["result_id"] in path:
                    out = (UNRESOLVED, ["%s consumed %s, which cannot be resolved" % (rid, name(h))])
                    continue
                dep_status, dep_chain = judge(dep, path | {rid})
                if dep_status == STALE:
                    out = (STALE, ["%s consumed %s" % (rid, name(h))] + dep_chain)
                    break
                if dep_status == UNRESOLVED and out[0] == OK:
                    out = (UNRESOLVED, ["%s consumed %s" % (rid, name(h))] + dep_chain)
        memo[rid] = out
        return out

    return {r["result_id"]: judge(r, frozenset()) for r in records}


def scenario():
    """The one T1-style scenario: P1 makes A, verifier V rejects A, P2 makes B from A."""
    impl_a = b"def add(a, b):\n    return str(a) + b\n"
    typecheck_log = b"typecheck FAILED: add() returns str, spec says int\n"
    verdict = b"REJECT implementation A: typecheck failed\n"
    tests_b = b"def test_add():\n    assert add(1, '2') == '12'\n"
    test_run_log = b"1 passed (against implementation A)\n"

    a = {"task_id": "T-001", "result_id": "R-A", "produced_by": "P1",
         "consumes": [], "evidence_refs": [],
         "rule_version": "jrr-0.1", "result_hash": sha256(impl_a),
         "created_at": "2026-09-29T10:00:00Z"}
    v = {"task_id": "T-001", "result_id": "R-V", "produced_by": "V",
         "consumes": [], "evidence_refs": [sha256(typecheck_log)],
         "rule_version": "jrr-0.1", "result_hash": sha256(verdict),
         "created_at": "2026-09-29T10:05:00Z",
         "rejects": [a["result_hash"]]}
    b = {"task_id": "T-001", "result_id": "R-B", "produced_by": "P2",
         "consumes": [a["result_hash"]], "evidence_refs": [sha256(test_run_log)],
         "rule_version": "jrr-0.1", "result_hash": sha256(tests_b),
         "created_at": "2026-09-29T10:07:00Z"}
    return [a, v, b]


def main():
    records = scenario()
    print(json.dumps(records, indent=2))
    result = evaluate(records)
    for rid, (status, chain) in result.items():
        print("%-4s %-17s %s" % (rid, status, " -> ".join(chain)))

    detected = (result["R-A"][0] == INVALID
                and result["R-V"][0] == OK
                and result["R-B"] == (STALE, ["R-B consumed R-A", "R-A rejected by R-V"]))

    # Ablation: the eight given fields alone. Without `rejects`, no record can say A is invalid.
    stripped = copy.deepcopy(records)
    for r in stripped:
        r.pop("rejects", None)
    blind = evaluate(stripped)
    gap_shown = blind["R-B"][0] == OK
    print("8 fields only   -> R-B is %s (stale dependency not detectable)" % blind["R-B"][0])
    print("8 + `rejects`   -> R-B is %s" % result["R-B"][0])

    passed = detected and gap_shown
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
