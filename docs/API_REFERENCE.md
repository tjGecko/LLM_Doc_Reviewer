# API Reference
## Developer Documentation for Auto-Reviewer

### 📡 Python API

Auto-Reviewer can be used as a Python library for programmatic access.

#### Basic Usage

```python
from auto_reviewer import ReviewEngine, ReviewConfig, AgentConfig
from pathlib import Path

# Create configuration
agents = [
    AgentConfig(
        name="Content Reviewer",
        tone="analytical, constructive",
        goals=["Evaluate content accuracy", "Check depth of analysis"],
        rubric={
            "criteria": ["Accuracy", "Depth", "Clarity"],
            "scale_min": 1,
            "scale_max": 5
        }
    )
]

config = ReviewConfig(
    agents=agents,
    llm_model="gpt-4o-mini",
    temperature=0.3,
    max_tokens=2000,
    embedder_model="sentence-transformers/all-MiniLM-L6-v2"
)

# Initialize engine
engine = ReviewEngine(config)

# Review document
results = engine.review_document(
    document_path="essay.txt",
    output_dir="output/"
)

# Process results
for result in results:
    print(f"Agent: {result.agent_name}")
    print(f"Score: {result.overall_score}")
    print(f"Comments: {result.comments}")
```

#### Configuration Classes

##### ReviewConfig
```python
class ReviewConfig:
    agents: List[AgentConfig]
    global_rubric: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 2000
    max_workers: int = 4
    embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
```

##### AgentConfig
```python
class AgentConfig:
    name: str
    role: str
    focus: str
    goal: str
    backstory: str
    criteria: List[Dict[str, Any]]
    specific_instructions: Optional[str] = None
```

##### ReviewResult
```python
class ReviewResult:
    agent_id: str
    agent_name: str
    paragraph_number: int
    overall_score: float
    confidence: float
    comments: str
    rewritten_text: Optional[str]
    review_timestamp: str
    scores: Dict[str, float]
```

---

### 🛠️ Command Line Interface

#### Basic Commands

```bash
# Review a document
auto-reviewer \
    --doc essay.txt \
    --agents agents.json \
    --out results/ \
    --rubric rubric.md

# With custom settings  
auto-reviewer \
    --doc essay.txt \
    --agents agents.json \
    --out results/ \
    --workers 6 \
    --temperature 0.1 \
    --model gpt-4o

# Dry run (show config without processing)
auto-reviewer \
    --doc essay.txt \
    --agents agents.json \
    --dry-run

# Debug mode
auto-reviewer \
    --doc essay.txt \
    --agents agents.json \
    --debug
```

#### CLI Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--doc` | Path | Document to review | Required |
| `--agents` | Path | Agent configuration file | Required |
| `--out` | Path | Output directory | `outputs` |
| `--rubric` | Path | Global rubric file | None |
| `--workers` | Integer | Number of concurrent workers | 4 |
| `--embedder` | String | Embedding model name | From env |
| `--temperature` | Float | LLM temperature (0.0-2.0) | From env |
| `--model` | String | LLM model name | From env |
| `--debug` | Flag | Enable debug logging | False |
| `--dry-run` | Flag | Show config without running | False |

---

### 🐳 Docker API

#### Running with Docker

```bash
# Basic usage
docker run --rm \
    -v "${PWD}/input:/app/input" \
    -v "${PWD}/output:/app/output" \
    auto-reviewer auto-reviewer \
    --doc /app/input/essay.txt \
    --agents /app/input/agents.json \
    --out /app/output/review

# With environment variables
docker run --rm \
    -e OPENAI_API_KEY=your_key \
    -e OPENAI_MODEL=gpt-4o \
    -e TEMPERATURE=0.3 \
    -v "${PWD}:/app/workspace" \
    auto-reviewer auto-reviewer \
    --doc /app/workspace/essay.txt \
    --agents /app/workspace/agents.json \
    --out /app/workspace/output
```

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for LLM service | `lm-studio` |
| `OPENAI_API_BASE` | Base URL for LLM API | `http://localhost:1234/v1` |
| `OPENAI_MODEL` | Model name | `openai/gpt-oss-20b` |
| `TEMPERATURE` | LLM temperature | `0.2` |
| `MAX_WORKERS` | Maximum concurrent workers | `4` |
| `MAX_TOKENS` | Maximum tokens per response | `2000` |
| `EMBED_MODEL` | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |

---

### 📂 File Formats

#### Agent Configuration (JSON)

