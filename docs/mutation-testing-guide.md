# Mutation Testing Guide for Is It Stolen

**Date:** 2025-10-09
**Status:** Implementation Guide

---

## Overview

Mutation testing evaluates test suite quality by introducing small bugs (mutations) into source code and verifying that tests catch them. If tests pass with mutated code, you have a gap in coverage.

### Why Mutation Testing?

- **Code coverage shows lines executed** - but not if they're properly tested
- **Mutation score shows quality** - measures if tests actually verify behavior
- **Find weak tests** - exposes tests that don't properly assert
- **Improve test design** - guides better assertions and edge case coverage

**Example:** A test might execute a line but not verify its output. Code coverage would show 100%, but mutation testing would catch this gap.

---

## Recommended Tool: mutmut

**mutmut** is the most mature Python mutation testing framework.

### Key Features

- ✅ Supports pytest, unittest, nose
- ✅ Fast caching of results
- ✅ HTML reports
- ✅ Focused mutations (operators, conditionals, literals)
- ✅ CI/CD integration

### Installation

```bash
# Add to dev dependencies
poetry add --group dev mutmut
```

### Basic Configuration

Create `.mutmut.toml`:

```toml
[mutmut]
# Paths to mutate
paths_to_mutate = "src/"

# Test command
runner = "poetry run pytest -x --tb=short"

# Directories/files to exclude
exclude = [
    "tests/",
    "alembic/",
    "__init__.py",
]

# Additional pytest options for faster mutation runs
tests_dir = "tests/"
```

---

## Recommended Phased Approach

Given your codebase size (7,038 lines), run mutation testing **incrementally** rather than all at once.

### Phase 1: Start with Domain Layer (Recommended)

**Why domain first?**

- Pure business logic (no I/O)
- Fast tests (no database/network)
- High value (core business rules)
- Isolated (no external dependencies)

**Target modules:**

```bash
src/domain/value_objects/
src/domain/entities/
src/domain/services/
```

**Run mutation testing:**

```bash
# Test a single module
mutmut run --paths-to-mutate=src/domain/value_objects/location.py

# View results
mutmut results

# Show specific mutation
mutmut show <mutation-id>

# Generate HTML report
mutmut html
```

**Expected time:** ~5-10 minutes per value object

### Phase 2: Application Layer

**Target modules:**

```bash
src/application/commands/
src/application/queries/
```

**Why second?**

- Orchestration logic
- Mock dependencies (still fast)
- Critical business flows

**Run mutation testing:**

```bash
mutmut run --paths-to-mutate=src/application/commands/report_stolen_item.py
```

**Expected time:** ~10-20 minutes per command handler

### Phase 3: Infrastructure Layer (Optional)

**Target modules:**

```bash
src/infrastructure/persistence/repositories/
src/infrastructure/config/
```

**Why optional/last?**

- Integration tests are slower
- More external dependencies
- Lower mutation score expected (acceptable)

**Consider skipping:**

- `src/infrastructure/whatsapp/client.py` - External API calls
- Database models - Mostly ORM definitions

---

## Interpreting Results

### Mutation Score

```text
Mutation Score = (Killed Mutations / Total Mutations) × 100
```

**Industry benchmarks:**

- 60-70%: Good
- 70-80%: Very Good
- 80-90%: Excellent
- 90%+: Exceptional (diminishing returns)

### Mutation States

1. **Killed** ✅ - Test failed with mutation (GOOD)

   - Your tests caught the bug

2. **Survived** ⚠️ - Test passed with mutation (BAD)

   - Test gap - mutation wasn't detected

3. **Timeout** ⏱️ - Test took too long

   - Infinite loop introduced by mutation

4. **Suspicious** 🤔 - Inconsistent results
   - Flaky test or non-deterministic code

### Example Output

```bash
$ mutmut results

Total: 127 mutations
Killed: 104 (81.9%)
Survived: 18 (14.2%)
Timeout: 3 (2.4%)
Suspicious: 2 (1.6%)

Mutation Score: 81.9%
```

