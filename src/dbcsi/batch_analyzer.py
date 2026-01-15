"""
Statspack 배치 분석 모듈

여러 Statspack 파일을 한 번에 분석하는 기능을 제공합니다.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import statistics

from .parser import StatspackParser
from .exceptions import StatspackParseError, StatspackFileError
from .data_models import StatspackData, AWRData
from .migration_analyzer import MigrationAnalyzer, MigrationComplexity, TargetDatabase
from .logging_config import get_logger

# 로거 초기화
logger = get_logger("batch_analyzer")


@dataclass
class BatchFileResult:
    """배치 분석 개별 파일 결과"""
    filepath: str
    filename: str
    success: bool
    error_message: Optional[str] = None
    statspack_data: Optional[Union[StatspackData, AWRData]] = None
    migration_analysis: Optional[Dict[TargetDatabase, MigrationComplexity]] = None
    timestamp: Optional[str] = None  # 파일의 타임스탬프 (추세 분석용)


@dataclass
class TrendMetrics:
    """추세 분석 메트릭"""
    metric_name: str
    values: List[float]
    timestamps: List[str]
    avg: float
    min_val: float
    max_val: float
    std_dev: float
    trend: str  # "increasing", "decreasing", "stable"
    change_pct: float  # 첫 값 대비 마지막 값의 변화율


@dataclass
class Anomaly:
    """이상 징후"""
    timestamp: str
    filename: str
    metric_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: str  # "low", "medium", "high"
    description: str


@dataclass
class TrendAnalysisResult:
    """추세 분석 결과"""
    cpu_trend: Optional[TrendMetrics] = None
    io_trend: Optional[TrendMetrics] = None
    memory_trend: Optional[TrendMetrics] = None
    buffer_cache_trend: Optional[TrendMetrics] = None
    anomalies: List[Anomaly] = field(default_factory=list)


@dataclass
class BatchAnalysisResult:
    """배치 분석 전체 결과"""
    total_files: int
    successful_files: int
    failed_files: int
    file_results: List[BatchFileResult]
    analysis_timestamp: str
    trend_analysis: Optional[TrendAnalysisResult] = None


class BatchAnalyzer:
    """
    Statspack 배치 분석기
    
    디렉토리 내의 여러 .out 파일을 한 번에 분석합니다.
    """
    
    def __init__(self, directory: str):
        """
        배치 분석기 초기화
        
        Args:
            directory: Statspack 파일이 있는 디렉토리 경로
            
        Raises:
            FileNotFoundError: 디렉토리가 존재하지 않는 경우
            NotADirectoryError: 경로가 디렉토리가 아닌 경우
        """
        self.directory = Path(directory)
        
        # 디렉토리 존재 확인
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # 디렉토리인지 확인
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    def find_statspack_files(self) -> List[Path]:
        """
        디렉토리에서 .out 파일 찾기
        
        Returns:
            .out 파일 경로 리스트 (정렬됨)
        """
        # .out 확장자를 가진 파일 찾기
        out_files = list(self.directory.glob("*.out"))
        
        # 파일명으로 정렬
        out_files.sort(key=lambda p: p.name)
        
        return out_files
    
    def analyze_batch(
        self, 
        analyze_migration: bool = False,
        target: Optional[TargetDatabase] = None,
        analyze_trends: bool = False
    ) -> BatchAnalysisResult:
        """
        배치 파일 분석 실행
        
        각 파일을 순차적으로 파싱하고, 오류 발생 시 건너뛰고 계속 진행합니다.
        
        Args:
            analyze_migration: 마이그레이션 난이도 분석 포함 여부
            target: 특정 타겟 데이터베이스 (None이면 모든 타겟)
            analyze_trends: 추세 분석 포함 여부
            
        Returns:
            BatchAnalysisResult: 배치 분석 결과
        """
        # .out 파일 찾기
        out_files = self.find_statspack_files()
        
        if not out_files:
            # 파일이 없어도 빈 결과 반환
            return BatchAnalysisResult(
                total_files=0,
                successful_files=0,
                failed_files=0,
                file_results=[],
                analysis_timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            )
        
        file_results = []
        successful_count = 0
        failed_count = 0
        
        # 각 파일 순차 처리
        for filepath in out_files:
            result = self._analyze_single_file(
                filepath, 
                analyze_migration=analyze_migration,
                target=target
            )
            
            file_results.append(result)
            
            if result.success:
                successful_count += 1
            else:
                failed_count += 1
        
        # 추세 분석 (선택적)
        trend_analysis = None
        if analyze_trends and successful_count > 1:
            trend_analysis = self._analyze_trends(file_results)
        
        # 배치 분석 결과 생성
        return BatchAnalysisResult(
            total_files=len(out_files),
            successful_files=successful_count,
            failed_files=failed_count,
            file_results=file_results,
            analysis_timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            trend_analysis=trend_analysis
        )
    
    def _analyze_single_file(
        self,
        filepath: Path,
        analyze_migration: bool = False,
        target: Optional[TargetDatabase] = None
    ) -> BatchFileResult:
        """
        단일 파일 분석
        
        Args:
            filepath: 파일 경로
            analyze_migration: 마이그레이션 난이도 분석 포함 여부
            target: 특정 타겟 데이터베이스
            
        Returns:
            BatchFileResult: 파일 분석 결과
        """
        try:
            # 파일 타입 자동 감지 (AWR vs Statspack)
            file_type = self._detect_file_type(filepath)
            
            # 적절한 파서 선택
            if file_type == "awr":
                from src.dbcsi.parser import AWRParser
                parser = AWRParser(str(filepath))
            else:
                parser = StatspackParser(str(filepath))
            
            # 파일 파싱
            statspack_data = parser.parse()
            
            # 타임스탬프 추출 (파일명 또는 데이터에서)
            timestamp = self._extract_timestamp(filepath, statspack_data)
            
            # 마이그레이션 분석 (선택적)
            migration_analysis = None
            if analyze_migration:
                # AWR 데이터인 경우 EnhancedMigrationAnalyzer 사용
                if hasattr(statspack_data, 'is_awr') and statspack_data.is_awr():
                    from src.dbcsi.migration_analyzer import EnhancedMigrationAnalyzer
                    analyzer = EnhancedMigrationAnalyzer(statspack_data)
                else:
                    analyzer = MigrationAnalyzer(statspack_data)
                
                migration_analysis = analyzer.analyze(target=target)
            
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=True,
                statspack_data=statspack_data,
                migration_analysis=migration_analysis,
                timestamp=timestamp
            )
            
        except (StatspackParseError, StatspackFileError) as e:
            # 파싱 오류 - 건너뛰고 계속 진행
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            # 기타 예외 - 건너뛰고 계속 진행
            return BatchFileResult(
                filepath=str(filepath),
                filename=filepath.name,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _detect_file_type(self, filepath: Path) -> str:
        """
        파일 타입 자동 감지 (AWR vs Statspack)
        
        파일 내용의 처음 몇 줄을 읽어서 AWR 특화 마커를 찾습니다.
        
        Args:
            filepath: 파일 경로
            
        Returns:
            "awr" 또는 "statspack"
        """
        awr_markers = [
            "~~BEGIN-IOSTAT-FUNCTION~~",
            "~~BEGIN-PERCENT-CPU~~",
            "~~BEGIN-PERCENT-IO~~",
            "~~BEGIN-WORKLOAD~~",
            "~~BEGIN-BUFFER-CACHE~~"
        ]
        
        try:
            # UTF-8로 시도
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(50000)  # 처음 50KB만 읽기
        except UnicodeDecodeError:
            # Latin-1로 폴백
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read(50000)
            except Exception:
                # 읽기 실패 시 Statspack으로 간주
                return "statspack"
        except Exception:
            return "statspack"
        
        # AWR 마커 확인
        for marker in awr_markers:
            if marker in content:
                return "awr"
        
        return "statspack"
    
    def _extract_timestamp(self, filepath: Path, data: Union[StatspackData, AWRData]) -> str:
        """
        파일 또는 데이터에서 타임스탬프 추출
        
        Args:
            filepath: 파일 경로
            data: Statspack 또는 AWR 데이터
            
        Returns:
            타임스탬프 문자열
        """
        # 1. 데이터에서 타임스탬프 추출 시도
        if data.main_metrics and len(data.main_metrics) > 0:
            # 마지막 스냅샷의 종료 시간 사용
            return data.main_metrics[-1].end
        
        # 2. 파일 수정 시간 사용
        try:
            mtime = filepath.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            # 3. 현재 시간 사용 (최후의 수단)
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _analyze_trends(self, file_results: List[BatchFileResult]) -> TrendAnalysisResult:
        """
        추세 분석 수행
        
        Args:
            file_results: 파일 분석 결과 리스트
            
        Returns:
            TrendAnalysisResult: 추세 분석 결과
        """
        # 성공한 결과만 필터링
        successful_results = [r for r in file_results if r.success and r.statspack_data]
        
        if len(successful_results) < 2:
            return TrendAnalysisResult()
        
        # 타임스탬프 순으로 정렬
        successful_results.sort(key=lambda r: r.timestamp or "")
        
        # CPU 추세 분석
        cpu_trend = self._analyze_cpu_trend(successful_results)
        
        # I/O 추세 분석
        io_trend = self._analyze_io_trend(successful_results)
        
        # 메모리 추세 분석
        memory_trend = self._analyze_memory_trend(successful_results)
        
        # 버퍼 캐시 추세 분석 (AWR 데이터만)
        buffer_cache_trend = self._analyze_buffer_cache_trend(successful_results)
        
        # 이상 징후 감지
        anomalies = self._detect_anomalies(successful_results, cpu_trend, io_trend, memory_trend, buffer_cache_trend)
        
        return TrendAnalysisResult(
            cpu_trend=cpu_trend,
            io_trend=io_trend,
            memory_trend=memory_trend,
            buffer_cache_trend=buffer_cache_trend,
            anomalies=anomalies
        )
    
    def _analyze_cpu_trend(self, results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """CPU 사용률 추세 분석"""
        values = []
        timestamps = []
        
        for result in results:
            if result.statspack_data and result.statspack_data.main_metrics:
                # 평균 CPU 사용률 계산
                avg_cpu = statistics.mean([m.cpu_per_s for m in result.statspack_data.main_metrics if m.cpu_per_s > 0])
                if avg_cpu > 0:
                    values.append(avg_cpu)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return self._calculate_trend_metrics("CPU Usage (per second)", values, timestamps)
    
    def _analyze_io_trend(self, results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """I/O 부하 추세 분석"""
        values = []
        timestamps = []
        
        for result in results:
            if result.statspack_data and result.statspack_data.main_metrics:
                # 평균 I/O (읽기 + 쓰기 IOPS) 계산
                avg_io = statistics.mean([
                    m.read_iops + m.write_iops 
                    for m in result.statspack_data.main_metrics 
                    if (m.read_iops + m.write_iops) > 0
                ])
                if avg_io > 0:
                    values.append(avg_io)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return self._calculate_trend_metrics("I/O IOPS", values, timestamps)
    
    def _analyze_memory_trend(self, results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """메모리 사용량 추세 분석"""
        values = []
        timestamps = []
        
        for result in results:
            if result.statspack_data and result.statspack_data.memory_metrics:
                # 평균 메모리 사용량 계산
                avg_memory = statistics.mean([m.total_gb for m in result.statspack_data.memory_metrics])
                if avg_memory > 0:
                    values.append(avg_memory)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return self._calculate_trend_metrics("Memory Usage (GB)", values, timestamps)
    
    def _analyze_buffer_cache_trend(self, results: List[BatchFileResult]) -> Optional[TrendMetrics]:
        """버퍼 캐시 히트율 추세 분석 (AWR 전용)"""
        values = []
        timestamps = []
        
        for result in results:
            # AWR 데이터인지 확인
            if isinstance(result.statspack_data, AWRData) and result.statspack_data.buffer_cache_stats:
                # 평균 히트율 계산
                avg_hit_ratio = statistics.mean([b.hit_ratio for b in result.statspack_data.buffer_cache_stats])
                if avg_hit_ratio > 0:
                    values.append(avg_hit_ratio)
                    timestamps.append(result.timestamp or "")
        
        if len(values) < 2:
            return None
        
        return self._calculate_trend_metrics("Buffer Cache Hit Ratio (%)", values, timestamps)
    
    def _calculate_trend_metrics(self, metric_name: str, values: List[float], timestamps: List[str]) -> TrendMetrics:
        """
        추세 메트릭 계산
        
        Args:
            metric_name: 메트릭 이름
            values: 값 리스트
            timestamps: 타임스탬프 리스트
            
        Returns:
            TrendMetrics: 추세 메트릭
        """
        avg = statistics.mean(values)
        min_val = min(values)
        max_val = max(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 추세 판단 (첫 값과 마지막 값 비교)
        change_pct = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0.0
        
        if abs(change_pct) < 5:
            trend = "stable"
        elif change_pct > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return TrendMetrics(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            avg=avg,
            min_val=min_val,
            max_val=max_val,
            std_dev=std_dev,
            trend=trend,
            change_pct=change_pct
        )
    
    def _detect_anomalies(
        self, 
        results: List[BatchFileResult],
        cpu_trend: Optional[TrendMetrics],
        io_trend: Optional[TrendMetrics],
        memory_trend: Optional[TrendMetrics],
        buffer_cache_trend: Optional[TrendMetrics]
    ) -> List[Anomaly]:
        """
        이상 징후 감지
        
        급격한 성능 변화를 감지합니다:
        - CPU 사용률 급증 (평균 대비 2 표준편차 이상)
        - I/O 부하 급증 (평균 대비 2 표준편차 이상)
        - 메모리 사용량 급증 (평균 대비 2 표준편차 이상)
        - 버퍼 캐시 히트율 급락 (평균 대비 2 표준편차 이하)
        
        Args:
            results: 파일 분석 결과 리스트
            cpu_trend: CPU 추세
            io_trend: I/O 추세
            memory_trend: 메모리 추세
            buffer_cache_trend: 버퍼 캐시 추세
            
        Returns:
            이상 징후 리스트
        """
        anomalies = []
        
        # CPU 이상 징후 감지
        if cpu_trend and cpu_trend.std_dev > 0:
            threshold_high = cpu_trend.avg + (2 * cpu_trend.std_dev)
            threshold_low = cpu_trend.avg - (2 * cpu_trend.std_dev)
            
            for i, (value, timestamp) in enumerate(zip(cpu_trend.values, cpu_trend.timestamps)):
                if value > threshold_high:
                    severity = "high" if value > threshold_high * 1.5 else "medium"
                    anomalies.append(Anomaly(
                        timestamp=timestamp,
                        filename=results[i].filename if i < len(results) else "",
                        metric_name="CPU Usage",
                        value=value,
                        expected_range=(threshold_low, threshold_high),
                        severity=severity,
                        description=f"CPU 사용률이 평균({cpu_trend.avg:.2f}) 대비 {((value - cpu_trend.avg) / cpu_trend.avg * 100):.1f}% 증가했습니다."
                    ))
        
        # I/O 이상 징후 감지
        if io_trend and io_trend.std_dev > 0:
            threshold_high = io_trend.avg + (2 * io_trend.std_dev)
            threshold_low = io_trend.avg - (2 * io_trend.std_dev)
            
            for i, (value, timestamp) in enumerate(zip(io_trend.values, io_trend.timestamps)):
                if value > threshold_high:
                    severity = "high" if value > threshold_high * 1.5 else "medium"
                    anomalies.append(Anomaly(
                        timestamp=timestamp,
                        filename=results[i].filename if i < len(results) else "",
                        metric_name="I/O IOPS",
                        value=value,
                        expected_range=(threshold_low, threshold_high),
                        severity=severity,
                        description=f"I/O 부하가 평균({io_trend.avg:.2f}) 대비 {((value - io_trend.avg) / io_trend.avg * 100):.1f}% 증가했습니다."
                    ))
        
        # 메모리 이상 징후 감지
        if memory_trend and memory_trend.std_dev > 0:
            threshold_high = memory_trend.avg + (2 * memory_trend.std_dev)
            threshold_low = memory_trend.avg - (2 * memory_trend.std_dev)
            
            for i, (value, timestamp) in enumerate(zip(memory_trend.values, memory_trend.timestamps)):
                if value > threshold_high:
                    severity = "medium"
                    anomalies.append(Anomaly(
                        timestamp=timestamp,
                        filename=results[i].filename if i < len(results) else "",
                        metric_name="Memory Usage",
                        value=value,
                        expected_range=(threshold_low, threshold_high),
                        severity=severity,
                        description=f"메모리 사용량이 평균({memory_trend.avg:.2f} GB) 대비 {((value - memory_trend.avg) / memory_trend.avg * 100):.1f}% 증가했습니다."
                    ))
        
        # 버퍼 캐시 히트율 이상 징후 감지 (하락)
        if buffer_cache_trend and buffer_cache_trend.std_dev > 0:
            threshold_high = buffer_cache_trend.avg + (2 * buffer_cache_trend.std_dev)
            threshold_low = buffer_cache_trend.avg - (2 * buffer_cache_trend.std_dev)
            
            for i, (value, timestamp) in enumerate(zip(buffer_cache_trend.values, buffer_cache_trend.timestamps)):
                if value < threshold_low:
                    severity = "high" if value < threshold_low * 0.9 else "medium"
                    anomalies.append(Anomaly(
                        timestamp=timestamp,
                        filename=results[i].filename if i < len(results) else "",
                        metric_name="Buffer Cache Hit Ratio",
                        value=value,
                        expected_range=(threshold_low, threshold_high),
                        severity=severity,
                        description=f"버퍼 캐시 히트율이 평균({buffer_cache_trend.avg:.2f}%) 대비 {((buffer_cache_trend.avg - value) / buffer_cache_trend.avg * 100):.1f}% 하락했습니다."
                    ))
        
        # 심각도 순으로 정렬 (high > medium > low)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 3))
        
        return anomalies
