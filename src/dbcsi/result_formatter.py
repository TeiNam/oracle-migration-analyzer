"""
Statspack Result Formatter

Statspack 분석 결과를 JSON 및 Markdown 형식으로 출력하는 모듈입니다.
Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 14.1, 14.2, 14.3, 14.4, 14.5를 구현합니다.
"""

import json
import os
from datetime import datetime
from typing import Union, Dict, Any
from pathlib import Path

from src.dbcsi.data_models import (
    StatspackData,
    MigrationComplexity,
    TargetDatabase,
    statspack_to_dict,
    dict_to_statspack,
    migration_complexity_to_dict,
    dict_to_migration_complexity
)


class StatspackResultFormatter:
    """Statspack 분석 결과 포맷터
    
    Requirements:
    - 13.1: JSON 형식 출력
    - 13.2: Markdown 형식 출력
    - 13.3: JSON 역직렬화
    - 13.4: Round-trip 직렬화 지원
    - 13.5: Markdown 보고서 완전성
    - 14.1: reports/YYYYMMDD/ 폴더에 저장
    - 14.2: 폴더 자동 생성
    - 14.3: 배치 분석 리포트 저장
    - 14.4: 타임스탬프 기반 파일명
    - 14.5: 파일 쓰기 권한 예외 처리
    """
    
    @staticmethod
    def to_json(data: Union[StatspackData, Dict[TargetDatabase, MigrationComplexity]]) -> str:
        """분석 결과를 JSON 형식으로 변환
        
        Requirements 13.1을 구현합니다.
        - 유효한 JSON 형식으로 출력
        - Enum 타입을 문자열로 변환
        - 모든 필드 포함
        
        Args:
            data: StatspackData 또는 MigrationComplexity 딕셔너리
            
        Returns:
            JSON 형식의 문자열
        """
        if isinstance(data, StatspackData):
            # StatspackData를 딕셔너리로 변환
            data_dict = statspack_to_dict(data)
            data_dict["_type"] = "StatspackData"
        elif isinstance(data, dict):
            # MigrationComplexity 딕셔너리 변환
            data_dict = {}
            for target, complexity in data.items():
                key = target.value if isinstance(target, TargetDatabase) else str(target)
                data_dict[key] = migration_complexity_to_dict(complexity)
            data_dict["_type"] = "MigrationComplexityDict"
        else:
            raise ValueError(f"지원하지 않는 데이터 타입: {type(data)}")
        
        # JSON 문자열로 변환 (들여쓰기 포함, 한글 유니코드 이스케이프 방지)
        return json.dumps(data_dict, indent=2, ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str) -> Union[StatspackData, Dict[TargetDatabase, MigrationComplexity]]:
        """JSON 문자열을 분석 결과 객체로 변환
        
        Requirements 13.3, 13.4를 구현합니다.
        - JSON 문자열을 파싱하여 원본 객체 생성
        - Enum 타입 복원
        - Round-trip 지원
        
        Args:
            json_str: JSON 형식의 문자열
            
        Returns:
            StatspackData 또는 MigrationComplexity 딕셔너리
            
        Raises:
            ValueError: JSON 파싱 실패 시
        """
        try:
            data_dict = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {e}")
        
        # 타입 확인
        data_type = data_dict.pop("_type", None)
        
        if data_type == "StatspackData":
            return dict_to_statspack(data_dict)
        elif data_type == "MigrationComplexityDict":
            # MigrationComplexity 딕셔너리 복원
            result = {}
            for key, value in data_dict.items():
                # 타겟 데이터베이스 복원
                target = None
                for t in TargetDatabase:
                    if t.value == key:
                        target = t
                        break
                if target:
                    result[target] = dict_to_migration_complexity(value)
            return result
        else:
            raise ValueError(f"알 수 없는 데이터 타입: {data_type}")
    
    @staticmethod
    def to_markdown(statspack_data: StatspackData, 
                    migration_analysis: Dict[TargetDatabase, MigrationComplexity] = None) -> str:
        """분석 결과를 Markdown 형식으로 변환
        
        Requirements 13.2, 13.5를 구현합니다.
        - 가독성 좋은 Markdown 보고서 생성
        - 모든 필수 섹션 포함
        
        Args:
            statspack_data: Statspack 파싱 데이터
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목
        md.append("# Statspack 분석 보고서\n")
        md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. 시스템 정보 요약
        md.append("## 1. 시스템 정보 요약\n")
        os_info = statspack_data.os_info
        if os_info:
            md.append(f"- **데이터베이스 이름**: {os_info.db_name or 'N/A'}")
            md.append(f"- **DBID**: {os_info.dbid or 'N/A'}")
            md.append(f"- **버전**: {os_info.version or 'N/A'}")
            md.append(f"- **배너**: {os_info.banner or 'N/A'}")
            md.append(f"- **플랫폼**: {os_info.platform_name or 'N/A'}")
            md.append(f"- **CPU 개수**: {os_info.num_cpus or 'N/A'}")
            md.append(f"- **CPU 코어 수**: {os_info.num_cpu_cores or 'N/A'}")
            md.append(f"- **물리 메모리**: {os_info.physical_memory_gb or 'N/A'} GB")
            md.append(f"- **인스턴스 수**: {os_info.instances or 'N/A'}")
            md.append(f"- **RDS 환경**: {'예' if os_info.is_rds else '아니오'}")
            md.append(f"- **캐릭터셋**: {os_info.character_set or 'N/A'}")
            md.append(f"- **총 DB 크기**: {os_info.total_db_size_gb or 'N/A'} GB")
            
            # PL/SQL 코드 통계 추가
            if os_info.count_lines_plsql or os_info.count_packages or os_info.count_procedures or os_info.count_functions:
                md.append("\n**PL/SQL 코드 통계:**")
                if os_info.count_lines_plsql:
                    md.append(f"- **PL/SQL 코드 라인 수**: {os_info.count_lines_plsql:,}")
                if os_info.count_packages:
                    md.append(f"- **패키지 수**: {os_info.count_packages}")
                if os_info.count_procedures:
                    md.append(f"- **프로시저 수**: {os_info.count_procedures}")
                if os_info.count_functions:
                    md.append(f"- **함수 수**: {os_info.count_functions}")
            
            # 스키마 및 테이블 통계 추가
            if os_info.count_schemas or os_info.count_tables:
                md.append("\n**데이터베이스 오브젝트 통계:**")
                if os_info.count_schemas:
                    md.append(f"- **스키마 수**: {os_info.count_schemas}")
                if os_info.count_tables:
                    md.append(f"- **테이블 수**: {os_info.count_tables}")
            
            md.append("")
        
        # 2. 메모리 사용량 통계
        if statspack_data.memory_metrics:
            md.append("## 2. 메모리 사용량 통계\n")
            md.append("| Snap ID | Instance | SGA (GB) | PGA (GB) | Total (GB) |")
            md.append("|---------|----------|----------|----------|------------|")
            for metric in statspack_data.memory_metrics[:10]:  # 최대 10개만 표시
                md.append(f"| {metric.snap_id} | {metric.instance_number} | "
                         f"{metric.sga_gb:.2f} | {metric.pga_gb:.2f} | {metric.total_gb:.2f} |")
            if len(statspack_data.memory_metrics) > 10:
                md.append(f"\n*({len(statspack_data.memory_metrics) - 10}개 항목 더 있음)*")
            md.append("")
        
        # 3. 디스크 사용량 통계
        if statspack_data.disk_sizes:
            md.append("## 3. 디스크 사용량 통계\n")
            md.append("| Snap ID | Size (GB) |")
            md.append("|---------|-----------|")
            for disk in statspack_data.disk_sizes[:10]:  # 최대 10개만 표시
                md.append(f"| {disk.snap_id} | {disk.size_gb:.2f} |")
            if len(statspack_data.disk_sizes) > 10:
                md.append(f"\n*({len(statspack_data.disk_sizes) - 10}개 항목 더 있음)*")
            md.append("")
        
        # 4. 주요 성능 메트릭 요약
        if statspack_data.main_metrics:
            md.append("## 4. 주요 성능 메트릭 요약\n")
            md.append("| 시간 | Duration (m) | CPU/s | Read IOPS | Write IOPS | Commits/s |")
            md.append("|------|--------------|-------|-----------|------------|-----------|")
            for metric in statspack_data.main_metrics[:10]:  # 최대 10개만 표시
                md.append(f"| {metric.end} | {metric.dur_m:.1f} | {metric.cpu_per_s:.2f} | "
                         f"{metric.read_iops:.2f} | {metric.write_iops:.2f} | {metric.commits_s:.2f} |")
            if len(statspack_data.main_metrics) > 10:
                md.append(f"\n*({len(statspack_data.main_metrics) - 10}개 항목 더 있음)*")
            md.append("")
        
        # 5. Top 대기 이벤트
        if statspack_data.wait_events:
            md.append("## 5. Top 대기 이벤트\n")
            md.append("| Snap ID | Wait Class | Event Name | % DBT | Total Time (s) |")
            md.append("|---------|------------|------------|-------|----------------|")
            for event in statspack_data.wait_events[:20]:  # 최대 20개만 표시
                md.append(f"| {event.snap_id} | {event.wait_class} | {event.event_name} | "
                         f"{event.pctdbt:.2f} | {event.total_time_s:.2f} |")
            if len(statspack_data.wait_events) > 20:
                md.append(f"\n*({len(statspack_data.wait_events) - 20}개 항목 더 있음)*")
            md.append("")
        
        # 6. 사용된 Oracle 기능 목록
        if statspack_data.features:
            md.append("## 6. 사용된 Oracle 기능 목록\n")
            md.append("| Feature Name | Detected Usages | Currently Used |")
            md.append("|--------------|-----------------|----------------|")
            for feature in statspack_data.features:
                used_str = "예" if feature.currently_used else "아니오"
                md.append(f"| {feature.name} | {feature.detected_usages} | {used_str} |")
            md.append("")
        
        # 7. SGA 조정 권장사항
        if statspack_data.sga_advice:
            md.append("## 7. SGA 조정 권장사항\n")
            md.append("| SGA Size (MB) | Size Factor | Est. DB Time | Est. Physical Reads |")
            md.append("|---------------|-------------|--------------|---------------------|")
            for advice in statspack_data.sga_advice[:10]:  # 최대 10개만 표시
                md.append(f"| {advice.sga_size} | {advice.sga_size_factor:.2f} | "
                         f"{advice.estd_db_time} | {advice.estd_physical_reads} |")
            if len(statspack_data.sga_advice) > 10:
                md.append(f"\n*({len(statspack_data.sga_advice) - 10}개 항목 더 있음)*")
            md.append("")
        
        # 8. 마이그레이션 분석 결과
        if migration_analysis:
            md.append("## 8. 마이그레이션 분석 결과\n")
            for target, complexity in migration_analysis.items():
                md.append(f"### {target.value}\n")
                md.append(f"- **난이도 점수**: {complexity.score:.2f} / 10.0")
                md.append(f"- **난이도 레벨**: {complexity.level}")
                md.append("")
                
                # 점수 구성 요소
                if complexity.factors:
                    md.append("**점수 구성 요소:**\n")
                    for factor, score in complexity.factors.items():
                        md.append(f"- {factor}: {score:.2f}")
                    md.append("")
                
                # RDS 인스턴스 추천
                if complexity.instance_recommendation:
                    rec = complexity.instance_recommendation
                    md.append("**RDS 인스턴스 추천:**\n")
                    md.append(f"- **인스턴스 타입**: {rec.instance_type}")
                    md.append(f"- **vCPU**: {rec.vcpu}")
                    md.append(f"- **메모리**: {rec.memory_gib} GiB")
                    md.append(f"- **현재 CPU 사용률**: {rec.current_cpu_usage_pct:.2f}%")
                    md.append(f"- **현재 메모리 사용량**: {rec.current_memory_gb:.2f} GB")
                    md.append(f"- **CPU 여유분**: {rec.cpu_headroom_pct:.2f}%")
                    md.append(f"- **메모리 여유분**: {rec.memory_headroom_pct:.2f}%")
                    if rec.estimated_monthly_cost_usd:
                        md.append(f"- **예상 월간 비용**: ${rec.estimated_monthly_cost_usd:.2f}")
                    md.append("")
                
                # 권장사항
                if complexity.recommendations:
                    md.append("**권장사항:**\n")
                    for rec in complexity.recommendations:
                        md.append(f"- {rec}")
                    md.append("")
                
                # 경고
                if complexity.warnings:
                    md.append("**경고:**\n")
                    for warning in complexity.warnings:
                        md.append(f"- ⚠️ {warning}")
                    md.append("")
                
                # 다음 단계
                if complexity.next_steps:
                    md.append("**다음 단계:**\n")
                    for step in complexity.next_steps:
                        md.append(f"- {step}")
                    md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def save_report(content: str, 
                   filename: str, 
                   format: str = "md",
                   base_dir: str = "reports",
                   db_name: str = None) -> str:
        """리포트를 날짜별/DB별 폴더에 저장
        
        Requirements 14.1, 14.2, 14.4, 14.5를 구현합니다.
        - reports/YYYYMMDD/{db_name}/ 폴더에 저장
        - 폴더 자동 생성
        - 타임스탬프 기반 파일명
        - DB별 폴더 분리
        - 파일 쓰기 권한 예외 처리
        
        Args:
            content: 저장할 내용
            filename: 기본 파일명 (확장자 제외)
            format: 파일 형식 ("md" 또는 "json")
            base_dir: 기본 디렉토리 (기본값: "reports")
            db_name: 데이터베이스 이름 (선택적, 폴더명으로 사용됨)
            
        Returns:
            저장된 파일의 전체 경로
            
        Raises:
            PermissionError: 파일 쓰기 권한이 없을 때
            OSError: 기타 파일 시스템 오류
        """
        # 날짜 폴더 생성
        today = datetime.now().strftime("%Y%m%d")
        
        # DB 이름이 있으면 날짜 폴더 아래에 DB 폴더 생성
        if db_name:
            # DB 이름에서 폴더명에 사용할 수 없는 문자 제거
            safe_db_name = "".join(c for c in db_name if c.isalnum() or c in ('-', '_')).lower()
            report_dir = Path(base_dir) / today / safe_db_name
        else:
            report_dir = Path(base_dir) / today
        
        try:
            # 폴더가 없으면 생성
            report_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"폴더 생성 권한이 없습니다: {report_dir}") from e
        except OSError as e:
            raise OSError(f"폴더 생성 중 오류 발생: {report_dir}") from e
        
        # 타임스탬프 추가
        timestamp = datetime.now().strftime("%H%M%S")
        full_filename = f"{filename}_{timestamp}.{format}"
        
        filepath = report_dir / full_filename
        
        try:
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except PermissionError as e:
            raise PermissionError(f"파일 쓰기 권한이 없습니다: {filepath}") from e
        except OSError as e:
            raise OSError(f"파일 저장 중 오류 발생: {filepath}") from e
        
        return str(filepath)
    
    @staticmethod
    def batch_to_markdown(batch_result) -> str:
        """배치 분석 결과를 Markdown 형식으로 변환
        
        Requirements 14.3을 구현합니다.
        - 전체 요약 통계
        - 개별 파일 결과
        
        Args:
            batch_result: BatchAnalysisResult 객체
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # 제목
        md.append("# Statspack 배치 분석 보고서\n")
        md.append(f"분석 시간: {batch_result.analysis_timestamp}\n")
        
        # 전체 요약
        md.append("## 전체 요약\n")
        md.append(f"- **총 파일 수**: {batch_result.total_files}")
        md.append(f"- **성공**: {batch_result.successful_files}")
        md.append(f"- **실패**: {batch_result.failed_files}")
        success_rate = (batch_result.successful_files / batch_result.total_files * 100) if batch_result.total_files > 0 else 0
        md.append(f"- **성공률**: {success_rate:.1f}%")
        md.append("")
        
        # 성공한 파일 목록
        successful_files = [r for r in batch_result.file_results if r.success]
        if successful_files:
            md.append("## 성공한 파일\n")
            md.append("| 파일명 | DB 이름 | 버전 | 총 크기 (GB) |")
            md.append("|--------|---------|------|--------------|")
            for result in successful_files:
                db_name = result.statspack_data.os_info.db_name or "N/A"
                version = result.statspack_data.os_info.version or "N/A"
                size = result.statspack_data.os_info.total_db_size_gb or 0
                md.append(f"| {result.filename} | {db_name} | {version} | {size:.2f} |")
            md.append("")
        
        # 실패한 파일 목록
        failed_files = [r for r in batch_result.file_results if not r.success]
        if failed_files:
            md.append("## 실패한 파일\n")
            md.append("| 파일명 | 오류 메시지 |")
            md.append("|--------|-------------|")
            for result in failed_files:
                error_msg = result.error_message or "알 수 없는 오류"
                # 오류 메시지가 너무 길면 줄임
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                md.append(f"| {result.filename} | {error_msg} |")
            md.append("")
        
        # 마이그레이션 분석 요약 (있는 경우)
        if successful_files and successful_files[0].migration_analysis:
            md.append("## 마이그레이션 난이도 요약\n")
            
            # 각 타겟별로 통계 계산
            targets = list(successful_files[0].migration_analysis.keys())
            
            for target in targets:
                md.append(f"### {target.value}\n")
                md.append("| 파일명 | DB 이름 | 난이도 점수 | 난이도 레벨 | 추천 인스턴스 |")
                md.append("|--------|---------|-------------|-------------|---------------|")
                
                for result in successful_files:
                    if result.migration_analysis and target in result.migration_analysis:
                        complexity = result.migration_analysis[target]
                        db_name = result.statspack_data.os_info.db_name or "N/A"
                        instance = complexity.instance_recommendation.instance_type if complexity.instance_recommendation else "N/A"
                        md.append(f"| {result.filename} | {db_name} | {complexity.score:.2f} | "
                                 f"{complexity.level} | {instance} |")
                md.append("")
        
        # 개별 파일 상세 정보
        if successful_files:
            md.append("## 개별 파일 상세 정보\n")
            for result in successful_files:
                md.append(f"### {result.filename}\n")
                
                os_info = result.statspack_data.os_info
                md.append(f"- **DB 이름**: {os_info.db_name or 'N/A'}")
                md.append(f"- **버전**: {os_info.version or 'N/A'}")
                md.append(f"- **총 크기**: {os_info.total_db_size_gb or 'N/A'} GB")
                md.append(f"- **CPU 개수**: {os_info.num_cpus or 'N/A'}")
                md.append(f"- **메모리**: {os_info.physical_memory_gb or 'N/A'} GB")
                
                # 메모리 메트릭 요약
                if result.statspack_data.memory_metrics:
                    avg_total = sum(m.total_gb for m in result.statspack_data.memory_metrics) / len(result.statspack_data.memory_metrics)
                    md.append(f"- **평균 메모리 사용량**: {avg_total:.2f} GB")
                
                # 마이그레이션 분석 (있는 경우)
                if result.migration_analysis:
                    md.append("\n**마이그레이션 난이도:**")
                    for target, complexity in result.migration_analysis.items():
                        md.append(f"- {target.value}: {complexity.score:.2f} ({complexity.level})")
                
                md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def batch_to_json(batch_result) -> str:
        """배치 분석 결과를 JSON 형식으로 변환
        
        Requirements 14.3을 구현합니다.
        
        Args:
            batch_result: BatchAnalysisResult 객체
            
        Returns:
            JSON 형식의 문자열
        """
        result_dict = {
            "_type": "BatchAnalysisResult",
            "total_files": batch_result.total_files,
            "successful_files": batch_result.successful_files,
            "failed_files": batch_result.failed_files,
            "analysis_timestamp": batch_result.analysis_timestamp,
            "file_results": []
        }
        
        for file_result in batch_result.file_results:
            file_dict = {
                "filepath": file_result.filepath,
                "filename": file_result.filename,
                "success": file_result.success,
                "error_message": file_result.error_message
            }
            
            # 성공한 경우 데이터 포함
            if file_result.success and file_result.statspack_data:
                from src.dbcsi.data_models import statspack_to_dict
                file_dict["statspack_data"] = statspack_to_dict(file_result.statspack_data)
                
                # 마이그레이션 분석 포함
                if file_result.migration_analysis:
                    from src.dbcsi.data_models import migration_complexity_to_dict
                    migration_dict = {}
                    for target, complexity in file_result.migration_analysis.items():
                        migration_dict[target.value] = migration_complexity_to_dict(complexity)
                    file_dict["migration_analysis"] = migration_dict
            
            result_dict["file_results"].append(file_dict)
        
        return json.dumps(result_dict, indent=2, ensure_ascii=False)


