# Advanced Configuration Guide
## For Teachers, Administrators, and Power Users

### 🎓 Creating Custom Agent Configurations

The power of Auto-Reviewer lies in its customizable AI agents. You can create specialized reviewers for any subject or assignment type.

#### Agent Configuration Structure

Each agent configuration file (`agents.json`) has this structure:

```json
{
  "model": "${OPENAI_MODEL}",
  "max_agents": 7,
  "agents": [
    {
      "name": "Agent Name",
      "tone": "professional, helpful, specific",
      "goals": [
        "Primary objective",
        "Secondary objective", 
        "Additional focus area"
      ],
      "rubric": {
        "criteria": [
          "Criterion 1",
          "Criterion 2",
          "Criterion 3"
        ],
        "scale_min": 1,
        "scale_max": 5
      },
      "kb_refs": [],
      "retrieval": {
        "top_k": 4,
        "use_neighbors": true,
        "similarity_threshold": 0.7
      }
    }
  ]
}
```

#### Agent Properties Explained

**name**: What the agent is called in reports
**tone**: How the agent communicates (professional, encouraging, direct, etc.)
**goals**: 2-4 specific objectives the agent focuses on
**rubric.criteria**: What aspects the agent evaluates (3-5 items recommended)
**rubric.scale_min/max**: Scoring range (typically 1-5 or 1-10)
**retrieval.top_k**: How many document chunks to analyze (3-6 recommended)
**retrieval.similarity_threshold**: How closely related content must be (0.5-0.8)

---

### 📚 Subject-Specific Agent Templates

#### History Essay Agents
```json
{
  "model": "${OPENAI_MODEL}",
  "max_agents": 7,
  "agents": [
    {
      "name": "Historical Accuracy Specialist",
      "tone": "scholarly, precise, fact-focused",
      "goals": [
        "Verify historical facts and dates",
        "Check for anachronisms and misconceptions",
        "Assess understanding of historical context",
        "Evaluate use of primary vs secondary sources"
      ],
      "rubric": {
        "criteria": [
          "Factual Accuracy",
          "Historical Context",
          "Source Quality",
          "Chronological Understanding"
        ],
        "scale_min": 1,
        "scale_max": 5
      }
    },
    {
      "name": "Argument Structure Analyst", 
      "tone": "logical, constructive, analytical",
      "goals": [
        "Evaluate thesis statement clarity",
        "Assess argument development and logic",
        "Check for counterargument consideration",
        "Review conclusion effectiveness"
      ],
      "rubric": {
        "criteria": [
          "Thesis Clarity",
          "Argument Development",
          "Evidence Integration",
          "Logical Flow"
        ],
        "scale_min": 1,
        "scale_max": 5
      }
    }
  ]
}
```

#### Mathematics Problem-Solving Agents
```json
{
  "name": "Mathematical Reasoning Expert",
  "tone": "precise, step-by-step, encouraging",
  "goals": [
    "Verify mathematical accuracy of calculations",
    "Assess problem-solving approach and strategy",
    "Evaluate explanation of mathematical concepts",
    "Check for proper use of mathematical notation"
  ],
  "rubric": {
    "criteria": [
      "Calculation Accuracy",
      "Problem-Solving Strategy", 
      "Concept Explanation",
      "Mathematical Notation"
    ],
    "scale_min": 1,
    "scale_max": 10
  }
}
```

#### English Literature Agents
```json
{
  "name": "Literary Analysis Specialist",
  "tone": "insightful, interpretive, culturally aware",
  "goals": [
    "Evaluate depth of textual analysis",
    "Assess understanding of literary devices",
    "Check for supported interpretations with evidence",
    "Review understanding of historical/cultural context"
  ],
  "rubric": {
    "criteria": [
      "Textual Analysis Depth",
      "Literary Device Recognition",
      "Evidence-Based Interpretation",
      "Contextual Understanding"
    ],
    "scale_min": 1,
    "scale_max": 5
  }
}
```

---

### 📐 Custom Rubric Development

#### Rubric Design Principles