```json
{
  "model": "${OPENAI_MODEL}",
  "max_agents": 7,
  "agents": [
    {
      "name": "Content Reviewer",
      "tone": "analytical, constructive, detailed",
      "goals": [
        "Evaluate content accuracy and depth",
        "Assess supporting evidence quality",
        "Check logical flow and coherence"
      ],
      "rubric": {
        "criteria": [
          "Content Accuracy",
          "Evidence Quality",
          "Logical Flow",
          "Depth of Analysis"
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

#### Output Format (JSON)

```json
{
  "agent_id": "content_reviewer_001",
  "agent_name": "Content Reviewer",
  "paragraph_number": 1,
  "overall_score": 3.8,
  "confidence": 0.85,
  "comments": "The paragraph demonstrates good understanding...",
  "rewritten_text": "Revised version with improvements...",
  "review_timestamp": "2024-03-15T14:30:00Z",
  "scores": {
    "Content Accuracy": 4.0,
    "Evidence Quality": 3.5,
    "Logical Flow": 4.0,
    "Depth of Analysis": 3.8
  }
}
```

#### Rubric Format (Markdown)

```markdown
# Essay Rubric

## Content Quality (40 points)
- **Excellent (36-40)**: Demonstrates deep understanding...
- **Good (32-35)**: Shows solid understanding...
- **Satisfactory (28-31)**: Basic understanding evident...
- **Needs Improvement (20-27)**: Limited understanding...
- **Poor (0-19)**: Little to no understanding...

## Organization (30 points)
- **Excellent (27-30)**: Clear, logical structure...
- **Good (24-26)**: Generally well organized...
- **Satisfactory (21-23)**: Basic organization present...
- **Needs Improvement (15-20)**: Poor organization...
- **Poor (0-14)**: No clear organization...
```

---

### 🔌 Integration Examples

#### LMS Integration (Canvas, Moodle, etc.)

```python
# Example: Canvas API integration
import requests
from auto_reviewer import ReviewEngine

def review_canvas_submissions(course_id, assignment_id):
    # Fetch submissions from Canvas
    submissions = canvas_api.get_submissions(course_id, assignment_id)
    
    for submission in submissions:
        # Download submission file
        essay_content = download_submission(submission['id'])
        
        # Review with Auto-Reviewer
        results = engine.review_document(essay_content)
        
        # Post feedback back to Canvas
        feedback = format_feedback_for_canvas(results)
        canvas_api.update_submission(
            course_id, 
            assignment_id, 
            submission['id'], 
            comment=feedback
        )
```

#### Google Classroom Integration

```python
# Example: Google Classroom integration
from googleapiclient.discovery import build
from auto_reviewer import ReviewEngine

def review_classroom_assignments(course_id, coursework_id):
    service = build('classroom', 'v1', credentials=creds)
    
    # Get submissions
    submissions = service.courses().courseWork().studentSubmissions().list(
        courseId=course_id,
        courseWorkId=coursework_id
    ).execute()
    
    for submission in submissions['studentSubmissions']:
        # Process each submission
        results = process_submission_with_auto_reviewer(submission)
        
        # Return private comment with feedback
        service.courses().courseWork().studentSubmissions().return_(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission['id'],
            body={
                'draftGrade': calculate_grade(results),
                'assignedGrade': calculate_grade(results)
            }
        ).execute()
```

#### Batch Processing Script

```python
# Example: Batch process multiple essays
import os
from pathlib import Path
from auto_reviewer import ReviewEngine, ReviewConfig

def batch_review_essays(essays_dir, output_dir, agents_config):
    engine = ReviewEngine(ReviewConfig.from_file(agents_config))
    
    for essay_file in Path(essays_dir).glob('*.txt'):
        print(f"Processing {essay_file.name}...")
        
        try:
            results = engine.review_document(
                essay_file,
                output_dir / essay_file.stem
            )
            
            # Generate summary report
            generate_summary_report(results, output_dir / f"{essay_file.stem}_summary.md")
            
        except Exception as e:
            print(f"Error processing {essay_file.name}: {e}")

