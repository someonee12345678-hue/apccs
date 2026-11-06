"""Exercise local Shaper envelopes, field boundaries and five complete boxes.

Inputs: fictional words, shipped shape examples and temporary directories.
Outputs: real normal/bad-input assertions, including A7 source checks.
Errors: any broken assertion makes the standalone suite fail.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

import apccs_shaper as shaper
import apccs_readability_gate as gate


ROOT = Path(__file__).resolve().parents[1]


def _catalog() -> dict:
    """Inputs: shipped catalog. Outputs: parsed JSON. Errors: malformed files raise."""
    return json.loads((ROOT / "plan/shapes/catalog.json").read_text(encoding="utf-8"))


def _template(shape_id: str = "batch") -> dict:
    """Inputs: shape ID. Outputs: parsed template. Errors: malformed files raise."""
    return json.loads((ROOT / "plan/shapes" / shape_id / "template.json").read_text(encoding="utf-8"))


class ApccsBatchA8ShaperTests(unittest.TestCase):
    """Inputs: synthetic test cases. Outputs: Shaper acceptance evidence. Errors: assertions."""

    print("Canary check: SHAPER = VALIDATED -> packet")

    def test_a801_01_enqueues_share_and_labeled_issue_in_one_inbox(self) -> None:
        """Inputs: two supplied source kinds. Outputs: distinct exact JSON receipts. Errors: assertions."""
        words = "  batch\r\ntitle: Fictional garden board\r\nUnicode: café ☃\n  "
        with tempfile.TemporaryDirectory() as scratch:
            before = Path.cwd()
            receipts = [shaper.enqueue_builder_words(scratch, kind, "fixture:001", labels, words)
                        for kind, labels in [("local_share", []), ("github_issue", ["words", "example"])]]
            self.assertNotEqual(receipts[0]["item_id"], receipts[1]["item_id"])
            self.assertEqual(Path.cwd(), before)
            for receipt in receipts:
                path = Path(receipt["path"])
                self.assertTrue(path.is_relative_to(Path(scratch)))
                saved = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(saved, receipt["envelope"])
                self.assertEqual(saved["source"]["original_words"], words)
                self.assertEqual(saved["source_sha256"], shaper._digest(words))
                self.assertEqual(gate.check_time_and_hash_values(saved["source"]["received_at"], saved["source_sha256"])["status"], "PASS")

    def test_a801_02_rejects_unlabeled_issue_and_bad_path(self) -> None:
        """Inputs: invalid envelopes/paths. Outputs: refusals with no items. Errors: assertions."""
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bad = [("github_issue", "ref", [], "words"), ("github_issue", "ref", ["Words"], "words"),
                   ("other", "ref", [], "words"), ([], "ref", [], "words"),
                   ("local_share", "", [], "words"), ("local_share", "ref", [], " \n"),
                   ("local_share", "ref", [], "\ud800"), ("local_share", "ref", [1], "words")]
            for args in bad:
                with self.subTest(args=str(args)), self.assertRaises(ValueError):
                    shaper.enqueue_builder_words(root, *args)
            for path in ["relative", "/", root / "absent", root / ".." / root.name]:
                with self.subTest(path=str(path)), self.assertRaises(ValueError):
                    shaper.enqueue_builder_words(path, "local_share", "ref", [], "batch")
            self.assertEqual(list(root.iterdir()), [])
            alias = root / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                shaper.enqueue_builder_words(alias, "local_share", "ref", [], "batch")
            self.assertEqual(list(root.iterdir()), [alias])

    def test_a802_01_selects_each_catalog_shape_deterministically(self) -> None:
        """Inputs: catalog keywords. Outputs: all five exact selections. Errors: assertions."""
        table = _catalog()["keywords"]
        for keyword, shape_id in table.items():
            result = shaper.select_builder_shape("Please " + keyword.upper() + ".", table)
            self.assertEqual(result["shape_id"], shape_id)
            self.assertEqual(result, shaper.select_builder_shape("Please " + keyword.upper() + ".", table))
        self.assertEqual(shaper.select_builder_shape("rebatchable", {"batch": "batch"})["shape_id"], "ASK")

    def test_a802_02_asks_on_no_match_or_ambiguous_match(self) -> None:
        """Inputs: unknown/conflicting words and invalid tables. Outputs: ASK/refusal. Errors: assertions."""
        table = _catalog()["keywords"]
        self.assertEqual(shaper.select_builder_shape("hello", table)["reason"], "no_match")
        result = shaper.select_builder_shape("batch and handoff", table)
        self.assertEqual(result["shape_id"], "ASK")
        self.assertEqual(result["conflicting_shapes"], ["batch", "handoff"])
        for words, mapping in [(None, table), ("batch", {}), ("batch", {"batch": "unknown"}),
                               ("batch", {"batch": "batch", "BATCH": "rule"})]:
            with self.assertRaises(ValueError):
                shaper.select_builder_shape(words, mapping)

    def test_a803_01_off_fills_known_fields_and_keeps_asks(self) -> None:
        """Inputs: explicit/absent/duplicate fields. Outputs: OFF packet and safe suggestions. Errors: assertions."""
        template = _template()
        template["source_metadata"] = {"source_kind": "local_share", "source_ref": "fixture:002",
                                       "labels": [], "received_at": "2026-11-06T00:00:00+00:00"}
        words = "batch\r\ntitle: Fictional garden board\r\n"
        forbidden = Mock(side_effect=AssertionError("OFF must not call AI"))
        packet = shaper.fill_builder_shape_fields("batch", words, template, ai_filler=forbidden)
        forbidden.assert_not_called()
        self.assertEqual(packet["fields"]["title"], "Fictional garden board")
        self.assertEqual(packet["fields"]["done_means"], "ASK")
        self.assertEqual(packet["source"], {**template["source_metadata"], "original_words": words})
        self.assertEqual(shaper.validate_builder_shape_packet(packet, {"templates": {"batch": template}})["status"], "PASS")
        suggest = Mock(return_value={"done_means": "Synthetic checks pass"})
        assisted = shaper.fill_builder_shape_fields("batch", words, template, "ASSIST", suggest)
        self.assertEqual(assisted["fields"]["done_means"], "ASK")
        self.assertEqual(assisted["suggestions"]["done_means"]["status"], "suggested")
        self.assertNotIn("title", suggest.call_args.args[0]["ask_fields"])
        self.assertEqual(shaper.validate_builder_shape_packet(assisted, {"templates": {"batch": template}})["status"], "PASS")
        duplicated = shaper.fill_builder_shape_fields("batch", "title: first\ntitle: second\n", _template())
        self.assertEqual(duplicated["fields"]["title"], "ASK")

    def test_a803_02_rejects_bad_mode_or_ai_overwrite(self) -> None:
        """Inputs: bad modes/suggestions/enums. Outputs: refusal without mutation. Errors: assertions."""
        template = _template()
        baseline = deepcopy(template)
        for mode in ["ON", "off", None]:
            with self.assertRaises(ValueError):
                shaper.fill_builder_shape_fields("batch", "batch", template, mode)
        for proposal in [{"source_ref": "forged"}, {"title": "overwrite"}, {"done_means": 7}, [],
                         {"target_repo": "not/an/allowed/repo"}]:
            with self.assertRaises(ValueError):
                shaper.fill_builder_shape_fields("batch", "title: explicit\n", template, "ASSIST", Mock(return_value=proposal))
        self.assertEqual(template, baseline)
        protected = _template("decision_row")
        with self.assertRaises(ValueError):
            shaper.fill_builder_shape_fields("decision_row", "decision", protected, "ASSIST", Mock(return_value={"decided_by": "Owner"}))
        def _mutating_suggester(request: dict) -> dict:
            request["ask_fields"]["source_ref"] = {"type": "string"}
            return {"source_ref": "forged"}
        with self.assertRaises(ValueError):
            shaper.fill_builder_shape_fields("batch", "batch", template, "ASSIST", _mutating_suggester)

    def test_a804_01_accepts_valid_packet_with_verbatim_source(self) -> None:
        """Inputs: partial packets and valid transitions. Outputs: PASS without mutation. Errors: assertions."""
        template = _template("handoff")
        words = "  handoff\ncurrent_state: Fictional board ready\n\t"
        packet = shaper.fill_builder_shape_fields("handoff", words, template)
        before = deepcopy(packet)
        for status, previous in [("prepared", None), ("validated", "prepared"), ("review_pending", "validated")]:
            candidate = deepcopy(packet)
            candidate["state"] = {"version": 1, "status": status, "previous": previous}
            self.assertEqual(shaper.validate_builder_shape_packet(candidate, {"templates": {"handoff": template}})["status"], "PASS")
        self.assertEqual(packet, before)
        self.assertEqual(packet["source"]["original_words"], words)

    def test_a804_02_rejects_off_shape_or_changed_source(self) -> None:
        """Inputs: forged fields/source/state/approval. Outputs: field-level FAIL. Errors: assertions."""
        template = _template()
        packet = shaper.fill_builder_shape_fields("batch", "title: Fictional board\n", template)
        mutations = []
        for key, value in [("extra", 1), ("schema_version", True), ("fields", {}),
                           ("shape_id", []), ("authorization", {"owner_approved": True, "may_execute": False}),
                           ("state", {"version": 1, "status": "approved", "previous": "prepared"})]:
            changed = deepcopy(packet); changed[key] = value; mutations.append(changed)
        changed = deepcopy(packet); changed["source"]["original_words"] += "changed"; mutations.append(changed)
        changed = deepcopy(packet); changed["fields"]["title"] = "Invented"; mutations.append(changed)
        changed = deepcopy(packet); changed["suggestions"] = {"done_means": {"value": "done", "status": "approved"}}; mutations.append(changed)
        changed = deepcopy(packet); changed["source"]["source_kind"] = []; mutations.append(changed)
        changed = deepcopy(packet); del changed["source"]; mutations.append(changed)
        for changed in mutations:
            result = shaper.validate_builder_shape_packet(changed, {"templates": {"batch": template}})
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(result["errors"])

    def test_a805_01_catalog_lists_complete_valid_boxes(self) -> None:
        """Inputs: shipped catalog/boxes. Outputs: all five validated templates. Errors: assertions."""
        result = shaper.validate_shape_box_catalog(_catalog(), ROOT)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(set(result["templates"]), shaper.SHAPE_IDS)

    def test_a805_02_rejects_missing_duplicate_or_outside_box(self) -> None:
        """Inputs: broken references/files/examples. Outputs: FAIL for each. Errors: assertions."""
        catalog = _catalog()
        variants = []
        changed = deepcopy(catalog); changed["boxes"].pop(); variants.append(changed)
        changed = deepcopy(catalog); changed["boxes"][1] = deepcopy(changed["boxes"][0]); variants.append(changed)
        changed = deepcopy(catalog); changed["boxes"][0]["readme"] = "../outside.md"; variants.append(changed)
        changed = deepcopy(catalog); changed["boxes"][0]["test"] = "code/test_apccs_shaper.py#missing"; variants.append(changed)
        for changed in variants:
            self.assertEqual(shaper.validate_shape_box_catalog(changed, ROOT)["status"], "FAIL")
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            shutil.copytree(ROOT / "plan/shapes", root / "plan/shapes")
            (root / "code").mkdir()
            shutil.copyfile(ROOT / "code/test_apccs_shaper.py", root / "code/test_apccs_shaper.py")
            example = root / "plan/shapes/batch/example.json"
            example.unlink()
            self.assertEqual(shaper.validate_shape_box_catalog(catalog, root)["status"], "FAIL")
            example.symlink_to(ROOT / "plan/shapes/batch/example.json")
            self.assertEqual(shaper.validate_shape_box_catalog(catalog, root)["status"], "FAIL")
        with patch.object(shaper, "validate_builder_shape_packet", return_value={"status": "FAIL"}):
            self.assertEqual(shaper.validate_shape_box_catalog(catalog, ROOT)["status"], "FAIL")

    def _box(self, shape_id: str) -> None:
        """Inputs: one shipped box. Outputs: packet/selection assertions. Errors: assertions."""
        template = _template(shape_id)
        example = json.loads((ROOT / "plan/shapes" / shape_id / "example.json").read_text(encoding="utf-8"))
        self.assertEqual(shaper.validate_builder_shape_packet(example, {"templates": {shape_id: template}})["status"], "PASS")
        self.assertEqual(shaper.select_builder_shape(example["source"]["original_words"], _catalog()["keywords"])["shape_id"], shape_id)
        self.assertFalse(example["authorization"]["may_execute"])

    def test_a805_box_batch(self) -> None:
        """Inputs: batch box. Outputs: verified example. Errors: assertions."""
        self._box("batch")

    def test_a805_box_rule(self) -> None:
        """Inputs: rule box. Outputs: verified example. Errors: assertions."""
        self._box("rule")

    def test_a805_box_research_ask(self) -> None:
        """Inputs: research box. Outputs: verified example. Errors: assertions."""
        self._box("research_ask")

    def test_a805_box_decision_row(self) -> None:
        """Inputs: decision box. Outputs: verified example. Errors: assertions."""
        self._box("decision_row")

    def test_a805_box_handoff(self) -> None:
        """Inputs: handoff box. Outputs: verified example. Errors: assertions."""
        self._box("handoff")

    def test_a8_open_standards(self) -> None:
        """Inputs: both new Python modules. Outputs: A7 doc/name/format checks. Errors: assertions."""
        for name in ["apccs_shaper.py", "test_apccs_shaper.py"]:
            source = (ROOT / "code" / name).read_text(encoding="utf-8")
            for checker in [gate.check_docstrings_from_ast, gate.check_pep8_names_from_ast,
                            gate.check_open_data_writes_from_ast]:
                result = checker(source, name)
                self.assertEqual(result["status"], "PASS", result)

    def test_a8_offline_envelope_to_checked_packet(self) -> None:
        """Inputs: supplied fictional issue text. Outputs: full local pipeline. Errors: assertions."""
        words = "batch\ntitle: Fictional seed board\ntarget_repo: someonee12345678-hue/apccs\n"
        with tempfile.TemporaryDirectory() as scratch:
            receipt = shaper.enqueue_builder_words(scratch, "github_issue", "fixture:003", ["words"], words)
            source = receipt["envelope"]["source"]
            selected = shaper.select_builder_shape(source["original_words"], _catalog()["keywords"])
            template = _template(selected["shape_id"])
            template["source_metadata"] = {key: value for key, value in source.items() if key != "original_words"}
            packet = shaper.fill_builder_shape_fields(selected["shape_id"], words, template)
            self.assertEqual(shaper.validate_builder_shape_packet(packet, {"templates": {"batch": template}})["status"], "PASS")
            changed = deepcopy(packet)
            changed["source"]["source_ref"] = "forged"
            self.assertEqual(shaper.validate_builder_shape_packet(changed, {"templates": {"batch": template}})["status"], "FAIL")
            self.assertEqual(packet["fields"]["done_means"], "ASK")
            self.assertFalse(packet["authorization"]["may_execute"])

    def test_a8_bad_container_inputs_fail_closed(self) -> None:
        """Inputs: malformed top-level containers. Outputs: FAIL or ValueError. Errors: assertions."""
        for value in [None, [], "text", 7, True]:
            self.assertEqual(shaper.validate_builder_shape_packet(value, {})["status"], "FAIL")
            self.assertEqual(shaper.validate_shape_box_catalog(value, ROOT)["status"], "FAIL")
            with self.assertRaises(ValueError):
                shaper.fill_builder_shape_fields("batch", "batch", value)


if __name__ == "__main__":
    unittest.main()
