# Data

This directory contains sample data, completed forms, and visualizations for the accident report bot system.

## 📁 Contents

### Sample Forms
- **`completed_form.json`** - Example of a completed accident report form
- Shows the expected data structure and format for collected information

### Visualizations
- **`graph.png`** - System architecture or workflow visualization
- **`form_workflow_graph.png`** - Visual representation of the form workflow process

## 📊 Data Structure

### Completed Form Format
The `completed_form.json` demonstrates the expected structure for accident report data:

```json
{
  "date_of_accident": "2024-01-15",
  "time_of_accident": "14:30",
  "location": "Main Street intersection",
  "description": "Vehicle collision at traffic light",
  "injuries": "Minor bruising on left arm",
  "witnesses": "John Smith (witness contact info)"
}
```

## 🎯 Usage

### For Testing
- Use sample data files to test form validation
- Reference completed forms to verify data collection accuracy
- Visualizations help understand system flow

### For Development
- Copy sample data structure for new form templates
- Use as reference for expected input/output formats
- Validate against these examples during development

### For Analysis
- Analyze completed forms to improve question flow
- Use visualizations to identify bottlenecks or issues
- Track form completion patterns and success rates

## 🔧 Utilities

To generate new sample data or update visualizations:
1. Use scripts in `../scripts/` for data analysis
2. Run bot tests to generate new sample forms
3. Update visualizations when workflow changes
