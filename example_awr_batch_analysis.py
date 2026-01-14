#!/usr/bin/env python3
"""
AWR 배치 파일 분석 예제

이 스크립트는 여러 AWR 파일을 일괄 분석하여 추세를 파악하고
배치 리포트를 생성하는 방법을 보여줍니다.

사용법:
    python example_awr_batch_analysis.py
"""

import os
from datetime import datetime
from pathlib import Path

from src.dbcsi.batch_analyzer import BatchAnalyzer
from src.dbcsi.data_models import TargetDatabase


def main():
    """AWR 배치 파일 분석 예제"""
    
    # 1. AWR 파일 디렉토리 설정
    awr_directory = "sample_code"
    
    if not os.path.exists(awr_directory):
        print(f"❌ 디렉토리를 찾을 수 없습니다: {awr_directory}")
        return
    
    print("=" * 80)
    print("📊 AWR 배치 파일 분석 예제")
    print("=" * 80)
    print(f"\n분석 디렉토리: {awr_directory}\n")
    
    # 2. AWR 파일 검색
    awr_files = list(Path(awr_directory).glob("*awr*.out"))
    
    if not awr_files:
        print(f"⚠️  AWR 파일을 찾을 수 없습니다. Statspack 파일로 대체합니다.")
        awr_files = list(Path(awr_directory).glob("*statspack*.out"))
    
    if not awr_files:
        print(f"❌ 분석할 파일을 찾을 수 없습니다.")
        return
    
    print(f"발견된 파일: {len(awr_files)}개")
    for f in awr_files:
        print(f"  - {f.name}")
    print()
    
    # 3. 배치 분석 실행
    print("=" * 80)
    print("🔍 배치 분석 실행 중...")
    print("=" * 80)
    print()
    
    # 배치 분석기 초기화
    analyzer = BatchAnalyzer(awr_directory)
    
    # 타겟 DB 선택
    target = TargetDatabase.RDS_ORACLE
    
    # 배치 분석 실행
    batch_result = analyzer.analyze_batch(
        target=target,
        analyze_migration=True
    )
    
    print(f"✅ 배치 분석 완료\n")
    
    # 4. 결과 요약 출력
    print("=" * 80)
    print("📋 배치 분석 결과 요약")
    print("=" * 80)
    print(f"\n전체 파일 수: {batch_result.total_files}")
    print(f"분석 성공: {batch_result.successful_files}")
    print(f"분석 실패: {batch_result.failed_files}")
    
    if batch_result.successful_files > 0:
        # 평균 점수 계산 - migration_analysis에서 첫 번째 타겟의 점수 사용
        scores = []
        for r in batch_result.file_results:
            if r.migration_analysis:
                # 첫 번째 타겟의 점수 사용
                first_complexity = next(iter(r.migration_analysis.values()))
                scores.append(first_complexity.score)
        
        if scores:
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            print(f"\n평균 난이도 점수: {avg_score:.2f} / 10.0")
            print(f"최소 난이도 점수: {min_score:.2f}")
            print(f"최대 난이도 점수: {max_score:.2f}")
            
            # 난이도 레벨별 분포
            level_counts = {}
            for result in batch_result.file_results:
                if result.migration_analysis:
                    first_complexity = next(iter(result.migration_analysis.values()))
                    level = first_complexity.level
                    level_counts[level] = level_counts.get(level, 0) + 1
            
            print(f"\n난이도 레벨별 분포:")
            for level, count in level_counts.items():
                percentage = (count / len(scores)) * 100
                print(f"  - {level}: {count}개 ({percentage:.1f}%)")
            
            # 상위 복잡도 파일
            sorted_results = sorted(
                [(r, next(iter(r.migration_analysis.values())).score) 
                 for r in batch_result.file_results if r.migration_analysis],
                key=lambda x: x[1],
                reverse=True
            )
            
            print(f"\n복잡도 높은 파일 Top 5:")
            for i, (result, score) in enumerate(sorted_results[:5], 1):
                print(f"  {i}. {Path(result.filepath).name}: {score:.2f}")
    
    # 실패한 파일
    failed_results = [r for r in batch_result.file_results if r.error_message]
    if failed_results:
        print(f"\n실패한 파일:")
        for result in failed_results:
            print(f"  - {Path(result.filepath).name}: {result.error_message}")
    
    print()
    
    # 5. 추세 분석 (파일이 여러 개인 경우)
    if batch_result.successful_files > 1:
        print("=" * 80)
        print("📈 추세 분석")
        print("=" * 80)
        print()
        
        # 시간순 정렬 (파일명 기준)
        sorted_results = sorted(
            [r for r in batch_result.file_results if r.migration_analysis],
            key=lambda x: x.filepath
        )
        
        print("시간별 난이도 변화:")
        for result in sorted_results:
            file_name = Path(result.filepath).name
            first_complexity = next(iter(result.migration_analysis.values()))
            print(f"  - {file_name}: {first_complexity.score:.2f}")
        
        # 평균 대비 변화
        if len(sorted_results) >= 2:
            first_complexity = next(iter(sorted_results[0].migration_analysis.values()))
            last_complexity = next(iter(sorted_results[-1].migration_analysis.values()))
            first_score = first_complexity.score
            last_score = last_complexity.score
            change = last_score - first_score
            
            print(f"\n난이도 변화:")
            print(f"  - 초기: {first_score:.2f}")
            print(f"  - 최종: {last_score:.2f}")
            print(f"  - 변화량: {change:+.2f}")
            
            if change > 0:
                print(f"  ⚠️  난이도가 증가했습니다. 시스템 복잡도가 높아지고 있습니다.")
            elif change < 0:
                print(f"  ✅ 난이도가 감소했습니다. 최적화가 진행되고 있습니다.")
            else:
                print(f"  ➡️  난이도가 유지되고 있습니다.")
        
        print()
    
    # 6. 리포트 저장
    print("=" * 80)
    print("💾 배치 리포트 저장")
    print("=" * 80)
    
    # 출력 디렉토리 생성
    output_dir = "reports"
    date_dir = datetime.now().strftime("%Y%m%d")
    full_output_dir = os.path.join(output_dir, date_dir)
    os.makedirs(full_output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 배치 요약 리포트 저장
    summary_path = os.path.join(full_output_dir, f"batch_summary_{timestamp}.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# AWR 배치 분석 리포트\n\n")
        f.write(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 요약\n\n")
        f.write(f"- 전체 파일 수: {batch_result.total_files}\n")
        f.write(f"- 분석 성공: {batch_result.successful_files}\n")
        f.write(f"- 분석 실패: {batch_result.failed_files}\n")
        
        if batch_result.successful_files > 0:
            # 평균 점수 계산
            scores = []
            for r in batch_result.file_results:
                if r.migration_analysis:
                    first_complexity = next(iter(r.migration_analysis.values()))
                    scores.append(first_complexity.score)
            
            if scores:
                avg_score = sum(scores) / len(scores)
                f.write(f"- 평균 난이도: {avg_score:.2f}\n\n")
                
                # 난이도 레벨별 분포
                level_counts = {}
                for result in batch_result.file_results:
                    if result.migration_analysis:
                        first_complexity = next(iter(result.migration_analysis.values()))
                        level = first_complexity.level
                        level_counts[level] = level_counts.get(level, 0) + 1
                
                f.write(f"## 난이도 레벨별 분포\n\n")
                for level, count in level_counts.items():
                    percentage = (count / len(scores)) * 100
                    f.write(f"- {level}: {count}개 ({percentage:.1f}%)\n")
                
                # 상위 복잡도 파일
                sorted_results = sorted(
                    [(r, next(iter(r.migration_analysis.values())).score) 
                     for r in batch_result.file_results if r.migration_analysis],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                f.write(f"\n## 복잡도 높은 파일 Top 10\n\n")
                for i, (result, score) in enumerate(sorted_results[:10], 1):
                    f.write(f"{i}. {Path(result.filepath).name}: {score:.2f}\n")
    
    print(f"✅ 배치 요약 리포트 저장: {summary_path}")
    
    # 개별 파일 리포트 저장 (선택적)
    successful_results = [r for r in batch_result.file_results if r.migration_analysis]
    if successful_results:
        for result in successful_results:
            file_name = Path(result.filepath).stem
            individual_path = os.path.join(full_output_dir, f"{file_name}_{timestamp}.md")
            
            first_complexity = next(iter(result.migration_analysis.values()))
            
            with open(individual_path, "w", encoding="utf-8") as f:
                f.write(f"# {file_name} 분석 리포트\n\n")
                f.write(f"난이도 점수: {first_complexity.score:.2f} / 10.0\n")
                f.write(f"난이도 레벨: {first_complexity.level}\n\n")
                f.write(f"## 권장사항\n\n")
                for rec in first_complexity.recommendations:
                    f.write(f"- {rec}\n")
        
        print(f"✅ 개별 파일 리포트 저장: {len(successful_results)}개")
    
    print()
    print("=" * 80)
    print("✅ 배치 분석 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
