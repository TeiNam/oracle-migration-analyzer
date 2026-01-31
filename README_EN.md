# Oracle Migration Analyzer

A collection of Python-based tools for analyzing Oracle database migration complexity.

> [한국어](./README.md)

## Tools

### 1. Oracle Complexity Analyzer
Analyzes the complexity of Oracle SQL and PL/SQL code and evaluates migration difficulty to PostgreSQL or MySQL on a 0-10 scale.

### 2. DBCSI Analyzer (AWR/Statspack)
Parses DBCSI AWR or Statspack result files to analyze Oracle database performance metrics and resource usage, and evaluates migration difficulty to RDS for Oracle, Aurora MySQL, and Aurora PostgreSQL.

### 3. Migration Recommendation Engine
Integrates results from the DBCSI analyzer (performance metrics) and SQL/PL/SQL analyzer (code complexity) to recommend the optimal migration strategy. Uses a decision tree to select the most suitable strategy among Replatform (RDS for Oracle SE2), Refactor to Aurora MySQL, and Refactor to Aurora PostgreSQL, and generates a comprehensive report including recommendation rationale, alternative strategies, risk factors, and migration roadmap.

---

## Installation

```bash
# Clone repository
git clone <repository-url>
cd oracle-migration-analyzer

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package (development mode)
pip install -e .
```

---

## 1. Oracle Complexity Analyzer

### Key Features

- ✅ **SQL Query Complexity Analysis**: Evaluates structural complexity across 6 categories
- ✅ **PL/SQL Object Analysis**: Analyzes packages, procedures, functions, triggers, etc.
- ✅ **Target DB-Specific Weights**: Optimized complexity calculation for PostgreSQL/MySQL
- ✅ **Oracle-Specific Feature Detection**: Automatically detects CONNECT BY, PIVOT, analytic functions, etc.
- ✅ **Conversion Guide**: Provides target DB-specific alternatives for detected Oracle features
- ✅ **Batch Folder Analysis**: Fast analysis of large files with parallel processing
- ✅ **Multiple Output Formats**: Generates JSON and Markdown reports

### CLI Usage

#### Single File Analysis

```bash
# Analyze SQL file with PostgreSQL target (default)
oracle-complexity-analyzer -f query.sql

# Analyze PL/SQL file with MySQL target
oracle-complexity-analyzer -f package.pls -t mysql

# Save results as Markdown file
oracle-complexity-analyzer -f query.sql -o markdown

# Save results as JSON file
oracle-complexity-analyzer -f query.sql -o json
```

#### Batch Folder Analysis

```bash
# Analyze all SQL/PL/SQL files in a folder
oracle-complexity-analyzer -d sample_code -t postgresql -o markdown

# Analyze folder with MySQL as target
oracle-complexity-analyzer -d /path/to/sql/files -t mysql -o markdown

# Specify number of parallel workers (default: CPU cores)
oracle-complexity-analyzer -d sample_code -w 8 -o markdown
```

#### Output Structure

Analysis results are automatically saved **reflecting the original file's folder structure**:

**When parent folder exists** (e.g., `sample_code/file.sql`, `MKDB/file.sql`):
```
reports/
└── {original_folder_name}/    # Automatically reflects parent folder name
    ├── PGSQL/
    │   ├── sql_complexity_PGSQL.md      # Integrated report (batch analysis)
    │   ├── sql_complexity_PGSQL.json    # JSON report (batch analysis)
    │   ├── file1.md                     # Individual file report
    │   ├── file1.json
    │   └── ...
    └── MySQL/
        ├── sql_complexity_MySQL.md
        ├── sql_complexity_MySQL.json
        ├── file1.md
        └── ...
```

**When no parent folder exists** (e.g., `file.sql` in root directory):
```
reports/
└── YYYYMMDD/              # Date folder (e.g., 20260118)
    ├── file_postgresql.json
    ├── file_postgresql.md
    ├── file_mysql.json
    └── file_mysql.md
```

**Examples**:
- Analyzing `sample_code/query.sql` → `reports/sample_code/PGSQL/query.json`
- Analyzing `MKDB/procedure.pls` → `reports/MKDB/MySQL/procedure.md`
- Analyzing `test.sql` → `reports/20260118/test_postgresql.json`

### Command Line Options

**Required Options (choose one)**:
- `-f FILE`, `--file FILE`: Path to single SQL/PL/SQL file to analyze
- `-d DIR`, `--directory DIR`: Path to folder to analyze (including subfolders)

**Optional Options**:
- `-t DB`, `--target DB`: Select target database
  - `postgresql`, `pg`: PostgreSQL (default)
  - `mysql`, `my`: MySQL

