---
inclusion: always
---

# AI-First Development Guidelines

## Core Principles
- This codebase is maintained by AI agents - optimize for AI comprehension and maintainability
- Prioritize clear, explicit code patterns over implicit conventions
- Favor verbose, self-documenting code over clever shortcuts
- Maintain good architecture practices while optimizing for AI workflow

## Code Organization
- Use pipenv for Python dependency management (works better on Ubuntu)
- Break down large files into smaller, focused modules when possible
- Each module should have a single, clear responsibility
- Prefer explicit imports over wildcard imports

## Architecture Patterns
- Follow separation of concerns - keep business logic, data access, and presentation layers distinct
- Use dependency injection patterns for better testability and modularity
- Implement consistent error handling patterns across the application
- Maintain clear API contracts between components

## AI-Specific Considerations
- Include comprehensive docstrings and type hints for all functions
- Use descriptive variable and function names that clearly indicate purpose
- Avoid complex nested logic - prefer flat, readable control flow
- Include inline comments for business logic decisions
- Structure code to minimize context switching between files

## File Structure Guidelines
- Group related functionality in dedicated modules
- Use consistent naming conventions across the project
- Keep configuration separate from implementation
- Maintain clear boundaries between different application layers