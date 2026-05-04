# Skill: Deep Paper Analysis

Perform a systematic deep analysis of a single academic paper.

## Prerequisites

- MCP tools: `get_paper`, `get_paper_summary`, `find_related_papers`, `get_paper_annotations`
- The paper should be in your library with AI summary generated

## Workflow

### Step 1: Select Paper
Tell the AI which paper to analyze (by title or ID).

### Step 2: Retrieve Full Context
The AI fetches:
- Full metadata (authors, year, journal, DOI)
- Abstract and AI summary
- Your annotations and notes
- Related papers for comparison

### Step 3: Structured Analysis
The AI analyzes across these dimensions:

```json
{
  "research_problem": "What problem does this paper address? Why is it important?",
  "methodology": "What methods are used? Are they appropriate?",
  "contributions": "What are the key novel contributions?",
  "results": "What are the main findings? Are they convincing?",
  "strengths": "What does this paper do well?",
  "weaknesses": "What are the limitations or gaps?",
  "connections": "How does this relate to other papers in your library?"
}
```

### Step 4: Actionable Output
The AI provides:
- **Executive Summary**: 2-3 sentence overview
- **Key Takeaways**: Bullet points for your research
- **Critical Assessment**: Strengths and weaknesses
- **Follow-up Questions**: What to investigate next
- **Related Papers**: Papers to read next from your library

## Example Prompt

```
Deeply analyze the paper "Attention Is All You Need" in my library. 
Focus on: the methodological innovations, how it compares to previous 
approaches, and its impact on the field. Also check if I have any 
related papers I should read next.
```

## Output Format

```markdown
## Paper Analysis: [Title]

### Executive Summary
[2-3 sentence overview]

### Key Contributions
- [Contribution 1]
- [Contribution 2]

### Critical Assessment
**Strengths:**
- [Strength]

**Weaknesses:**
- [Weakness]

### Connections to Your Library
- [Connection to paper X]
- [Connection to paper Y]

### Suggested Next Reading
- [Paper A] — because...
- [Paper B] — because...
```
