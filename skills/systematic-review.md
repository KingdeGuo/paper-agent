# Skill: Systematic Literature Review

Conduct a full systematic literature review (SLR) following academic best practices.

## Prerequisites

- MCP tools: `search_papers`, `get_paper`, `get_paper_summary`, `export_citation`, `search_arxiv`, `ask_library`
- A well-defined research question

## Workflow

### Step 1: Define Research Questions
Formulate your SLR research questions using PICo (Population, phenomenon of Interest, Context) or similar framework.

### Step 2: Search Strategy
The AI conducts comprehensive searches across:
- Your local library (`search_papers`)
- arXiv (`search_arxiv`)
- CrossRef (`export_citation` can look up DOIs)

### Step 3: Screening & Selection
The AI helps you apply inclusion/exclusion criteria:
- **Title/Abstract screening**: Quick relevance check
- **Full-text screening**: Detailed methodology check
- **Quality assessment**: Score each paper

### Step 4: Data Extraction
For each selected paper, the AI extracts:
- Research context and goals
- Methodology details
- Key findings and effect sizes
- Limitations noted by authors

### Step 5: Synthesis
The AI produces:
- **Descriptive synthesis**: Tables, frequencies, distributions
- **Thematic synthesis**: Emerging themes and patterns
- **Quality assessment**: Risk of bias evaluation

### Step 6: Write SLR Report
Structured output:
- Introduction and research questions
- Search methodology (PRISMA-compliant)
- Results and synthesis
- Discussion and implications
- Limitations of the review
- Conclusions

## Example Prompt

```
Conduct a systematic review on "the application of large language models 
in systematic review automation." I have papers in my library on NLP, 
LLMs, and evidence synthesis. Follow PRISMA guidelines and extract 
methodology details, performance metrics, and limitations.
```

## Output Format

```markdown
## Systematic Literature Review: [Title]

### 1. Introduction
[Background and research questions]

### 2. Methodology
- Search strategy
- Inclusion/exclusion criteria
- Quality assessment framework

### 3. Results
- PRISMA flow diagram (text)
- Summary table of included studies
- Thematic synthesis

### 4. Discussion
[Interpretation, implications, limitations]

### 5. Conclusion
[Key takeaways and future directions]

### References
[Full bibliography]
```
