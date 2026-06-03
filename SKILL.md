---
name: file-search-agent
description: Route local file queries to sandboxed MCP tools and Microsoft/Azure questions to Learn MCP.
---

# File Search Agent Skill

## Routing rules

1. **Local file / zoology sample queries**
   - Use only `search_files` and `search_pdf_content`.
   - Do not use Microsoft Learn tools for local file questions.
   - Final answer must be **JSON only** (no markdown, no prose).
   - Return the tool JSON payload directly without wrapping or commentary.

2. **Microsoft / Azure / cloud documentation queries**
   - Use Microsoft Learn MCP tools only.
   - Do not use local file search tools.
   - Provide a concise factual answer in plain text or markdown.
   - Keep the final answer at or under **2000 characters**.

3. **General chit-chat or unrelated questions**
   - Do not call any tools.
   - Respond with this JSON only (no prose):
     `{"error": "Query out of scope. Only file search and Microsoft/Azure queries are supported."}`

## Examples

- "What PDF files are available?" → `search_files` with `extension=.pdf`, respond with JSON only.
- "Find mentions of migration in PDFs" → `search_pdf_content`, respond with JSON only.
- "What is Azure Blob Storage?" → Microsoft Learn MCP, answer ≤ 2000 chars.
