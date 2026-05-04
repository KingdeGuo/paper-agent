# Skill: Academic Writing Assistant

Write academic text with proper citation support from your Paper Agent library.

## Prerequisites

- MCP tools: `search_papers`, `get_paper`, `export_citation`, `ask_library`
- Papers relevant to your writing topic in your library

## Workflow

### Step 1: Define Writing Task
Tell the AI:
- What you're writing (introduction, methods, discussion, etc.)
- Your main argument or finding
- Target journal or venue (for formatting)

### Step 2: Gather Supporting Evidence
The AI searches your library for papers that:
- Support your claims (agreement)
- Challenge your claims (counterarguments to address)
- Provide methodological precedent
- Offer relevant comparisons

### Step 3: Write with Citations
The AI produces text with inline citations:
```markdown
Recent work has shown that transformer efficiency can be improved 
through sparse attention patterns [Smith et al., 2023; Zhang, 2024]. 
However, these approaches often trade off quality for speed [Lee, 2023].
```

### Step 4: Generate Reference List
The AI generates a properly formatted bibliography using your chosen style.

## Example Prompt

```
Help me write the "Results" section for my paper on efficient transformers. 
My key finding is that our sparse attention method achieves 2x speedup 
with only 3% accuracy drop. Find supporting papers from my library that 
show similar tradeoffs, and cite them appropriately.
```

## Output Format

```markdown
## [Section Title]

[Well-structured academic text with proper citations]

### References
[Formatted bibliography]
```
