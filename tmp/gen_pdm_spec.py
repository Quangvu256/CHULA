#!/usr/bin/env python3
"""Generate the Predictive Maintenance IFC requirements spec FROM the knowledge graph.

Single source of truth: every requirement cites the KG node ids it derives from,
and generation FAILS if a cited node does not exist in the extraction files.
The only hand-authored part is the IFC probe (which entities / property sets to
look for) - that is IFC domain knowledge the standards delegate to ISO 16739.
The Pset_Risk property names are not hand-authored either: they are read from
the field_* nodes' ifc4_3 / ifc4_0 / ifc2x3 keys (ISO 19650-6 Annex D, Table D.2).

Outputs:
  tmp/pdm_ifc_requirements.json  - machine-readable, consumed by check_ifc_pdm.py
  tmp/pdm_use_case_spec.md       - human-readable use case specification
"""
import json, sys

FILES = ["iso19650-1_extraction_v4.json", "iso19650-2_extraction_v1.json",
         "iso19650-3_extraction_v1.2.json", "iso19650-4_extraction_v1.json", "iso19650-5_extraction_v1.json",
         "iso19650-6_extraction_v2.json"]
KG = {}
for f in FILES:
    for n in json.load(open(f))["nodes"]:
        KG[n["id"]] = n


def modality(n):
    """normative / informative / interpretive, taken from the graph - never guessed.

    A requirement resting on an informative annex is a weaker justification than one
    resting on a 'shall', and the reader is entitled to see which is which. The
    extraction files record this three ways, in order of authority."""
    a = n.get("assertion_status", "")
    if a.startswith("normative") and "informative" in a:
        return "mixed"
    if a.startswith("normative"):
        return "normative"
    if a == "informative_example":
        return "informative"
    if a == "interpretive_pdm":
        return "interpretive"
    # extraction convention: every informative node says so at the head of its note
    if n.get("note", "").startswith("Informative"):
        return "informative"
    return {"terms_clause": "normative", "body_clause": "normative",
            "schema_table": "normative", "schema_table_annex": "informative",
            "informative_annex": "informative",
            "mixed_normative_informative": "mixed"}.get(n.get("source_type", ""), "unknown")


def cite(*ids):
    out = []
    for i in ids:
        if i not in KG:
            sys.exit(f"FATAL: requirement cites unknown KG node {i!r}")
        n = KG[i]
        out.append({"node": i, "name": n["name"],
                    "definition": n["definition"],
                    "pdm_relevance": n.get("pdm_relevance", "low"),
                    "modality": modality(n),
                    "standard": n["provenance"]["standard"],
                    "clause": n["provenance"]["clause"]})
    return out


def probe_human(p):
    """One plain sentence describing what the checker actually looks for."""
    k = p["kind"]
    ents = ", ".join(p.get("entities", [])[:6])
    more = len(p.get("entities", [])) - 6
    ents += f" and {more} more" if more > 0 else ""
    if k == "entity_any":
        return f"At least one instance of: {ents}."
    if k == "identifiers":
        return (f"Every equipment occurrence has a unique GlobalId, and at least "
                f"{p['min_named']:.0%} of them carry a Name or Tag.")
    if k == "containment":
        return (f"A spatial tree exists ({', '.join(p['spatial'][:4])}...) "
                f"and at least {p['min_contained']:.0%} of equipment sits inside it.")
    if k == "system_assignment":
        return ("At least one IfcSystem / IfcDistributionSystem exists and equipment "
                "is assigned to it through IfcRelAssignsToGroup.")
    if k == "classification":
        return ("Equipment is linked to an IfcClassificationReference through "
                "IfcRelAssociatesClassification.")
    if k == "pset_coverage":
        what = (", ".join(p["psets"]) if "psets" in p
                else f"a {p['psets_prefix_suffix'][0]}...{p['psets_prefix_suffix'][1]} set")
        return f"At least {p['min']:.0%} of equipment carries {what}."
    if k == "pset_risk":
        return ("A Pset_Risk property set is present, and its property names are matched "
                "against the ones ISO 19650-6 Annex D Table D.2 gives for the file's own "
                "IFC version (IFC4.3, IFC4.0 or IFC2x3).")
    if k == "property_name_contains":
        return f"Any property whose name contains '{p['needle']}'."
    if k == "pset_any":
        return f"Any of these property sets: {', '.join(p['psets'])}."
    return k