- `-o FORMAT`, `--output FORMAT`: Select output format
  - `console`: Console output only (default)
  - `json`: Save as JSON file
  - `markdown`: Save as Markdown file
  - `both`: Console output + JSON/Markdown files

- `-w N`, `--workers N`: Number of parallel workers (for folder analysis; default: CPU cores)

### Complexity Level Classification

| Score Range | Level | Recommendation |
|------------|-------|----------------|
| 0-1 | Very Simple | Automatic conversion |
| 1-3 | Simple | Function replacement |
| 3-5 | Medium | Partial rewrite |
| 5-7 | Complex | Significant rewrite |
| 7-9 | Very Complex | Mostly rewrite |
| 9-10 | Extremely Complex | Complete redesign |

---

## 2. DBCSI Analyzer (AWR/Statspack)

### Key Features

- ✅ **AWR/Statspack File Parsing**: Automatic parsing of DBCSI result files (.out)
- ✅ **Percentile-Based Analysis**: Utilizes percentile metrics like P99, P95, P90 (AWR)
- ✅ **Function-Specific I/O Analysis**: Statistics by function like LGWR, DBWR, Direct I/O (AWR)
- ✅ **Workload Pattern Analysis**: Classification of CPU-intensive/I/O-intensive workloads (AWR)
- ✅ **Buffer Cache Efficiency**: Hit rate analysis and optimization recommendations (AWR)
- ✅ **Precise Instance Sizing**: RDS instance recommendations based on P99 metrics
- ✅ **Migration Difficulty Calculation**: 0-10 scale difficulty evaluation by target DB
- ✅ **Batch File Analysis**: Bulk processing of multiple files
- ✅ **Multiple Output Formats**: Generates JSON and Markdown reports

### CLI Usage

#### Single File Analysis

```bash
# Basic analysis (all target DBs)
dbcsi-analyzer --file sample_code/dbcsi_awr_sample01.out

# Analyze specific target DB only
dbcsi-analyzer --file awr_sample.out --target aurora-postgresql

# Generate detailed report (including AWR-specific sections)
dbcsi-analyzer --file awr_sample.out --detailed

# Output in JSON format
dbcsi-analyzer --file awr_sample.out --format json

# Include migration analysis
dbcsi-analyzer --file awr_sample.out --analyze-migration --detailed
```

#### Batch File Analysis

```bash
# Analyze all AWR/Statspack files in a directory
dbcsi-analyzer --directory sample_code --format markdown

# Batch analysis with a specific target DB
dbcsi-analyzer --directory /path/to/files --target aurora-postgresql
```

#### Output Structure

Analysis results are automatically saved **reflecting the original file's folder structure**:

**When parent folder exists** (e.g., `sample_code/awr.out`):
```
reports/
└── {original_folder_name}/    # Automatically reflects parent folder name
    ├── dbcsi_awr_sample01.md
    ├── dbcsi_statspack_sample01.md
    └── ...
```

**When no parent folder exists** (e.g., `awr.out` in root directory):
```
reports/
└── YYYYMMDD/              # Date folder (e.g., 20260118)
    ├── awr_analysis.md
    └── ...
```

### Command Line Options

**Required Options (choose one)**:
- `--file FILE`: Path to single AWR/Statspack file to analyze
- `--directory DIR`: Path to directory to analyze (all .out files)

**Optional Options**:
- `--format FORMAT`: Select output format
  - `json`: JSON format
  - `markdown`: Markdown format (default)

- `--target TARGET`: Select target database
  - `rds-oracle`: RDS for Oracle
  - `aurora-mysql`: Aurora MySQL 8.0
  - `aurora-postgresql`: Aurora PostgreSQL 16
  - `all`: All targets (default)

- `--analyze-migration`: Include migration difficulty analysis

- `--detailed`: Generate a detailed report including AWR-specific sections

- `--compare FILE1 FILE2`: Compare two AWR files

- `--percentile PERCENTILE`: Percentile to use for analysis
  - `99`: P99 (default)
  - `95`: P95
  - `90`: P90
  - `75`: P75
  - `median`: Median
  - `average`: Average

- `--language LANG`: Report language
  - `ko`: Korean (default)
  - `en`: English

### AWR vs Statspack Differences

| Feature | Statspack | AWR |
|---------|-----------|-----|
| Basic Performance Metrics | ✅ | ✅ |
| Percentile Metrics (P99, P95) | ❌ | ✅ |
| Function-Specific I/O Statistics | ❌ | ✅ |
| Workload Pattern Analysis | ❌ | ✅ |
| Buffer Cache Efficiency | ❌ | ✅ |
| Time-Based Analysis | ❌ | ✅ |
| Precise Instance Sizing | ✅ | ✅✅ (More accurate) |
| Analysis Reliability | Medium | High |

