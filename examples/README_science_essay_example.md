# Science Essay Review Example: Jumping Spider Care

This example demonstrates how to use the auto-reviewer system to evaluate a high school student's science essay about caring for jumping spiders in a terrarium.

## Files Included

### 1. `student_essay_jumping_spiders.txt`
A realistic first draft of a high school student's three-paragraph essay about jumping spider care. This essay intentionally includes:
- **Strengths**: Good basic information, logical organization, practical advice
- **Areas for improvement**: Informal language, lack of specific measurements, missing scientific terminology, limited depth of analysis

### 2. `science_essay_rubric.md`
A comprehensive rubric designed for evaluating high school science essays, including:
- Content Knowledge & Accuracy (25 points)
- Organization & Structure (20 points) 
- Scientific Writing Style (15 points)
- Evidence & Examples (15 points)
- Grammar & Mechanics (10 points)
- Critical Thinking & Analysis (15 points)

### 3. `science_essay_agents.json`
Four specialized reviewing agents configured to evaluate different aspects of the essay:
- **Science Content Reviewer**: Focuses on biological accuracy and scientific terminology
- **Writing Style & Organization Reviewer**: Evaluates academic writing conventions and structure
- **Evidence & Detail Reviewer**: Assesses use of specific examples and supporting evidence
- **Critical Thinking & Analysis Reviewer**: Looks for analytical thinking beyond description

## How to Run This Example

### Using Docker (Recommended)

```bash
# Build the container if you haven't already
docker build -t auto-reviewer .

# Run the review
docker run --rm -v "${PWD}/examples:/app/examples" -v "${PWD}/output:/app/output" \
    auto-reviewer auto-reviewer \
    --doc /app/examples/student_essay_jumping_spiders.txt \
    --agents /app/examples/science_essay_agents.json \
    --rubric /app/examples/science_essay_rubric.md \
    --out /app/output/spider_essay_review \
    --workers 4 \
    --temperature 0.3
```

### Using Python Directly

```bash
# Make sure you're in the project root
cd /path/to/auto_reviewer

# Run the review
python -m auto_reviewer.cli \
    --doc examples/student_essay_jumping_spiders.txt \
    --agents examples/science_essay_agents.json \
    --rubric examples/science_essay_rubric.md \
    --out outputs/spider_essay_review \
    --workers 4 \
    --temperature 0.3
```

## Expected Output

The system will generate several output files:

### Individual Agent Reviews
- `agent_0_Science_Content_Reviewer.json` - Scientific accuracy assessment
- `agent_1_Writing_Style_Organization_Reviewer.json` - Writing quality evaluation  
- `agent_2_Evidence_Detail_Reviewer.json` - Evidence and specificity analysis
- `agent_3_Critical_Thinking_Analysis_Reviewer.json` - Analytical thinking assessment

### Consolidated Reports
- `run.json` - Complete review data with all agent responses
- `consolidated.json` - Summary statistics and recommendations
- `review_report.md` - Human-readable comprehensive report

### Agent-Specific Reports
- `Science_Content_Reviewer.md` - Biology teacher's detailed feedback
- `Writing_Style_Organization_Reviewer.md` - English teacher's writing feedback
- `Evidence_Detail_Reviewer.md` - Evidence specialist's suggestions
- `Critical_Thinking_Analysis_Reviewer.md` - Analysis specialist's evaluation

## What the Review Will Likely Find

Based on the essay content, expect the agents to identify:

### Strengths
- Clear three-paragraph structure
- Practical, actionable care instructions
- Basic understanding of jumping spider biology
- Logical organization from setup to feeding to conclusion

### Areas for Improvement
- **Language**: Informal phrases like "really cool," "tons of space," "super cold"
- **Specificity**: Vague measurements ("5-10 gallons," "room temperature")
- **Scientific terminology**: Missing terms like "substrate," "humidity," "predatory behavior"
- **Evidence**: Lack of specific data, sources, or quantitative details
- **Analysis**: Mostly descriptive rather than analytical content
- **Safety**: Missing important safety considerations

### Suggested Improvements
- Replace informal language with scientific terminology
- Add specific measurements and data points
- Include more detailed explanations of biological processes
- Strengthen transitions between paragraphs
- Add analytical content about why certain care practices are important

## Customizing This Example

### Modifying the Agents
Edit `science_essay_agents.json` to:
- Adjust criteria weights for different focus areas
- Add or remove evaluation criteria
- Modify agent expertise and backgrounds
- Change specific instructions for different essay types

### Adapting the Rubric
Modify `science_essay_rubric.md` to:
- Adjust point distributions for different assignment types
- Add subject-specific criteria
- Change grade level expectations
- Include assignment-specific requirements

### Creating New Test Essays
Use this essay as a template to create:
- Different science topics (chemistry, physics, environmental science)
- Various grade levels (middle school, college prep, AP level)
- Different assignment types (lab reports, research papers, case studies)
- Multiple draft versions showing improvement over time

## Expected Review Time

- **Processing time**: 2-5 minutes depending on system resources
- **Agent reviews**: Each agent typically generates 200-500 words of feedback
- **Total output**: 15-20 files with comprehensive analysis and recommendations

This example provides a realistic baseline for testing the auto-reviewer system's ability to provide constructive, detailed feedback on student scientific writing.