# Pset_Risk property names straight from the KG (Annex D, Table D.2)
pset_risk = {"ifc4_3": [], "ifc4_0": [], "ifc2x3": []}
for i, n in KG.items():
    if i.startswith("field_"):
        for ver in pset_risk:
            v = n.get(ver, "")
            if v and not v.startswith(("(", "-")):
                pset_risk[ver] += [p.strip() for p in v.split(";")]

EQUIPMENT = [  # IfcDistributionElement occurrence subtypes = maintainable plant
    "IfcPump", "IfcFan", "IfcCompressor", "IfcChiller", "IfcBoiler",
    "IfcCoolingTower", "IfcUnitaryEquipment", "IfcAirToAirHeatRecovery",
    "IfcHeatExchanger", "IfcEvaporator", "IfcEvaporativeCooler", "IfcHumidifier",
    "IfcTank", "IfcFilter", "IfcDuctSilencer", "IfcAirTerminal", "IfcAirTerminalBox",
    "IfcDamper", "IfcValve", "IfcElectricMotor", "IfcElectricGenerator",
    "IfcTransformer", "IfcSwitchingDevice", "IfcDistributionChamberElement",
    "IfcFlowMovingDevice", "IfcEnergyConversionDevice", "IfcFlowController",
    "IfcDistributionElement", "IfcDistributionControlElement",
]
SENSORS = ["IfcSensor", "IfcSensorType", "IfcFlowInstrument", "IfcController",
           "IfcControllerType", "IfcUnitaryControlElement", "IfcActuator"]
SPATIAL = ["IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcSpace", "IfcFacility",
           "IfcFacilityPart", "IfcBridge", "IfcRoad", "IfcRailway", "IfcMarineFacility"]

