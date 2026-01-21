"""
차트 생성 모듈

AWR/Statspack 분석 결과를 시각화하는 차트를 생성합니다.

사용 예제:
    from src.dbcsi.formatters import ChartGenerator
    
    # 메모리 사용량 차트 생성
    chart_file = ChartGenerator.generate_memory_usage_chart(
        snap_ids=[1, 2, 3, 4, 5],
        sga_data=[10.5, 11.2, 10.8, 11.5, 11.0],
        pga_data=[2.1, 2.3, 2.2, 2.4, 2.3],
        total_data=[12.6, 13.5, 13.0, 13.9, 13.3],
        output_path="reports/analysis.md"
    )
    
    # CPU 사용량 차트 생성
    chart_file = ChartGenerator.generate_cpu_usage_chart(
        timestamps=["10:00", "11:00", "12:00"],
        cpu_data=[45.2, 52.1, 48.5],
        output_path="reports/analysis.md"
    )
    
    # IOPS 차트 생성
    chart_file = ChartGenerator.generate_iops_chart(
        timestamps=["10:00", "11:00", "12:00"],
        read_iops=[1200, 1350, 1280],
        write_iops=[800, 920, 850],
        output_path="reports/analysis.md"
    )
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChartGenerator:
    """차트 생성 클래스
    
    matplotlib을 사용하여 다양한 차트를 생성합니다.
    """
    
    @staticmethod
    def generate_memory_usage_chart(
        snap_ids: List[int],
        sga_data: List[float],
        pga_data: List[float],
        total_data: List[float],
        output_path: str,
        title: str = "Memory Usage Trend",
        xlabel: str = "Snap ID",
        ylabel: str = "Memory (GB)"
    ) -> Optional[str]:
        """메모리 사용량 추이 차트 생성
        
        Args:
            snap_ids: 스냅샷 ID 리스트
            sga_data: SGA 메모리 사용량 (GB)
            pga_data: PGA 메모리 사용량 (GB)
            total_data: 총 메모리 사용량 (GB)
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # GUI 없이 사용
            import matplotlib.pyplot as plt
            
            # 그래프 생성
            plt.figure(figsize=(12, 6))
            plt.plot(snap_ids, sga_data, marker='o', label='SGA', linewidth=2)
            plt.plot(snap_ids, pga_data, marker='s', label='PGA', linewidth=2)
            plt.plot(snap_ids, total_data, marker='^', label='Total', linewidth=2, linestyle='--')
            
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = Path(output_path).stem + '_memory_chart.png'
            chart_path = output_dir / chart_filename
            
            logger.info(f"메모리 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            # 파일이 실제로 생성되었는지 확인
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"메모리 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"메모리 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"메모리 사용량 그래프 생성 실패: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_cpu_usage_chart(
        timestamps: List[str],
        cpu_data: List[float],
        output_path: str,
        title: str = "CPU Usage Trend",
        xlabel: str = "Time",
        ylabel: str = "CPU per Second"
    ) -> Optional[str]:
        """CPU 사용량 추이 차트 생성
        
        Args:
            timestamps: 시간 리스트
            cpu_data: CPU 사용량 데이터
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 6))
            plt.plot(range(len(cpu_data)), cpu_data, marker='o', linewidth=2, color='#2E86AB')
            
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = Path(output_path).stem + '_cpu_chart.png'
            chart_path = output_dir / chart_filename
            
            logger.info(f"CPU 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"CPU 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"CPU 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"CPU 사용량 그래프 생성 실패: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_iops_chart(
        timestamps: List[str],
        read_iops: List[float],
        write_iops: List[float],
        output_path: str,
        title: str = "IOPS Trend",
        xlabel: str = "Time",
        ylabel: str = "IOPS"
    ) -> Optional[str]:
        """IOPS 추이 차트 생성
        
        Args:
            timestamps: 시간 리스트
            read_iops: Read IOPS 데이터
            write_iops: Write IOPS 데이터
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 6))
            plt.plot(range(len(read_iops)), read_iops, marker='o', label='Read IOPS', linewidth=2)
            plt.plot(range(len(write_iops)), write_iops, marker='s', label='Write IOPS', linewidth=2)
            
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = Path(output_path).stem + '_iops_chart.png'
            chart_path = output_dir / chart_filename
            
            logger.info(f"IOPS 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"IOPS 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"IOPS 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"IOPS 그래프 생성 실패: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_disk_usage_chart(
        snap_ids: List[int],
        disk_data: List[float],
        output_path: str,
        title: str = "Disk Usage Trend",
        xlabel: str = "Snap ID",
        ylabel: str = "Disk Size (GB)"
    ) -> Optional[str]:
        """디스크 사용량 추이 차트 생성
        
        Args:
            snap_ids: 스냅샷 ID 리스트
            disk_data: 디스크 사용량 (GB)
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 6))
            plt.plot(snap_ids, disk_data, marker='o', linewidth=2, color='#A23B72')
            plt.fill_between(snap_ids, disk_data, alpha=0.3, color='#A23B72')
            
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = Path(output_path).stem + '_disk_chart.png'
            chart_path = output_dir / chart_filename
            
            logger.info(f"디스크 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"디스크 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"디스크 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"디스크 사용량 그래프 생성 실패: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_performance_metrics_chart(
        timestamps: List[str],
        cpu_data: List[float],
        read_iops_data: List[float],
        write_iops_data: List[float],
        commits_data: List[float],
        output_path: str,
        title: str = "Performance Metrics Trend",
        max_points: int = 24
    ) -> Optional[str]:
        """주요 성능 메트릭 추이 차트 생성 (4개 서브플롯)
        
        Args:
            timestamps: 시간 리스트
            cpu_data: CPU/s 데이터
            read_iops_data: Read IOPS 데이터
            write_iops_data: Write IOPS 데이터
            commits_data: Commits/s 데이터
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            title: 차트 제목
            max_points: 최대 표시 데이터 포인트 수
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # 데이터 포인트 제한
            display_count = min(max_points, len(cpu_data))
            x_range = range(display_count)
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            # CPU/s
            ax1.plot(x_range, cpu_data[:display_count], marker='o', linewidth=2, color='#2E86AB')
            ax1.set_title('CPU per Second', fontsize=12, fontweight='bold')
            ax1.set_ylabel('CPU/s', fontsize=10)
            ax1.grid(True, alpha=0.3)
            
            # Read IOPS
            ax2.plot(x_range, read_iops_data[:display_count], marker='s', linewidth=2, color='#A23B72')
            ax2.set_title('Read IOPS', fontsize=12, fontweight='bold')
            ax2.set_ylabel('IOPS', fontsize=10)
            ax2.grid(True, alpha=0.3)
            
            # Write IOPS
            ax3.plot(x_range, write_iops_data[:display_count], marker='^', linewidth=2, color='#F18F01')
            ax3.set_title('Write IOPS', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Time Index', fontsize=10)
            ax3.set_ylabel('IOPS', fontsize=10)
            ax3.grid(True, alpha=0.3)
            
            # Commits/s
            ax4.plot(x_range, commits_data[:display_count], marker='d', linewidth=2, color='#6A994E')
            ax4.set_title('Commits per Second', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Time Index', fontsize=10)
            ax4.set_ylabel('Commits/s', fontsize=10)
            ax4.grid(True, alpha=0.3)
            
            plt.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = Path(output_path).stem + '_performance_chart.png'
            chart_path = output_dir / chart_filename
            
            logger.info(f"성능 메트릭 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"성능 메트릭 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"성능 메트릭 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"성능 메트릭 그래프 생성 실패: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_wait_events_chart(
        event_names: List[str],
        wait_times: List[float],
        output_path: str,
        title: str = "Top Wait Events",
        max_events: int = 10
    ) -> Optional[str]:
        """Top 대기 이벤트 차트 생성 (수평 막대 차트)
        
        Args:
            event_names: 이벤트 이름 리스트
            wait_times: 대기 시간 (초) 리스트
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            title: 차트 제목
            max_events: 최대 표시 이벤트 수
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # 상위 N개만 표시
            display_count = min(max_events, len(event_names))
            names = event_names[:display_count]
            times = wait_times[:display_count]
            
            # 이벤트 이름이 너무 길면 줄임
            short_names = []
            for name in names:
                if len(name) > 40:
                    short_names.append(name[:37] + '...')
                else:
                    short_names.append(name)
            
            plt.figure(figsize=(12, max(6, display_count * 0.5)))
            colors = plt.cm.viridis(range(display_count))
            plt.barh(range(display_count), times, color=colors, alpha=0.8)
            plt.yticks(range(display_count), short_names, fontsize=9)
            
            plt.xlabel('Total Wait Time (seconds)', fontsize=12)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = Path(output_path).stem + '_wait_events_chart.png'
            chart_path = output_dir / chart_filename
            
            logger.info(f"대기 이벤트 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"대기 이벤트 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"대기 이벤트 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"대기 이벤트 그래프 생성 실패: {e}", exc_info=True)
            return None
    
    @staticmethod
    def generate_bar_chart(
        labels: List[str],
        values: List[float],
        output_path: str,
        chart_name: str = "bar_chart",
        title: str = "Bar Chart",
        xlabel: str = "Category",
        ylabel: str = "Value",
        color: str = '#2E86AB'
    ) -> Optional[str]:
        """막대 차트 생성
        
        Args:
            labels: 카테고리 레이블 리스트
            values: 값 리스트
            output_path: 출력 파일 경로 (Markdown 파일 경로)
            chart_name: 차트 파일명 (확장자 제외)
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            color: 막대 색상
            
        Returns:
            생성된 차트 파일명 (상대 경로), 실패 시 None
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 6))
            plt.bar(range(len(values)), values, color=color, alpha=0.7)
            plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
            
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            
            # 이미지 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = f"{Path(output_path).stem}_{chart_name}.png"
            chart_path = output_dir / chart_filename
            
            logger.info(f"막대 그래프 저장 중: {chart_path}")
            plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
            plt.close()
            
            if chart_path.exists():
                file_size = chart_path.stat().st_size
                logger.info(f"막대 그래프 생성 완료: {chart_path} ({file_size} bytes)")
                return chart_filename
            else:
                logger.warning(f"막대 그래프 파일이 생성되지 않음: {chart_path}")
                return None
                
        except Exception as e:
            logger.warning(f"막대 그래프 생성 실패: {e}", exc_info=True)
            return None
