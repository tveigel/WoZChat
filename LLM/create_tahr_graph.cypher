// Clear existing data and create constraints
MATCH (n) DETACH DELETE n;
CREATE CONSTRAINT field_id_unique IF NOT EXISTS FOR (f:Field) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT loop_id_unique IF NOT EXISTS FOR (l:LoopController) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT condition_id_unique IF NOT EXISTS FOR (c:Condition) REQUIRE c.id IS UNIQUE;

/* ---------- 1. NODE CREATION ---------- */
UNWIND [
  /* Core */
  {id:'START', question:'—', thoughtProcess:'Virtual start anchor', goldAnswer:'—', type:'anchor'},
  {id:'Q1', question:'Date of accident', thoughtProcess:'Establishes legal/insurance timeframe; anchors time‑series data.', goldAnswer:'2024‑05‑07', type:'field'},
  {id:'Q2', question:'Local time (HH:MM)', thoughtProcess:'Enables synchronisation with traffic‑light outage logs & witness timelines.', goldAnswer:'07:45', type:'field'},
  {id:'Q3', question:'Town / city', thoughtProcess:'Determines jurisdiction and police precinct.', goldAnswer:'Riverton', type:'field'},
  {id:'Q4', question:'Precise location (street & landmark)', thoughtProcess:'Pin‑points scene for crash‑map heat‑analysis; distinguishes intersections.', goldAnswer:'Main St & Oak St, Riverton', type:'field'},
  {id:'Q5', question:'Weather conditions (list)', thoughtProcess:'Context for visibility & traction factors; feeds risk models.', goldAnswer:'Heavy rain', type:'field'},
  {id:'Q5a', question:'Describe other weather', thoughtProcess:'Captures edge cases not on list (fog, hail) – richer dataset.', goldAnswer:'', type:'field'},
  {id:'Q6', question:'Lighting (daylight/dusk/night)', thoughtProcess:'Captures illumination conditions for hazard correlation.', goldAnswer:'Daylight', type:'field'},
  {id:'Q7', question:'Narrative: step‑by‑step description', thoughtProcess:'Core causal chain; lets experts reconstruct events.', goldAnswer:'Vehicle A travelling east … Vehicle B failed to yield …', type:'field'},
  /* Vehicle A */
  {id:'VA8', question:'Vehicle identifier', thoughtProcess:'Index for loop logic; links occupants & damage.', goldAnswer:'A', type:'field'},
  {id:'VA9', question:'Make & model', thoughtProcess:'Needed for recall notices & crashworthiness analysis.', goldAnswer:'Ford Focus', type:'field'},
  {id:'VA10', question:'Year', thoughtProcess:'Determines safety‑feature set & valuation.', goldAnswer:'2019', type:'field'},
  {id:'VA11', question:'Registration plate', thoughtProcess:'Legal identifier for insurance lookup.', goldAnswer:'RI‑AF 224', type:'field'},
  {id:'VA13', question:'Moving or stationary', thoughtProcess:'Branch to speed field; informs fault analysis.', goldAnswer:'Moving', type:'field'},
  {id:'VA12', question:'Speed before impact (km/h)', thoughtProcess:'Energy of collision & fault share.', goldAnswer:'50', type:'field'},
  {id:'VA14', question:'Airbags deployed?', thoughtProcess:'Relates to injury severity & repair cost.', goldAnswer:'Yes', type:'field'},
  {id:'VA15', question:'Driver full name', thoughtProcess:'Legal identity.', goldAnswer:'Alex Müller', type:'field'},
  {id:'VA16', question:'Driver age', thoughtProcess:'Demographic risk factor.', goldAnswer:'34', type:'field'},
  {id:'VA17', question:'Gender', thoughtProcess:'Optional statistical demographic.', goldAnswer:'Male', type:'field'},
  {id:'VA18', question:'Alcohol/substance suspected?', thoughtProcess:'Liability & police escalation.', goldAnswer:'No', type:'field'},
  {id:'VA18a', question:'Substance details', thoughtProcess:'Evidence chain if substance = Yes.', goldAnswer:'', type:'field'},
  {id:'VA19', question:'# Passengers', thoughtProcess:'Sets loop for passenger sub‑block.', goldAnswer:'0', type:'field'},
  /* Vehicle B */
  {id:'VB8', question:'Vehicle identifier', thoughtProcess:'Index for loop logic; links occupants & damage.', goldAnswer:'B', type:'field'},
  {id:'VB9', question:'Make & model', thoughtProcess:'Needed for recall notices & crashworthiness analysis.', goldAnswer:'VW Golf', type:'field'},
  {id:'VB10', question:'Year', thoughtProcess:'Determines safety‑feature set & valuation.', goldAnswer:'2017', type:'field'},
  {id:'VB11', question:'Registration plate', thoughtProcess:'Legal identifier for insurance lookup.', goldAnswer:'RI‑SB 771', type:'field'},
  {id:'VB13', question:'Moving or stationary', thoughtProcess:'Branch to speed field; informs fault analysis.', goldAnswer:'Moving', type:'field'},
  {id:'VB12', question:'Speed before impact (km/h)', thoughtProcess:'Energy of collision & fault share.', goldAnswer:'40', type:'field'},
  {id:'VB14', question:'Airbags deployed?', thoughtProcess:'Relates to injury severity & repair cost.', goldAnswer:'Yes', type:'field'},
  {id:'VB15', question:'Driver full name', thoughtProcess:'Legal identity.', goldAnswer:'Sara Becker', type:'field'},
  {id:'VB16', question:'Driver age', thoughtProcess:'Demographic risk factor.', goldAnswer:'29', type:'field'},
  {id:'VB17', question:'Gender', thoughtProcess:'Optional statistical demographic.', goldAnswer:'Female', type:'field'},
  {id:'VB18', question:'Alcohol/substance suspected?', thoughtProcess:'Liability & police escalation.', goldAnswer:'No', type:'field'},
  {id:'VB18a', question:'Substance details', thoughtProcess:'Evidence chain if substance = Yes.', goldAnswer:'', type:'field'},
  {id:'VB19', question:'# Passengers', thoughtProcess:'Sets loop for passenger sub‑block.', goldAnswer:'1', type:'field'},
  /* Passenger Template (for loops) */
  {id:'VP_TEMPLATE', question:'Passenger details template', thoughtProcess:'Template for passenger information loop', goldAnswer:'', type:'template'},
  {id:'VPN', question:'Passenger name', thoughtProcess:'Medical follow‑up & liability.', goldAnswer:'', type:'field'},
  {id:'VPA', question:'Passenger age', thoughtProcess:'Injury risk profile.', goldAnswer:'', type:'field'},
  {id:'VPG', question:'Passenger gender', thoughtProcess:'Demographic stat.', goldAnswer:'', type:'field'},
  /* Passenger instances (examples) */
  {id:'VP1N', question:'Passenger 1 name', thoughtProcess:'Medical follow‑up & liability.', goldAnswer:'Lena Becker', type:'field'},
  {id:'VP1A', question:'Passenger 1 age', thoughtProcess:'Injury risk profile.', goldAnswer:'5', type:'field'},
  {id:'VP1G', question:'Passenger 1 gender', thoughtProcess:'Demographic stat.', goldAnswer:'Female', type:'field'},
  /* Injuries */
  {id:'Q20', question:'Any injuries?', thoughtProcess:'Branch to injury block.', goldAnswer:'Yes', type:'field'},
  {id:'Q20a1', question:'Injured person #1', thoughtProcess:'Victim registry.', goldAnswer:'Alex Müller', type:'field'},
  {id:'Q20b1', question:'Injury type #1', thoughtProcess:'Medical urgency & severity code.', goldAnswer:'Right‑side rib pain', type:'field'},
  {id:'Q20c1', question:'Medical help required?', thoughtProcess:'Resource dispatch.', goldAnswer:'No', type:'field'},
  {id:'Q20a2', question:'Injured person #2', thoughtProcess:'Victim registry.', goldAnswer:'Lena Becker', type:'field'},
  {id:'Q20b2', question:'Injury type #2', thoughtProcess:'Medical urgency & severity code.', goldAnswer:'Minor forehead cut', type:'field'},
  {id:'Q20c2', question:'Medical help required?', thoughtProcess:'Resource dispatch.', goldAnswer:'No', type:'field'},
  /* Damage & hazard */
  {id:'Q21', question:'Describe visible vehicle damage', thoughtProcess:'Repair cost estimation & forensic matching.', goldAnswer:'Dent and broken side windows on A; crumpled bonnet, broken left headlight on B.', type:'field'},
  {id:'Q22', question:'Hazardous fluid spilled?', thoughtProcess:'Environmental & fire risk trigger.', goldAnswer:'Yes', type:'field'},
  {id:'Q22a', question:'Fluid description & quantity', thoughtProcess:'Guides clean‑up crew.', goldAnswer:'Engine oil ≈ 1 L', type:'field'},
  /* Witnesses */
  {id:'Q23', question:'Any witnesses?', thoughtProcess:'Credible third‑party testimony flag.', goldAnswer:'Yes', type:'field'},
  {id:'Q23a1', question:'Witness 1 name', thoughtProcess:'Contact for statement.', goldAnswer:'Marko Jensen', type:'field'},
  {id:'Q23b1', question:'Witness 1 phone', thoughtProcess:'Reachability.', goldAnswer:'+49 171 5551234', type:'field'},
  {id:'Q23c1', question:'Witness 1 statement', thoughtProcess:'Evidence.', goldAnswer:'Pedestrian saw Vehicle B run flashing yellow.', type:'field'},
  {id:'Q23a2', question:'Witness 2 name', thoughtProcess:'Contact for statement.', goldAnswer:'Elena Torres', type:'field'},
  {id:'Q23b2', question:'Witness 2 phone', thoughtProcess:'Reachability.', goldAnswer:'+49 176 93744122', type:'field'},
  {id:'Q23c2', question:'Witness 2 statement', thoughtProcess:'Evidence.', goldAnswer:'Cyclist confirms heavy rain and simultaneous approach.', type:'field'},
  /* Police & comments */
  {id:'Q24', question:'Police present?', thoughtProcess:'Branch to officer info.', goldAnswer:'Yes', type:'field'},
  {id:'Q24a', question:'Officer name', thoughtProcess:'Accountability & follow‑up.', goldAnswer:'Kim Nguyen', type:'field'},
  {id:'Q24b', question:'Badge/ID', thoughtProcess:'Authentication.', goldAnswer:'4581', type:'field'},
  {id:'Q25', question:'Additional comments', thoughtProcess:'Free field for unstructured insights.', goldAnswer:'', type:'field'},
  {id:'END', question:'—', thoughtProcess:'Terminal node for export/logging.', goldAnswer:'—', type:'anchor'}
] AS row
CREATE (n:Field)
SET n.id = row.id,
    n.question = row.question,
    n.thoughtProcess = row.thoughtProcess,
    n.goldAnswer = row.goldAnswer,
    n.type = row.type;

