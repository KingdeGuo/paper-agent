# Skill: Daily Research Briefing

Get a concise, AI-generated daily briefing about new papers, reading progress, and research trends.

## Prerequisites

- MCP tools: `get_library_stats`, `get_reading_list`, `generate_research_digest`, `search_arxiv`
- Active papers in your library with various reading statuses

## Workflow

### Step 1: Morning Briefing
The AI runs this automatically when prompted:

1. **Library Stats**: Total, processing, reading progress
2. **Reading Queue**: Papers marked "to_read" that need attention
3. **In Progress**: Papers you're currently reading
4. **Recent Activity**: Recently added or updated papers
5. **arXiv Radar**: New papers from your field on arXiv

### Step 2: Review & Prioritize
The AI suggests which papers to prioritize today:
- Papers nearing deadlines
- Papers most related to your current project
- Papers with high citation potential

### Step 3: Quick Digest
For each priority paper, the AI provides a 1-sentence TL;DR so you can decide what to read deeply.

## Example Prompt

```
Give me my daily research briefing. Include my reading progress, 
what's new in my library, and any interesting papers from arXiv 
in the cs.AI and cs.CL categories.
```

## Output Format

```markdown
## 📋 Daily Research Briefing — [Date]

### 📊 Library Overview
- Total: 45 papers | Read: 12 | Reading: 3 | To Read: 8

### 📖 Today's Priority Reading
1. **Paper X** — [1-sentence TL;DR] — Due for review
2. **Paper Y** — [1-sentence TL;DR] — Related to current project

### 🔍 New on arXiv (cs.AI)
- **Paper Z** — [brief description] — Imported to your library

### ✅ Progress
- Yesterday: Read 2 papers, Added 3 annotations
- This week: 65% of weekly reading goal
```