---

## Common Mutation Types

### 1. Operator Mutations

**Original:**

```python
if latitude > MAX_LATITUDE:
    raise ValueError("Invalid latitude")
```

**Mutated:**

```python
if latitude >= MAX_LATITUDE:  # Changed > to >=
    raise ValueError("Invalid latitude")
```

**How to kill:** Test the boundary value

```python
def test_rejects_latitude_above_maximum():
    with pytest.raises(ValueError):
        Location(latitude=90.1, longitude=0)  # Just above max

def test_accepts_maximum_latitude():
    location = Location(latitude=90.0, longitude=0)  # Exactly at max
    assert location.latitude == 90.0
```

### 2. Literal Mutations

**Original:**

```python
MIN_DESCRIPTION_LENGTH = 10
if len(description) < MIN_DESCRIPTION_LENGTH:
    raise ValueError("Description too short")
```

**Mutated:**

```python
MIN_DESCRIPTION_LENGTH = 11  # Changed constant
```

**How to kill:** Test the boundary

```python
def test_rejects_description_below_minimum():
    with pytest.raises(ValueError):
        StolenItem.create(description="9 chars!!")  # 9 chars

def test_accepts_minimum_length_description():
    item = StolenItem.create(description="10 chars!!")  # Exactly 10
    assert item.description == "10 chars!!"
```

### 3. Boolean Mutations

**Original:**

```python
if is_verified and has_police_reference:
    return VerificationStatus.CONFIRMED
```

**Mutated:**

```python
if is_verified or has_police_reference:  # Changed and to or
    return VerificationStatus.CONFIRMED
```

**How to kill:** Test all combinations

```python
def test_requires_both_verification_and_police_reference():
    # Both true
    assert get_status(True, True) == VerificationStatus.CONFIRMED

    # Only one true
    assert get_status(True, False) != VerificationStatus.CONFIRMED
    assert get_status(False, True) != VerificationStatus.CONFIRMED

    # Both false
    assert get_status(False, False) != VerificationStatus.CONFIRMED
```

### 4. Return Value Mutations

**Original:**

```python
def distance_to(self, other: Location) -> float:
    # ... calculation ...
    return distance_km
```

**Mutated:**

```python
def distance_to(self, other: Location) -> float:
    # ... calculation ...
    return None  # Changed return value
```

**How to kill:** Assert the return value

```python
def test_calculates_distance_between_locations():
    london = Location(51.5074, -0.1278)
    paris = Location(48.8566, 2.3522)

    distance = london.distance_to(paris)

    assert distance is not None  # Catches None mutation
    assert isinstance(distance, float)
    assert 340 < distance < 350  # Roughly 344km
```

---

## Practical Example: Location Value Object

### Before Mutation Testing

```python
# src/domain/value_objects/location.py
@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not MIN_LATITUDE <= self.latitude <= MAX_LATITUDE:
            raise ValueError("Invalid latitude")
```

**Test (weak):**

```python
def test_creates_location():
    location = Location(51.5074, -0.1278)
    assert location.latitude == 51.5074
```

**Mutation survivors:**

- Changing `<=` to `<` in bounds check
- Changing `MIN_LATITUDE` value
- Changing error message

### After Mutation Testing (Improved)

```python
def test_creates_valid_location():
    """Should create location with valid coordinates."""
    location = Location(51.5074, -0.1278)
    assert location.latitude == 51.5074
    assert location.longitude == -0.1278

def test_rejects_latitude_below_minimum():
    """Should reject latitude below -90."""
    with pytest.raises(ValueError, match="Invalid latitude"):
        Location(-90.1, 0)

def test_rejects_latitude_above_maximum():
    """Should reject latitude above 90."""
    with pytest.raises(ValueError, match="Invalid latitude"):
        Location(90.1, 0)

def test_accepts_minimum_latitude():
    """Should accept latitude of exactly -90."""
    location = Location(-90.0, 0)
    assert location.latitude == -90.0

def test_accepts_maximum_latitude():
    """Should accept latitude of exactly 90."""
    location = Location(90.0, 0)
    assert location.latitude == 90.0
```