/* ---------- Loop Controllers ---------- */
UNWIND [
  {id:'PASSENGER_LOOP', maxIterations:10, description:'Loop for collecting passenger data'},
  {id:'INJURY_LOOP', maxIterations:20, description:'Loop for collecting injury data'},
  {id:'WITNESS_LOOP', maxIterations:10, description:'Loop for collecting witness data'}
] AS loop
CREATE (l:LoopController)
SET l.id = loop.id,
    l.maxIterations = loop.maxIterations,
    l.description = loop.description;

/* ---------- Condition Nodes ---------- */
UNWIND [
  {id:'WEATHER_OTHER', expression:'weather == "Other"', description:'Check if weather is Other'},
  {id:'VEHICLE_MOVING', expression:'movement == "Moving"', description:'Check if vehicle is moving'},
  {id:'SUBSTANCE_SUSPECTED', expression:'substance == "Yes"', description:'Check if substance suspected'},
  {id:'HAS_PASSENGERS', expression:'passengerCount > 0', description:'Check if vehicle has passengers'},
  {id:'HAS_INJURIES', expression:'injuries == "Yes"', description:'Check if there are injuries'},
  {id:'FLUID_SPILLED', expression:'fluidSpilled == "Yes"', description:'Check if hazardous fluid spilled'},
  {id:'HAS_WITNESSES', expression:'witnesses == "Yes"', description:'Check if there are witnesses'},
  {id:'POLICE_PRESENT', expression:'police == "Yes"', description:'Check if police present'}
] AS cond
CREATE (c:Condition)
SET c.id = cond.id,
    c.expression = cond.expression,
    c.description = cond.description;