---

## 3. Migration Recommendation Engine

### Key Features

- ✅ **Analysis Result Integration**: Integrates DBCSI (performance metrics) and SQL/PL/SQL (code complexity) analysis results
- ✅ **Decision Engine**: Automatically determines the optimal strategy based on code complexity and performance metrics
- ✅ **3 Migration Strategies**:
  - **Replatform**: RDS for Oracle SE2 Single (minimize code changes)
  - **Refactor to Aurora MySQL**: Migrate simple SQL/PL/SQL to the application level
  - **Refactor to Aurora PostgreSQL**: Convert complex PL/SQL to PL/pgSQL
- ✅ **Comprehensive Recommendation Report**: Includes recommendation rationale, alternative strategies, risk factors, and migration roadmap
- ✅ **Executive Summary**: Non-technical summary for executives
- ✅ **Multiple Output Formats**: Generates Markdown and JSON reports
- ✅ **Korean/English Support**: Multilingual report generation

### CLI Usage

#### Basic Usage

```bash
# Generate a recommendation report by specifying a folder in the reports directory
migration-recommend --reports-dir reports/sample_code

# Output in JSON format
migration-recommend --reports-dir reports/sample_code --format json

# Generate an English report
migration-recommend --reports-dir reports/sample_code --language en
```

#### Legacy Mode (Specify Individual Files)

```bash
# Directly specify the DBCSI file and SQL directory
migration-recommend \
  --dbcsi sample_code/dbcsi_awr_sample01.out \
  --sql-dir sample_code \
  --output reports/recommendation.md

# Recommendation based on SQL/PL/SQL analysis only (without DBCSI performance metrics)
migration-recommend \
  --sql-dir sample_code \
  --output reports/recommendation.md
```

#### Output Structure

Recommendation reports are generated at the following location:

```
reports/
└── {analysis_target_folder}/
    └── migration_recommendation.md    # Recommendation report
```

### Command Line Options

**Required Options (choose one)**:
- `--reports-dir DIR`: Path to folder containing analysis reports (recommended)
- `--sql-dir DIR`: Directory path containing SQL/PL-SQL files (legacy mode)

**Optional Options**:
- `--dbcsi FILE`: DBCSI analysis result file path (legacy mode)
- `--format FORMAT`: Select output format
  - `markdown`: Markdown format (default)
  - `json`: JSON format
- `--output PATH`: Output file path (uses an automatic path if not specified)
- `--language LANG`: Report language
  - `ko`: Korean (default)
  - `en`: English
- `--target TARGET`: Target DB for SQL/PL/SQL analysis (default: postgresql)
  - `postgresql`: Aurora PostgreSQL
  - `mysql`: Aurora MySQL

### Decision Tree

The migration strategy selects one of three options based on complexity and code characteristics:

| Strategy | Condition Summary |
|----------|-------------------|
| **Replatform** (RDS Oracle SE2) | Very high complexity or large codebase |
| **Aurora MySQL** | Low complexity with simple CRUD operations |
| **Aurora PostgreSQL** | Medium complexity or PostgreSQL-friendly features |

