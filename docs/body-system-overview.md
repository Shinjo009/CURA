# Body system overview

Tapping Blood Report or Bio-AI Report opens a visual overview built from the member's structured
report data. No model call is made to build it. CURA's model is used only when the member asks a
question from the overview.

## Endpoints

| Endpoint | Returns |
| --- | --- |
| `GET /api/v1/me/body-systems?report_id=` | Blood results grouped by body system, one result record each |
| `GET /api/v1/me/bio-ai-risks?report_id=` | Predicted risks the Bio-AI report returned, grouped for display |

Both read through the existing cached report providers. `report_id` selects a historical report and
an unknown id is a 404. A provider outage is a plain 503 and the frontend falls back to the chat
explanation.

## Registry (versioned data, no code change to edit)

`backend/app/biomarkers/data/`

- `biomarker_registry_v1.csv`: one row per source group and test, with the proposed canonical id,
  primary system and secondary systems. Original laboratory names are never rewritten.
- `registry_overlay_v1.json`: aliases, CURA key bridge, spelling repairs, derived indices, review
  notes and the group level allergy list.
- `risk_registry_v1.json`: Bio-AI risk codes grouped into display areas.

The registry is a proposed design mapping, not a laboratory classification. A bad edit (a test with
two primary systems, a bridge to an unknown id) fails at load.

## Rules the builder follows

- Only results in the selected report produce output. A system with no results has no card, and a
  missing test is never shown as normal.
- Each result is one record. Cross listed results appear under their primary system and are listed
  by id under related systems, so report wide counts never double count. Sleep and Recovery has no
  primary tests and appears only through related results.
- Values, units, reference ranges, flags and dates are the report's own. The report's flag wins. A
  lab range is used only when the report gave no flag.
- Exact duplicate records collapse. A repeat with a different value keeps one and lists the other.
  The same test in a different unit is never merged or trended.
- Unknown tests are kept under Other results with a mapping review flag.
- Derived indices are listed as given, never recomputed, and never a key finding.
- Allergy is a separate section, group level only, and is not a diagnosis.
- Bio-AI predictions are a separate registry and are labelled as predicted risk. Nothing is inferred
  from blood results.

## Not in the supplied registry yet

Ferritin, Free T4, bare Transferrin, plain CRP, blood pressure, BMI, waist and postprandial glucose
are not in the supplied list. They appear under Other results until they are added to the CSV.
Qualitative urine results (colour, cast, crystals) arrive from the provider as non numeric, so they
show as "No result" until the provider contract carries text values.