/* ---------- 2. RELATIONSHIPS (Enhanced DAG edges) ---------- */
/* Core flow relationships */
UNWIND [
  /* Core linear spine */
  ['START','Q1','NEXT'],['Q1','Q2','NEXT'],['Q2','Q3','NEXT'],['Q3','Q4','NEXT'],['Q4','Q5','NEXT'],
  ['Q6','Q7','NEXT'],['Q7','VA8','NEXT'],
  /* Vehicle A */
  ['VA8','VA9','NEXT'],['VA9','VA10','NEXT'],['VA10','VA11','NEXT'],['VA11','VA13','NEXT'],
  ['VA14','VA15','NEXT'],['VA15','VA16','NEXT'],['VA16','VA17','NEXT'],['VA17','VA18','NEXT'],
  ['VA19','VB8','NEXT'],
  /* Vehicle B */
  ['VB8','VB9','NEXT'],['VB9','VB10','NEXT'],['VB10','VB11','NEXT'],['VB11','VB13','NEXT'],
  ['VB14','VB15','NEXT'],['VB15','VB16','NEXT'],['VB16','VB17','NEXT'],['VB17','VB18','NEXT'],
  /* Damage & hazard */
  ['Q21','Q22','NEXT'],
  /* Police & comments */
  ['Q25','END','NEXT']
] AS rel
MATCH (a:Field {id:rel[0]}),(b:Field {id:rel[1]})
CREATE (a)-[:FLOWS_TO {type:rel[2]}]->(b);

