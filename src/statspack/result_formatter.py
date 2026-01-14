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

from src.statspack.data_models import (
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
            md.append("| Snap | Duration (m) | CPU/s | Read IOPS | Write IOPS | Commits/s |")
            md.append("|------|--------------|-------|-----------|------------|-----------|")
            for metric in statspack_data.main_metrics[:10]:  # 최대 10개만 표시
                md.append(f"| {metric.snap} | {metric.dur_m:.1f} | {metric.cpu_per_s:.2f} | "
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
                from src.statspack.data_models import statspack_to_dict
                file_dict["statspack_data"] = statspack_to_dict(file_result.statspack_data)
                
                # 마이그레이션 분석 포함
                if file_result.migration_analysis:
                    from src.statspack.data_models import migration_complexity_to_dict
                    migration_dict = {}
                    for target, complexity in file_result.migration_analysis.items():
                        migration_dict[target.value] = migration_complexity_to_dict(complexity)
                    file_dict["migration_analysis"] = migration_dict
            
            result_dict["file_results"].append(file_dict)
        
        return json.dumps(result_dict, indent=2, ensure_ascii=False)
