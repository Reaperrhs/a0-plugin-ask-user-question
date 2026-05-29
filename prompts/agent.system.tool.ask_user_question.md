# Ask User Question

Use this tool to ask the user structured clarifying questions when their request is ambiguous or you need specific preferences before proceeding. Rather than guessing, present clear options and let them choose.

## When to Use

- The user's request has multiple valid interpretations
- You need to choose between distinct approaches, styles, or strategies
- There are trade-offs the user should decide on (speed vs quality, simplicity vs features)
- You want to confirm the user's intent before starting a large task
- The user might have a strong preference that affects the outcome

## Parameters

- **questions** (array, required): 1-4 structured questions. Each question has:
  - **question** (string): The question text, must end with `?`
  - **header** (string): Short tab label, max 16 characters
  - **options** (array): 2-4 options, each with:
    - **label** (string): 1-5 words, max 60 characters. Cannot use reserved labels: `Other`, `Type something.`, `Chat about this`, `Next ->`
    - **description** (string): Brief explanation of this option
    - **preview** (string, optional): Markdown content shown in a preview pane when selected
  - **multiSelect** (boolean, optional): Allow selecting multiple options (default: false)
- **timeout** (integer, optional): Seconds to wait for response (default: 300)

## Example

```json
{
  "questions": [
    {
      "question": "Which architecture style do you prefer for this service?",
      "header": "Architecture",
      "options": [
        {
          "label": "Microservices",
          "description": "Distributed services with independent deployment and scaling",
          "preview": "## Microservices\n\n- Independent deploy\n- Service mesh\n- Event-driven"
        },
        {
          "label": "Modular Monolith",
          "description": "Single deployable with well-defined module boundaries"
        },
        {
          "label": "Serverless",
          "description": "Functions-as-a-service with auto-scaling and pay-per-use"
        }
      ]
    },
    {
      "question": "What is the priority for this project?",
      "header": "Priority",
      "multiSelect": false,
      "options": [
        {"label": "Speed", "description": "Ship fast, iterate later"},
        {"label": "Quality", "description": "Production-grade from the start"},
        {"label": "Cost-efficient", "description": "Minimize infrastructure and dev time"}
      ]
    }
  ]
}
```

## Important Notes

- The tool will wait for the user to answer. It does NOT break the agent loop.
- If the user declines or the timeout expires, the tool returns a message so you can proceed with your best judgment.
- An `Other` option is automatically provided so users can type custom answers.
- Users can also add notes to each question for additional context.
- Use this tool proactively when clarity matters, but do not overuse it for simple questions.
