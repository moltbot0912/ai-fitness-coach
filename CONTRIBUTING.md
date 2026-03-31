# Contributing to AI Fitness Coach

Thank you for your interest in contributing! This document covers guidelines and conventions for the project.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-fitness-coach.git
   cd ai-fitness-coach
   ```
3. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Project Structure

```
ai-fitness-coach/
  src/
    kai-cli.py         # Main CLI -- all fitness commands live here
    db_manager.py      # SQLite database layer (pure functions, no global state)
    exercises.md       # Exercise database (Markdown format)
  config/
    .env.example       # Environment variable template
    profile.example.json         # User profile template
    group-config.example.md      # WhatsApp group personality template
  cron/
    workout-reminder.sh  # Automated WhatsApp reminder script
    install-cron.sh      # Cron job installer
  docs/                  # Documentation
  data/                  # SQLite database (git-ignored)
```

## Code Conventions

### Python (kai-cli.py, db_manager.py)

- **Python 3.8+ compatibility** -- do not use features introduced after 3.8 (e.g., walrus operator is fine, but `match` statements from 3.10 are not).
- **Standard library only** -- no external pip packages. This keeps deployment simple (no virtualenvs, no pip installs).
- **db_manager.py** uses pure functions: each function accepts a `db_path` argument, opens its own connection, and returns Python dicts or lists. No global state, no singletons.
- **kai-cli.py** uses `argparse` with subcommands. Each command is a function that receives `args`.
- Use clear variable names and add comments for non-obvious logic.

### Shell Scripts (cron/, setup.sh)

- Use `set -euo pipefail` at the top.
- Use full absolute paths for commands that will run via cron.
- Quote all variables.

### Markdown (docs/, config templates)

- Use `--` for em dashes (not Unicode characters).
- Code blocks should specify the language for syntax highlighting.

## What to Contribute

### Adding Exercises

Edit `src/exercises.md` following the existing format:

```markdown
## Muscle Group Name
### Equipment: Equipment Type
- Exercise Name
- Another Exercise
```

Equipment types recognized by the suggestion engine: `Barbell`, `Dumbbell`, `Cable`, `Machine`, `Bodyweight`.

### Adding CLI Commands

1. Add a new subcommand in the `argparse` setup section of `kai-cli.py`.
2. Write the handler function following the pattern of existing commands.
3. If it needs new database operations, add them to `db_manager.py`.
4. Update the command reference in `docs/COMMANDS.md`.
5. Update the group config template (`config/group-config.example.md`) to include the new command in the `## Tools` section.

### Other Ideas

- Localization and language support
- Fitness API integrations (smartwatches, fitness trackers)
- Progress chart or visualization generation
- New tracking categories (hydration, supplements, etc.)
- Test coverage (pytest)

## Submitting Changes

1. Make sure the CLI still works:
   ```bash
   python3 src/kai-cli.py --help
   python3 src/kai-cli.py quick-status
   ```
2. If you changed db_manager.py, verify the database initializes cleanly:
   ```bash
   rm -f /tmp/test_kai.db
   python3 src/db_manager.py /tmp/test_kai.db
   ```
3. Commit with a clear message describing what and why.
4. Push to your fork and open a Pull Request.

## Files NOT to Commit

These are in `.gitignore` for a reason -- they contain personal data:

- `.env` -- user environment variables
- `config/profile.json` -- user fitness profile
- `data/` -- SQLite database with personal health data
- `*.log` -- log files

## Questions?

Open an issue on GitHub or start a discussion. We are happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