**Result:** All mutations killed ✅

---

## Integration with CI/CD

### Option 1: Run on Specific Paths (Recommended)

Add to `.github/workflows/ci.yml`:

```yaml
mutation-testing:
  name: Mutation Testing (Domain Layer)
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v5

    - name: Set up Python
      uses: actions/setup-python@v6
      with:
        python-version: "3.13"

    - name: Install Poetry
      uses: snok/install-poetry@v1

    - name: Install dependencies
      run: poetry install

    - name: Run mutation testing on domain layer
      run: |
        poetry run mutmut run --paths-to-mutate=src/domain/
        poetry run mutmut results
      continue-on-error: true # Don't fail build initially

    - name: Generate mutation report
      if: always()
      run: poetry run mutmut html

    - name: Upload mutation report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: mutation-report
        path: html/
```

### Option 2: Weekly Full Scan

```yaml
name: Mutation Testing (Full)

on:
  schedule:
    - cron: "0 2 * * 0" # Sundays at 2am
  workflow_dispatch: # Manual trigger

jobs:
  mutation-test:
    name: Full Mutation Testing
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      # ... same as above but without --paths-to-mutate filter
```

### Option 3: Pre-commit Hook (Optional)

For critical modules, add local mutation testing:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: mutation-test-value-objects
      name: Mutation Test Value Objects
      entry: poetry run mutmut run --paths-to-mutate=src/domain/value_objects/
      language: system
      pass_filenames: false
      stages: [manual] # Only run when explicitly called
```

Run with: `git commit --no-verify` to skip, or `pre-commit run mutation-test-value-objects --all-files`

---

## Best Practices

### 1. Start Small

- Begin with one module (e.g., `location.py`)
- Learn the tool and patterns
- Expand gradually

### 2. Focus on High-Value Code

Priority order:

1. Domain value objects and entities
2. Domain services (business logic)
3. Application command handlers
4. Critical infrastructure (repositories)

### 3. Don't Chase 100%

- 80-90% mutation score is excellent
- Some mutations are equivalent (code style changes)
- Diminishing returns after 90%

### 4. Use Mutations to Guide Test Design

- Survived mutation = missing test case
- Add specific test for that scenario
- Re-run mutations to verify

### 5. Exclude Low-Value Code

```toml
[mutmut]
exclude = [
    "tests/",
    "alembic/",
    "__init__.py",
    "*/models.py",  # ORM models
    "*/schemas.py",  # Pydantic schemas
]
```

### 6. Cache Results

mutmut caches results in `.mutmut-cache`:

- Add to `.gitignore`
- Speeds up re-runs significantly
- Only re-tests changed code

---

## Makefile Commands

Add to `Makefile`:

```makefile
# Mutation testing
mutation-test: ## Run mutation testing on domain layer
  poetry run mutmut run --paths-to-mutate=src/domain/

mutation-test-all: ## Run mutation testing on entire codebase (slow)
  poetry run mutmut run

mutation-results: ## Show mutation testing results
  poetry run mutmut results

mutation-show: ## Show details of a specific mutation (usage: make mutation-show id=1)
  poetry run mutmut show $(id)

mutation-html: ## Generate HTML report of mutation testing
  poetry run mutmut html
  @echo "Report generated in html/index.html"

mutation-clean: ## Clean mutation testing cache
  rm -rf .mutmut-cache html/
