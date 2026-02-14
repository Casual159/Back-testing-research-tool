# Pre-commit Hooks Setup Guide

Pre-commit hooks automatically check your code quality **before** you commit.

## What gets checked:
- ✅ **Black** - Code formatting
- ✅ **flake8** - Linting (code quality)
- ✅ **isort** - Import sorting
- ✅ **mypy** - Type checking
- ✅ **bandit** - Security issues
- ✅ **General checks** - trailing whitespace, large files, merge conflicts

---

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install git hooks
pre-commit install

# 3. (Optional) Run on all files to test
pre-commit run --all-files
```

---

## Usage

### Automatic (recommended)
Pre-commit hooks run **automatically** when you `git commit`:

```bash
git add .
git commit -m "add feature"

# Hooks run automatically:
# ✓ black - reformatted 2 files
# ✓ flake8 - passed
# ✓ mypy - passed
# → Commit succeeds
```

If hooks fail, **commit is blocked**:
```bash
git commit -m "add feature"

# ✗ black - would reformat 2 files
# ✗ flake8 - found 3 errors
# → Commit blocked, fix issues first
```

### Manual run
Run hooks manually without committing:

```bash
# Check all files
pre-commit run --all-files

# Check specific files
pre-commit run --files api/main.py core/backtest/engine.py

# Run specific hook
pre-commit run black --all-files
```

---

## Skip hooks (use sparingly!)

```bash
# Skip all hooks for emergency commits
git commit -m "hotfix" --no-verify

# Not recommended - fix issues instead!
```

---

## Configuration

### File locations
- **Pre-commit config**: `.pre-commit-config.yaml`
- **Tool config**: `pyproject.toml`

### Customization

**Exclude files from checks:**
```yaml
# .pre-commit-config.yaml
- id: mypy
  exclude: ^(tests/|scripts/)  # skip these directories
```

**Change Black line length:**
```toml
# pyproject.toml
[tool.black]
line-length = 120  # default: 100
```

---

## Troubleshooting

### "command not found: pre-commit"
```bash
pip install pre-commit
```

### Hooks are outdated
```bash
pre-commit autoupdate  # updates to latest versions
```

### Disable hooks temporarily
```bash
pre-commit uninstall  # removes git hooks
pre-commit install    # re-enables
```

---

## What happens when?

| Action | What runs |
|--------|-----------|
| `git commit` | All hooks automatically |
| `git push` | Nothing (hooks only on commit) |
| `pre-commit run --all-files` | All hooks manually |

---

## Benefits

1. **Consistency** - everyone's code looks the same
2. **Early error detection** - catch issues before CI/CD
3. **Code quality** - automated linting and type checking
4. **Security** - bandit finds common vulnerabilities
5. **Fast feedback** - fix issues locally, not in CI

---

## Next Steps

After installing:
1. Run `pre-commit run --all-files` to format existing code
2. Commit the reformatted files
3. From now on, hooks run automatically on every commit