1. **Clear Criteria**: Each criterion should be specific and measurable
2. **Appropriate Scale**: Match scale to assignment complexity
3. **Balanced Weighting**: Distribute points according to importance
4. **Grade-Level Appropriate**: Match expectations to student level

#### Sample Rubric Templates

**Elementary Level (Grades 3-5):**
```markdown
# Elementary Writing Rubric

## Ideas and Content (25 points)
- **4-5**: Clear main idea with good details
- **2-3**: Main idea present but needs more details  
- **1**: Unclear main idea, few details

## Organization (20 points)
- **4-5**: Clear beginning, middle, end
- **2-3**: Some organization present
- **1**: No clear organization

## Word Choice (15 points)
- **4-5**: Uses interesting, appropriate words
- **2-3**: Uses some good word choices
- **1**: Uses simple, basic words only
```

**High School Level (Grades 9-12):**
```markdown
# High School Academic Essay Rubric

## Thesis and Argument (30 points)
- **Excellent (26-30)**: Clear, sophisticated thesis with compelling argument
- **Good (21-25)**: Clear thesis with solid argument development
- **Satisfactory (16-20)**: Basic thesis with adequate argument
- **Needs Improvement (11-15)**: Weak or unclear thesis
- **Poor (0-10)**: No clear thesis or argument

## Evidence and Analysis (25 points)
- **Excellent (23-25)**: Strong evidence with sophisticated analysis
- **Good (18-22)**: Good evidence with solid analysis
- **Satisfactory (14-17)**: Adequate evidence with basic analysis
- **Needs Improvement (10-13)**: Weak evidence or analysis
- **Poor (0-9)**: Little to no evidence or analysis
```

#### Adaptive Rubrics by Assignment Type

**Research Papers:**
- Source Quality (20%)
- Research Integration (20%) 
- Original Analysis (25%)
- Academic Writing Style (20%)
- Citations and Bibliography (15%)

**Creative Writing:**
- Creativity and Originality (25%)
- Character Development (20%)
- Plot Structure (20%)
- Use of Literary Devices (15%)
- Grammar and Style (20%)

**Lab Reports:**
- Scientific Method Application (25%)
- Data Accuracy and Presentation (25%)
- Analysis and Interpretation (25%) 
- Scientific Writing Style (15%)
- Safety and Ethics (10%)

---

### 🔧 Performance Tuning

#### Processing Speed Optimization

**For Faster Processing:**
```bash
# Increase workers (if you have good hardware)
MAX_WORKERS=6

# Use lower temperature for consistency
TEMPERATURE=0.2

# Reduce retrieval chunks
"top_k": 3
```

**For Better Quality:**
```bash
# Reduce workers for more thorough analysis
MAX_WORKERS=2

# Higher temperature for more creative feedback
TEMPERATURE=0.5

# More retrieval chunks for context
"top_k": 6
```

#### Memory Management

**High-Memory Systems (16GB+ RAM):**
```bash
MAX_WORKERS=8
EMBED_BATCH_SIZE=64
```

**Low-Memory Systems (8GB RAM):**
```bash
MAX_WORKERS=2
EMBED_BATCH_SIZE=16
MAX_TOKENS=1000
```

#### AI Model Selection

**For Speed:**
- LM Studio: `microsoft/Phi-3.5-mini-instruct-GGUF`
- OpenAI: `gpt-4o-mini`

**For Quality:**
- LM Studio: `mistralai/Mistral-7B-Instruct-v0.3-GGUF`
- OpenAI: `gpt-4o`

**For Balance:**
- LM Studio: `microsoft/Phi-3-medium-4k-instruct-GGUF`
- OpenAI: `gpt-4o-mini`

---

### 🏫 Classroom Integration

#### Batch Processing Multiple Essays

Create a script to process multiple essays:

```bash
#!/bin/bash
# Process all essays in a folder

for essay in essays/*.txt; do
  echo "Processing $essay..."
  
  docker run --rm \
    -v "${PWD}:/app/workspace" \
    -v "${PWD}/output:/app/output" \
    auto-reviewer auto-reviewer \
    --doc "/app/workspace/$essay" \
    --agents /app/workspace/class_agents.json \
    --rubric /app/workspace/class_rubric.md \
    --out "/app/output/$(basename $essay .txt)_review"
done
```

