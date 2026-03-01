# CLAUDE.md

This file provides guidance for AI assistants (Claude and others) working in this repository. Keep this file updated as the project evolves.

## Repository Overview

**Repository:** lucpol/Claude
**Status:** Active development

This repository is currently being initialized. Update this section as the project's purpose and structure become established.

## Repository Structure

```
Claude/
├── CLAUDE.md        # AI assistant guidance (this file)
├── index.html       # Página web estática principal
└── styles.css       # Estilos de la página
```

Update this tree as directories and files are added.

## Development Workflow

### Branch Strategy

- All development happens on feature branches: `claude/<description>-<session-id>`
- Never push directly to `main` or `master`
- Use descriptive branch names that reflect the work being done

### Making Changes

1. Checkout or create the designated branch
2. Make focused, atomic commits with clear messages
3. Push to `origin <branch-name>` using: `git push -u origin <branch-name>`
4. Open a pull request for review before merging

### Commit Messages

Write commit messages in imperative mood with a short subject line (50 chars max):

```
Add user authentication module

- Implement JWT-based login flow
- Add password hashing with bcrypt
- Include unit tests for auth helpers
```

Avoid vague messages like "fix stuff" or "updates".

## Git Operations

### Pushing Changes

```bash
git push -u origin <branch-name>
```

Branch names must follow the pattern `claude/<description>-<session-id>` or they will be rejected.

### Handling Network Failures

If push fails due to network errors, retry with exponential backoff:
- Attempt 1: immediate
- Attempt 2: wait 2s
- Attempt 3: wait 4s
- Attempt 4: wait 8s
- Attempt 5: wait 16s

Do **not** retry on permission (403) errors — check branch name first.

## Code Conventions

Establish these conventions once a primary language/framework is chosen. Common patterns to document here:

- **Language & runtime version** (e.g., Python 3.12, Node.js 22, Go 1.23)
- **Formatter & linter** (e.g., `ruff`, `eslint`, `gofmt`) with commands to run them
- **Testing framework** and how to run the test suite
- **Environment variables** required and how to configure them (`.env.example`)
- **Dependency management** (e.g., `pip`, `npm`, `go mod`)

## Running the Project

Document commands here as they are established:

```bash
# Install dependencies
# <command>

# Run development server
# python3 -m http.server 8000

# Run tests
# <command>

# Run linter/formatter
# <command>
```

## Testing

- Write tests for all new functionality
- Tests must pass before merging a PR
- Aim for meaningful coverage, not just a coverage number
- Keep unit tests fast; integration/e2e tests in a separate suite

## Security

- Never commit secrets, credentials, API keys, or `.env` files
- Use environment variables for all sensitive configuration
- Add `.env` to `.gitignore` from the start
- Review OWASP Top 10 considerations when building web-facing code

## AI Assistant Guidelines

When working in this repository as an AI assistant:

1. **Read before writing** — always read existing files before editing them
2. **Stay focused** — only make changes directly requested or clearly necessary
3. **No over-engineering** — avoid adding abstractions, helpers, or error handling for hypothetical scenarios
4. **No unsolicited cleanup** — do not refactor, add comments, or rename variables in code you did not change
5. **Delete unused code** — do not leave dead code with `// removed` comments; remove it entirely
6. **Keep this file current** — update `CLAUDE.md` whenever significant structural or workflow changes occur
7. **Commit atomically** — one logical change per commit
8. **Ask when uncertain** — if requirements are ambiguous, clarify before implementing

## Updating This File

This file should be updated when:
- The project language or framework is decided
- A build/test/lint pipeline is added
- New conventions are adopted by the team
- The directory structure changes significantly
- Deployment or CI/CD workflows are introduced
