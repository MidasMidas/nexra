# Random Marketplace Skill Usability Test

Date: 2026-04-13

Test goal:

- Simulate a first-time Nexra user
- Randomly inspect 10 marketplace skills
- Judge whether the user can understand the skill and continue to use it outside Nexra

Important scope note:

- Nexra v1 does not execute marketplace skills directly
- "Usable" here means the skill has enough description, source page, setup hints, or tool schema for a user or agent to continue outside Nexra

## Result summary

- Clearly usable outside Nexra: 7
- Usable but setup-dependent: 2
- Not recommended for first-time users: 1

## Sampled skills

1. Node Code Sandbox MCP
   - Verdict: Usable
   - Reason: Clear source page, installation steps, tool schema, and usage examples.

2. Koalr
   - Verdict: Setup-dependent
   - Reason: Clear value proposition, but requires engineering metrics and deployment data context to be meaningful for a first-time user.

3. MCP DB Python
   - Verdict: Usable
   - Reason: Description clearly states read-only MySQL inspection and JSON-RPC style usage. Good fit for a user who already has MySQL access.

4. MCP Server Memory File
   - Verdict: Usable
   - Reason: Clear memory tool behavior and simple text-file storage model. Easy to understand and continue using outside Nexra.

5. Jumpseller
   - Verdict: Usable
   - Reason: Clear commerce use case and source page with generated API-based MCP guidance. Best for users who already operate a Jumpseller store.

6. Slack MCP Server
   - Verdict: Usable
   - Reason: Clear integration purpose and setup direction. Requires Slack token configuration, but the use case is easy to understand.

7. Warp SQL Server MCP
   - Verdict: Usable
   - Reason: Strong documentation, setup guidance, security model, examples, and environment variable reference.

8. figma-mcp-go
   - Verdict: Usable but setup-dependent
   - Reason: The catalog entry is attractive, but it assumes Figma workflow context and plugin-bridge setup.

9. TypeScript MCP Server Boilerplate
   - Verdict: Not recommended for first-time users
   - Reason: It is a starter template for building MCP servers, not a ready-made business skill for ordinary users.

10. MySQL MCP Server
    - Verdict: Usable
    - Reason: Clear setup docs, installation examples for MCP clients, and direct explanation of required environment variables.

## Notes

- Database-oriented skills tend to be the easiest to evaluate because they often publish explicit setup and environment variable examples.
- Boilerplate/template skills reduce marketplace quality for first-time users because they look like usable skills but are actually development starters.
- Nexra should expose stronger labels such as:
  - Ready to use
  - Requires external credentials
  - Requires local runtime
  - Template / starter project

## Productized labels

The marketplace now uses these four labels in the UI:

- `Ready to use`
- `Requires external credentials`
- `Requires local runtime`
- `Template / starter`

These labels are heuristic and are meant to help first-time users scan the marketplace faster. Provider documentation is still the source of truth for final setup and calling requirements.