#### Grade Book Integration

Auto-Reviewer outputs can be imported into most gradebook systems:

1. **Export scores to CSV:**
   - Use the `consolidated.json` output
   - Extract numeric scores for each criterion
   - Format as CSV for gradebook import

2. **Student Feedback Distribution:**
   - Individual `review_report.md` files for each student
   - Automated email distribution via school systems
   - LMS integration through file upload

#### Peer Review Facilitation

Use Auto-Reviewer to train students in giving feedback:

1. **Model Review Process:**
   - Show students AI feedback on sample essays
   - Discuss what makes good feedback
   - Compare AI and human perspectives

2. **Peer Review Training:**
   - Students review the same essay as AI
   - Compare student feedback to AI feedback
   - Identify gaps and improvement areas

3. **Guided Peer Review:**
   - Students use AI feedback as a starting point
   - Add personal observations and suggestions
   - Develop critical reading skills

---

### 📊 Analytics and Reporting

#### Tracking Student Progress

Create custom reports by modifying the output processing:

```python
# Example: Track improvement over time
def analyze_student_progress(student_reviews):
    scores_over_time = []
    for review in student_reviews:
        overall_score = review['overall_rating']
        timestamp = review['run_timestamp']
        scores_over_time.append((timestamp, overall_score))
    
    return calculate_trend(scores_over_time)
```

#### Class-Level Analytics

```python
# Example: Class performance summary
def class_summary(all_reviews):
    criteria_scores = defaultdict(list)
    
    for review in all_reviews:
        for criterion, score in review['consolidated_scores'].items():
            criteria_scores[criterion].append(score)
    
    summary = {}
    for criterion, scores in criteria_scores.items():
        summary[criterion] = {
            'mean': statistics.mean(scores),
            'std_dev': statistics.stdev(scores),
            'improvement_needed': sum(1 for s in scores if s < 3.0)
        }
    
    return summary
```

---

### 🔐 Privacy and Security

#### Data Privacy Considerations

**Local Processing (LM Studio):**
- ✅ Student essays never leave your computer
- ✅ No internet connection required
- ✅ Complete privacy control
- ✅ FERPA compliant when used locally

**Cloud Processing (OpenAI):**
- ⚠️ Essays sent to external servers
- ⚠️ Review privacy policies carefully
- ⚠️ Consider data residency requirements
- ⚠️ May require additional privacy agreements

#### Recommended Privacy Setup

1. **Use LM Studio for sensitive content**
2. **Anonymize essays before processing** (remove names, school identifiers)
3. **Regular cleanup of output folders**
4. **Secure storage of configuration files**

#### GDPR/FERPA Compliance

**For Educational Use:**
- Document your data processing procedures
- Ensure student/parent consent where required
- Implement data retention policies
- Provide clear opt-out mechanisms
- Regular privacy impact assessments

---

### 🚀 Advanced Deployment

#### Server Deployment

For school-wide deployment, consider:

1. **Centralized Docker Setup:**
   ```bash
   # Run as a service with persistent storage
   docker run -d \
     --name auto-reviewer-server \
     -v /school/essays:/app/essays \
     -v /school/output:/app/output \
     -p 8080:8080 \
     auto-reviewer
   ```

2. **Web Interface Development:**
   - Flask/Django web frontend
   - File upload interface
   - Results dashboard
   - User authentication

3. **API Integration:**
   - RESTful API for LMS integration
   - Webhook support for automated processing
   - Batch processing queues

#### Monitoring and Maintenance

```bash
# Monitor system resources
docker stats auto-reviewer

# Check logs
docker logs auto-reviewer

# Update and restart
docker pull auto-reviewer:latest
docker restart auto-reviewer
```

---

## 🎯 Next Steps

With these advanced configurations, you can:

1. **Customize for any subject area**
2. **Scale for classroom or school use**  
3. **Integrate with existing educational technology**
4. **Maintain student privacy and security**
5. **Track learning progress over time**

**Remember**: Start simple with the basic configurations, then gradually add complexity as you become comfortable with the system!