# PdM use case - IFC information requirements

Acceptance criteria for an IFC model feeding the Predictive Maintenance
Cognitive Digital Twin. Generated from the ISO 19650 knowledge graph by
`backend/gen_pdm_spec.py`; every row cites the graph nodes it derives from.
In ISO 19650 terms this is EIR-level content: it refines the AIR of
ISO 19650-3 Annex A and the H&S schema of ISO 19650-6 for one use case.

| ID | Requirement | Level | Derived from |
|----|-------------|-------|--------------|
| M1 | Maintainable equipment is modelled as typed distribution elements | MANDATORY | ISO 19650-1 3.2.8 (term_asset); ISO 19650-3 A.4.4 (term_asset_system_description) |
| M2 | Equipment carries stable unique identifiers (GlobalId unique, Name/Tag set) | MANDATORY | ISO 19650-3 A.4.1 (term_asset_unique_identifier); ISO 19650-6 4.3.2; Table 1; 4.3.3; Table 2; 4.3.4; Table 3; 4.3.5; Table 4; Annex A; Table A.1 (field_identifier); ISO 19650-6 4.4; Figure 2; Figure 3 (term_hs_identifier) |
| M3 | Spatial structure exists and equipment is contained in it | MANDATORY | ISO 19650-1 3.1.2 (term_space); ISO 19650-6 4.3.2; Table 1; 4.3.3; Table 2; 4.3.4; Table 3; 4.3.5; Table 4; Annex A; Table A.1 (field_associated_location); ISO 19650-3 A.4.1 (term_asset_location_spatial_context) |
| M4 | Systems are modelled and equipment is assigned to them | MANDATORY | ISO 19650-3 A.4.4 (term_asset_system_description); ISO 19650-6 Annex D; Table D.1; Table D.2 (term_ifc_representation); ISO 19650-3 A.4.4 (term_asset_function_interdependency) |
| M5 | Equipment is classified against an external convention | MANDATORY | ISO 19650-6 4.3.7; Annex B (term_hs_categorization); ISO 19650-6 4.3.2; Table 1; 4.3.3; Table 2; 4.3.4; Table 3; 4.3.5; Table 4; Annex A; Table A.1 (field_category) |
| R1 | Manufacturer and model data on equipment (Pset_ManufacturerTypeInformation) | scored w=3 | ISO 19650-3 A.4.4 (term_vendor_lead_time); ISO 19650-3 A.4.4 (term_spares_inventory_information) |
| R2 | Engineering/design parameters on equipment (Pset_*Common) | scored w=3 | ISO 19650-3 A.4.2 (term_asset_design_parameters); ISO 19650-3 5.1.3; A.4.4 (term_asset_condition_duty) |
| R3 | Condition monitoring points modelled (sensors/instruments/controllers) | scored w=3 | ISO 19650-3 A.5 (term_condition_monitoring_system); ISO 19650-3 A.5 (term_scada_system); ISO 19650-5 B.3.4 (term_iot_security_assessment) |
| R4 | Health and safety risks attached via Pset_Risk | scored w=2 | ISO 19650-6 Annex D; Table D.1; Table D.2 (term_ifc_representation); ISO 19650-6 4.3.3; Table 2; 4.3.4; Table 3; Annex A; Table A.1 (field_level_of_risk); ISO 19650-6 4.3.3; Table 2; 4.3.4; Table 3; Annex C; Table C.1; Annex A; Table A.1 (field_likelihood); ISO 19650-6 4.3.3; Table 2; 4.3.4; Table 3; Annex C; Table C.1; Annex A; Table A.1 (field_consequence) |
| R5 | Maintenance activities present (IfcTask / work schedule) | scored w=2 | ISO 19650-3 A.4.1 (term_maintenance_inspection_schedule); ISO 19650-6 Annex D; Table D.1; Table D.2 (term_ifc_representation) |
| R6 | Commissioning data recorded | scored w=1 | ISO 19650-3 A.4.2 (term_asset_commissioning_data) |
| R7 | Warranty / service life data recorded | scored w=1 | ISO 19650-3 A.4.4 (term_asset_performance_target); ISO 19650-3 A.4.1 (term_maintenance_history) |
| R8 | Spaces/zones modelled (not just storeys) | scored w=1 | ISO 19650-1 3.1.2 (term_space); ISO 19650-6 4.3.2; Table 1; 4.3.3; Table 2; 4.3.4; Table 3; 4.3.5; Table 4; Annex A; Table A.1 (field_associated_location) |

Verdict: **CDT-ready** = all mandatory + score >= 0.8; **conditional** = all mandatory + score >= 0.5 (or one mandatory miss at score >= 0.7); otherwise **not ready**.

Run: `python3 backend/audit/check_ifc_pdm.py <model.ifc>`
