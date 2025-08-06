/* ───────────── 0. Wipe any old data  ───────────── */
MATCH (n) DETACH DELETE n;

/* ───────────── 1. Constraints (idempotent) ───────────── */
CREATE CONSTRAINT question_uid  IF NOT EXISTS FOR (q:Question)      REQUIRE q.uid IS UNIQUE;
CREATE CONSTRAINT block_uid     IF NOT EXISTS FOR (b:Block)         REQUIRE b.uid IS UNIQUE;
CREATE CONSTRAINT loop_uid      IF NOT EXISTS FOR (l:LoopController)REQUIRE l.uid IS UNIQUE;
CREATE CONSTRAINT anchor_uid    IF NOT EXISTS FOR (a:Anchor)        REQUIRE a.uid IS UNIQUE;

/* ───────────── 2. Nodes  +  Relationships in ONE statement ───────────── */
CREATE
/* Anchors */
  (start:Anchor  {uid:'START', display:'Start', kind:'start'}),
  (finish:Anchor {uid:'END',   display:'End',   kind:'end'}),

/* Top‑level questions Q1–Q8 */
  (q1:Question {uid:'Q1',  display:'Date of accident',          fieldType:'date',     required:true}),
  (q2:Question {uid:'Q2',  display:'Time of accident',          fieldType:'time',     required:true}),
  (q3:Question {uid:'Q3',  display:'Location of accident',      fieldType:'string',   required:true}),
  (q4:Question {uid:'Q4',  display:'Road surface condition',    fieldType:'enum',     required:true}),
  (q5:Question {uid:'Q5',  display:'Weather',                   fieldType:'enum',     required:true}),
  (q6:Question {uid:'Q6',  display:'Lighting',                  fieldType:'enum',     required:true}),
  (q7:Question {uid:'Q7',  display:'Road type & controls',      fieldType:'mixed',    required:true}),
  (q8:Question {uid:'Q8',  display:'Number of vehicles',        fieldType:'integer',  required:true}),

/* Vehicle repeat‑block (Q8.1‑8.5) */
  (vbStart:Block {uid:'B_VEHICLE', display:'Vehicle block'}),
  (q81:Question {uid:'Q8.1', display:'Vehicle type / make / model', fieldType:'string',  required:true}),
  (q82:Question {uid:'Q8.2', display:'Licence plate',               fieldType:'string',  required:true}),
  (q83:Question {uid:'Q8.3', display:'Pre‑crash manoeuvre',         fieldType:'enum',    required:true}),
  (q84:Question {uid:'Q8.4', display:'Approx. speed (km/h)',        fieldType:'integer', required:false}),
  (q85:Question {uid:'Q8.5', display:'Damage description',          fieldType:'text',    required:false}),
  (vLoop:LoopController {uid:'LOOP_VEHICLE', display:'More vehicles?', loopType:'repeat-until-no'}),

/* Q9–Q10 */
  (q9: Question {uid:'Q9',  display:'Accident narrative',       fieldType:'longtext', required:true}),
  (q10:Question {uid:'Q10', display:'Contributing factors',     fieldType:'enum',     required:false}),

/* Injury branch (Q11) with repeat table rows */
  (q11:Question {uid:'Q11', display:'Any injuries?',            fieldType:'boolean',  required:true}),
  (ibStart:Block {uid:'B_INJURY', display:'Injury row'}),
  (q111:Question {uid:'Q11.1', display:'Role',                  fieldType:'enum',     required:true}),
  (q112:Question {uid:'Q11.2', display:'Vehicle #',             fieldType:'integer',  required:false}),
  (q113:Question {uid:'Q11.3', display:'Severity',              fieldType:'enum',     required:true}),
  (q114:Question {uid:'Q11.4', display:'Injury description',    fieldType:'text',     required:true}),
  (iLoop:LoopController {uid:'LOOP_INJURY', display:'More injuries?', loopType:'repeat-until-no'}),

/* Q12–Q15 with simple YES/NO follow‑ups */
  (q12:Question {uid:'Q12',  display:'Any fatalities?',                  fieldType:'boolean', required:true}),
  (q12a:Question{uid:'Q12A', display:'Describe fatalities',              fieldType:'text',    required:true}),
  (q13:Question {uid:'Q13',  display:'Property damage?',                 fieldType:'boolean', required:true}),
  (q13a:Question{uid:'Q13A', display:'Describe property damage',         fieldType:'text',    required:true}),
  (q14:Question {uid:'Q14',  display:'Witnesses present?',               fieldType:'boolean', required:true}),
  (q14a:Question{uid:'Q14A', display:'Witness names / contacts',         fieldType:'text',    required:true}),
  (q15:Question {uid:'Q15',  display:'Police report filed?',             fieldType:'boolean', required:true}),
  (q15a:Question{uid:'Q15A', display:'Report # and officer',             fieldType:'string',  required:true}),

/* Q16 */
  (q16:Question {uid:'Q16',  display:'Additional comments',              fieldType:'longtext',required:false}),

/* ─────────── Spine: START → Q1 … Q8 → Vehicle block → … ─────────── */
  (start)-[:NEXT]->(q1)-[:NEXT]->(q2)-[:NEXT]->(q3)-[:NEXT]->(q4)-[:NEXT]->(q5)
        -[:NEXT]->(q6)-[:NEXT]->(q7)-[:NEXT]->(q8)-[:NEXT]->(vbStart),

/* Vehicle sub‑block sequence */
  (vbStart)-[:NEXT]->(q81)-[:NEXT]->(q82)-[:NEXT]->(q83)-[:NEXT]->(q84)-[:NEXT]->(q85)
          -[:NEXT]->(vLoop),
  (vLoop)-[:LOOP]->(vbStart),          /* add another vehicle */
  (vLoop)-[:NEXT]->(q9),               /* exit loop → continue */

/* Continue spine Q9–Q10 */
  (q9)-[:NEXT]->(q10)-[:NEXT]->(q11),

/* Injury branch */
  (q11)-[:CONDITION_YES]->(ibStart),
  (ibStart)-[:NEXT]->(q111)-[:NEXT]->(q112)-[:NEXT]->(q113)-[:NEXT]->(q114)
          -[:NEXT]->(iLoop),
  (iLoop)-[:LOOP]->(ibStart),
  (iLoop)-[:NEXT]->(q12),
  (q11)-[:CONDITION_NO]->(q12),

/* Fatalities branch */
  (q12)-[:CONDITION_YES]->(q12a)-[:NEXT]->(q13),
  (q12)-[:CONDITION_NO]->(q13),

/* Property‑damage branch */
  (q13)-[:CONDITION_YES]->(q13a)-[:NEXT]->(q14),
  (q13)-[:CONDITION_NO]->(q14),

/* Witness branch */
  (q14)-[:CONDITION_YES]->(q14a)-[:NEXT]->(q15),
  (q14)-[:CONDITION_NO]->(q15),


/* Finish */
  (q16)-[:NEXT]->(finish);
