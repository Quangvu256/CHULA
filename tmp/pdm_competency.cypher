// Competency questions for the Predictive Maintenance use case.
// Each query must return rows on the loaded graph; together they prove the
// ontology can answer the questions the use case needs, not just store nodes.

// CQ1 - the PdM spine: from a sensor reading to a retrained model, end to end.
MATCH p = (:Iso19650 {id:'term_condition_monitoring_system'})
          -[:CONTRIBUTES_TO]->(:Iso19650 {id:'term_condition_observation'})
          -[:SUPPORTS]->(:Iso19650 {id:'term_pdm_model'})
          -[:RESULTS_IN]->(:Iso19650 {id:'term_remaining_useful_life_prediction'})
          -[:RESULTS_IN]->(:Iso19650 {id:'term_maintenance_alert'})
          -[:RESULTS_IN]->(:Iso19650 {id:'term_maintenance_work_order'})
          -[:RESULTS_IN]->(:Iso19650 {id:'term_maintenance_intervention_outcome'})
          -[:SUPPORTS]->(:Iso19650 {id:'term_pdm_model'})
RETURN [n IN nodes(p) | n.name] AS spine;

// CQ2 - what information does the standard require to feed the PdM model,
// and where does each requirement come from?
MATCH (src:Iso19650)-[r:SUPPORTS|CONTRIBUTES_TO]->(m:Iso19650 {id:'term_pdm_model'})
RETURN src.name, type(r), r.provenance_standard, r.provenance_clause
ORDER BY src.name;

// CQ3 - Part 6's safety loop: how does an equipment failure become a recorded
// safety incident, and how does that incident feed back into prediction?
MATCH (fm:Iso19650 {id:'term_failure_mode'})-[a:RESULTS_IN]->(inc:Iso19650 {id:'term_hs_incident'}),
      (inc)-[b:SUPPORTS]->(m:Iso19650 {id:'term_pdm_model'})
RETURN fm.name, inc.name, m.name, a.provenance_clause AS incident_basis, b.provenance_clause AS feedback_basis;

// CQ4 - alert priority: which risk grades exist, what do they mean
// operationally, and what maintenance urgency do they map to?
MATCH (g:Iso19650)-[:PART_OF]->(:Iso19650 {id:'term_level_of_risk'})
WHERE g.id STARTS WITH 'grade_'
RETURN g.name, g.operational_prioritization, g.level_of_risk_meaning
ORDER BY g.operational_prioritization;

// CQ5 - the record schema an implementation must produce: every property
// field of the risk sub-schema with its type and IFC 4.3 mapping.
MATCH (f:Iso19650)-[:PART_OF]->(:Iso19650 {id:'term_risk_sub_schema'})
WHERE f.id STARTS WITH 'field_'
RETURN f.name, f.specification, f.ifc4_3
ORDER BY f.name;

// CQ6 - the asset join: which schema fields resolve a record to a physical
// asset, and through which identifier?
MATCH (f:Iso19650 {id:'field_associated_product'})-[r:LINKED_TO]->(u:Iso19650 {id:'term_asset_unique_identifier'})
RETURN f.name, u.name, r.note;

// CQ7 - security governance: every PdM-loop node governed by the Part 5
// security information requirements.
MATCH (:Iso19650 {id:'term_security_information_requirements'})-[r:GOVERNS]->(x:Iso19650)
RETURN x.name, r.provenance_clause ORDER BY x.name;

// CQ8 - the two recorded normative conflicts an implementation must resolve.
MATCH (a:Iso19650)-[r:LINKED_TO|RESPONDS_TO]->(b:Iso19650)
WHERE r.note STARTS WITH 'CONFLICT'
RETURN a.name, b.name, r.note;

// CQ9 - provenance integrity: every relationship must carry standard+clause.
MATCH ()-[r]->()
WITH count(r) AS total,
     sum(CASE WHEN r.provenance_standard IS NULL OR r.provenance_clause IS NULL THEN 1 ELSE 0 END) AS missing
RETURN total, missing;

// CQ10 - interpretive edges are separable: the standards-only graph can be
// recovered by excluding USE-CASE EXTENSION provenance.
MATCH ()-[r]->()
RETURN r.provenance_standard AS source, count(*) AS edges
ORDER BY edges DESC;
