# handoff shape box

This is a fictional local example, not authorized work. The template defines the
exact string fields and any allowed values. Write an explicit `field_name: value`
line to populate a field. Missing or duplicate fields remain `ASK`; nothing is
inferred from prose. Source words stay attached verbatim.

- Template: `template.json`
- Worked example: `example.json`
- Test: `code/test_apccs_shaper.py#test_a805_box_handoff`

The checker rejects extra structure, changed source copies, invalid enums,
unapproved execution and invalid state transitions. `OFF` needs no AI. `ASSIST`
keeps values as separate suggested proposals; ASK fields remain unapproved.
The source SHA-256 detects inconsistent copies, not a replacement of both the
source and its digest. This is not identity authentication or an Owner signature.

A caller may copy verified source metadata into a template's `source_metadata`.
Without supplied metadata those values remain `ASK`. An issue's `words` label
permits local ingestion only; it never approves execution. Live phone/GitHub
adapters are NOT CHECKED. No connection is created by this box.

Undo: stop using generated packets and return to the existing prose handoff;
keep receipts and append a superseding catalog revision instead of deleting it.
