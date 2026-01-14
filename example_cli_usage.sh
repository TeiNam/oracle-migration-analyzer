#!/bin/bash
# Oracle Complexity Analyzer CLI 사용 예제

echo "=========================================="
echo "Oracle Complexity Analyzer CLI 사용 예제"
echo "=========================================="
echo ""

# 1. 단일 파일 분석 (PostgreSQL 타겟)
echo "1. 단일 파일 분석 (PostgreSQL 타겟)"
echo "------------------------------------------"
python -m src.oracle_complexity_analyzer \
    -f sample_code/sample_plsql01.sql \
    -t postgresql \
    -o reports
echo ""

# 2. 단일 파일 분석 (MySQL 타겟)
echo "2. 단일 파일 분석 (MySQL 타겟)"
echo "------------------------------------------"
python -m src.oracle_complexity_analyzer \
    -f sample_code/sample_plsql01.sql \
    -t mysql \
    -o reports
echo ""

# 3. 폴더 배치 분석 (PostgreSQL 타겟, 요약만)
echo "3. 폴더 배치 분석 (PostgreSQL 타겟, 요약만)"
echo "------------------------------------------"
python -m src.oracle_complexity_analyzer \
    -d sample_code \
    -t postgresql \
    -o reports
echo ""

# 4. 폴더 배치 분석 (MySQL 타겟, 상세 리포트 포함)
echo "4. 폴더 배치 분석 (MySQL 타겟, 상세 리포트 포함)"
echo "------------------------------------------"
python -m src.oracle_complexity_analyzer \
    -d sample_code \
    -t mysql \
    -o reports \
    --details
echo ""

# 5. 병렬 처리 워커 수 지정 (기본값: 4)
echo "5. 병렬 처리 워커 수 지정 (8개 워커)"
echo "------------------------------------------"
python -m src.oracle_complexity_analyzer \
    -d sample_code \
    -t postgresql \
    -o reports \
    --details \
    --workers 8
echo ""

echo "=========================================="
echo "분석 완료! reports/ 폴더에서 결과 확인"
echo "=========================================="