> 📖 For detailed decision logic and diagrams, see the [Decision Engine Documentation](docs/WHAT_IS_ORACLE_MIGRATION_ANALYZER.md#3-마이그레이션-전략-의사결정-트리).

### Strategy Characteristics

#### Replatform (RDS for Oracle SE2)

**Advantages**:
- Minimal code changes
- Fast migration (8-12 weeks)
- High compatibility

**Disadvantages**:
- Ongoing Oracle license costs
- Single instance only (no RAC support)
- High long-term TCO

**Suitable When**:
- Average SQL complexity >= 7.5 or PL/SQL complexity >= 7.0
- Complex object ratio >= 25% (min 70 objects)
- High complexity objects >= 50
- PL/SQL objects >= 500
- High risk from code changes

#### Refactor to Aurora MySQL

**Advantages**:
- Open source-based (no license costs)
- Low TCO
- Optimal for simple SQL processing

**Disadvantages**:
- All PL/SQL must be migrated to the application level
- Cannot use MySQL stored procedures
- No BULK operation support

**Suitable When**:
- Average SQL complexity <= 4.5
- Average PL/SQL complexity <= 4.0
- PL/SQL objects < 50
- BULK operations < 10
- PostgreSQL preference score < 2

#### Refactor to Aurora PostgreSQL

**Advantages**:
- PL/pgSQL is 70-75% Oracle-compatible
- BULK operation alternatives available
- Advanced feature support

**Disadvantages**:
- PL/SQL conversion work required
- BULK operation performance difference (20-50%)
- Some Oracle features are not supported

**Suitable When**:
- When MySQL conditions are not met (default choice)
- BULK operations >= 10
- PostgreSQL preference score >= 2
- Advanced features used (PIPELINED, REF CURSOR, etc.)
- External package dependencies (DBMS_LOB, UTL_FILE, etc.)

---

## Integrated Workflow

### Complete Analysis Process

```bash
# Step 1: SQL/PL-SQL complexity analysis
oracle-complexity-analyzer -d sample_code -t postgresql -o markdown

# Step 2: DBCSI performance analysis
dbcsi-analyzer --directory sample_code --format markdown

# Step 3: Generate migration recommendation report
migration-recommend --reports-dir reports/sample_code
```

### Report Folder Structure

Analysis results **automatically reflect the original file's folder structure**:

```
reports/
└── {original_folder_name}/    # e.g., sample_code, MKDB, etc.
    ├── PGSQL/
    │   ├── sql_complexity_PGSQL.md      # SQL complexity integrated report
    │   ├── sql_complexity_PGSQL.json
    │   ├── query1.md                    # Individual SQL file report
    │   └── ...
    ├── MySQL/
    │   ├── sql_complexity_MySQL.md
    │   └── ...
    ├── dbcsi_awr_sample01.md            # DBCSI performance report
    ├── dbcsi_statspack_sample01.md
    └── migration_recommendation.md       # Final recommendation report
```

**Folder Structure Rules**:
- If the original file has a parent folder, use that folder name (e.g., `sample_code/file.sql` → `reports/sample_code/`)
- If there is no parent folder, use a date folder (e.g., `file.sql` → `reports/20260118/`)

---

## Python API Usage

While the CLI is the primary interface, you can also use it directly as a library in Python code.

### Oracle Complexity Analyzer

```python
from src.oracle_complexity_analyzer import (
    OracleComplexityAnalyzer,
    BatchAnalyzer,
    TargetDatabase
)

# Create analyzer
analyzer = OracleComplexityAnalyzer(
    target_database=TargetDatabase.POSTGRESQL
)

# Batch folder analysis
batch_analyzer = BatchAnalyzer(analyzer, max_workers=4)
batch_result = batch_analyzer.analyze_folder("sample_code")

# Save results
batch_analyzer.export_batch_markdown(batch_result)
```

### DBCSI Analyzer

```python
from src.dbcsi.parser import StatspackParser
from src.dbcsi.migration_analyzer import MigrationAnalyzer
from src.dbcsi.result_formatter import StatspackResultFormatter

# Parse AWR file
parser = StatspackParser("sample_code/dbcsi_awr_sample01.out")
awr_data = parser.parse()

# Migration analysis
analyzer = MigrationAnalyzer(awr_data)
analysis_results = analyzer.analyze()

# Generate Markdown report
markdown_output = StatspackResultFormatter.to_markdown(
    awr_data, 
    analysis_results
)
```

### Migration Recommendation

```python
from src.migration_recommendation import (
    AnalysisResultIntegrator,
    MigrationDecisionEngine,
    RecommendationReportGenerator,
    MarkdownReportFormatter
)

# Integrate analysis results
integrator = AnalysisResultIntegrator()
integrated_result = integrator.integrate(
    dbcsi_result=dbcsi_data,
    sql_analysis=sql_results,
    plsql_analysis=plsql_results
)

# Generate recommendation report
decision_engine = MigrationDecisionEngine()
report_generator = RecommendationReportGenerator(decision_engine)
recommendation = report_generator.generate_recommendation(integrated_result)

# Output Markdown report
formatter = MarkdownReportFormatter()
markdown_report = formatter.format(recommendation, language="ko")
```

See the `example_*.py` files for detailed examples.

---

## Documentation

For more details, refer to the documents in the `docs/` folder:

- `complexity_postgresql.md`: PostgreSQL target complexity calculation formula
- `complexity_mysql.md`: MySQL target complexity calculation formula
- `oracle_complexity_formula.md`: Overall complexity calculation formula
- `migration_guide_aurora_pg16.md`: Aurora PostgreSQL 16 migration guide
- `migration_guide_aurora_mysql80.md`: Aurora MySQL 8.0 migration guide

---

## Testing

```bash
# Run all tests
pytest

# Test with coverage
pytest --cov=src --cov-report=html

# Run specific test only
pytest tests/test_sql_parser.py

# Run property-based tests only
pytest -m property
```

---

## License

MIT License

---

## Contributing

Issues and pull requests are welcome!

---

## Contact

If you encounter any problems or have questions, please open an issue.
