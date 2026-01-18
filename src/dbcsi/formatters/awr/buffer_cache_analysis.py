"""
AWR 버퍼 캐시 분석 모듈

버퍼 캐시 효율성 분석 섹션을 생성합니다.
"""

import statistics


class BufferCacheAnalysisMixin:
    """버퍼 캐시 효율성 분석 믹스인"""
    
    @staticmethod
    def _generate_buffer_cache_analysis(awr_data, language: str) -> str:
        """버퍼 캐시 효율성 분석 섹션 생성
        
        Args:
            awr_data: AWR 데이터
            language: 리포트 언어 ("ko" 또는 "en")
            
        Returns:
            버퍼 캐시 분석 섹션 문자열
        """
        md = []
        
        title = "## 버퍼 캐시 효율성 분석\n" if language == "ko" else "## Buffer Cache Efficiency Analysis\n"
        md.append(title)
        
        if not awr_data.buffer_cache_stats:
            md.append("버퍼 캐시 통계 데이터가 없습니다.\n" if language == "ko" else "No buffer cache statistics available.\n")
            return "\n".join(md)
        
        hit_ratios = [stat.hit_ratio for stat in awr_data.buffer_cache_stats if stat.hit_ratio is not None]
        cache_sizes = [stat.db_cache_gb for stat in awr_data.buffer_cache_stats if stat.db_cache_gb is not None]
        
        if not hit_ratios:
            md.append("버퍼 캐시 히트율 데이터가 없습니다.\n" if language == "ko" else "No buffer cache hit ratio data available.\n")
            return "\n".join(md)
        
        avg_hit_ratio = statistics.mean(hit_ratios)
        min_hit_ratio = min(hit_ratios)
        max_hit_ratio = max(hit_ratios)
        current_size_gb = statistics.mean(cache_sizes) if cache_sizes else 0.0
        
        if language == "ko":
            md.append("### 히트율 요약\n")
            md.append(f"- **평균 히트율**: {avg_hit_ratio:.2f}%")
            md.append(f"- **최소 히트율**: {min_hit_ratio:.2f}%")
            md.append(f"- **최대 히트율**: {max_hit_ratio:.2f}%")
            md.append(f"- **현재 버퍼 캐시 크기**: {current_size_gb:.2f} GB")
            md.append("")
            
            md.append("### 효율성 평가\n")
            if avg_hit_ratio >= 95:
                md.append("✅ **매우 우수**: 버퍼 캐시가 매우 효율적으로 동작하고 있습니다.")
            elif avg_hit_ratio >= 90:
                md.append("✅ **우수**: 버퍼 캐시가 효율적으로 동작하고 있습니다.")
            elif avg_hit_ratio >= 85:
                md.append("⚠️ **보통**: 버퍼 캐시 효율성 개선이 필요합니다.")
            else:
                md.append("❌ **낮음**: 버퍼 캐시 크기 증가가 필요합니다.")
        else:
            md.append("### Hit Ratio Summary\n")
            md.append(f"- **Average Hit Ratio**: {avg_hit_ratio:.2f}%")
            md.append(f"- **Minimum Hit Ratio**: {min_hit_ratio:.2f}%")
            md.append(f"- **Maximum Hit Ratio**: {max_hit_ratio:.2f}%")
            md.append(f"- **Current Buffer Cache Size**: {current_size_gb:.2f} GB")
        md.append("")
        
        return "\n".join(md)
