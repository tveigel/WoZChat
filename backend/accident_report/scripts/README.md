# Scripts

This directory contains analysis, debugging, and utility scripts for the accident report bot system.

## 🛠️ Available Scripts

### Analysis Scripts
- **`analyze_followups.py`** - Analyzes followup question patterns and effectiveness
  - Examines conversation flows
  - Identifies common user response patterns
  - Suggests improvements for question sequences

### Debugging Utilities
- **`debug_validator.py`** - Debug and test the form validator functionality
  - Test validation rules in isolation
  - Debug text normalization issues
  - Validate specific input scenarios

### Database Scripts
- **`create_tahr_graph.cypher`** - Neo4j Cypher script for creating graph visualizations
  - Creates relationship graphs of accident data
  - Useful for analyzing complex accident scenarios
  - Generates visual representations of data connections

## 🏃 Running Scripts

### Analysis Scripts
```bash
# Analyze followup patterns
python backend/accident_report/scripts/analyze_followups.py

# With specific data file
python backend/accident_report/scripts/analyze_followups.py --data ../data/completed_form.json
```

### Debugging Scripts
```bash
# Debug validator functionality
python backend/accident_report/scripts/debug_validator.py

# Test specific validation rules
python backend/accident_report/scripts/debug_validator.py --test-input "sample text"
```

### Database Scripts
```bash
# Run Neo4j graph creation (requires Neo4j running)
cypher-shell -u neo4j -p your_password < backend/accident_report/scripts/create_tahr_graph.cypher

# Or load in Neo4j browser
# Copy content of create_tahr_graph.cypher and paste in Neo4j browser
```

## 📊 Output and Results

### Analysis Output
- **Followup Analysis**: Generates reports on question effectiveness
- **Pattern Recognition**: Identifies common user behavior patterns
- **Recommendations**: Suggests improvements for bot conversation flow

### Debug Output
- **Validation Reports**: Shows which validation rules pass/fail
- **Text Processing**: Demonstrates text normalization and cleanup
- **Error Analysis**: Helps identify edge cases and validation issues

### Graph Visualization
- **Relationship Maps**: Visual connections between accident elements
- **Data Flow**: Shows how information relates within accident reports
- **Pattern Discovery**: Reveals hidden relationships in accident data

## 🔧 Dependencies

### Python Scripts
- Require the main accident_report modules to be importable
- May need additional analysis libraries (pandas, matplotlib)
- Use the same environment as the main application

### Database Scripts
- Require Neo4j to be installed and running
- Need appropriate database permissions
- May require specific graph database setup

## 🐛 Troubleshooting

### Import Issues
If scripts can't import modules, run from the project root:
```bash
cd /path/to/WebWOz
python backend/accident_report/scripts/script_name.py
```

### Database Connection Issues
For Neo4j scripts:
1. Ensure Neo4j is running: `sudo neo4j start`
2. Check credentials in the script
3. Verify database permissions
