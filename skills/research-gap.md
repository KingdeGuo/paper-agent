# Skill: Research Gap Analysis & Hypothesis Generation

Identify underexplored areas in a research field and generate novel, high-impact research hypotheses.

## Prerequisites

- MCP tools: `search_papers`, `get_paper`, `analyze_citation_network`, `ask_library`
- 10+ papers on your target research area in your library

## Workflow

### Step 1: Define Research Area
Tell the AI your research area and the specific sub-field to analyze.

### Step 2: Library Analysis
The AI searches your library for all papers in the area and examines:
- Publication timeline (is this field growing or declining?)
- Methodology trends (what methods dominate?)
- Author networks (who is working on what?)
- Citation patterns (which papers are most influential?)

### Step 3: Gap Identification
The AI identifies:

| Gap Type | Description |
|----------|-------------|
| **Methodology Gap** | Technique from field A not yet applied to field B |
| **Evidence Gap** | Contradictory findings that need resolution |
| **Population Gap** | Research only done in certain contexts/settings |
| **Practical Gap** | Theory exists but no practical implementation |
| **Temporal Gap** | Early findings not replicated with modern methods |

### Step 4: Hypothesis Generation
For each gap, the AI generates:
- **Research Question**: The specific question to answer
- **Proposed Approach**: Methodology and experimental design
- **Expected Impact**: How this would advance the field
- **Feasibility**: Data availability, required resources, timeline

## Example Prompt

```
Analyze my papers on "efficient transformer architectures" and identify 
research gaps. I'm particularly interested in gaps between theoretical 
efficiency gains and practical deployment. Generate 3 concrete research 
hypotheses I could pursue for my PhD.
```

## Output Format

```markdown
## Research Gap Analysis: [Area]

### Field Overview
[Summary of current state: 5 papers, key trends, etc.]

### Identified Gaps

**Gap 1: [Title]**
- Type: [Methodology/Evidence/Population/Practical/Temporal]
- Evidence: Papers A, B show X; Paper C shows Y — contradiction
- Proposed Hypothesis: [Concrete research question]
- Approach: [Methodology for addressing the gap]
- Expected Impact: [How field would advance]

**Gap 2: [Title]**
...
```
