# Installation Guide
## Setting Up Auto-Reviewer on Your Computer

### 🏁 Quick Install (Recommended)

The easiest way to use Auto-Reviewer is with **Docker** - it handles all the complicated stuff for you!

#### Step 1: Install Docker Desktop
1. Go to [docker.com](https://www.docker.com/products/docker-desktop/)
2. Download **Docker Desktop** for your operating system:
   - **Windows**: Download "Docker Desktop for Windows"
   - **Mac**: Download "Docker Desktop for Mac" 
   - **Linux**: Follow the instructions for your distribution

3. **Install Docker Desktop**:
   - Run the installer
   - Follow the setup wizard (use default settings)
   - Restart your computer when prompted

4. **Start Docker Desktop**:
   - Look for the Docker whale icon in your taskbar/system tray
   - If you see the whale icon, Docker is running! ✅
   - If not, open "Docker Desktop" from your applications

#### Step 2: Get Auto-Reviewer
Choose one of these options:

**Option A: Download ZIP (Easier)**
1. Go to [github.com/tjGecko/LLM_Doc_Reviewer](https://github.com/tjGecko/LLM_Doc_Reviewer)
2. Click the green "Code" button
3. Select "Download ZIP" 
4. Extract the ZIP file to a folder like `Documents/auto-reviewer`

**Option B: Use Git (If you know how)**
```bash
git clone https://github.com/tjGecko/LLM_Doc_Reviewer.git
cd LLM_Doc_Reviewer
```

#### Step 3: Build the Docker Image
1. **Open Terminal/Command Prompt**:
   - **Windows**: Press `Win + R`, type `cmd`, press Enter
   - **Mac**: Press `Cmd + Space`, type `terminal`, press Enter
   - **Linux**: Press `Ctrl + Alt + T`

2. **Navigate to the auto-reviewer folder**:
   ```bash
   cd Documents/auto-reviewer
   # (or wherever you extracted the files)
   ```

3. **Build the Docker image** (this takes 5-10 minutes the first time):
   ```bash
   docker build -t auto-reviewer .
   ```

4. **Test that it worked**:
   ```bash
   docker run --rm auto-reviewer auto-reviewer --help
   ```
   
   If you see the help text with all the options, it worked! 🎉

---

## 🛠️ LLM Setup (AI Brain)

Auto-Reviewer needs an AI "brain" to analyze your essays. You have several options:

### Option 1: LM Studio (Recommended - Free & Private) ⭐

**LM Studio** runs AI models locally on your computer - completely private and free!

#### Install LM Studio:
1. Go to [lmstudio.ai](https://lmstudio.ai)
2. Download LM Studio for your operating system
3. Install and open LM Studio

#### Download an AI Model:
1. In LM Studio, click the "🔍 Search" tab
2. Search for: `microsoft/Phi-3.5-mini-instruct-GGUF`
3. Download the model (about 2-4 GB)
4. Wait for it to finish downloading

#### Start the Local Server:
1. Click the "💬 Chat" tab in LM Studio
2. Select your downloaded model
3. Click "Start Server" button
4. You should see: `Server running on http://localhost:1234`

#### Test the Connection:
```bash
# This should work if LM Studio is running:
curl http://localhost:1234/v1/models
```

### Option 2: OpenAI API (Paid but Easy)

If you have an OpenAI account and want to pay per use:

1. Get your API key from [platform.openai.com](https://platform.openai.com/api-keys)
2. Create a `.env` file in your auto-reviewer folder:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4o-mini
   ```

### Option 3: Other Local AI (Advanced)

You can use other local AI solutions like:
- **Ollama** with models like Llama 3.1
- **vLLM** server setup
- **Hugging Face Transformers** API

---

## 📁 Project Structure

After installation, your folder should look like this:
```
auto-reviewer/
├── docs/                    # Documentation (you're here!)
├── examples/               # Sample essays and configs
│   ├── student_essay_jumping_spiders.txt
│   ├── science_essay_agents.json
│   └── science_essay_rubric.md
├── src/                    # The code (don't worry about this)
├── output/                 # Your results go here
├── .env                    # Your AI settings
├── Dockerfile              # Docker configuration
└── requirements.txt        # Python dependencies
```

---

## ⚙️ Configuration

### Environment Variables (.env file)

Create a `.env` file in your main folder with these settings:

**For LM Studio (Free):**
```bash
# LM Studio Settings
OPENAI_API_KEY=lm-studio
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_MODEL=microsoft/Phi-3.5-mini-instruct-GGUF

# Processing Settings  
TEMPERATURE=0.3
MAX_WORKERS=4
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**For OpenAI (Paid):**
```bash
# OpenAI Settings
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Processing Settings
TEMPERATURE=0.3
MAX_WORKERS=4
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### What These Settings Mean:

- **OPENAI_API_KEY**: Your AI service login token
- **OPENAI_API_BASE**: Where to find the AI service
- **OPENAI_MODEL**: Which AI model to use for reviews
- **TEMPERATURE**: How "creative" vs "consistent" the AI should be (0.1-1.0)
- **MAX_WORKERS**: How many essays to process at once (1-8)
- **EMBED_MODEL**: Which AI to use for understanding text (keep default)

---

## 🧪 Testing Your Installation

### Quick Test with Sample Essay:
```bash
# Make sure Docker is running, then try:
docker run --rm \
  -v "${PWD}/examples:/app/examples" \
  -v "${PWD}/output:/app/output" \
  auto-reviewer auto-reviewer \
  --doc /app/examples/student_essay_jumping_spiders.txt \
  --agents /app/examples/science_essay_agents.json \
  --rubric /app/examples/science_essay_rubric.md \
  --out /app/output/test_review
```

**What should happen:**
1. You see some startup messages
2. The AI analyzes the essay (takes 2-5 minutes)
3. Results appear in `output/test_review/` folder
4. You get files like `review_report.md` and individual agent reviews

**If it works**: Congratulations! 🎉 You're ready to review essays!

**If it doesn't work**: Check the troubleshooting section below.

---

## 🩺 Troubleshooting

### Docker Issues

**"Docker command not found"**
- Make sure Docker Desktop is installed and running
- Restart your terminal/command prompt
- On Windows, make sure you're using Command Prompt, not PowerShell

**"Cannot connect to Docker daemon"**
- Start Docker Desktop (look for whale icon in system tray)
- Wait for Docker to fully start (can take 1-2 minutes)
- Try the command again

**"No such image: auto-reviewer"**
- You need to build the image first: `docker build -t auto-reviewer .`
- Make sure you're in the right folder (should have `Dockerfile`)

### AI Connection Issues

**"Connection refused" or "Server not responding"**
- **For LM Studio**: Make sure the server is running (green "Server running" message)
- **For OpenAI**: Check your API key is correct and you have credits
- Test the connection manually:
  ```bash
  # For LM Studio:
  curl http://localhost:1234/v1/models
  
  # For OpenAI:
  curl -H "Authorization: Bearer your_api_key" https://api.openai.com/v1/models
  ```

**"Model not found"**
- **For LM Studio**: Make sure you downloaded and selected a model
- **For OpenAI**: Check your model name is correct (try `gpt-4o-mini`)

### File Issues

**"No such file or directory"**
- Check your file paths are correct
- Make sure your essay file exists and is named correctly
- Try using full paths: `/full/path/to/your/essay.txt`

**"Permission denied"**
- **Windows**: Run Command Prompt as Administrator
- **Mac/Linux**: Try adding `sudo` before the command
- Check that your essay file isn't open in another program

### Performance Issues

**"Very slow or hanging"**
- **Lower MAX_WORKERS**: Try `MAX_WORKERS=2` or `MAX_WORKERS=1`
- **Simpler model**: For LM Studio, try a smaller model
- **Check resources**: Make sure you have at least 4GB free RAM

**"Out of memory"**
- Close other programs
- Use a smaller AI model
- Set `MAX_WORKERS=1` in your .env file

---

## 🔄 Updating Auto-Reviewer

### Getting Updates:
```bash
# If you used Git:
git pull origin main
docker build -t auto-reviewer .

# If you downloaded ZIP:
# Download the new ZIP and replace your files
docker build -t auto-reviewer .
```

### Clean Reinstall:
```bash
# Remove old Docker image:
docker rmi auto-reviewer

# Rebuild:
docker build -t auto-reviewer .
```

---

## 🏆 You're All Set!

If you made it through this guide, you should have:
- ✅ Docker Desktop installed and running
- ✅ Auto-reviewer Docker image built
- ✅ AI service (LM Studio or OpenAI) configured
- ✅ Tested with the sample essay

**Next steps**: Head over to the [User Guide](USER_GUIDE.md) to start reviewing essays!

**Need help?** Check the troubleshooting section or ask a tech-savvy friend to help with the initial setup.

**Remember**: The setup is the hardest part - once it's working, using it is super easy! 🚀