REQS = [
    # --- MANDATORY: without these the model cannot join the KG / CDT at all ---
    dict(id="M1", mandatory=True, category="identification",
         title="Maintainable equipment is modelled as typed distribution elements",
         rationale="No typed plant, nothing to maintain: PdM needs pumps, fans, "
                   "chillers etc. as their IFC classes, not as untyped proxies.",
         probe={"kind": "entity_any", "entities": EQUIPMENT,
                "proxy_warn": "IfcBuildingElementProxy"},
         sources=cite("term_asset", "term_asset_system_description")),
    dict(id="M2", mandatory=True, category="identification",
         title="Equipment carries stable unique identifiers (GlobalId unique, Name/Tag set)",
         rationale="The unique asset identifier is the join key between the IFC "
                   "model, the H&S register and the condition time series.",
         probe={"kind": "identifiers", "entities": EQUIPMENT, "min_named": 0.8},
         sources=cite("term_asset_unique_identifier", "field_identifier",
                      "term_hs_identifier")),
    dict(id="M3", mandatory=True, category="structure",
         title="Spatial structure exists and equipment is contained in it",
         rationale="Risk and incident records resolve to 'space, location, zone "
                   "or site'; an element outside the spatial tree has no location.",
         probe={"kind": "containment", "spatial": SPATIAL, "entities": EQUIPMENT,
                "min_contained": 0.8},
         sources=cite("term_space", "field_associated_location",
                      "term_asset_location_spatial_context")),
    dict(id="M4", mandatory=True, category="structure",
         title="Systems are modelled and equipment is assigned to them",
         rationale="Annex D maps the H&S context product to IfcSystem, and the "
                   "asset/served-system description is one of the AIM contents "
                   "ISO 19650-3 Annex A gives as an example of commercial OIR.",
         probe={"kind": "system_assignment",
                "systems": ["IfcSystem", "IfcDistributionSystem", "IfcBuildingSystem"],
                "entities": EQUIPMENT},
         sources=cite("term_asset_system_description", "term_ifc_representation",
                      "term_asset_function_interdependency")),
    dict(id="M5", mandatory=True, category="identification",
         title="Equipment is classified against an external convention",
         rationale="Categorization shall follow the convention in the project/"
                   "asset information standard (e.g. Uniclass); classification is "
                   "how model elements join external code tables in the CDT.",
         probe={"kind": "classification", "entities": EQUIPMENT},
         sources=cite("term_hs_categorization", "field_category")),
    # --- RECOMMENDED: scored, each one unlocks part of the PdM loop ---
    dict(id="R1", mandatory=False, weight=3, category="technical_data",
         title="Manufacturer and model data on equipment (Pset_ManufacturerTypeInformation)",
         rationale="ISO 19650-3 Annex A lists vendor data and lead time as example AIM "
                   "content; manufacturer plus model is the minimum for failure-mode "
                   "libraries and spares planning.",
         probe={"kind": "pset_coverage", "entities": EQUIPMENT,
                "psets": ["Pset_ManufacturerTypeInformation"], "min": 0.5},
         sources=cite("term_vendor_lead_time", "term_spares_inventory_information")),
    dict(id="R2", mandatory=False, weight=3, category="technical_data",
         title="Engineering/design parameters on equipment (Pset_*Common)",
         rationale="Design parameters are the reference the condition data is "
                   "judged against (asset condition and duty).",
         probe={"kind": "pset_coverage", "entities": EQUIPMENT,
                "psets_prefix_suffix": ["Pset_", "Common"], "min": 0.5},
         sources=cite("term_asset_design_parameters", "term_asset_condition_duty")),
    dict(id="R3", mandatory=False, weight=3, category="monitoring",
         title="Condition monitoring points modelled (sensors/instruments/controllers)",
         rationale="The sensor is where the condition observation is produced; "
                   "without modelled monitoring points the twin cannot bind the "
                   "time series to locations. Also security-relevant: connected "
                   "plant is Annex B code 41.",
         probe={"kind": "entity_any", "entities": SENSORS},
         sources=cite("term_condition_monitoring_system", "term_scada_system",
                      "term_iot_security_assessment")),
    dict(id="R4", mandatory=False, weight=2, category="hs_risk",
         title="Health and safety risks attached via Pset_Risk",
         rationale="Annex D maps the Part 6 risk schema onto Pset_Risk; version-"
                   "appropriate property names are read from the KG.",
         probe={"kind": "pset_risk", "props_by_schema": pset_risk},
         sources=cite("term_ifc_representation", "field_level_of_risk",
                      "field_likelihood", "field_consequence")),
    dict(id="R5", mandatory=False, weight=2, category="maintenance",
         title="Maintenance activities present (IfcTask / work schedule)",
         rationale="ISO 19650-3 Annex A lists the future maintenance and inspection "
                   "schedule as example AIM content; Annex D maps H&S activity to "
                   "IfcTask.",
         probe={"kind": "entity_any",
                "entities": ["IfcTask", "IfcTaskType", "IfcWorkSchedule", "IfcWorkPlan"]},
         sources=cite("term_maintenance_inspection_schedule", "term_ifc_representation")),
    dict(id="R6", mandatory=False, weight=1, category="technical_data",
         title="Commissioning data recorded",
         rationale="Commissioning dates/data are the baseline the degradation "
                   "trend starts from.",
         probe={"kind": "property_name_contains", "needle": "commission"},
         sources=cite("term_asset_commissioning_data")),
    dict(id="R7", mandatory=False, weight=1, category="technical_data",
         title="Warranty / service life data recorded",
         rationale="Replacement planning input; supports RUL horizon sanity checks.",
         probe={"kind": "pset_any",
                "psets": ["Pset_Warranty", "Pset_ServiceLife", "Pset_Condition"]},
         sources=cite("term_asset_performance_target", "term_maintenance_history")),
    dict(id="R8", mandatory=False, weight=1, category="structure",
         title="Spaces/zones modelled (not just storeys)",
         rationale="Alignment/zone-level location is what lets a risk or a work "
                   "order be scoped to a zone; IfcSpace/IfcZone is the H&S "
                   "location target in Annex D.",
         probe={"kind": "entity_any", "entities": ["IfcSpace", "IfcZone"]},
         sources=cite("term_space", "field_associated_location")),
]

