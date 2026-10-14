"""스키마가 규칙을 실제로 막는지. usage: python -m unittest schema/test_schemas.py (jsonschema 필요)"""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def valid(schema, doc):
    return not list(Draft202012Validator(schema).iter_errors(doc))


class SchemaTests(unittest.TestCase):
    def test_schemas_are_valid(self):
        for f in HERE.glob("*.schema.json"):
            Draft202012Validator.check_schema(load(f.name))

    def test_examples_pass(self):
        self.assertTrue(valid(load("character.schema.json"), load("examples/m40.character.json")))
        self.assertTrue(valid(load("reference.schema.json"), load("examples/m40.reference.json")))
        self.assertTrue(valid(load("candidate.schema.json"), load("examples/m40.candidate.quoted.json")))

    def test_real_person_cannot_be_identity_input(self):
        ref = load("examples/m40.reference.json")
        ref.update(rights_status="LICENSED_COMMERCIAL", allowed_use="identity_input")
        self.assertFalse(valid(load("reference.schema.json"), ref))

    def test_unverified_rights_limit_use(self):
        ref = load("examples/m40.reference.json")
        ref.update(subject="generated_character", allowed_use="style_mood_only")
        self.assertFalse(valid(load("reference.schema.json"), ref))
        ref.update(rights_status="OWNED")
        self.assertTrue(valid(load("reference.schema.json"), ref))

    def test_no_generation_without_spend_approval(self):
        c = load("examples/m40.candidate.quoted.json")
        c["state"] = "GENERATING"
        self.assertFalse(valid(load("candidate.schema.json"), c))
        c["cost"].update(approved_by="owner", approved_at="2026-10-14T10:00:00Z")
        self.assertTrue(valid(load("candidate.schema.json"), c))

    def lock(self):
        return {
            "lock_id": "DF-LOCK-M40-V1", "character_id": "DF-CHAR-M40", "version": "v1.0.0", "supersedes": None,
            "master_candidate_ids": ["DF-CAND-M40-R2-03"],
            "master_media": [{"view": "front", "generation_id": "gen-1", "sha256": "a" * 64}],
            "higgsfield": {"element_id": None, "soul_id": None, "created_from_generation_ids": []},
            "identity_eval": {"engine_version": "0.1.0", "policy": {}, "intra_master_min_cosine": 0.7,
                              "protected_max_cosine": {"SOPHIE_V1_1": 0.1}},
            "rights_checklist": {"no_real_person_identity_input": True, "references_rights_cleared": True,
                                 "model_terms_commercial_ok": True, "protected_distinct": True},
            "approvals": [{"role": "human_owner", "by": "owner", "at": "2026-10-14T10:00:00Z", "decision": "approve"}],
            "locked_at": "2026-10-14T10:00:00Z", "immutable": True,
        }

    def test_master_lock_requires_human_owner_and_rights(self):
        schema = load("master_lock.schema.json")
        self.assertTrue(valid(schema, self.lock()))
        gpt_only = self.lock()
        gpt_only["approvals"] = [{"role": "gpt_hq", "by": "gpt", "at": "2026-10-14T10:00:00Z", "decision": "approve"}]
        self.assertFalse(valid(schema, gpt_only))
        rights = self.lock()
        rights["rights_checklist"]["no_real_person_identity_input"] = False
        self.assertFalse(valid(schema, rights))
        mutable = copy.deepcopy(self.lock())
        mutable["immutable"] = False
        self.assertFalse(valid(schema, mutable))


if __name__ == "__main__":
    unittest.main()
