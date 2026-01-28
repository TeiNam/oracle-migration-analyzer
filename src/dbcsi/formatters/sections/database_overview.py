"""
데이터베이스 개요 섹션 포맷터

마이그레이션 대상 Oracle 데이터베이스의 기본 정보를 표시합니다.
"""

from typing import Optional
from ...models import StatspackData


class DatabaseOverviewFormatter:
    """데이터베이스 개요 포맷터"""
    
    @staticmethod
    def format(data: StatspackData, language: str = "ko") -> str:
        """데이터베이스 개요 섹션 포맷
        
        Args:
            data: Statspack/AWR 데이터
            language: 출력 언어 ("ko" 또는 "en")
            
        Returns:
            Markdown 형식의 문자열
        """
        if language == "ko":
            return DatabaseOverviewFormatter._format_ko(data)
        return DatabaseOverviewFormatter._format_en(data)
    
    @staticmethod
    def _format_ko(data: StatspackData) -> str:
        """한국어 데이터베이스 개요"""
        lines = []
        os_info = data.os_info
        
        if not os_info:
            return ""
        
        lines.append("## 📊 데이터베이스 개요\n")
        lines.append("### 이 섹션의 목적\n")
        lines.append("마이그레이션 대상 Oracle 데이터베이스의 기본 정보를 보여줍니다.")
        lines.append("이 정보는 AWS 타겟 환경(Aurora, RDS 등)의 인스턴스 크기와 구성을 결정하는 데 사용됩니다.\n")
        
        # 기본 정보 테이블
        lines.append("### 기본 정보\n")
        lines.append("| 항목 | 값 | 설명 |")
        lines.append("|------|-----|------|")
        
        lines.append(f"| 데이터베이스 이름 | {os_info.db_name or 'N/A'} | "
                    "마이그레이션 대상 DB를 식별하는 이름입니다 |")
        lines.append(f"| Oracle 버전 | {os_info.version or 'N/A'} | "
                    "현재 사용 중인 Oracle 버전입니다. 버전에 따라 사용 가능한 기능이 다릅니다 |")
        lines.append(f"| DBID | {os_info.dbid or 'N/A'} | "
                    "Oracle이 내부적으로 사용하는 고유 식별자입니다 |")
        lines.append(f"| 플랫폼 | {os_info.platform_name or 'N/A'} | "
                    "데이터베이스가 실행 중인 운영체제입니다 |")
        
        # 문자셋 설명
        charset = os_info.character_set or 'N/A'
        charset_desc = "데이터베이스에 저장된 문자의 인코딩 방식입니다. "
        if "UTF8" in charset.upper():
            charset_desc += "UTF8은 다국어를 지원하며 Aurora와 호환됩니다"
        lines.append(f"| 문자셋 | {charset} | {charset_desc} |")
        
        # 인스턴스 정보
        instance_count = os_info.instances or 1
        is_rac = instance_count > 1
        rac_str = f"{instance_count} (RAC)" if is_rac else f"{instance_count} (단일 인스턴스)"
        rac_desc = ("여러 서버가 하나의 DB를 공유하는 고가용성 구성입니다. "
                   "Aurora로 마이그레이션 시 Multi-AZ로 대체합니다" if is_rac 
                   else "단일 서버에서 실행 중입니다. 마이그레이션이 상대적으로 단순합니다")
        lines.append(f"| 인스턴스 수 | {rac_str} | {rac_desc} |")
        
        # RDS 여부
        rds_str = "예" if os_info.is_rds else "아니오"
        rds_desc = ("이미 AWS RDS에서 실행 중입니다. Aurora로 업그레이드가 용이합니다" 
                   if os_info.is_rds else "온프레미스 또는 다른 클라우드에서 실행 중입니다")
        lines.append(f"| RDS 환경 | {rds_str} | {rds_desc} |")
        
        lines.append("")
        
        # 크기 및 리소스 정보
        lines.append("### 크기 및 리소스 정보\n")
        lines.append("> **왜 중요한가요?**")
        lines.append("> 이 정보를 바탕으로 AWS에서 적절한 인스턴스 타입(예: db.r6g.xlarge)과")
        lines.append("> 스토리지 크기를 선택합니다. 과소 산정하면 성능 문제가, 과대 산정하면 비용 낭비가 발생합니다.\n")
        
        lines.append("| 항목 | 값 | 설명 |")
        lines.append("|------|-----|------|")
        
        db_size = os_info.total_db_size_gb
        if db_size:
            size_desc = "실제 데이터가 차지하는 디스크 공간입니다. "
            if db_size > 1000:
                size_desc += "대용량이므로 마이그레이션 시간이 오래 걸릴 수 있습니다"
            elif db_size > 100:
                size_desc += "중간 규모로 일반적인 마이그레이션 절차를 적용합니다"
            else:
                size_desc += "소규모로 빠른 마이그레이션이 가능합니다"
            lines.append(f"| 전체 DB 크기 | {db_size:,.1f} GB | {size_desc} |")
        else:
            lines.append("| 전체 DB 크기 | N/A | 데이터 파일 총 크기 |")
        
        memory = os_info.physical_memory_gb
        if memory:
            mem_desc = f"현재 서버의 총 메모리입니다. Aurora 인스턴스 선택 시 참고합니다"
            lines.append(f"| 물리 메모리 | {memory:,.1f} GB | {mem_desc} |")
        else:
            lines.append("| 물리 메모리 | N/A | 서버 총 메모리 |")
        
        cpu_cores = os_info.num_cpu_cores
        if cpu_cores:
            cpu_desc = f"현재 서버의 CPU 코어 수입니다. AWS vCPU 산정 기준이 됩니다"
            lines.append(f"| CPU 코어 수 | {cpu_cores} | {cpu_desc} |")
        else:
            lines.append("| CPU 코어 수 | N/A | 서버 CPU 코어 |")
        
        num_cpus = os_info.num_cpus
        if num_cpus:
            lines.append(f"| CPU 수 | {num_cpus} | 논리 CPU 수 (하이퍼스레딩 포함) |")
        
        lines.append("")
        
        # 마이그레이션 시사점
        lines.append("### 마이그레이션 시사점\n")
        lines.append("> 위 정보를 바탕으로 분석한 마이그레이션 관련 주요 사항입니다.\n")
        
        implications = []
        
        # 문자셋 분석
        charset = os_info.character_set or ""
        if "UTF8" in charset.upper() or "AL32UTF8" in charset.upper():
            implications.append("- ✅ **문자셋 호환**: UTF8 계열이므로 Aurora와 호환됩니다. "
                              "한글, 특수문자 등이 정상적으로 마이그레이션됩니다")
        elif charset:
            implications.append(f"- ⚠️ **문자셋 변환 필요**: 현재 문자셋({charset})이 UTF8이 아닙니다. "
                              "마이그레이션 전 문자 변환 테스트가 필요합니다")
        
        # RAC 분석
        if is_rac:
            implications.append("- ⚠️ **RAC 구성 변경 필요**: 현재 여러 서버가 하나의 DB를 공유하는 RAC 구성입니다. "
                              "Aurora는 단일 Writer 구조이므로 Multi-AZ 또는 Global Database로 대체합니다")
        else:
            implications.append("- ✅ **단순한 구성**: 단일 인스턴스이므로 마이그레이션 복잡도가 낮습니다")
        
        # RDS 분석
        if os_info.is_rds:
            implications.append("- ℹ️ **RDS 업그레이드 가능**: 이미 AWS RDS에서 실행 중이므로 "
                              "Aurora로의 업그레이드가 상대적으로 용이합니다")
        
        # DB 크기 분석
        if db_size:
            if db_size > 1000:
                implications.append(f"- ⚠️ **대용량 DB**: {db_size:,.0f}GB 규모이므로 "
                                  "마이그레이션에 수 시간~수일이 소요될 수 있습니다. "
                                  "다운타임 최소화를 위해 DMS CDC 방식을 권장합니다")
            elif db_size > 100:
                implications.append(f"- ℹ️ **중간 규모 DB**: {db_size:,.0f}GB 규모로 "
                                  "일반적인 마이그레이션 절차를 적용합니다")
            else:
                implications.append(f"- ✅ **소규모 DB**: {db_size:,.0f}GB로 빠른 마이그레이션이 가능합니다. "
                                  "전체 백업/복원 방식도 고려할 수 있습니다")
        
        if implications:
            lines.extend(implications)
        else:
            lines.append("- 추가 분석 필요")
        
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_en(data: StatspackData) -> str:
        """영어 데이터베이스 개요"""
        lines = []
        os_info = data.os_info
        
        if not os_info:
            return ""
        
        lines.append("## 📊 Database Overview\n")
        lines.append("> Basic information about the Oracle database for migration.")
        lines.append("> Used as a basis for target environment configuration and compatibility review.\n")
        
        lines.append("### Basic Information\n")
        lines.append("| Item | Value | Description |")
        lines.append("|------|-------|-------------|")
        
        lines.append(f"| Database Name | {os_info.db_name or 'N/A'} | Migration target DB identifier |")
        lines.append(f"| Oracle Version | {os_info.version or 'N/A'} | Source DB version |")
        lines.append(f"| DBID | {os_info.dbid or 'N/A'} | Database unique identifier |")
        lines.append(f"| Platform | {os_info.platform_name or 'N/A'} | Operating system |")
        lines.append(f"| Character Set | {os_info.character_set or 'N/A'} | Character encoding |")
        
        instance_count = os_info.instances or 1
        is_rac = instance_count > 1
        rac_str = f"{instance_count} (RAC)" if is_rac else f"{instance_count} (Single)"
        lines.append(f"| Instance Count | {rac_str} | RAC configuration |")
        
        rds_str = "Yes" if os_info.is_rds else "No"
        lines.append(f"| RDS Environment | {rds_str} | Already on AWS RDS |")
        
        lines.append("")
        
        lines.append("### Size and Resource Information\n")
        lines.append("| Item | Value | Description |")
        lines.append("|------|-------|-------------|")
        
        db_size = os_info.total_db_size_gb
        if db_size:
            lines.append(f"| Total DB Size | {db_size:,.1f} GB | Total data file size |")
        else:
            lines.append("| Total DB Size | N/A | Total data file size |")
        
        memory = os_info.physical_memory_gb
        if memory:
            lines.append(f"| Physical Memory | {memory:,.1f} GB | Server total memory |")
        else:
            lines.append("| Physical Memory | N/A | Server total memory |")
        
        cpu_cores = os_info.num_cpu_cores
        if cpu_cores:
            lines.append(f"| CPU Cores | {cpu_cores} | Server CPU cores |")
        else:
            lines.append("| CPU Cores | N/A | Server CPU cores |")
        
        lines.append("")
        
        return "\n".join(lines)
