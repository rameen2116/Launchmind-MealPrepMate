# 🚀 LaunchMind - MealPrepMate

## 📋 Startup Idea

**MealPrepMate** is a personalized weekly meal planning service that saves busy professionals time and reduces food waste by providing tailored recipes and grocery lists based on their unique dietary needs and schedule. Our AI-powered platform helps users plan healthy meals efficiently, automate grocery shopping, and maintain better nutrition while reducing stress and food waste. Whether you're a working professional, software engineer, or busy parent, MealPrepMate makes meal planning simple, affordable, and sustainable.

---

## 🏗️ Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     🧠 CEO AGENT (Orchestrator)              │
│         Decomposes ideas, reviews specs, routes feedback     │
└──────────────┬──────────────────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐
│PRODUCT │ │ENGINEER│ │MARKETING│ │   QA   │
└────────┘ └────────┘ └─────────┘ └────────┘
    │          │          │          │
    └──────────┼──────────┼──────────┘
               │
    ┌──────────┴──────────┬──────────┐
    │                     │          │
    ▼                     ▼          ▼
  📊 PRODUCT SPEC    🌐 GITHUB    📧 SENDGRID
                     💬 SLACK      📱 SLACK
```

### **Agent Responsibilities:**

| Agent | Input | Output | Process |
|-------|-------|--------|---------|
| **CEO** | Startup Idea | Orchestration Decisions | Decomposes tasks, reviews specs, routes feedback loops |
| **Product** | Startup Idea | Product Spec (personas, features, stories) | Generates comprehensive product specification using LLM |
| **Engineer** | Product Spec | GitHub PR, HTML Landing Page | Builds landing page and creates GitHub PR with code |
| **Marketing** | Product Spec | Email, Slack Message, Tagline | Generates marketing copy and sends emails/Slack posts |
| **QA** | All Outputs | Validation Report | Reviews all outputs against spec, posts GitHub comments |

### **Message Flow:**
1. CEO broadcasts startup idea → Product
2. Product generates spec → CEO reviews
3. CEO approves → Engineer + Marketing (parallel)
4. Engineer creates PR + Marketing sends emails
5. CEO sends all outputs → QA
6. QA validates and provides feedback
7. If failed: CEO routes revisions → Engineer/Marketing
8. Loop continues until QA passes

---

## 🛠️ Setup Instructions

### **Prerequisites**
- Python 3.8+
- Git
- GitHub account with token
- SendGrid account with API key
- Slack workspace with bot token
- Groq API key

### **1. Clone Repository**
```bash
git clone https://github.com/rameen2116/Launchmind-MealPrepMate.git
cd mealprepmate
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Set Environment Variables**

Create a `.env` file in the project root:
```bash
# GitHub API
GITHUB_TOKEN=ghp_your_token_here
REPO_NAME=username/repo-name

# Groq LLM
GROQ_API_KEY=gsk_your_key_here

# SendGrid Email
SENDGRID_API_KEY=SG.your_key_here
SENDER_EMAIL=your-sender@gmail.com
TEST_EMAIL=your-test@gmail.com

# Slack Bot
SLACK_BOT_TOKEN=xoxb-your-token-here
```

### **4. Run the System**
```bash
python main.py
```

This will:
- ✅ Decompose startup idea into tasks
- ✅ Generate product specification with personas and features
- ✅ Create GitHub issue and pull request with landing page
- ✅ Generate and send marketing emails
- ✅ Post updates to Slack
- ✅ Run QA validation and provide feedback
- ✅ Execute revision loops until QA passes

---

## 🌐 Platform Integrations

### **1. GitHub** 🔗
- **What**: Creates issues, commits HTML, opens pull requests
- **Actions**:
  - Creates GitHub Issue with product spec details
  - Commits HTML landing page to feature branch
  - Opens Pull Request for code review
  - Posts QA inline comments on PR
- **Links**: GitHub PR created during execution shown in output
- **Example**: https://github.com/rameen2116/Launchmind-MealPrepMate/pull/34

### **2. SendGrid Email** 📧
- **What**: Sends marketing emails to stakeholders
- **Actions**:
  - Sends personalized email with marketing tagline
  - Includes product benefits and call-to-action
  - HTML formatted professional emails
- **Triggers**: On first iteration + every revision cycle
- **Status**: Check SendGrid dashboard for delivery metrics

### **3. Slack** 💬
- **What**: Posts launch announcements and updates
- **Actions**:
  - Posts startup launch to #launches channel
  - Includes tagline, description, and PR link
  - Uses Block Kit formatting for rich messages
  - Updates on each iteration
- **Workspace**: https://launchmind-workspace.slack.com/
- **Channel**: #launches
- **Screenshot**: Slack bot posts launch updates with PR links

### **4. Groq LLM** 🤖
- **What**: Powers all agent decisions and content generation
- **Actions**:
  - Generates product specs with LLM
  - Creates marketing copy and taglines
  - Performs QA validation
  - Provides feedback for revisions
- **Model**: llama-3.1-8b-instant
- **Features**: Fast, free tier available, retry logic with fallbacks

---

## 💬 Slack Integration

