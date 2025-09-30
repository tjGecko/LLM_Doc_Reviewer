# Auto-Reviewer User Guide
## Get AI Feedback on Your Essays - Made Simple! 📝✨

### What is Auto-Reviewer?

Auto-Reviewer is like having **4 different teachers** review your essay at the same time! Each AI teacher looks at different things:

- 🔬 **Science Teacher**: Checks if your science facts are correct
- ✍️ **English Teacher**: Looks at your writing style and organization  
- 📊 **Evidence Expert**: Makes sure you have good examples and details
- 🤔 **Critical Thinking Coach**: Helps you think deeper about your topic

**Best part**: It's **completely free** and runs on your own computer - no internet required!

---

## 🚀 Quick Start (5 Minutes!)

### Step 1: Get Your Essay Ready
- Save your essay as a **text file** (.txt) 
- Example: `my_essay.txt`
- **Tip**: Copy and paste from Google Docs or Word into a simple text file

### Step 2: Download the Example Files
The system comes with example files you can use right away:
- `student_essay_jumping_spiders.txt` - Example student essay
- `science_essay_agents.json` - The AI teachers configuration  
- `science_essay_rubric.md` - Grading rubric

### Step 3: Run the Review (Choose Your Method)

#### Option A: Super Easy Docker Method ⭐ **RECOMMENDED**
```bash
# Just copy and paste this command:
docker run --rm \
  -v "${PWD}/examples:/app/examples" \
  -v "${PWD}/output:/app/output" \
  auto-reviewer auto-reviewer \
  --doc /app/examples/student_essay_jumping_spiders.txt \
  --agents /app/examples/science_essay_agents.json \
  --rubric /app/examples/science_essay_rubric.md \
  --out /app/output/my_review
```

#### Option B: Use Your Own Essay
```bash
# Replace 'my_essay.txt' with your essay filename:
docker run --rm \
  -v "${PWD}:/app/workspace" \
  -v "${PWD}/output:/app/output" \
  auto-reviewer auto-reviewer \
  --doc /app/workspace/my_essay.txt \
  --agents /app/workspace/examples/science_essay_agents.json \
  --rubric /app/workspace/examples/science_essay_rubric.md \
  --out /app/output/my_review
```

### Step 4: See Your Results! 🎉
Look in the `output/my_review` folder for:
- **Individual teacher reviews** (4 separate files)
- **Summary report** with overall scores
- **Suggestions for improvement**

---

## 📋 What You'll Get Back

### Individual Teacher Reports
Each AI teacher gives you:
- **Scores** (1-5 scale) on different aspects
- **Specific comments** about what's good and what needs work
- **Suggestions** for how to improve
- **Rewritten examples** showing how to fix problems

### Overall Summary Report
- **Overall grade** based on all teachers' input
- **Strengths** your essay already has
- **Top 3 things to improve** 
- **Before/after examples** of improvements

---

## 🎯 Perfect for These Essay Types

### Science Essays ✅ **WORKS GREAT**
- Biology, Chemistry, Physics topics
- Lab reports and experiments
- Science fair projects
- Nature and environment topics

### Other Essays ✅ **ALSO WORKS**  
- History and social studies
- Literature analysis
- Personal narratives
- Argumentative essays

### What It Checks For

#### Content Quality 🔬
- **Accuracy**: Are your facts correct?
- **Depth**: Did you explain things well enough?
- **Examples**: Do you have good supporting details?

#### Writing Quality ✍️
- **Organization**: Does your essay flow logically?
- **Grammar**: Are there spelling/grammar mistakes?
- **Style**: Does it sound academic and professional?

#### Critical Thinking 🤔  
- **Analysis**: Do you explain WHY things happen?
- **Connections**: Do you link different ideas together?
- **Problem-solving**: Do you suggest solutions?

---

## 💡 Tips for Best Results

### Before You Submit
- **Write a complete first draft** - don't submit partial work
- **Include specific examples** - vague writing gets lower scores
- **Write 3+ paragraphs** - very short essays don't get good feedback
- **Check basic spelling** first - focus the AI on bigger issues

### Understanding Your Scores

| Score | What It Means | What To Do |
|-------|---------------|-------------|
| **5** | Excellent! | Keep doing what you're doing |
| **4** | Good work | Minor improvements possible |
| **3** | Okay, but needs work | Follow the suggestions |
| **2** | Needs significant improvement | Major revision recommended |
| **1** | Poor, major problems | Consider rewriting from scratch |