# Which step of the PdM control loop each requirement serves, and what actually
# breaks without it. This is the "why" the UI shows; keeping it here rather than
# in the page means the explanation ships with the spec.
WHY = {
    "M1": ("The thing being maintained",
           "There is nothing to hang condition data, risks or work orders on. A model full of "
           "untyped proxies cannot tell a pump from a handrail, so no asset register can be built "
           "from it and the whole loop has no subject."),
    "M2": ("Join key - every step",
           "The IFC model, the health and safety register and the condition time series each end "
           "up with their own private key for the same pump. Nothing can be joined, so the "
           "sensor reading can never be attributed to the asset it came from."),
    "M3": ("Where the risk or the work happens",
           "Risk, incident and work-order records cannot resolve a location. Maintenance planning "
           "loses access routes and exclusion zones, and a risk cannot be scoped to a zone."),
    "M4": ("System context and knock-on effect",
           "Criticality cannot be reasoned about: you cannot tell that this pump failing takes the "
           "whole chilled water loop down, so alert prioritisation degrades to per-component "
           "guessing."),
    "M5": ("Joining external code tables",
           "Categorisation has no anchor, so equipment cannot be matched to failure-mode "
           "libraries, spares catalogues or the regional risk classification. ISO 19650-6 4.3.7 "
           "delegates categorisation to exactly such an external convention."),
    "R1": ("Failure-mode library and spares",
           "Failure modes have to be guessed rather than looked up from the manufacturer's data, "
           "and spares and lead time cannot be planned. Pilot can still run on generic models."),
    "R2": ("Baseline the condition data is judged against",
           "There is no design duty point to compare a reading against, so anomaly detection has "
           "to learn every threshold from scratch instead of starting from the design envelope."),
    "R3": ("Where the measurement comes from",
           "The twin has no modelled measurement points, so the time series cannot be bound to a "
           "location in the model. Readings can still be attached by asset tag, but the spatial "
           "reasoning is lost - and connected plant is also the ISO 19650-5 security surface."),
    "R4": ("The safety half of the loop",
           "The programme can only be measured on downtime, not on safety outcome. Risks stay in "
           "spreadsheets outside the model and cannot be queried against the equipment they "
           "belong to."),
    "R5": ("Existing maintenance regime",
           "The current schedule is invisible, so predicted interventions cannot be compared with "
           "or merged into what is already planned - a common cause of duplicated work orders."),
    "R6": ("Start of the degradation curve",
           "There is no commissioning baseline, so age-based and trend-based models have no "
           "origin and remaining-life estimates lose their reference point."),
    "R7": ("Replacement planning and sanity checks",
           "Warranty and service-life bounds are unknown, so remaining-life predictions cannot be "
           "sanity-checked against the expected life of the equipment."),
    "R8": ("Fine-grained location",
           "Location resolution stops at storey level. Permits, exclusion zones and zone-scoped "
           "risks all become imprecise."),
}
for r in REQS:
    r["loop_step"], r["if_missing"] = WHY[r["id"]]
    r["probe_human"] = probe_human(r["probe"])
    mods = {s["modality"] for s in r["sources"]}
    r["basis"] = ("normative" if mods <= {"normative"} else
                  "informative" if mods <= {"informative"} else "mixed")

