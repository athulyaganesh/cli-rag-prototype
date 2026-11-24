# Coding Conventions

## 1. Naming Standards
- **Clarity over brevity:** Use descriptive, unambiguous names. Avoid single-letter variables except for standard loop counters (`i`, `j`) or math coordinates.
- **Booleans:** Prefix boolean variables and functions with `is_`, `has_`, `can_`, or `should_` (e.g., `is_valid`, `has_permission`).
- **Functions/Methods:** Start with an action verb describing the operation (e.g., `fetch_user`, `calculate_total`, `validate_payload`).
- **Constants:** Use `UPPER_SNAKE_CASE` for module-level configuration and magic numbers. Never hardcode magic numbers inside logic.

## 2. Commenting & Documentation
- **Comment *why*, never *what*:** Do not write inline comments that narrate obvious code (e.g., `# increment counter`). Only add comments to explain non-obvious edge cases, business rules, or external API quirks.
- **Docstrings:** Write concise docstrings for public functions, classes, and modules explaining inputs, outputs, and raised exceptions. Skip docstrings on trivial private helpers.
- **No dead code:** Delete unused code, imports, and commented-out blocks completely. Do not leave `// TODO` placeholders unless explicitly requested.
- **ELI15**: but make it short and easy to understand. 

## 3. Types & Data Modeling
- **Strict typing:** Include complete type annotations on all function signatures and return types.
- **Avoid untyped structures:** Do not pass raw dictionaries or `Any` types across module boundaries. Define explicit schemas, dataclasses, or interfaces (`[Pydantic / TypeScript interfaces / dataclasses]`).

## 4. Error Handling & Logging
- **Fail fast & explicitly:** Never use bare `try/except` blocks or silently swallow errors. Catch ALL errors and display. 
- **Boundary handling:** Raise domain-specific errors in core logic; catch and translate them into user-facing responses only at the outer API/UI boundary.
- **Structured logging:** Use the project logger (`[logger setup]`), never `print()` or `console.log()`, for runtime diagnostics.

## 5. Structure & Reference Patterns
- **Single responsibility:** Keep functions focused on one task (aim for under 40 lines). Extract complex conditionals into well-named helper functions.
- **Follow existing patterns:** Match the exact file layout, naming, and error-handling style used in `[path/to/your/best_reference_file]`.
