"""
여러 DB의 리포트를 저장하는 예제

폴더 구조: reports/YYYYMMDD/{db_name}/
"""

from src.statspack.data_models import StatspackData, OSInformation
from src.statspack.result_formatter import StatspackResultFormatter


def main():
    # 여러 DB의 샘플 데이터 생성
    databases = [
        ("PRODDB", "운영 데이터베이스"),
        ("TESTDB", "테스트 데이터베이스"),
        ("DEVDB", "개발 데이터베이스"),
    ]
    
    print("=" * 80)
    print("여러 DB의 리포트 저장 예제")
    print("=" * 80)
    
    for db_name, description in databases:
        # 샘플 데이터 생성
        statspack_data = StatspackData(
            os_info=OSInformation(
                db_name=db_name,
                version="19.0.0.0",
                banner=f"Oracle Database 19c - {description}"
            )
        )
        
        # Markdown 생성
        markdown = StatspackResultFormatter.to_markdown(statspack_data)
        
        # 파일 저장
        filepath = StatspackResultFormatter.save_report(
            content=markdown,
            filename="statspack_analysis",
            format="md",
            db_name=db_name
        )
        
        print(f"\n{db_name} 리포트 저장됨: {filepath}")
    
    print("\n" + "=" * 80)
    print("폴더 구조 확인:")
    print("=" * 80)
    
    import subprocess
    from datetime import datetime
    
    today = datetime.now().strftime("%Y%m%d")
    result = subprocess.run(
        ["ls", "-lh", f"reports/{today}/"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    
    print("\n각 DB 폴더 내용:")
    for db_name, _ in databases:
        safe_db_name = db_name.lower()
        print(f"\n{db_name} 폴더:")
        result = subprocess.run(
            ["ls", "-lh", f"reports/{today}/{safe_db_name}/"],
            capture_output=True,
            text=True
        )
        print(result.stdout)


if __name__ == "__main__":
    main()
