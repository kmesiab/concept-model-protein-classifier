# .comet/ Directory

## Purpose

Extended working memory system for AI-human collaboration, specifically for Comet (AI DevOps assistant) and developer collaboration.

## Structure

- `SESSION_STATE.md` - Local only, tracks active project context
- `README.md` - This file, committed to explain the system

## Usage Protocol

### When SESSION_STATE.md Gets Updated

- After major milestones (PR merged, deployment succeeded, architecture decisions)
- Before ending long work sessions (capture state for next session)  
- When context shifts (moving between infra/API/docs work)
- After resolving blockers

### What Gets Updated

- Timestamp, current focus, completed tasks
- Infrastructure changes (high-level only)
- Known issues, next priorities
- **Use placeholders**: Reference Terraform variables like `${var.state_bucket_name}` instead of actual resource names

## Rationale

As AI-human collaboration grows more sophisticated, maintaining context across sessions becomes critical. This directory:

- Keeps collaboration artifacts separate from production code
- Hidden from casual browsing but accessible when needed
- Can evolve organically as we discover what works best
- Doesn't interfere with existing docs/ structure

## Privacy Note

SESSION_STATE.md is gitignored to:

- Prevent merge conflicts from parallel work
- Keep potentially sensitive infrastructure details local
- Allow each developer to maintain their own working context

This paradigm can be adopted across projects for consistent AI-human collaboration patterns.
