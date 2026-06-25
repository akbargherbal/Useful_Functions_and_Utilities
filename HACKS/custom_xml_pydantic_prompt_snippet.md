I want the LLM to generate its content in custom XML format because XML with CDATA sections eliminates escaping nightmares—I can wrap all code content in `<![CDATA[...]]>` tags and include quotes, newlines, and special characters without any escaping, which makes the LLM's job much easier and reduces parsing failures. The system prompt should explicitly tell the LLM to respond with ONLY valid XML using a specific structure I'll define, wrapping all code/content fields in CDATA, and ordering elements logically (config files first, then application files). While we're at it, we also need to write the parser function that takes the LLM's XML response and parses it using Pydantic: this function should use `lxml` with `recover=True` to handle malformed XML gracefully, extract text from each XML element (CDATA is handled automatically by lxml), convert the extracted data into a Python dictionary, then pass that dictionary to a Pydantic model using `MyModel(**data_dict)` for validation—this gives us XML's forgiveness during generation and Pydantic's strict validation after parsing, and the parser should include try-except blocks to catch both XML parsing errors and Pydantic validation errors with clear error messages showing what went wrong.

---

Here's what the LLM would respond with:

```xml
<project>
  <project_name>nextjs-todo-app</project_name>
  <description>Simple todo app with add/remove/complete functionality</description>
  <files>
    <file>
      <path>package.json</path>
      <content><![CDATA[
{
  "name": "nextjs-todo-app",
  "version": "0.1.0",
  "dependencies": {
    "next": "14.0.0",
    "react": "^18",
    ...
  }
}
      ]]></content>
    </file>
    <file>
      <path>app/layout.tsx</path>
      <content><![CDATA[
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
      ]]></content>
    </file>
    <file>
      <path>app/page.tsx</path>
      <content><![CDATA[
'use client'
import { useState } from 'react'

export default function TodoApp() {
  const [todos, setTodos] = useState([])
  // ... rest of component logic
  return <div>...</div>
}
      ]]></content>
    </file>
    <file>
      <path>components/TodoItem.tsx</path>
      <content><![CDATA[
// Component code here...
      ]]></content>
    </file>
  </files>
</project>
```

**Key points:**

- All code wrapped in `<![CDATA[...]]>` — no escaping needed
- Clear hierarchy: project → files → individual file elements
- Each file has `<path>` and `<content>` tags
- Parser just needs to loop through `<file>` elements and extract these two fields

---