```

---

## Expected Timeline

### Initial Setup

- Install and configure: **30 minutes**
- First run on one module: **15 minutes**
- Learn patterns: **1 hour**

### Domain Layer (Phased)

- Value objects (5 modules): **2-3 hours**
- Entities (2 modules): **2-3 hours**
- Domain services: **1-2 hours**
- **Total: ~1 day**

### Application Layer (Phased)

- Command handlers: **3-4 hours**
- Query handlers: **2-3 hours**
- **Total: 1 day**

### Infrastructure Layer (Optional)

- Repositories: **4-5 hours**
- Configuration: **1-2 hours**
- **Total: 1 day**

#### **Full implementation: 2-3 days spread over 2-3 weeks**

---

## Example Workflow

### Week 1: Domain Value Objects

```bash
# Day 1: Setup and Location
poetry add --group dev mutmut
mutmut run --paths-to-mutate=src/domain/value_objects/location.py
mutmut results  # 78% - need better boundary tests
# Add boundary tests
mutmut run --paths-to-mutate=src/domain/value_objects/location.py
mutmut results  # 92% ✅

# Day 2: Phone Number
mutmut run --paths-to-mutate=src/domain/value_objects/phone_number.py
# ... improve tests ...

# Day 3: Item Category
mutmut run --paths-to-mutate=src/domain/value_objects/item_category.py
# ... improve tests ...
```

### Week 2: Domain Entities

```bash
# Day 1: StolenItem (large)
mutmut run --paths-to-mutate=src/domain/entities/stolen_item.py
# ... improve tests ...
```

### Week 3: Application Commands

```bash
# Day 1: ReportStolenItem
mutmut run --paths-to-mutate=src/application/commands/report_stolen_item.py
# ... improve tests ...
```

---

## Advanced: Cosmic Ray (Alternative)

If mutmut doesn't meet needs, consider **Cosmic Ray**:

```bash
poetry add --group dev cosmic-ray
```

Pros:

- More mutation operators
- Better parallelization
- SQLite result storage

Cons:

- More complex configuration
- Slower for large codebases

---

## Key Metrics to Track

### Per Module

- Total mutations
- Mutation score %
- Time to run
- Improvement over time

### Overall

- Average mutation score
- Coverage of critical paths
- Test suite effectiveness trends

### Example Report

```bash
Domain Layer Mutation Testing Report - 2025-10-09

Module                    | Mutations | Score | Time
--------------------------|-----------|-------|------
location.py               |       45  | 92%   | 3m
phone_number.py           |       38  | 89%   | 2m
item_category.py          |       25  | 94%   | 1m
stolen_item.py            |      127  | 81%   | 8m
--------------------------|-----------|-------|------
TOTAL                     |      235  | 87%   | 14m

Target: 85%+ ✅
```

---

## Troubleshooting

### Issue: Mutation testing too slow

**Solution:**

```bash
# Run in parallel (if available)
mutmut run --runner="pytest -x -n auto"

# Test only changed files
mutmut run --paths-to-mutate=src/domain/value_objects/location.py

# Use faster test runner
mutmut run --runner="pytest -x --tb=line"
```

### Issue: Too many equivalent mutations

**Solution:**

```toml
[mutmut]
# Skip specific mutation types if they create too many equivalents
skip_operators = ["ArithmeticMutation"]
```

### Issue: Flaky tests causing suspicious mutations

**Solution:**

1. Fix flaky tests first
2. Use `pytest-randomly` to expose flakiness
3. Mock time/random operations properly

---

## Conclusion

Mutation testing is a powerful technique to validate test quality. For your codebase:

1. **Start with domain layer** - highest value, fastest feedback
2. **Target 80-90% mutation score** - excellent quality benchmark
3. **Run incrementally** - don't try to do everything at once
4. **Use insights to improve tests** - focus on behavior verification
5. **Integrate into workflow** - weekly runs or pre-release checks

**Expected benefit:** Discover 10-20% more test gaps beyond code coverage, significantly improving test suite reliability.

---

_Guide created: 2025-10-09_
_Tool: mutmut v2.x_
_Target: Python 3.13 with pytest_