### **Slack Workspace Invite:**
👉 **[Join LaunchMind Slack Workspace](https://join.slack.com/t/launchmind-workspace/shared_invite/zt-your-invite-code)**

### **Bot in Action:**
The bot posts structured launch notifications in the `#launches` channel:

```
🚀 Plan Healthy Meals, Save Time, Reduce Waste

Say goodbye to takeout and last-minute grocery trips with our 
personalized weekly meal planning service...

PR: https://github.com/rameen2116/Launchmind-MealPrepMate/pull/34
Status: 🎉 Live
```

**Features**:
- ✅ Real-time launch notifications
- ✅ PR links for code review
- ✅ Tagline and description preview
- ✅ Status indicators (generating, reviewing, live)

---

## 📌 GitHub PR

### **Engineer Agent Creates:**
- **PR Link**: https://github.com/rameen2116/Launchmind-MealPrepMate/pull/34
- **Contents**: Single HTML landing page with:
  - Responsive design (mobile/tablet/desktop)
  - Product features prominently displayed
  - Call-to-action buttons
  - Professional styling
  - Semantic HTML with accessibility

### **QA Comments:**
- QA agent posts inline code review comments
- Identified issues linked to product spec mismatches
- Comments categorize problems (HTML, marketing, consistency)
- Enables revision tracking through GitHub

---

## 📊 Workflow Outputs

### **Execution Summary**
When you run `python main.py`, you'll see:

```
🧠 CEO STARTED
📋 EXECUTION SUMMARY
   ✅ Product Approved
   ✅ Engineer Complete
   ✅ Marketing Complete  
   ✅ QA FINAL STATUS: PASSED

📩 MESSAGE PASSING FLOW
   1. CEO → Product: Task received
   2. Product → CEO: Spec generated
   ... (full message trace)

🚀 PLATFORM OUTPUTS
   📌 GitHub PR: https://github.com/...
   📧 Email Subject: Unlock Healthy Meals...
   💬 Slack Posted: ✅ Yes

📜 DETAILED DECISION LOG
   • Product Review: APPROVED
   • QA Review: PASS (0 issues)
```

---

## 🔄 Feedback Loop Example

```
Iteration 1:
  ✓ Product spec generated
  ✓ Engineer creates PR #34
  ✓ Marketing posts to Slack
  ✗ QA finds 5 issues

Iteration 2:
  ← CEO routes issues to Engineer
  ✓ Engineer revises HTML (PR #35)
  ✗ QA finds 2 remaining issues

Iteration 3:
  ← CEO routes issues to Marketing
  ✓ Marketing revises tagline
  ✓ QA PASSES - System approved
```

---

## ⚙️ Configuration Files

### **requirements.txt**
```
groq==0.4.1
requests==2.31.0
sendgrid==6.11.0
python-dotenv==1.0.0
```

### **.env.example**
Copy this template for your local setup:
```
GITHUB_TOKEN=
REPO_NAME=username/repo-name
GROQ_API_KEY=
SENDGRID_API_KEY=
SENDER_EMAIL=
TEST_EMAIL=
SLACK_BOT_TOKEN=
```

---

## 📈 Metrics & Monitoring

### **SendGrid Dashboard:**
- Monitor email delivery rates
- Track open rates and bounces
- View suppression lists

### **GitHub Dashboard:**
- Track PR creation and reviews
- Monitor issue counts
- View commit history

### **Slack Analytics:**
- Message activity in #launches
- Engagement metrics
- Bot interaction history

---

## 🐛 Troubleshooting

### **Email Not Arriving?**
- Check SendGrid dashboard for delivery status (often deferred to Gmail)
- Use non-Gmail test address (Gmail rate-limits free tier)
- Verify `SENDGRID_API_KEY` is valid
- Check `.env` file has `SENDER_EMAIL` and `TEST_EMAIL`

### **GitHub Errors?**
- Verify `GITHUB_TOKEN` has repo access
- Check `REPO_NAME` format: `username/repo`
- Ensure token has write permissions

### **Slack Not Posting?**
- Verify bot has access to `#launches` channel
- Check `SLACK_BOT_TOKEN` is valid
- Ensure bot is in workspace

### **LLM Failures?**
- Check `GROQ_API_KEY` is valid
- Verify internet connection
- System retries 3 times automatically

---

## 📚 Project Structure

```
mealprepmate/
├── main.py                 # Entry point
├── message_bus.py          # Inter-agent communication
├── llm.py                  # Groq LLM integration
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── agents/
    ├── ceo_agent.py       # Orchestrator
    ├── product_agent.py   # Product spec generation
    ├── engineer_agent.py  # GitHub & HTML creation
    ├── marketing_agent.py # Email & Slack posts
    └── qa_agent.py        # Validation & feedback
```

---

## 🎯 Key Features

✅ **Multi-Agent Orchestration**: CEO coordinates product, engineer, marketing, QA  
✅ **Autonomous Feedback Loops**: Agents revise based on QA feedback  
✅ **Real Platform Integration**: GitHub, Slack, SendGrid actually used  
✅ **LLM-Powered**: All decisions made by Groq LLM  
✅ **Error Handling**: Retry logic, fallback defaults  
✅ **Structured Outputs**: Decision logs, message traces, validation reports  
✅ **Iteration Tracking**: Monitors progress until QA passes  