### Making Improvements
1. **Start with the lowest scores** - fix biggest problems first
2. **Read all 4 teachers' comments** - they each notice different things  
3. **Focus on one area at a time** - don't try to fix everything at once
4. **Use the specific examples** provided in the feedback
5. **Run it again** after making changes to see improvement!

---

## 🛠️ Customizing for Your Needs

### Different Types of Teachers
You can modify `science_essay_agents.json` to create different types of reviewers:

#### For Math Essays:
- Math Content Expert
- Problem-Solving Specialist  
- Calculation Checker
- Explanation Clarity Coach

#### For History Essays:
- Historical Accuracy Checker
- Evidence and Sources Expert
- Argument Structure Analyst  
- Writing Style Coordinator

#### For Creative Writing:
- Character Development Expert
- Plot Structure Analyst
- Creative Language Coach
- Audience Engagement Specialist

### Different Rubrics
Create your own `my_rubric.md` file based on:
- Your teacher's grading criteria
- Assignment requirements
- Class standards
- Personal goals

---

## ❗ Common Problems & Solutions

### "Command not found" Error
**Problem**: Docker isn't installed or running
**Solution**: 
1. Install Docker Desktop from docker.com
2. Make sure Docker Desktop is running (you'll see a whale icon)
3. Try the command again

### "File not found" Error  
**Problem**: Essay file path is wrong
**Solution**:
1. Make sure your essay file is in the right folder
2. Check the filename matches exactly (including .txt)
3. Use the full path: `/full/path/to/your/essay.txt`

### "No output generated" Error
**Problem**: Essay might be too short or in wrong format
**Solution**:
1. Make sure essay is at least 3 paragraphs
2. Save as plain text (.txt), not Word doc
3. Check that file has actual content

### Reviews Don't Make Sense
**Problem**: AI didn't understand your topic
**Solution**:
1. Add more context/background in your essay
2. Use clearer topic sentences  
3. Try a different set of agents more suited to your topic

---

## 🎓 Examples and Practice

### Try These Sample Essays
The system includes sample essays you can practice with:

1. **Jumping Spider Care** (`student_essay_jumping_spiders.txt`)
   - Science/biology topic
   - Shows common high school writing issues
   - Good for learning what the system looks for

2. **Your Own Work**
   - Start with a complete draft
   - Run it through the system
   - Make improvements based on feedback
   - Run it again to see progress!

### Learning Exercise
1. **Run the sample essay** first to see how it works
2. **Read all the feedback** carefully
3. **Try to improve the sample essay** based on suggestions
4. **Run your improved version** to see better scores
5. **Apply what you learned** to your own essays

---

## 🔧 Advanced Features (Optional)

### Custom Temperature Settings
- **Higher temperature** (0.7-1.0): More creative, varied feedback
- **Lower temperature** (0.1-0.3): More consistent, focused feedback
- **Default** (0.3): Good balance for most essays

### Multiple Review Rounds  
1. **First draft**: Get overall feedback and major issues
2. **Second draft**: Focus on specific improvements
3. **Final draft**: Check for polish and final details

### Saving and Organizing Results
```bash
# Create folders by assignment:
mkdir "english_essay_1"
docker run ... --out /app/output/english_essay_1

# Or by date:
mkdir "review_2024_03_15" 
docker run ... --out /app/output/review_2024_03_15
```

---

## 📞 Getting Help

### If You're Stuck
1. **Read this guide again** - answers to most questions are here
2. **Try the sample essay first** - make sure basic system works  
3. **Check the examples folder** - lots of sample files to learn from
4. **Ask a tech-savvy friend** - Docker setup is the trickiest part

### For Teachers
- This tool is designed to **supplement**, not replace human feedback
- Great for **first drafts** and **peer review** processes
- Helps students **self-edit** before submission
- Provides **consistent feedback** on basic writing principles

---

## 🌟 Success Stories

> *"I used this on my biology essay about photosynthesis. It caught that I was using casual language like 'really important' instead of scientific terms. My teacher said my revised essay was much more professional!"* - Sarah, 10th grade

> *"The Critical Thinking coach helped me realize I was just describing my experiment but not explaining WHY the results mattered. Added a whole section about applications and got an A!"* - Marcus, 11th grade  

> *"Used this for peer reviews in our English class. Students got much better at giving specific feedback after seeing how the AI teachers worked."* - Ms. Rodriguez, English Teacher

---

## 🎉 You're Ready to Go!

**Remember**: This tool is here to help you become a better writer, not to do the writing for you. Use the feedback to learn and improve!

**Happy writing!** 📝✨