/* Conditional branches */
UNWIND [
  ['Q5','WEATHER_OTHER'],['Q5a','Q6'],
  ['Q5','Q6'],  /* default path when weather != "Other" */
  ['VA13','VEHICLE_MOVING'],['VA12','VA14'],['VA13','VA14'], /* stationary path */
  ['VA18','SUBSTANCE_SUSPECTED'],['VA18a','VA19'],['VA18','VA19'], /* no substance path */
  ['VB13','VEHICLE_MOVING'],['VB12','VB14'],['VB13','VB14'], /* stationary path */
  ['VB18','SUBSTANCE_SUSPECTED'],['VB18a','VB19'],['VB18','VB19'], /* no substance path */
  ['VB19','HAS_PASSENGERS'],
  ['Q20','HAS_INJURIES'],
  ['Q22','FLUID_SPILLED'],['Q22a','Q23'],['Q22','Q23'], /* no fluid path */
  ['Q23','HAS_WITNESSES'],
  ['Q24','POLICE_PRESENT'],['Q24a','Q24b'],['Q24b','Q25'],['Q24','Q25'] /* no police path */
] AS rel
MATCH (a:Field {id:rel[0]})
MATCH (target)
WHERE (target:Condition AND target.id = rel[1]) OR (target:Field AND target.id = rel[1])
CREATE (a)-[:CONDITIONAL_FLOW]->(target);

/* Loop definitions */
MATCH (passengerLoop:LoopController {id:'PASSENGER_LOOP'})
MATCH (vb19:Field {id:'VB19'})
MATCH (vpTemplate:Field {id:'VP_TEMPLATE'})
MATCH (q20:Field {id:'Q20'})
CREATE (vb19)-[:ENTERS_LOOP]->(passengerLoop)
CREATE (passengerLoop)-[:LOOP_BODY]->(vpTemplate)
CREATE (passengerLoop)-[:LOOP_EXIT]->(q20);

/* Template instantiation (passenger loop body) */
MATCH (template:Field {id:'VP_TEMPLATE'})
MATCH (vpn:Field {id:'VPN'})
MATCH (vpa:Field {id:'VPA'})
MATCH (vpg:Field {id:'VPG'})
CREATE (template)-[:INSTANTIATES]->(vpn)
CREATE (vpn)-[:FLOWS_TO {type:'NEXT'}]->(vpa)
CREATE (vpa)-[:FLOWS_TO {type:'NEXT'}]->(vpg);

/* Injury loop */
MATCH (injuryLoop:LoopController {id:'INJURY_LOOP'})
MATCH (q20:Field {id:'Q20'})
MATCH (q20a1:Field {id:'Q20a1'})
MATCH (q21:Field {id:'Q21'})
CREATE (q20)-[:ENTERS_LOOP]->(injuryLoop)
CREATE (injuryLoop)-[:LOOP_BODY]->(q20a1)
CREATE (injuryLoop)-[:LOOP_EXIT]->(q21);

/* Witness loop */
MATCH (witnessLoop:LoopController {id:'WITNESS_LOOP'})
MATCH (q23:Field {id:'Q23'})
MATCH (q23a1:Field {id:'Q23a1'})
MATCH (q24:Field {id:'Q24'})
CREATE (q23)-[:ENTERS_LOOP]->(witnessLoop)
CREATE (witnessLoop)-[:LOOP_BODY]->(q23a1)
CREATE (witnessLoop)-[:LOOP_EXIT]->(q24);
