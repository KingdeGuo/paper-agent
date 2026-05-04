# Skill: Literature Review Generation

Generate a comprehensive, well-structured literature review section for a research paper or thesis.

## Prerequisites

- MCP tools: `get_paper`, `search_papers`, `get_paper_summary`, `export_citation`
- At least 5-10 papers on your topic in your Paper Agent library

## Workflow

### Step 1: Define Scope
Tell the AI your research topic, the angle you want to take, and how many papers to include.

### Step 2: Search Your Library
The AI will search your library for relevant papers using `search_papers` with your topic keywords.

### Step 3: Retrieve Details
For each relevant paper, the AI retrieves title, authors, year, abstract, and AI summary.

### Step 4: Thematic Organization
The AI groups papers by:
- Research approach (theoretical vs empirical)
- Methodology (qualitative vs quantitative)
- Findings (supporting vs contradictory)
- Time period (earlier foundations vs recent advances)

### Step 5: Write the Review
The AI produces a structured literature review with:
- Thematic sections with clear headings
- Comparative analysis within each theme
- Transition sentences connecting themes
- Identification of research gaps
- Proper citations in your chosen format

## Example Prompt

```
I need a literature review on "attention mechanisms in transformer architectures" 
for a machine learning paper. I have about 15 papers in my library on this topic. 
Focus on: evolution from self-attention to sparse attention, efficiency improvements, 
and applications in long-context tasks. Use APA style citations.
```

## Output Format

```markdown
## Related Work

### Evolution of Attention Mechanisms
[Paragraph comparing early vs modern approaches, with citations]

### Efficiency Improvements
[Paragraph discussing sparse attention, linear attention, etc.]

### Long-Context Applications
[Paragraph on applications in document-level tasks]

### Research Gaps
[Paragraph identifying what's missing]
```

## Tips
- Be specific about your focus area for better results
- Include contradictory findings for a balanced review
- Specify citation style (APA, MLA, IEEE, Chicago)
- Ask for a summary table of compared papers
