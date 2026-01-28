# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Oracle Migration Analyzer - Python tools for analyzing Oracle database migration feasibility to cloud platforms (RDS Oracle, Aurora PostgreSQL, Aurora MySQL). Provides SQL/PL-SQL complexity scoring (0-10 scale), AWR/Statspack performance analysis, and automated migration strategy recommendations.

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests with coverage
pytest

# Run a single test file
pytest tests/test_complexity_calculator.py -v

# Run a single test by name
pytest tests/test_plsql_parser.py::TestPLSQLParser::test_package_detection -v

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m property      # Property-based tests (Hypothesis)

# Code formatting
black src tests

# Type checking
mypy src

# Linting
flake8 src tests
```

## CLI Entry Points

```bash
oracle-complexity-analyzer -f <file.sql> -t postgresql -o markdown  # SQL/PL-SQL analysis
dbcsi-analyzer --file <awr.out> --format markdown --analyze-migration  # AWR/Statspack analysis
migration-recommend --reports-dir reports/sample_data  # Migration recommendation
plsql-splitter -f <file.pls> -o output_dir  # Split PL/SQL files
```

## Architecture

### Three Integrated Analyzers

1. **Oracle Complexity Analyzer** (`src/oracle_complexity_analyzer/`): Parses SQL/PL-SQL files, calculates complexity scores using target-specific weights (PostgreSQL/MySQL)

2. **DBCSI Analyzer** (`src/dbcsi/`): Parses AWR/Statspack output, analyzes performance metrics, recommends RDS instance sizing

3. **Migration Recommendation Engine** (`src/migration_recommendation/`): Integrates both analyzers' output, uses decision tree to recommend Replatform vs Refactor strategy

### Data Flow

```
SQL/PL-SQL Files → Parsers (src/parsers/) → ComplexityCalculator (src/calculators/)
                                                      ↓
AWR/Statspack Files → DBCSI Parsers → MigrationAnalyzer
                                                      ↓
                                   AnalysisResultIntegrator (src/migration_recommendation/integrator.py)
                                                      ↓
                                   MigrationDecisionEngine (decision_engine.py)
                                                      ↓
                                   RecommendationReportGenerator (report_generator/)
```

### Key Design Patterns

- **ComplexityCalculator** uses mixin pattern combining `SQLComplexityCalculator` + `PLSQLComplexityCalculator` + `ComplexityMetrics`
- **MigrationDecisionEngine** uses decision matrix (PL/SQL count × complexity threshold)
- Target-specific weights are in `src/oracle_complexity_analyzer/weights.py`
- Oracle-specific features/constants are in `src/oracle_complexity_analyzer/constants.py`

### Decision Engine Thresholds (v2.2.0)

- Replatform SQL/PL-SQL: 6.0
- MySQL PL-SQL: 3.5
- MySQL SQL: 4.0
- MySQL PL/SQL count: 20

## Code Style

- Black formatting: line-length 100
- mypy strict mode enabled
- Python 3.8+ compatibility required
- Documentation primarily in Korean
