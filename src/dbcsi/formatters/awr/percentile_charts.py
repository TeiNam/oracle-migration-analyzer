"""
AWR 백분위수 차트 모듈

백분위수 분포 차트 섹션을 생성합니다.
"""


class PercentileChartsMixin:
    """백분위수 차트 생성 믹스인"""
    
    @staticmethod
    def _generate_percentile_charts(awr_data) -> str:
        """백분위수 차트 생성
        
        Args:
            awr_data: AWR 데이터
            
        Returns:
            백분위수 차트 섹션 문자열
        """
        md = []
        
        md.append("## 백분위수 분포 차트\n")
        
        # CPU 백분위수
        if awr_data.percentile_cpu:
            md.append("### CPU 사용률 백분위수 분포\n")
            md.append("| 백분위수 | CPU 코어 수 |")
            md.append("|----------|-------------|")
            
            percentile_order = [
                ("Average", "평균"),
                ("Median", "중간값"),
                ("75th_percentile", "75%"),
                ("90th_percentile", "90%"),
                ("95th_percentile", "95%"),
                ("99th_percentile", "99%"),
                ("Maximum_or_peak", "최대")
            ]
            
            for key, label in percentile_order:
                # 인스턴스 번호 없는 키 우선, 있으면 _1 등의 키도 확인
                cpu_data = None
                if key in awr_data.percentile_cpu:
                    cpu_data = awr_data.percentile_cpu[key]
                else:
                    # 인스턴스 번호가 있는 키 찾기 (예: "99th_percentile_1")
                    for k, v in awr_data.percentile_cpu.items():
                        if k.startswith(key + "_"):
                            cpu_data = v
                            break
                
                if cpu_data:
                    md.append(f"| {label} | {cpu_data.on_cpu} |")
            md.append("")
        
        # I/O 백분위수
        if awr_data.percentile_io:
            md.append("### I/O 부하 백분위수 분포\n")
            md.append("| 백분위수 | IOPS | MB/s |")
            md.append("|----------|------|------|")
            
            percentile_order = [
                ("Average", "평균"),
                ("Median", "중간값"),
                ("75th_percentile", "75%"),
                ("90th_percentile", "90%"),
                ("95th_percentile", "95%"),
                ("99th_percentile", "99%"),
                ("Maximum_or_peak", "최대")
            ]
            
            for key, label in percentile_order:
                # 인스턴스 번호 없는 키 우선, 있으면 _1 등의 키도 확인
                io_data = None
                if key in awr_data.percentile_io:
                    io_data = awr_data.percentile_io[key]
                else:
                    # 인스턴스 번호가 있는 키 찾기
                    for k, v in awr_data.percentile_io.items():
                        if k.startswith(key + "_"):
                            io_data = v
                            break
                
                if io_data:
                    md.append(f"| {label} | {io_data.rw_iops:,} | {io_data.rw_mbps} |")
            md.append("")
        
        md.append("### 백분위수 해석 가이드\n")
        md.append("- **99% (99th percentile)**: 99%의 시간 동안 이 값 이하 (권장 사이징 기준)")
        md.append("- P99 값에 30% 여유분을 추가하여 인스턴스 크기를 결정하는 것을 권장합니다.\n")
        
        return "\n".join(md)