# Usage
batch_review_essays(
    essays_dir="./student_essays",
    output_dir="./reviews", 
    agents_config="./class_agents.json"
)
```

---

### 📊 Output Processing

#### Extracting Scores for Gradebooks

```python
def extract_scores_to_csv(review_results, output_file):
    import csv
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['student_name', 'overall_score'] + \
                    list(review_results[0].scores.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in review_results:
            row = {
                'student_name': result.student_name,
                'overall_score': result.overall_score,
                **result.scores
            }
            writer.writerow(row)
```

#### Generating Progress Reports

```python
def generate_progress_report(student_reviews_over_time):
    """Generate a progress report showing improvement over time."""
    
    progress_data = []
    for timestamp, results in student_reviews_over_time:
        avg_score = sum(r.overall_score for r in results) / len(results)
        
        # Analyze specific criteria
        criteria_scores = {}
        for criterion in results[0].scores.keys():
            criterion_scores = [r.scores[criterion] for r in results]
            criteria_scores[criterion] = sum(criterion_scores) / len(criterion_scores)
        
        progress_data.append({
            'timestamp': timestamp,
            'overall_score': avg_score,
            'criteria_scores': criteria_scores,
            'improvement_areas': identify_improvement_areas(criteria_scores)
        })
    
    return progress_data
```

---

### 🔒 Error Handling

#### Common Exceptions

```python
from auto_reviewer.exceptions import (
    DocumentLoadError,
    AgentConfigError, 
    LLMConnectionError,
    ReviewProcessingError
)

try:
    results = engine.review_document("essay.txt", "output/")
except DocumentLoadError as e:
    print(f"Could not load document: {e}")
except AgentConfigError as e:
    print(f"Agent configuration error: {e}")
except LLMConnectionError as e:
    print(f"LLM service unavailable: {e}")
except ReviewProcessingError as e:
    print(f"Review processing failed: {e}")
```

#### Retry Logic

```python
import time
from typing import Optional

def review_with_retry(
    engine: ReviewEngine,
    document_path: str,
    output_dir: str,
    max_retries: int = 3,
    delay: float = 1.0
) -> Optional[List[ReviewResult]]:
    
    for attempt in range(max_retries):
        try:
            return engine.review_document(document_path, output_dir)
        except LLMConnectionError:
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1} after {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print("Max retries exceeded")
                return None
    
    return None
```

---

### ⚡ Performance Optimization

#### Async Processing

```python
import asyncio
from auto_reviewer import AsyncReviewEngine

async def review_multiple_essays(essay_paths, agents_config):
    engine = AsyncReviewEngine(agents_config)
    
    # Process multiple essays concurrently
    tasks = [
        engine.review_document(essay_path, f"output/{essay_path.stem}")
        for essay_path in essay_paths
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results and exceptions
    successful_reviews = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Failed to process {essay_paths[i]}: {result}")
        else:
            successful_reviews.append(result)
    
    return successful_reviews
```

#### Memory Management

```python
def review_large_batch(essay_paths, agents_config, batch_size=5):
    """Process essays in batches to manage memory usage."""
    
    all_results = []
    
    for i in range(0, len(essay_paths), batch_size):
        batch = essay_paths[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}...")
        
        # Process batch
        batch_results = []
        engine = ReviewEngine(agents_config)  # Fresh engine for each batch
        
        for essay_path in batch:
            results = engine.review_document(essay_path, f"output/{essay_path.stem}")
            batch_results.extend(results)
        
        all_results.extend(batch_results)
        
        # Clear memory between batches
        del engine
        import gc
        gc.collect()
    
    return all_results
```

---

### 🧪 Testing

#### Unit Tests

```python
import unittest
from auto_reviewer import ReviewEngine, ReviewConfig, AgentConfig

class TestAutoReviewer(unittest.TestCase):
    
    def setUp(self):
        self.test_config = ReviewConfig(
            agents=[
                AgentConfig(
                    name="Test Agent",
                    tone="neutral",
                    goals=["Test goal"],
                    rubric={"criteria": ["Test"], "scale_min": 1, "scale_max": 5}
                )
            ]
        )
        
    def test_document_review(self):
        engine = ReviewEngine(self.test_config)
        
        # Mock document
        with open("test_essay.txt", "w") as f:
            f.write("This is a test essay with multiple paragraphs.")
        
        results = engine.review_document("test_essay.txt", "test_output/")
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        self.assertIsInstance(results[0].overall_score, float)
```

#### Integration Tests

```python
def test_end_to_end_review():
    """Test complete review workflow."""
    
    # Setup test data
    create_test_essay("test_files/sample_essay.txt")
    create_test_agents("test_files/agents.json")
    create_test_rubric("test_files/rubric.md")
    
    # Run review
    results = run_review(
        doc="test_files/sample_essay.txt",
        agents="test_files/agents.json",
        rubric="test_files/rubric.md",
        output="test_output/"
    )
    
    # Verify outputs
    assert_output_files_exist("test_output/")
    assert_scores_in_valid_range(results)
    assert_comments_not_empty(results)
```

---

This API documentation provides comprehensive coverage for developers wanting to integrate or extend Auto-Reviewer. For additional examples and use cases, check the `examples/` directory in the repository.