spec = {
    "use_case": "Predictive Maintenance on a Cognitive Digital Twin",
    "derived_from": FILES,
    "how_generated": (
        "Each requirement is a triple: (1) an anchor into the knowledge graph, cited by node id - "
        "generation aborts if a cited node no longer exists; (2) an IFC probe, which is the only "
        "hand-authored part, because ISO 19650 delegates the IFC schema itself to ISO 16739; and "
        "(3) a gating level - MANDATORY when the data cannot be joined at all without it, "
        "otherwise a weight from 1 to 3. The Pset_Risk property names are not hand-authored "
        "either: they are read from the field_* nodes' ifc4_3 / ifc4_0 / ifc2x3 keys, which carry "
        "ISO 19650-6 Annex D Table D.2."),
    "normative_basis_for_automated_checking": {
        "statement": "ISO 19650-4:2022 gives this checker its normative standing: 3.2.3 Note 3 "
                     "allows an information reviewer to be an artificial intelligence agent or an "
                     "automated rules-based process; 7.2 makes conformance against the chosen "
                     "exchange schema a review criterion; 7.6 asks for completeness checks against "
                     "requirement-derived checklists using repeatable automated processes. An IFC "
                     "readiness audit under this specification is therefore an information review "
                     "in the ISO 19650-4 sense, not an extra-standard invention.",
        "sources": cite("term_information_reviewer", "criterion_conformance",
                        "criterion_completeness"),
    },
    "modality_note": (
        "Each citation is tagged normative, informative or mixed, straight from the extraction "
        "files. ISO 19650-3 Annex A and ISO 19650-5 Annex B are informative: they give 'examples "
        "of information that can be required within an AIM', not obligations. ISO 19650-6 Annex C "
        "and Annex D are informative too. A requirement whose basis is entirely informative is "
        "still sound engineering for this use case, but it is a recommendation of the series "
        "rather than a rule of it - M4 is the one mandatory gate in that position."),
    "verdict_rule": {
        "cdt_ready": "all mandatory pass AND recommended score >= 0.8",
        "conditional": "all mandatory pass AND recommended score >= 0.5, or exactly one mandatory fails with score >= 0.7",
        "not_ready": "otherwise",
    },
    "requirements": REQS,
}
json.dump(spec, open("tmp/pdm_ifc_requirements.json", "w"), indent=2)

# ---- human-readable spec ----
md = ["# PdM use case - IFC information requirements",
      "",
      "Acceptance criteria for an IFC model feeding the Predictive Maintenance",
      "Cognitive Digital Twin. Generated from the ISO 19650 knowledge graph by",
      "`tmp/gen_pdm_spec.py`; every row cites the graph nodes it derives from.",
      "In ISO 19650 terms this is EIR-level content: it refines the AIR of",
      "ISO 19650-3 Annex A and the H&S schema of ISO 19650-6 for one use case.",
      "",
      "| ID | Requirement | Level | Derived from |"     ,
      "|----|-------------|-------|--------------|"]
for r in REQS:
    src = "; ".join(f"{s['standard']} {s['clause']} ({s['node']})" for s in r["sources"])
    lvl = "MANDATORY" if r["mandatory"] else f"scored w={r['weight']}"
    md.append(f"| {r['id']} | {r['title']} | {lvl} | {src} |")
md += ["", "Verdict: **CDT-ready** = all mandatory + score >= 0.8; "
       "**conditional** = all mandatory + score >= 0.5 (or one mandatory miss at "
       "score >= 0.7); otherwise **not ready**.",
       "", "Run: `python3 tmp/check_ifc_pdm.py <model.ifc>`"]
open("tmp/pdm_use_case_spec.md", "w").write("\n".join(md) + "\n")

print(f"OK: {len(REQS)} requirements ({sum(1 for r in REQS if r['mandatory'])} mandatory), "
      f"all citations resolved against the KG")
print("Pset_Risk properties from KG:", {k: len(v) for k, v in pset_risk.items()})