class EnhancedResultFormatter(StatspackResultFormatter):
    """AWR 분석 결과 포맷터 - StatspackResultFormatter 확장
    
    Requirements:
    - 15.1: 상세 분석 리포트 생성
    - 15.2: Executive Summary 생성
    - 15.3: 백분위수 차트 생성
    - 17.2, 17.3: 추세 분석 리포트 생성
    - 13.3: AWR vs Statspack 비교 리포트
    """
    
    @staticmethod
    def to_detailed_markdown(awr_data, 
                            migration_analysis=None,
                            language: str = "ko") -> str:
        """상세 Markdown 보고서 생성
        
        Requirements 15.1을 구현합니다.
        - Executive Summary
        - 시스템 정보 요약
        - 성능 메트릭 요약 (백분위수 포함)
        - 워크로드 패턴 분석
        - 버퍼 캐시 효율성 분석
        - I/O 함수별 분석
        - 시간대별 리소스 사용 패턴
        - 마이그레이션 난이도 평가
        - 인스턴스 사이징 권장사항
        - 최적화 권장사항
        
        Args:
            awr_data: AWR 파싱 데이터 (AWRData 또는 StatspackData)
            migration_analysis: 마이그레이션 난이도 분석 결과 (선택적)
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        md = []
        
        # AWR 데이터인지 확인
        is_awr = hasattr(awr_data, 'is_awr') and awr_data.is_awr()
        
        # 제목
        if language == "ko":
            title = "AWR 상세 분석 보고서" if is_awr else "Statspack 분석 보고서"
        else:
            title = "AWR Detailed Analysis Report" if is_awr else "Statspack Analysis Report"
        
        md.append(f"# {title}\n")
        md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Executive Summary (AWR인 경우에만)
        if is_awr and migration_analysis:
            md.append(EnhancedResultFormatter._generate_executive_summary(
                awr_data, migration_analysis, language
            ))
        
        # 기본 Statspack 섹션 (기존 to_markdown 활용)
        base_report = StatspackResultFormatter.to_markdown(awr_data, migration_analysis)
        # 제목 제거 (이미 추가했으므로)
        base_lines = base_report.split('\n')
        base_content = '\n'.join(base_lines[2:])  # 첫 두 줄 제거
        md.append(base_content)
        
        # AWR 특화 섹션
        if is_awr:
            # 워크로드 패턴 분석
            if hasattr(awr_data, 'workload_profiles') and awr_data.workload_profiles:
                md.append(EnhancedResultFormatter._generate_workload_analysis(awr_data, language))
            
            # 버퍼 캐시 효율성 분석
            if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
                md.append(EnhancedResultFormatter._generate_buffer_cache_analysis(awr_data, language))
            
            # I/O 함수별 분석
            if hasattr(awr_data, 'iostat_functions') and awr_data.iostat_functions:
                md.append(EnhancedResultFormatter._generate_io_function_analysis(awr_data, language))
            
            # 백분위수 차트
            if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
                md.append(EnhancedResultFormatter._generate_percentile_charts(awr_data))
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_executive_summary(awr_data, migration_analysis, language: str) -> str:
        """Executive Summary 생성 (비기술적 언어)
        
        Requirements 15.2를 구현합니다.
        
        Args:
            awr_data: AWR 데이터
            migration_analysis: 마이그레이션 분석 결과
            language: 리포트 언어
            
        Returns:
            Executive Summary 섹션 문자열
        """
        md = []
        
        if language == "ko":
            md.append("## 경영진 요약 (Executive Summary)\n")
            
            # 현재 시스템 개요
            md.append("### 현재 시스템 개요\n")
            os_info = awr_data.os_info
            if os_info:
                db_name = os_info.db_name or "N/A"
                version = os_info.version or "N/A"
                db_size = os_info.total_db_size_gb or 0
                cpu_count = os_info.num_cpus or os_info.num_cpu_cores or 0
                memory_gb = os_info.physical_memory_gb or 0
                
                md.append(f"현재 **{db_name}** 데이터베이스는 Oracle {version} 버전으로 운영되고 있으며, "
                         f"총 **{db_size:.1f}GB**의 데이터를 저장하고 있습니다. "
                         f"시스템은 **{cpu_count}개의 CPU 코어**와 **{memory_gb:.1f}GB의 메모리**로 구성되어 있습니다.\n")
            
            # 마이그레이션 권장사항
            md.append("### 마이그레이션 권장사항\n")
            
            if migration_analysis:
                # 가장 낮은 난이도의 타겟 찾기
                sorted_targets = sorted(migration_analysis.items(), key=lambda x: x[1].score)
                best_target, best_complexity = sorted_targets[0]
                
                md.append(f"분석 결과, **{best_target.value}**로의 마이그레이션이 가장 적합합니다. "
                         f"예상 난이도는 **{best_complexity.level}**이며, "
                         f"마이그레이션 점수는 10점 만점에 **{best_complexity.score:.1f}점**입니다.\n")
                
                # 각 타겟별 요약
                md.append("#### 타겟별 마이그레이션 난이도\n")
                for target, complexity in sorted_targets:
                    md.append(f"- **{target.value}**: {complexity.level} ({complexity.score:.1f}/10.0)")
                    if complexity.instance_recommendation:
                        rec = complexity.instance_recommendation
                        md.append(f"  - 권장 인스턴스: {rec.instance_type} ({rec.vcpu} vCPU, {rec.memory_gib} GiB)")
                md.append("")
            
            # 주요 발견사항
            md.append("### 주요 발견사항\n")
            
            # 성능 특성
            if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
                p99_cpu_data = awr_data.percentile_cpu.get("99th_percentile")
                if p99_cpu_data:
                    md.append(f"- **CPU 사용률**: 99번째 백분위수 기준 {p99_cpu_data.on_cpu}개 코어 사용")
            
            if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
                p99_io_data = awr_data.percentile_io.get("99th_percentile")
                if p99_io_data:
                    md.append(f"- **I/O 부하**: 99번째 백분위수 기준 {p99_io_data.rw_iops:,} IOPS, {p99_io_data.rw_mbps} MB/s")
            
            # 버퍼 캐시 효율성
            if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
                import statistics
                hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
                if hit_ratios:
                    avg_hit_ratio = statistics.mean(hit_ratios)
                    if avg_hit_ratio < 90:
                        md.append(f"- **버퍼 캐시 효율성**: 평균 히트율 {avg_hit_ratio:.1f}% (개선 필요)")
                    else:
                        md.append(f"- **버퍼 캐시 효율성**: 평균 히트율 {avg_hit_ratio:.1f}% (양호)")
            
            md.append("")
            
            # 권장 조치사항
            md.append("### 권장 조치사항\n")
            
            if migration_analysis and best_complexity:
                for i, rec in enumerate(best_complexity.recommendations[:5], 1):
                    md.append(f"{i}. {rec}")
            
            md.append("")
            
            # 예상 일정 및 비용
            md.append("### 예상 일정 및 비용\n")
            
            if migration_analysis and best_complexity:
                if best_complexity.score <= 3.0:
                    md.append("- **예상 마이그레이션 기간**: 2-4주")
                    md.append("- **리스크 수준**: 낮음")
                elif best_complexity.score <= 6.0:
                    md.append("- **예상 마이그레이션 기간**: 1-3개월")
                    md.append("- **리스크 수준**: 중간")
                else:
                    md.append("- **예상 마이그레이션 기간**: 3-6개월 이상")
                    md.append("- **리스크 수준**: 높음")
                
                if best_complexity.instance_recommendation and best_complexity.instance_recommendation.estimated_monthly_cost_usd:
                    cost = best_complexity.instance_recommendation.estimated_monthly_cost_usd
                    md.append(f"- **예상 월간 운영 비용**: ${cost:,.2f}")
            
            md.append("")
        
        else:  # English
            md.append("## Executive Summary\n")
            
            # Current System Overview
            md.append("### Current System Overview\n")
            os_info = awr_data.os_info
            if os_info:
                db_name = os_info.db_name or "N/A"
                version = os_info.version or "N/A"
                db_size = os_info.total_db_size_gb or 0
                cpu_count = os_info.num_cpus or os_info.num_cpu_cores or 0
                memory_gb = os_info.physical_memory_gb or 0
                
                md.append(f"The **{db_name}** database is currently running on Oracle {version}, "
                         f"storing a total of **{db_size:.1f}GB** of data. "
                         f"The system is configured with **{cpu_count} CPU cores** and **{memory_gb:.1f}GB of memory**.\n")
            
            # Migration Recommendations
            md.append("### Migration Recommendations\n")
            
            if migration_analysis:
                # Find the target with the lowest complexity
                sorted_targets = sorted(migration_analysis.items(), key=lambda x: x[1].score)
                best_target, best_complexity = sorted_targets[0]
                
                md.append(f"Based on the analysis, migration to **{best_target.value}** is most suitable. "
                         f"The expected complexity level is **{best_complexity.level}**, "
                         f"with a migration score of **{best_complexity.score:.1f} out of 10.0**.\n")
                
                # Summary by target
                md.append("#### Migration Complexity by Target\n")
                for target, complexity in sorted_targets:
                    md.append(f"- **{target.value}**: {complexity.level} ({complexity.score:.1f}/10.0)")
                    if complexity.instance_recommendation:
                        rec = complexity.instance_recommendation
                        md.append(f"  - Recommended instance: {rec.instance_type} ({rec.vcpu} vCPU, {rec.memory_gib} GiB)")
                md.append("")
            
            # Key Findings
            md.append("### Key Findings\n")
            
            # Performance characteristics
            if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
                p99_cpu_data = awr_data.percentile_cpu.get("99th_percentile")
                if p99_cpu_data:
                    md.append(f"- **CPU Usage**: {p99_cpu_data.on_cpu} cores at 99th percentile")
            
            if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
                p99_io_data = awr_data.percentile_io.get("99th_percentile")
                if p99_io_data:
                    md.append(f"- **I/O Load**: {p99_io_data.rw_iops:,} IOPS, {p99_io_data.rw_mbps} MB/s at 99th percentile")
            
            # Buffer cache efficiency
            if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
                import statistics
                hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
                if hit_ratios:
                    avg_hit_ratio = statistics.mean(hit_ratios)
                    if avg_hit_ratio < 90:
                        md.append(f"- **Buffer Cache Efficiency**: Average hit ratio {avg_hit_ratio:.1f}% (needs improvement)")
                    else:
                        md.append(f"- **Buffer Cache Efficiency**: Average hit ratio {avg_hit_ratio:.1f}% (good)")
            
            md.append("")
            
            # Recommended Actions
            md.append("### Recommended Actions\n")
            
            if migration_analysis and best_complexity:
                for i, rec in enumerate(best_complexity.recommendations[:5], 1):
                    md.append(f"{i}. {rec}")
            
            md.append("")
            
            # Estimated Timeline and Cost
            md.append("### Estimated Timeline and Cost\n")
            
            if migration_analysis and best_complexity:
                if best_complexity.score <= 3.0:
                    md.append("- **Estimated Migration Duration**: 2-4 weeks")
                    md.append("- **Risk Level**: Low")
                elif best_complexity.score <= 6.0:
                    md.append("- **Estimated Migration Duration**: 1-3 months")
                    md.append("- **Risk Level**: Medium")
                else:
                    md.append("- **Estimated Migration Duration**: 3-6+ months")
                    md.append("- **Risk Level**: High")
                
                if best_complexity.instance_recommendation and best_complexity.instance_recommendation.estimated_monthly_cost_usd:
                    cost = best_complexity.instance_recommendation.estimated_monthly_cost_usd
                    md.append(f"- **Estimated Monthly Operating Cost**: ${cost:,.2f}")
            
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_workload_analysis(awr_data, language: str) -> str:
        """워크로드 패턴 분석 섹션 생성
        
        Requirements 15.1을 구현합니다.
        
        Args:
            awr_data: AWR 데이터
            language: 리포트 언어
            
        Returns:
            워크로드 분석 섹션 문자열
        """
        md = []
        
        if language == "ko":
            md.append("## 워크로드 패턴 분석\n")
        else:
            md.append("## Workload Pattern Analysis\n")
        
        if not hasattr(awr_data, 'workload_profiles') or not awr_data.workload_profiles:
            if language == "ko":
                md.append("워크로드 프로파일 데이터가 없습니다.\n")
            else:
                md.append("No workload profile data available.\n")
            return "\n".join(md)
        
        # 이벤트별 DB Time 집계
        event_totals = {}
        module_totals = {}
        hour_totals = {}
        
        for profile in awr_data.workload_profiles:
            # 유휴 이벤트 제외
            if "IDLE" in profile.event.upper():
                continue
            
            # 이벤트별 집계
            event_name = profile.event
            if event_name not in event_totals:
                event_totals[event_name] = 0
            event_totals[event_name] += profile.total_dbtime_sum
            
            # 모듈별 집계
            module_name = profile.module
            if module_name not in module_totals:
                module_totals[module_name] = 0
            module_totals[module_name] += profile.total_dbtime_sum
            
            # 시간대별 집계
            try:
                hour = profile.sample_start.split()[1].split(':')[0]
                if hour not in hour_totals:
                    hour_totals[hour] = 0
                hour_totals[hour] += profile.aas_comp
            except:
                pass
        
        # 총 DB Time 계산
        total_dbtime = sum(event_totals.values())
        
        if total_dbtime == 0:
            if language == "ko":
                md.append("워크로드 데이터가 충분하지 않습니다.\n")
            else:
                md.append("Insufficient workload data.\n")
            return "\n".join(md)
        
        # CPU vs I/O 비율 계산
        cpu_time = sum(v for k, v in event_totals.items() if "CPU" in k.upper())
        io_time = sum(v for k, v in event_totals.items() if "I/O" in k.upper())
        
        cpu_pct = (cpu_time / total_dbtime) * 100
        io_pct = (io_time / total_dbtime) * 100
        
        # 워크로드 패턴 타입 결정
        pattern_type = "Mixed"
        if cpu_pct > 50:
            pattern_type = "CPU-intensive"
        elif io_pct > 50:
            pattern_type = "IO-intensive"
        
        # 대화형 vs 배치형 판단
        interactive_modules = ["SQL*Plus", "JDBC Thin Client", "sqlplus"]
        batch_modules = ["SQL Loader", "Data Pump"]
        
        is_interactive = any(im in str(module_totals.keys()) for im in interactive_modules)
        is_batch = any(bm in str(module_totals.keys()) for bm in batch_modules)
        
        if is_interactive:
            pattern_type = "Interactive"
        elif is_batch:
            pattern_type = "Batch"
        
        # 워크로드 패턴 요약
        if language == "ko":
            md.append("### 워크로드 패턴 요약\n")
            md.append(f"- **패턴 타입**: {pattern_type}")
            md.append(f"- **CPU 비율**: {cpu_pct:.1f}%")
            md.append(f"- **I/O 비율**: {io_pct:.1f}%")
            md.append("")
        else:
            md.append("### Workload Pattern Summary\n")
            md.append(f"- **Pattern Type**: {pattern_type}")
            md.append(f"- **CPU Ratio**: {cpu_pct:.1f}%")
            md.append(f"- **I/O Ratio**: {io_pct:.1f}%")
            md.append("")
        
        # 상위 이벤트
        sorted_events = sorted(event_totals.items(), key=lambda x: x[1], reverse=True)
        
        if language == "ko":
            md.append("### 상위 대기 이벤트\n")
            md.append("| 순위 | 이벤트 이름 | DB Time (센티초) | 비율 |")
        else:
            md.append("### Top Wait Events\n")
            md.append("| Rank | Event Name | DB Time (centiseconds) | Percentage |")
        
        md.append("|------|-------------|----------------------|------------|")
        
        for i, (event, dbtime) in enumerate(sorted_events[:10], 1):
            pct = (dbtime / total_dbtime) * 100
            md.append(f"| {i} | {event} | {dbtime:,} | {pct:.1f}% |")
        
        md.append("")
        
        # 상위 모듈
        sorted_modules = sorted(module_totals.items(), key=lambda x: x[1], reverse=True)
        
        if language == "ko":
            md.append("### 주요 애플리케이션 모듈\n")
            md.append("| 순위 | 모듈 이름 | DB Time (센티초) | 비율 |")
        else:
            md.append("### Top Application Modules\n")
            md.append("| Rank | Module Name | DB Time (centiseconds) | Percentage |")
        
        md.append("|------|-----------|----------------------|------------|")
        
        for i, (module, dbtime) in enumerate(sorted_modules[:10], 1):
            pct = (dbtime / total_dbtime) * 100
            md.append(f"| {i} | {module} | {dbtime:,} | {pct:.1f}% |")
        
        md.append("")
        
        # 피크 시간대
        if hour_totals:
            import statistics
            avg_load = statistics.mean(hour_totals.values())
            peak_threshold = avg_load * 1.5
            peak_hours = sorted([hour for hour, load in hour_totals.items() if load >= peak_threshold])
            
            if peak_hours:
                if language == "ko":
                    md.append("### 피크 시간대\n")
                    md.append(f"평균 부하의 1.5배 이상인 시간대: **{', '.join([f'{h}:00' for h in peak_hours])}**\n")
                else:
                    md.append("### Peak Hours\n")
                    md.append(f"Hours with load 1.5x above average: **{', '.join([f'{h}:00' for h in peak_hours])}**\n")
        
        # 권장사항
        if language == "ko":
            md.append("### 워크로드 기반 권장사항\n")
            
            if pattern_type == "CPU-intensive":
                md.append("- CPU 집약적 워크로드입니다. 컴퓨트 최적화 인스턴스를 권장합니다.")
                md.append("- 쿼리 튜닝 및 인덱스 최적화를 통해 CPU 사용률을 낮출 수 있습니다.")
            elif pattern_type == "IO-intensive":
                md.append("- I/O 집약적 워크로드입니다. 스토리지 최적화 인스턴스를 권장합니다.")
                md.append("- 인덱스 최적화, 파티셔닝, 버퍼 캐시 증가를 고려하세요.")
            elif pattern_type == "Interactive":
                md.append("- 대화형 워크로드입니다. 연결 풀링 및 세션 관리 최적화를 권장합니다.")
                md.append("- 응답 시간 최적화에 집중하세요.")
            elif pattern_type == "Batch":
                md.append("- 배치 워크로드입니다. 병렬 처리 및 파티셔닝 전략을 권장합니다.")
                md.append("- 처리량 최적화에 집중하세요.")
            
            md.append("")
        else:
            md.append("### Workload-Based Recommendations\n")
            
            if pattern_type == "CPU-intensive":
                md.append("- CPU-intensive workload. Compute-optimized instances are recommended.")
                md.append("- Query tuning and index optimization can reduce CPU usage.")
            elif pattern_type == "IO-intensive":
                md.append("- I/O-intensive workload. Storage-optimized instances are recommended.")
                md.append("- Consider index optimization, partitioning, and increasing buffer cache.")
            elif pattern_type == "Interactive":
                md.append("- Interactive workload. Connection pooling and session management optimization are recommended.")
                md.append("- Focus on response time optimization.")
            elif pattern_type == "Batch":
                md.append("- Batch workload. Parallel processing and partitioning strategies are recommended.")
                md.append("- Focus on throughput optimization.")
            
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_buffer_cache_analysis(awr_data, language: str) -> str:
        """버퍼 캐시 효율성 분석 섹션 생성
        
        Requirements 15.1을 구현합니다.
        
        Args:
            awr_data: AWR 데이터
            language: 리포트 언어
            
        Returns:
            버퍼 캐시 분석 섹션 문자열
        """
        md = []
        
        if language == "ko":
            md.append("## 버퍼 캐시 효율성 분석\n")
        else:
            md.append("## Buffer Cache Efficiency Analysis\n")
        
        if not hasattr(awr_data, 'buffer_cache_stats') or not awr_data.buffer_cache_stats:
            if language == "ko":
                md.append("버퍼 캐시 통계 데이터가 없습니다.\n")
            else:
                md.append("No buffer cache statistics available.\n")
            return "\n".join(md)
        
        # 히트율 통계 계산
        import statistics
        
        hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
        cache_sizes = [stat.db_cache_gb for stat in awr_data.buffer_cache_stats if stat.db_cache_gb is not None]
        disk_reads = [stat.dsk_reads for stat in awr_data.buffer_cache_stats if stat.dsk_reads is not None]
        
        if not hit_ratios:
            if language == "ko":
                md.append("버퍼 캐시 히트율 데이터가 없습니다.\n")
            else:
                md.append("No buffer cache hit ratio data available.\n")
            return "\n".join(md)
        
        avg_hit_ratio = statistics.mean(hit_ratios)
        min_hit_ratio = min(hit_ratios)
        max_hit_ratio = max(hit_ratios)
        current_size_gb = statistics.mean(cache_sizes) if cache_sizes else 0.0
        
        # 권장 크기 계산
        recommended_size_gb = current_size_gb
        optimization_needed = False
        
        if avg_hit_ratio < 80:
            recommended_size_gb = current_size_gb * 2.5
            optimization_needed = True
        elif avg_hit_ratio < 85:
            recommended_size_gb = current_size_gb * 2.0
            optimization_needed = True
        elif avg_hit_ratio < 90:
            recommended_size_gb = current_size_gb * 1.5
            optimization_needed = True
        elif avg_hit_ratio > 99.5:
            recommended_size_gb = current_size_gb * 0.8
        
        # 히트율 요약
        if language == "ko":
            md.append("### 히트율 요약\n")
            md.append(f"- **평균 히트율**: {avg_hit_ratio:.2f}%")
            md.append(f"- **최소 히트율**: {min_hit_ratio:.2f}%")
            md.append(f"- **최대 히트율**: {max_hit_ratio:.2f}%")
            md.append(f"- **현재 버퍼 캐시 크기**: {current_size_gb:.2f} GB")
            md.append("")
        else:
            md.append("### Hit Ratio Summary\n")
            md.append(f"- **Average Hit Ratio**: {avg_hit_ratio:.2f}%")
            md.append(f"- **Minimum Hit Ratio**: {min_hit_ratio:.2f}%")
            md.append(f"- **Maximum Hit Ratio**: {max_hit_ratio:.2f}%")
            md.append(f"- **Current Buffer Cache Size**: {current_size_gb:.2f} GB")
            md.append("")
        
        # 효율성 평가
        if language == "ko":
            md.append("### 효율성 평가\n")
            
            if avg_hit_ratio >= 95:
                md.append("✅ **매우 우수**: 버퍼 캐시가 매우 효율적으로 동작하고 있습니다.")
            elif avg_hit_ratio >= 90:
                md.append("✅ **우수**: 버퍼 캐시가 효율적으로 동작하고 있습니다.")
            elif avg_hit_ratio >= 85:
                md.append("⚠️ **보통**: 버퍼 캐시 효율성 개선이 필요합니다.")
            elif avg_hit_ratio >= 80:
                md.append("⚠️ **낮음**: 버퍼 캐시 크기 증가가 필요합니다.")
            else:
                md.append("❌ **매우 낮음**: 버퍼 캐시가 비효율적으로 동작하고 있습니다. 즉시 조치가 필요합니다.")
            
            md.append("")
        else:
            md.append("### Efficiency Assessment\n")
            
            if avg_hit_ratio >= 95:
                md.append("✅ **Excellent**: Buffer cache is operating very efficiently.")
            elif avg_hit_ratio >= 90:
                md.append("✅ **Good**: Buffer cache is operating efficiently.")
            elif avg_hit_ratio >= 85:
                md.append("⚠️ **Fair**: Buffer cache efficiency improvement needed.")
            elif avg_hit_ratio >= 80:
                md.append("⚠️ **Low**: Buffer cache size increase needed.")
            else:
                md.append("❌ **Very Low**: Buffer cache is operating inefficiently. Immediate action required.")
            
            md.append("")
        
        # 디스크 읽기 패턴
        if disk_reads:
            total_disk_reads = sum(disk_reads)
            avg_disk_reads = statistics.mean(disk_reads)
            
            if language == "ko":
                md.append("### 디스크 읽기 패턴\n")
                md.append(f"- **총 디스크 읽기**: {total_disk_reads:,}")
                md.append(f"- **평균 디스크 읽기**: {avg_disk_reads:,.0f}")
                md.append("")
            else:
                md.append("### Disk Read Pattern\n")
                md.append(f"- **Total Disk Reads**: {total_disk_reads:,}")
                md.append(f"- **Average Disk Reads**: {avg_disk_reads:,.0f}")
                md.append("")
        
        # 최적화 권장사항
        if language == "ko":
            md.append("### 최적화 권장사항\n")
            
            if optimization_needed:
                md.append(f"1. **버퍼 캐시 크기 증가**: 현재 {current_size_gb:.2f} GB에서 {recommended_size_gb:.2f} GB로 증가 권장")
                
                if avg_hit_ratio < 85:
                    md.append("2. **인덱스 최적화**: 불필요한 테이블 스캔을 줄이기 위해 인덱스를 최적화하세요.")
                    md.append("3. **쿼리 튜닝**: 비효율적인 쿼리를 식별하고 최적화하세요.")
                    md.append("4. **파티셔닝 고려**: 대용량 테이블에 파티셔닝을 적용하여 I/O를 줄이세요.")
                
                if min_hit_ratio < 80:
                    md.append("5. **피크 시간대 모니터링**: 히트율이 낮은 시간대를 식별하고 원인을 분석하세요.")
            
            elif avg_hit_ratio > 99.5:
                md.append(f"1. **버퍼 캐시 크기 감소 고려**: 현재 {current_size_gb:.2f} GB에서 {recommended_size_gb:.2f} GB로 감소 가능")
                md.append("2. 과도한 버퍼 캐시는 메모리 낭비일 수 있습니다.")
                md.append("3. 감소된 메모리를 다른 용도(PGA, 애플리케이션)로 활용할 수 있습니다.")
            
            else:
                md.append("1. 현재 버퍼 캐시 크기가 적절합니다.")
                md.append("2. 정기적으로 히트율을 모니터링하세요.")
                md.append("3. 워크로드 변화에 따라 조정이 필요할 수 있습니다.")
            
            md.append("")
        else:
            md.append("### Optimization Recommendations\n")
            
            if optimization_needed:
                md.append(f"1. **Increase Buffer Cache Size**: Recommend increasing from {current_size_gb:.2f} GB to {recommended_size_gb:.2f} GB")
                
                if avg_hit_ratio < 85:
                    md.append("2. **Index Optimization**: Optimize indexes to reduce unnecessary table scans.")
                    md.append("3. **Query Tuning**: Identify and optimize inefficient queries.")
                    md.append("4. **Consider Partitioning**: Apply partitioning to large tables to reduce I/O.")
                
                if min_hit_ratio < 80:
                    md.append("5. **Monitor Peak Hours**: Identify and analyze time periods with low hit ratios.")
            
            elif avg_hit_ratio > 99.5:
                md.append(f"1. **Consider Reducing Buffer Cache Size**: Can reduce from {current_size_gb:.2f} GB to {recommended_size_gb:.2f} GB")
                md.append("2. Excessive buffer cache may be a waste of memory.")
                md.append("3. Freed memory can be used for other purposes (PGA, applications).")
            
            else:
                md.append("1. Current buffer cache size is appropriate.")
                md.append("2. Monitor hit ratio regularly.")
                md.append("3. Adjustments may be needed as workload changes.")
            
            md.append("")
        
        # 타겟 데이터베이스별 고려사항
        if language == "ko":
            md.append("### 타겟 데이터베이스별 고려사항\n")
            md.append("- **RDS for Oracle**: 버퍼 캐시 크기를 SGA 파라미터로 조정 가능")
            md.append("- **Aurora PostgreSQL**: shared_buffers 파라미터로 조정 (일반적으로 메모리의 25%)")
            md.append("- **Aurora MySQL**: innodb_buffer_pool_size 파라미터로 조정 (일반적으로 메모리의 70-80%)")
            md.append("")
        else:
            md.append("### Target Database Considerations\n")
            md.append("- **RDS for Oracle**: Adjust buffer cache size via SGA parameters")
            md.append("- **Aurora PostgreSQL**: Adjust via shared_buffers parameter (typically 25% of memory)")
            md.append("- **Aurora MySQL**: Adjust via innodb_buffer_pool_size parameter (typically 70-80% of memory)")
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_io_function_analysis(awr_data, language: str) -> str:
        """I/O 함수별 분석 섹션 생성
        
        Requirements 15.1을 구현합니다.
        
        Args:
            awr_data: AWR 데이터
            language: 리포트 언어
            
        Returns:
            I/O 함수별 분석 섹션 문자열
        """
        md = []
        
        if language == "ko":
            md.append("## I/O 함수별 분석\n")
        else:
            md.append("## I/O Function Analysis\n")
        
        if not hasattr(awr_data, 'iostat_functions') or not awr_data.iostat_functions:
            if language == "ko":
                md.append("I/O 함수별 통계 데이터가 없습니다.\n")
            else:
                md.append("No I/O function statistics available.\n")
            return "\n".join(md)
        
        # 함수별 I/O 통계 집계
        import statistics
        
        function_stats = {}
        
        for iostat in awr_data.iostat_functions:
            func_name = iostat.function_name
            mb_per_s = iostat.megabytes_per_s
            
            if func_name not in function_stats:
                function_stats[func_name] = []
            function_stats[func_name].append(mb_per_s)
        
        # 총 I/O 계산
        total_io = sum(sum(values) for values in function_stats.values())
        
        if total_io == 0:
            if language == "ko":
                md.append("I/O 데이터가 충분하지 않습니다.\n")
            else:
                md.append("Insufficient I/O data.\n")
            return "\n".join(md)
        
        # 함수별 통계 테이블
        if language == "ko":
            md.append("### 함수별 I/O 통계\n")
            md.append("| 함수 이름 | 평균 (MB/s) | 최대 (MB/s) | 총 비율 | 상태 |")
        else:
            md.append("### I/O Statistics by Function\n")
            md.append("| Function Name | Average (MB/s) | Maximum (MB/s) | Total % | Status |")
        
        md.append("|---------------|----------------|----------------|---------|--------|")
        
        # 함수별 분석 결과 생성
        function_analysis = []
        
        for func_name, values in function_stats.items():
            avg_mb_per_s = statistics.mean(values)
            max_mb_per_s = max(values)
            pct_of_total = (sum(values) / total_io * 100)
            
            # 병목 여부 판단
            status = "✅"
            if func_name == "LGWR":
                if avg_mb_per_s > 100:
                    status = "❌ 병목" if language == "ko" else "❌ Bottleneck"
                elif avg_mb_per_s > 50:
                    status = "⚠️ 높음" if language == "ko" else "⚠️ High"
                elif avg_mb_per_s > 10:
                    status = "⚠️ 주의" if language == "ko" else "⚠️ Watch"
            elif func_name == "DBWR":
                if avg_mb_per_s > 100:
                    status = "❌ 병목" if language == "ko" else "❌ Bottleneck"
                elif avg_mb_per_s > 50:
                    status = "⚠️ 높음" if language == "ko" else "⚠️ High"
            elif "Direct" in func_name:
                if avg_mb_per_s > 100:
                    status = "❌ 병목" if language == "ko" else "❌ Bottleneck"
                elif avg_mb_per_s > 50:
                    status = "⚠️ 높음" if language == "ko" else "⚠️ High"
            
            function_analysis.append({
                "name": func_name,
                "avg": avg_mb_per_s,
                "max": max_mb_per_s,
                "pct": pct_of_total,
                "status": status
            })
        
        # I/O 비율 기준으로 정렬
        function_analysis.sort(key=lambda x: x["pct"], reverse=True)
        
        for func in function_analysis:
            md.append(f"| {func['name']} | {func['avg']:.2f} | {func['max']:.2f} | {func['pct']:.1f}% | {func['status']} |")
        
        md.append("")
        
        # 함수별 상세 분석 및 권장사항
        if language == "ko":
            md.append("### 함수별 상세 분석 및 권장사항\n")
        else:
            md.append("### Detailed Analysis and Recommendations by Function\n")
        
        for func in function_analysis:
            func_name = func["name"]
            avg_mb_per_s = func["avg"]
            
            if language == "ko":
                md.append(f"#### {func_name}\n")
            else:
                md.append(f"#### {func_name}\n")
            
            # LGWR 분석
            if func_name == "LGWR":
                if language == "ko":
                    md.append("**설명**: 로그 라이터 프로세스 - 리두 로그 버퍼를 디스크에 기록\n")
                    
                    if avg_mb_per_s > 100:
                        md.append("**상태**: ❌ 심각한 병목 현상")
                        md.append("\n**권장사항**:")
                        md.append("1. 로그 파일을 빠른 스토리지(SSD, NVMe)로 이동")
                        md.append("2. 커밋 빈도 최적화 (배치 커밋 고려)")
                        md.append("3. 리두 로그 파일 크기 및 개수 조정")
                        md.append("4. Aurora 마이그레이션 시 스토리지 아키텍처가 자동으로 최적화됨")
                    elif avg_mb_per_s > 50:
                        md.append("**상태**: ⚠️ 높은 I/O 부하")
                        md.append("\n**권장사항**:")
                        md.append("1. 로그 쓰기 최적화 고려")
                        md.append("2. 커밋 패턴 검토")
                        md.append("3. Aurora 마이그레이션 시 개선 예상")
                    elif avg_mb_per_s > 10:
                        md.append("**상태**: ⚠️ 모니터링 필요")
                        md.append("\n**권장사항**:")
                        md.append("1. LGWR I/O를 지속적으로 모니터링")
                        md.append("2. 트랜잭션 패턴 검토")
                    else:
                        md.append("**상태**: ✅ 정상")
                        md.append("\n현재 LGWR I/O는 정상 범위입니다.")
                else:
                    md.append("**Description**: Log Writer process - writes redo log buffer to disk\n")
                    
                    if avg_mb_per_s > 100:
                        md.append("**Status**: ❌ Severe bottleneck")
                        md.append("\n**Recommendations**:")
                        md.append("1. Move log files to faster storage (SSD, NVMe)")
                        md.append("2. Optimize commit frequency (consider batch commits)")
                        md.append("3. Adjust redo log file size and count")
                        md.append("4. Aurora migration will automatically optimize storage architecture")
                    elif avg_mb_per_s > 50:
                        md.append("**Status**: ⚠️ High I/O load")
                        md.append("\n**Recommendations**:")
                        md.append("1. Consider log write optimization")
                        md.append("2. Review commit patterns")
                        md.append("3. Improvement expected with Aurora migration")
                    elif avg_mb_per_s > 10:
                        md.append("**Status**: ⚠️ Monitoring needed")
                        md.append("\n**Recommendations**:")
                        md.append("1. Continuously monitor LGWR I/O")
                        md.append("2. Review transaction patterns")
                    else:
                        md.append("**Status**: ✅ Normal")
                        md.append("\nCurrent LGWR I/O is within normal range.")
            
            # DBWR 분석
            elif func_name == "DBWR":
                if language == "ko":
                    md.append("**설명**: 데이터베이스 라이터 프로세스 - 더티 버퍼를 디스크에 기록\n")
                    
                    if avg_mb_per_s > 100:
                        md.append("**상태**: ❌ 심각한 병목 현상")
                        md.append("\n**권장사항**:")
                        md.append("1. 버퍼 캐시 크기 증가")
                        md.append("2. 체크포인트 간격 조정")
                        md.append("3. 데이터 파일을 빠른 스토리지로 이동")
                        md.append("4. 쿼리 튜닝으로 불필요한 블록 변경 감소")
                    elif avg_mb_per_s > 50:
                        md.append("**상태**: ⚠️ 높은 I/O 부하")
                        md.append("\n**권장사항**:")
                        md.append("1. 버퍼 캐시 최적화 고려")
                        md.append("2. 쓰기 패턴 검토")
                    else:
                        md.append("**상태**: ✅ 정상")
                        md.append("\n현재 DBWR I/O는 정상 범위입니다.")
                else:
                    md.append("**Description**: Database Writer process - writes dirty buffers to disk\n")
                    
                    if avg_mb_per_s > 100:
                        md.append("**Status**: ❌ Severe bottleneck")
                        md.append("\n**Recommendations**:")
                        md.append("1. Increase buffer cache size")
                        md.append("2. Adjust checkpoint interval")
                        md.append("3. Move data files to faster storage")
                        md.append("4. Reduce unnecessary block changes through query tuning")
                    elif avg_mb_per_s > 50:
                        md.append("**Status**: ⚠️ High I/O load")
                        md.append("\n**Recommendations**:")
                        md.append("1. Consider buffer cache optimization")
                        md.append("2. Review write patterns")
                    else:
                        md.append("**Status**: ✅ Normal")
                        md.append("\nCurrent DBWR I/O is within normal range.")
            
            # Direct I/O 분석
            elif "Direct" in func_name:
                if language == "ko":
                    md.append("**설명**: 직접 I/O - 버퍼 캐시를 우회하는 I/O (병렬 쿼리, 정렬 등)\n")
                    
                    if avg_mb_per_s > 100:
                        md.append("**상태**: ❌ 높은 Direct I/O")
                        md.append("\n**권장사항**:")
                        md.append("1. 병렬 쿼리 최적화")
                        md.append("2. 임시 테이블스페이스 크기 조정")
                        md.append("3. 정렬 작업 최적화 (인덱스 활용)")
                        md.append("4. PGA 메모리 증가 고려")
                    elif avg_mb_per_s > 50:
                        md.append("**상태**: ⚠️ 주의 필요")
                        md.append("\n**권장사항**:")
                        md.append("1. Direct I/O 패턴 검토")
                        md.append("2. 병렬 처리 최적화")
                    else:
                        md.append("**상태**: ✅ 정상")
                        md.append("\n현재 Direct I/O는 정상 범위입니다.")
                else:
                    md.append("**Description**: Direct I/O - I/O bypassing buffer cache (parallel queries, sorts, etc.)\n")
                    
                    if avg_mb_per_s > 100:
                        md.append("**Status**: ❌ High Direct I/O")
                        md.append("\n**Recommendations**:")
                        md.append("1. Optimize parallel queries")
                        md.append("2. Adjust temporary tablespace size")
                        md.append("3. Optimize sort operations (use indexes)")
                        md.append("4. Consider increasing PGA memory")
                    elif avg_mb_per_s > 50:
                        md.append("**Status**: ⚠️ Attention needed")
                        md.append("\n**Recommendations**:")
                        md.append("1. Review Direct I/O patterns")
                        md.append("2. Optimize parallel processing")
                    else:
                        md.append("**Status**: ✅ Normal")
                        md.append("\nCurrent Direct I/O is within normal range.")
            
            # 기타 함수
            else:
                if language == "ko":
                    md.append(f"**설명**: {func_name} 함수의 I/O 활동\n")
                    md.append(f"**평균 I/O**: {avg_mb_per_s:.2f} MB/s\n")
                else:
                    md.append(f"**Description**: I/O activity for {func_name} function\n")
                    md.append(f"**Average I/O**: {avg_mb_per_s:.2f} MB/s\n")
            
            md.append("")
        
        # 전체 요약
        if language == "ko":
            md.append("### 전체 I/O 요약\n")
            md.append(f"- **총 I/O 부하**: {total_io:.2f} MB")
            md.append(f"- **주요 I/O 함수**: {function_analysis[0]['name']} ({function_analysis[0]['pct']:.1f}%)")
            
            # 병목 함수 식별
            bottleneck_funcs = [f for f in function_analysis if "병목" in f["status"] or "Bottleneck" in f["status"]]
            if bottleneck_funcs:
                md.append(f"- **병목 함수**: {', '.join([f['name'] for f in bottleneck_funcs])}")
                md.append("\n⚠️ **주의**: 병목 함수에 대한 즉시 조치가 필요합니다.")
            else:
                md.append("\n✅ 현재 심각한 I/O 병목은 없습니다.")
            
            md.append("")
        else:
            md.append("### Overall I/O Summary\n")
            md.append(f"- **Total I/O Load**: {total_io:.2f} MB")
            md.append(f"- **Primary I/O Function**: {function_analysis[0]['name']} ({function_analysis[0]['pct']:.1f}%)")
            
            # Identify bottleneck functions
            bottleneck_funcs = [f for f in function_analysis if "병목" in f["status"] or "Bottleneck" in f["status"]]
            if bottleneck_funcs:
                md.append(f"- **Bottleneck Functions**: {', '.join([f['name'] for f in bottleneck_funcs])}")
                md.append("\n⚠️ **Warning**: Immediate action required for bottleneck functions.")
            else:
                md.append("\n✅ No severe I/O bottlenecks currently.")
            
            md.append("")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_percentile_charts(awr_data) -> str:
        """백분위수 차트 생성 (Mermaid)
        
        Requirements 15.3을 구현합니다.
        
        Args:
            awr_data: AWR 데이터
            
        Returns:
            백분위수 차트 섹션 문자열
        """
        md = []
        
        md.append("## 백분위수 분포 차트\n")
        
        # CPU 백분위수 차트
        if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
            md.append("### CPU 사용률 백분위수 분포\n")
            
            # 백분위수 데이터 추출
            percentiles = []
            cpu_values = []
            
            # 정렬된 백분위수 순서
            percentile_order = [
                ("Average", "평균"),
                ("Median", "중간값"),
                ("75th_percentile", "75%"),
                ("90th_percentile", "90%"),
                ("95th_percentile", "95%"),
                ("97th_percentile", "97%"),
                ("99th_percentile", "99%"),
                ("99.9th_percentl", "99.9%"),
                ("99.99th_percntl", "99.99%"),
                ("Maximum_or_peak", "최대")
            ]
            
            for key, label in percentile_order:
                if key in awr_data.percentile_cpu:
                    cpu_data = awr_data.percentile_cpu[key]
                    percentiles.append(label)
                    cpu_values.append(cpu_data.on_cpu)
            
            if percentiles and cpu_values:
                # 테이블로 표시
                md.append("| 백분위수 | CPU 코어 수 |")
                md.append("|----------|-------------|")
                for label, value in zip(percentiles, cpu_values):
                    md.append(f"| {label} | {value} |")
                md.append("")
        
        # I/O 백분위수 차트
        if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
            md.append("### I/O 부하 백분위수 분포\n")
            
            # 백분위수 데이터 추출
            percentiles = []
            iops_values = []
            mbps_values = []
            
            # 정렬된 백분위수 순서
            percentile_order = [
                ("Average", "평균"),
                ("Median", "중간값"),
                ("75th_percentile", "75%"),
                ("90th_percentile", "90%"),
                ("95th_percentile", "95%"),
                ("97th_percentile", "97%"),
                ("99th_percentile", "99%"),
                ("99.9th_percentl", "99.9%"),
                ("Maximum_or_peak", "최대")
            ]
            
            for key, label in percentile_order:
                if key in awr_data.percentile_io:
                    io_data = awr_data.percentile_io[key]
                    percentiles.append(label)
                    iops_values.append(io_data.rw_iops)
                    mbps_values.append(io_data.rw_mbps)
            
            if percentiles and iops_values:
                # IOPS 테이블
                md.append("#### IOPS (읽기+쓰기)\n")
                md.append("| 백분위수 | IOPS |")
                md.append("|----------|------|")
                for label, value in zip(percentiles, iops_values):
                    md.append(f"| {label} | {value:,} |")
                md.append("")
                
                # MB/s 테이블
                md.append("#### 처리량 (MB/s)\n")
                md.append("| 백분위수 | MB/s |")
                md.append("|----------|------|")
                for label, value in zip(percentiles, mbps_values):
                    md.append(f"| {label} | {value} |")
                md.append("")
        
        # 백분위수 해석 가이드
        md.append("### 백분위수 해석 가이드\n")
        md.append("- **평균 (Average)**: 전체 기간의 평균값")
        md.append("- **중간값 (Median)**: 50번째 백분위수, 전체 값의 중간")
        md.append("- **75% (75th percentile)**: 75%의 시간 동안 이 값 이하")
        md.append("- **90% (90th percentile)**: 90%의 시간 동안 이 값 이하")
        md.append("- **95% (95th percentile)**: 95%의 시간 동안 이 값 이하")
        md.append("- **99% (99th percentile)**: 99%의 시간 동안 이 값 이하 (권장 사이징 기준)")
        md.append("- **99.9% (99.9th percentile)**: 99.9%의 시간 동안 이 값 이하")
        md.append("- **최대 (Maximum)**: 관측된 최대값 (일시적 스파이크 포함)\n")
        
        md.append("**인스턴스 사이징 권장사항**:")
        md.append("- P99 (99번째 백분위수) 값을 기준으로 인스턴스 크기를 결정하는 것을 권장합니다.")
        md.append("- P99 값에 30% 여유분을 추가하여 안정적인 운영을 보장합니다.")
        md.append("- 최대값은 일시적 스파이크일 수 있으므로 사이징 기준으로 사용하지 않습니다.")
        md.append("- 평균값만으로 사이징하면 피크 시간대에 성능 문제가 발생할 수 있습니다.\n")
        
        return "\n".join(md)
    
    @staticmethod
    def _generate_trend_report(awr_files: List, language: str) -> str:
        """추세 분석 리포트 생성
        
        Requirements 17.2, 17.3을 구현합니다.
        
        Args:
            awr_files: AWRData 객체 리스트
            language: 리포트 언어
            
        Returns:
            추세 분석 리포트 문자열
        """
        md = []
        
        if language == "ko":
            md.append("# AWR 추세 분석 보고서\n")
            md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md.append(f"분석 파일 수: {len(awr_files)}\n")
        else:
            md.append("# AWR Trend Analysis Report\n")
            md.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            md.append(f"Number of files analyzed: {len(awr_files)}\n")
        
        if len(awr_files) < 2:
            if language == "ko":
                md.append("추세 분석을 위해서는 최소 2개 이상의 AWR 파일이 필요합니다.\n")
            else:
                md.append("At least 2 AWR files are required for trend analysis.\n")
            return "\n".join(md)
        
        import statistics
        
        # 시계열 데이터 수집
        timestamps = []
        cpu_trends = []
        memory_trends = []
        iops_trends = []
        buffer_cache_trends = []
        
        for awr_data in awr_files:
            # 타임스탬프 (파일명 또는 스냅샷 시간에서 추출)
            if hasattr(awr_data, 'os_info') and awr_data.os_info:
                # 간단히 인덱스 사용
                timestamps.append(len(timestamps) + 1)
            
            # CPU 추세
            if hasattr(awr_data, 'percentile_cpu') and awr_data.percentile_cpu:
                p99_cpu = awr_data.percentile_cpu.get("99th_percentile")
                if p99_cpu:
                    cpu_trends.append(p99_cpu.on_cpu)
                else:
                    cpu_trends.append(None)
            else:
                cpu_trends.append(None)
            
            # 메모리 추세
            if hasattr(awr_data, 'memory_metrics') and awr_data.memory_metrics:
                avg_memory = statistics.mean(m.total_gb for m in awr_data.memory_metrics)
                memory_trends.append(avg_memory)
            else:
                memory_trends.append(None)
            
            # IOPS 추세
            if hasattr(awr_data, 'percentile_io') and awr_data.percentile_io:
                p99_io = awr_data.percentile_io.get("99th_percentile")
                if p99_io:
                    iops_trends.append(p99_io.rw_iops)
                else:
                    iops_trends.append(None)
            else:
                iops_trends.append(None)
            
            # 버퍼 캐시 히트율 추세
            if hasattr(awr_data, 'buffer_cache_stats') and awr_data.buffer_cache_stats:
                hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
                if hit_ratios:
                    buffer_cache_trends.append(statistics.mean(hit_ratios))
                else:
                    buffer_cache_trends.append(None)
            else:
                buffer_cache_trends.append(None)
        
        # CPU 추세 분석
        if any(v is not None for v in cpu_trends):
            if language == "ko":
                md.append("## CPU 사용률 추세\n")
            else:
                md.append("## CPU Usage Trend\n")
            
            # 유효한 값만 필터링
            valid_cpu = [v for v in cpu_trends if v is not None]
            
            if len(valid_cpu) >= 2:
                # 추세 계산
                first_value = valid_cpu[0]
                last_value = valid_cpu[-1]
                change_pct = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
                
                if language == "ko":
                    md.append(f"- **초기 값**: {first_value} 코어")
                    md.append(f"- **최종 값**: {last_value} 코어")
                    md.append(f"- **변화율**: {change_pct:+.1f}%")
                    
                    # 이상 징후 감지
                    if abs(change_pct) > 50:
                        md.append(f"\n⚠️ **이상 징후 감지**: CPU 사용률이 {abs(change_pct):.1f}% {'증가' if change_pct > 0 else '감소'}했습니다.")
                        md.append("원인 분석 및 조치가 필요합니다.\n")
                    elif abs(change_pct) > 30:
                        md.append(f"\n⚠️ **주의**: CPU 사용률이 {abs(change_pct):.1f}% {'증가' if change_pct > 0 else '감소'} 추세입니다.\n")
                    else:
                        md.append("\n✅ CPU 사용률이 안정적입니다.\n")
                else:
                    md.append(f"- **Initial value**: {first_value} cores")
                    md.append(f"- **Final value**: {last_value} cores")
                    md.append(f"- **Change rate**: {change_pct:+.1f}%")
                    
                    # Anomaly detection
                    if abs(change_pct) > 50:
                        md.append(f"\n⚠️ **Anomaly detected**: CPU usage {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}%.")
                        md.append("Root cause analysis and action required.\n")
                    elif abs(change_pct) > 30:
                        md.append(f"\n⚠️ **Warning**: CPU usage trending {'up' if change_pct > 0 else 'down'} by {abs(change_pct):.1f}%.\n")
                    else:
                        md.append("\n✅ CPU usage is stable.\n")
        
        # 메모리 추세 분석
        if any(v is not None for v in memory_trends):
            if language == "ko":
                md.append("## 메모리 사용량 추세\n")
            else:
                md.append("## Memory Usage Trend\n")
            
            valid_memory = [v for v in memory_trends if v is not None]
            
            if len(valid_memory) >= 2:
                first_value = valid_memory[0]
                last_value = valid_memory[-1]
                change_pct = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
                
                if language == "ko":
                    md.append(f"- **초기 값**: {first_value:.2f} GB")
                    md.append(f"- **최종 값**: {last_value:.2f} GB")
                    md.append(f"- **변화율**: {change_pct:+.1f}%")
                    
                    if abs(change_pct) > 30:
                        md.append(f"\n⚠️ **이상 징후 감지**: 메모리 사용량이 {abs(change_pct):.1f}% {'증가' if change_pct > 0 else '감소'}했습니다.\n")
                    elif abs(change_pct) > 20:
                        md.append(f"\n⚠️ **주의**: 메모리 사용량이 {abs(change_pct):.1f}% {'증가' if change_pct > 0 else '감소'} 추세입니다.\n")
                    else:
                        md.append("\n✅ 메모리 사용량이 안정적입니다.\n")
                else:
                    md.append(f"- **Initial value**: {first_value:.2f} GB")
                    md.append(f"- **Final value**: {last_value:.2f} GB")
                    md.append(f"- **Change rate**: {change_pct:+.1f}%")
                    
                    if abs(change_pct) > 30:
                        md.append(f"\n⚠️ **Anomaly detected**: Memory usage {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}%.\n")
                    elif abs(change_pct) > 20:
                        md.append(f"\n⚠️ **Warning**: Memory usage trending {'up' if change_pct > 0 else 'down'} by {abs(change_pct):.1f}%.\n")
                    else:
                        md.append("\n✅ Memory usage is stable.\n")
        
        # IOPS 추세 분석
        if any(v is not None for v in iops_trends):
            if language == "ko":
                md.append("## I/O 부하 추세\n")
            else:
                md.append("## I/O Load Trend\n")
            
            valid_iops = [v for v in iops_trends if v is not None]
            
            if len(valid_iops) >= 2:
                first_value = valid_iops[0]
                last_value = valid_iops[-1]
                change_pct = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
                
                if language == "ko":
                    md.append(f"- **초기 값**: {first_value:,} IOPS")
                    md.append(f"- **최종 값**: {last_value:,} IOPS")
                    md.append(f"- **변화율**: {change_pct:+.1f}%")
                    
                    if abs(change_pct) > 50:
                        md.append(f"\n⚠️ **이상 징후 감지**: I/O 부하가 {abs(change_pct):.1f}% {'증가' if change_pct > 0 else '감소'}했습니다.\n")
                    elif abs(change_pct) > 30:
                        md.append(f"\n⚠️ **주의**: I/O 부하가 {abs(change_pct):.1f}% {'증가' if change_pct > 0 else '감소'} 추세입니다.\n")
                    else:
                        md.append("\n✅ I/O 부하가 안정적입니다.\n")
                else:
                    md.append(f"- **Initial value**: {first_value:,} IOPS")
                    md.append(f"- **Final value**: {last_value:,} IOPS")
                    md.append(f"- **Change rate**: {change_pct:+.1f}%")
                    
                    if abs(change_pct) > 50:
                        md.append(f"\n⚠️ **Anomaly detected**: I/O load {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}%.\n")
                    elif abs(change_pct) > 30:
                        md.append(f"\n⚠️ **Warning**: I/O load trending {'up' if change_pct > 0 else 'down'} by {abs(change_pct):.1f}%.\n")
                    else:
                        md.append("\n✅ I/O load is stable.\n")
        
        # 버퍼 캐시 히트율 추세 분석
        if any(v is not None for v in buffer_cache_trends):
            if language == "ko":
                md.append("## 버퍼 캐시 히트율 추세\n")
            else:
                md.append("## Buffer Cache Hit Ratio Trend\n")
            
            valid_cache = [v for v in buffer_cache_trends if v is not None]
            
            if len(valid_cache) >= 2:
                first_value = valid_cache[0]
                last_value = valid_cache[-1]
                change = last_value - first_value
                
                if language == "ko":
                    md.append(f"- **초기 값**: {first_value:.2f}%")
                    md.append(f"- **최종 값**: {last_value:.2f}%")
                    md.append(f"- **변화**: {change:+.2f}%p")
                    
                    if change < -5:
                        md.append(f"\n⚠️ **이상 징후 감지**: 버퍼 캐시 히트율이 {abs(change):.2f}%p 하락했습니다.")
                        md.append("버퍼 캐시 크기 증가 또는 쿼리 최적화가 필요합니다.\n")
                    elif change < -2:
                        md.append(f"\n⚠️ **주의**: 버퍼 캐시 히트율이 {abs(change):.2f}%p 하락 추세입니다.\n")
                    elif change > 2:
                        md.append(f"\n✅ 버퍼 캐시 히트율이 {change:.2f}%p 개선되었습니다.\n")
                    else:
                        md.append("\n✅ 버퍼 캐시 히트율이 안정적입니다.\n")
                else:
                    md.append(f"- **Initial value**: {first_value:.2f}%")
                    md.append(f"- **Final value**: {last_value:.2f}%")
                    md.append(f"- **Change**: {change:+.2f}%p")
                    
                    if change < -5:
                        md.append(f"\n⚠️ **Anomaly detected**: Buffer cache hit ratio decreased by {abs(change):.2f}%p.")
                        md.append("Buffer cache size increase or query optimization needed.\n")
                    elif change < -2:
                        md.append(f"\n⚠️ **Warning**: Buffer cache hit ratio trending down by {abs(change):.2f}%p.\n")
                    elif change > 2:
                        md.append(f"\n✅ Buffer cache hit ratio improved by {change:.2f}%p.\n")
                    else:
                        md.append("\n✅ Buffer cache hit ratio is stable.\n")
        
        # 전체 요약
        if language == "ko":
            md.append("## 전체 추세 요약\n")
            md.append("### 주요 발견사항\n")
            
            # 이상 징후 요약
            anomalies = []
            
            if any(v is not None for v in cpu_trends):
                valid_cpu = [v for v in cpu_trends if v is not None]
                if len(valid_cpu) >= 2:
                    change_pct = ((valid_cpu[-1] - valid_cpu[0]) / valid_cpu[0] * 100) if valid_cpu[0] > 0 else 0
                    if abs(change_pct) > 50:
                        anomalies.append(f"CPU 사용률 급격한 변화 ({change_pct:+.1f}%)")
            
            if any(v is not None for v in iops_trends):
                valid_iops = [v for v in iops_trends if v is not None]
                if len(valid_iops) >= 2:
                    change_pct = ((valid_iops[-1] - valid_iops[0]) / valid_iops[0] * 100) if valid_iops[0] > 0 else 0
                    if abs(change_pct) > 50:
                        anomalies.append(f"I/O 부하 급격한 변화 ({change_pct:+.1f}%)")
            
            if any(v is not None for v in buffer_cache_trends):
                valid_cache = [v for v in buffer_cache_trends if v is not None]
                if len(valid_cache) >= 2:
                    change = valid_cache[-1] - valid_cache[0]
                    if change < -5:
                        anomalies.append(f"버퍼 캐시 히트율 하락 ({change:.2f}%p)")
            
            if anomalies:
                md.append("**감지된 이상 징후:**\n")
                for anomaly in anomalies:
                    md.append(f"- ⚠️ {anomaly}")
                md.append("\n**권장 조치:**")
                md.append("1. 이상 징후가 발생한 시점의 애플리케이션 변경사항 확인")
                md.append("2. 해당 시점의 상세 AWR 리포트 분석")
                md.append("3. 필요시 인스턴스 크기 조정 또는 쿼리 최적화")
                md.append("4. 지속적인 모니터링 및 알람 설정\n")
            else:
                md.append("✅ 분석 기간 동안 심각한 이상 징후가 감지되지 않았습니다.\n")
        else:
            md.append("## Overall Trend Summary\n")
            md.append("### Key Findings\n")
            
            # Anomaly summary
            anomalies = []
            
            if any(v is not None for v in cpu_trends):
                valid_cpu = [v for v in cpu_trends if v is not None]
                if len(valid_cpu) >= 2:
                    change_pct = ((valid_cpu[-1] - valid_cpu[0]) / valid_cpu[0] * 100) if valid_cpu[0] > 0 else 0
                    if abs(change_pct) > 50:
                        anomalies.append(f"Rapid CPU usage change ({change_pct:+.1f}%)")
            
            if any(v is not None for v in iops_trends):
                valid_iops = [v for v in iops_trends if v is not None]
                if len(valid_iops) >= 2:
                    change_pct = ((valid_iops[-1] - valid_iops[0]) / valid_iops[0] * 100) if valid_iops[0] > 0 else 0
                    if abs(change_pct) > 50:
                        anomalies.append(f"Rapid I/O load change ({change_pct:+.1f}%)")
            
            if any(v is not None for v in buffer_cache_trends):
                valid_cache = [v for v in buffer_cache_trends if v is not None]
                if len(valid_cache) >= 2:
                    change = valid_cache[-1] - valid_cache[0]
                    if change < -5:
                        anomalies.append(f"Buffer cache hit ratio decline ({change:.2f}%p)")
            
            if anomalies:
                md.append("**Detected Anomalies:**\n")
                for anomaly in anomalies:
                    md.append(f"- ⚠️ {anomaly}")
                md.append("\n**Recommended Actions:**")
                md.append("1. Check application changes at the time of anomaly")
                md.append("2. Analyze detailed AWR reports for that period")
                md.append("3. Adjust instance size or optimize queries if needed")
                md.append("4. Set up continuous monitoring and alerts\n")
            else:
                md.append("✅ No severe anomalies detected during the analysis period.\n")
        
        return "\n".join(md)
    
    @staticmethod
    def compare_awr_reports(awr1, awr2, language: str) -> str:
        """두 AWR 리포트 비교
        
        Requirements 13.3을 구현합니다.
        
        Args:
            awr1: 첫 번째 AWR 데이터
            awr2: 두 번째 AWR 데이터
            language: 리포트 언어
            
        Returns:
            비교 리포트 문자열
        """
        md = []
        
        if language == "ko":
            md.append("# AWR 리포트 비교 분석\n")
            md.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        else:
            md.append("# AWR Report Comparison Analysis\n")
            md.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 리포트 타입 확인
        is_awr1 = hasattr(awr1, 'is_awr') and awr1.is_awr()
        is_awr2 = hasattr(awr2, 'is_awr') and awr2.is_awr()
        
        if language == "ko":
            md.append("## 리포트 타입\n")
            md.append(f"- **리포트 1**: {'AWR' if is_awr1 else 'Statspack'}")
            md.append(f"- **리포트 2**: {'AWR' if is_awr2 else 'Statspack'}")
            md.append("")
        else:
            md.append("## Report Type\n")
            md.append(f"- **Report 1**: {'AWR' if is_awr1 else 'Statspack'}")
            md.append(f"- **Report 2**: {'AWR' if is_awr2 else 'Statspack'}")
            md.append("")
        
        # 시스템 정보 비교
        if language == "ko":
            md.append("## 시스템 정보 비교\n")
            md.append("| 항목 | 리포트 1 | 리포트 2 | 변화 |")
        else:
            md.append("## System Information Comparison\n")
            md.append("| Item | Report 1 | Report 2 | Change |")
        
        md.append("|------|----------|----------|------|")
        
        # DB 이름
        db1 = awr1.os_info.db_name or "N/A"
        db2 = awr2.os_info.db_name or "N/A"
        md.append(f"| DB Name | {db1} | {db2} | {'-' if db1 == db2 else '변경됨' if language == 'ko' else 'Changed'} |")
        
        # 버전
        ver1 = awr1.os_info.version or "N/A"
        ver2 = awr2.os_info.version or "N/A"
        md.append(f"| Version | {ver1} | {ver2} | {'-' if ver1 == ver2 else '변경됨' if language == 'ko' else 'Changed'} |")
        
        # CPU
        cpu1 = awr1.os_info.num_cpus or awr1.os_info.num_cpu_cores or 0
        cpu2 = awr2.os_info.num_cpus or awr2.os_info.num_cpu_cores or 0
        cpu_change = cpu2 - cpu1
        md.append(f"| CPU Cores | {cpu1} | {cpu2} | {cpu_change:+d} |")
        
        # 메모리
        mem1 = awr1.os_info.physical_memory_gb or 0
        mem2 = awr2.os_info.physical_memory_gb or 0
        mem_change = mem2 - mem1
        md.append(f"| Memory (GB) | {mem1:.1f} | {mem2:.1f} | {mem_change:+.1f} |")
        
        # DB 크기
        size1 = awr1.os_info.total_db_size_gb or 0
        size2 = awr2.os_info.total_db_size_gb or 0
        size_change = size2 - size1
        size_change_pct = (size_change / size1 * 100) if size1 > 0 else 0
        md.append(f"| DB Size (GB) | {size1:.1f} | {size2:.1f} | {size_change:+.1f} ({size_change_pct:+.1f}%) |")
        
        md.append("")
        
        # 성능 메트릭 비교
        import statistics
        
        if language == "ko":
            md.append("## 성능 메트릭 비교\n")
        else:
            md.append("## Performance Metrics Comparison\n")
        
        # CPU 사용률 비교
        if is_awr1 and is_awr2:
            # AWR 데이터인 경우 P99 사용
            if hasattr(awr1, 'percentile_cpu') and awr1.percentile_cpu and hasattr(awr2, 'percentile_cpu') and awr2.percentile_cpu:
                p99_cpu1 = awr1.percentile_cpu.get("99th_percentile")
                p99_cpu2 = awr2.percentile_cpu.get("99th_percentile")
                
                if p99_cpu1 and p99_cpu2:
                    cpu1_val = p99_cpu1.on_cpu
                    cpu2_val = p99_cpu2.on_cpu
                    cpu_change = cpu2_val - cpu1_val
                    cpu_change_pct = (cpu_change / cpu1_val * 100) if cpu1_val > 0 else 0
                    
                    if language == "ko":
                        md.append(f"### CPU 사용률 (P99)\n")
                        md.append(f"- **리포트 1**: {cpu1_val} 코어")
                        md.append(f"- **리포트 2**: {cpu2_val} 코어")
                        md.append(f"- **변화**: {cpu_change:+d} 코어 ({cpu_change_pct:+.1f}%)")
                        
                        if abs(cpu_change_pct) > 30:
                            md.append(f"\n⚠️ **주의**: CPU 사용률이 {abs(cpu_change_pct):.1f}% {'증가' if cpu_change_pct > 0 else '감소'}했습니다.\n")
                        else:
                            md.append("")
                    else:
                        md.append(f"### CPU Usage (P99)\n")
                        md.append(f"- **Report 1**: {cpu1_val} cores")
                        md.append(f"- **Report 2**: {cpu2_val} cores")
                        md.append(f"- **Change**: {cpu_change:+d} cores ({cpu_change_pct:+.1f}%)")
                        
                        if abs(cpu_change_pct) > 30:
                            md.append(f"\n⚠️ **Warning**: CPU usage {'increased' if cpu_change_pct > 0 else 'decreased'} by {abs(cpu_change_pct):.1f}%.\n")
                        else:
                            md.append("")
        
        # 메모리 사용량 비교
        if awr1.memory_metrics and awr2.memory_metrics:
            mem1_avg = statistics.mean(m.total_gb for m in awr1.memory_metrics)
            mem2_avg = statistics.mean(m.total_gb for m in awr2.memory_metrics)
            mem_change = mem2_avg - mem1_avg
            mem_change_pct = (mem_change / mem1_avg * 100) if mem1_avg > 0 else 0
            
            if language == "ko":
                md.append(f"### 메모리 사용량 (평균)\n")
                md.append(f"- **리포트 1**: {mem1_avg:.2f} GB")
                md.append(f"- **리포트 2**: {mem2_avg:.2f} GB")
                md.append(f"- **변화**: {mem_change:+.2f} GB ({mem_change_pct:+.1f}%)")
                
                if abs(mem_change_pct) > 20:
                    md.append(f"\n⚠️ **주의**: 메모리 사용량이 {abs(mem_change_pct):.1f}% {'증가' if mem_change_pct > 0 else '감소'}했습니다.\n")
                else:
                    md.append("")
            else:
                md.append(f"### Memory Usage (Average)\n")
                md.append(f"- **Report 1**: {mem1_avg:.2f} GB")
                md.append(f"- **Report 2**: {mem2_avg:.2f} GB")
                md.append(f"- **Change**: {mem_change:+.2f} GB ({mem_change_pct:+.1f}%)")
                
                if abs(mem_change_pct) > 20:
                    md.append(f"\n⚠️ **Warning**: Memory usage {'increased' if mem_change_pct > 0 else 'decreased'} by {abs(mem_change_pct):.1f}%.\n")
                else:
                    md.append("")
        
        # I/O 부하 비교
        if is_awr1 and is_awr2:
            if hasattr(awr1, 'percentile_io') and awr1.percentile_io and hasattr(awr2, 'percentile_io') and awr2.percentile_io:
                p99_io1 = awr1.percentile_io.get("99th_percentile")
                p99_io2 = awr2.percentile_io.get("99th_percentile")
                
                if p99_io1 and p99_io2:
                    iops1 = p99_io1.rw_iops
                    iops2 = p99_io2.rw_iops
                    iops_change = iops2 - iops1
                    iops_change_pct = (iops_change / iops1 * 100) if iops1 > 0 else 0
                    
                    if language == "ko":
                        md.append(f"### I/O 부하 (P99 IOPS)\n")
                        md.append(f"- **리포트 1**: {iops1:,} IOPS")
                        md.append(f"- **리포트 2**: {iops2:,} IOPS")
                        md.append(f"- **변화**: {iops_change:+,} IOPS ({iops_change_pct:+.1f}%)")
                        
                        if abs(iops_change_pct) > 30:
                            md.append(f"\n⚠️ **주의**: I/O 부하가 {abs(iops_change_pct):.1f}% {'증가' if iops_change_pct > 0 else '감소'}했습니다.\n")
                        else:
                            md.append("")
                    else:
                        md.append(f"### I/O Load (P99 IOPS)\n")
                        md.append(f"- **Report 1**: {iops1:,} IOPS")
                        md.append(f"- **Report 2**: {iops2:,} IOPS")
                        md.append(f"- **Change**: {iops_change:+,} IOPS ({iops_change_pct:+.1f}%)")
                        
                        if abs(iops_change_pct) > 30:
                            md.append(f"\n⚠️ **Warning**: I/O load {'increased' if iops_change_pct > 0 else 'decreased'} by {abs(iops_change_pct):.1f}%.\n")
                        else:
                            md.append("")
        
        # 버퍼 캐시 히트율 비교
        if is_awr1 and is_awr2:
            if hasattr(awr1, 'buffer_cache_stats') and awr1.buffer_cache_stats and hasattr(awr2, 'buffer_cache_stats') and awr2.buffer_cache_stats:
                hit_ratios1 = [stat.hit_ratio for stat in awr1.buffer_cache_stats if stat.hit_ratio is not None]
                hit_ratios2 = [stat.hit_ratio for stat in awr2.buffer_cache_stats if stat.hit_ratio is not None]
                
                if hit_ratios1 and hit_ratios2:
                    avg1 = statistics.mean(hit_ratios1)
                    avg2 = statistics.mean(hit_ratios2)
                    change = avg2 - avg1
                    
                    if language == "ko":
                        md.append(f"### 버퍼 캐시 히트율\n")
                        md.append(f"- **리포트 1**: {avg1:.2f}%")
                        md.append(f"- **리포트 2**: {avg2:.2f}%")
                        md.append(f"- **변화**: {change:+.2f}%p")
                        
                        if change < -2:
                            md.append(f"\n⚠️ **주의**: 버퍼 캐시 히트율이 {abs(change):.2f}%p 하락했습니다.\n")
                        elif change > 2:
                            md.append(f"\n✅ 버퍼 캐시 히트율이 {change:.2f}%p 개선되었습니다.\n")
                        else:
                            md.append("")
                    else:
                        md.append(f"### Buffer Cache Hit Ratio\n")
                        md.append(f"- **Report 1**: {avg1:.2f}%")
                        md.append(f"- **Report 2**: {avg2:.2f}%")
                        md.append(f"- **Change**: {change:+.2f}%p")
                        
                        if change < -2:
                            md.append(f"\n⚠️ **Warning**: Buffer cache hit ratio decreased by {abs(change):.2f}%p.\n")
                        elif change > 2:
                            md.append(f"\n✅ Buffer cache hit ratio improved by {change:.2f}%p.\n")
                        else:
                            md.append("")
        
        # 요약 및 권장사항
        if language == "ko":
            md.append("## 요약 및 권장사항\n")
            md.append("### 주요 변화\n")
            
            # 주요 변화 요약
            changes = []
            
            if cpu_change != 0:
                changes.append(f"CPU 코어 수: {cpu_change:+d}")
            
            if mem_change != 0:
                changes.append(f"메모리: {mem_change:+.1f} GB")
            
            if size_change_pct > 10:
                changes.append(f"DB 크기: {size_change_pct:+.1f}% 증가")
            
            if changes:
                for change in changes:
                    md.append(f"- {change}")
                md.append("")
            else:
                md.append("시스템 구성에 큰 변화가 없습니다.\n")
            
            md.append("### 권장사항\n")
            md.append("1. 성능 메트릭의 변화 추세를 지속적으로 모니터링하세요.")
            md.append("2. 급격한 변화가 있는 경우 원인을 분석하세요.")
            md.append("3. 필요시 인스턴스 크기 조정을 고려하세요.")
            md.append("4. 정기적으로 AWR 리포트를 비교하여 추세를 파악하세요.")
            md.append("")
        else:
            md.append("## Summary and Recommendations\n")
            md.append("### Key Changes\n")
            
            # Key changes summary
            changes = []
            
            if cpu_change != 0:
                changes.append(f"CPU cores: {cpu_change:+d}")
            
            if mem_change != 0:
                changes.append(f"Memory: {mem_change:+.1f} GB")
            
            if size_change_pct > 10:
                changes.append(f"DB size: {size_change_pct:+.1f}% increase")
            
            if changes:
                for change in changes:
                    md.append(f"- {change}")
                md.append("")
            else:
                md.append("No significant changes in system configuration.\n")
            
            md.append("### Recommendations\n")
            md.append("1. Continuously monitor performance metric trends.")
            md.append("2. Analyze the root cause of any rapid changes.")
            md.append("3. Consider instance size adjustment if needed.")
            md.append("4. Regularly compare AWR reports to identify trends.")
            md.append("")
        
        return "\n".join(md)
