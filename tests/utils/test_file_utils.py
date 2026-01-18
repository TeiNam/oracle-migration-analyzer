"""
파일 유틸리티 함수 단위 테스트

src/utils/file_utils.py의 함수들을 테스트합니다.
"""

import pytest
import tempfile
from pathlib import Path

from src.utils.file_utils import (
    find_files_by_extension,
    read_file_with_encoding
)


class TestFindFilesByExtension:
    """확장자로 파일 찾기 테스트"""
    
    def test_find_files_single_extension(self, tmp_path):
        """단일 확장자로 파일 찾기"""
        # 테스트 파일 생성
        (tmp_path / "file1.sql").write_text("SELECT * FROM users;")
        (tmp_path / "file2.sql").write_text("SELECT * FROM orders;")
        (tmp_path / "file3.txt").write_text("text file")
        
        # .sql 파일만 찾기
        result = find_files_by_extension(tmp_path, [".sql"])
        
        assert len(result) == 2
        assert all(f.suffix == ".sql" for f in result)
        assert tmp_path / "file1.sql" in result
        assert tmp_path / "file2.sql" in result
    
    def test_find_files_multiple_extensions(self, tmp_path):
        """여러 확장자로 파일 찾기"""
        # 테스트 파일 생성
        (tmp_path / "query.sql").write_text("SELECT 1;")
        (tmp_path / "package.pls").write_text("CREATE PACKAGE;")
        (tmp_path / "report.out").write_text("report data")
        (tmp_path / "readme.txt").write_text("readme")
        
        # .sql, .pls, .out 파일 찾기
        result = find_files_by_extension(tmp_path, [".sql", ".pls", ".out"])
        
        assert len(result) == 3
        assert tmp_path / "query.sql" in result
        assert tmp_path / "package.pls" in result
        assert tmp_path / "report.out" in result
        assert tmp_path / "readme.txt" not in result
    
    def test_find_files_recursive(self, tmp_path):
        """재귀적으로 하위 디렉토리의 파일 찾기"""
        # 디렉토리 구조 생성
        subdir1 = tmp_path / "subdir1"
        subdir2 = tmp_path / "subdir2"
        nested = subdir1 / "nested"
        
        subdir1.mkdir()
        subdir2.mkdir()
        nested.mkdir()
        
        # 여러 위치에 파일 생성
        (tmp_path / "root.sql").write_text("root")
        (subdir1 / "sub1.sql").write_text("sub1")
        (subdir2 / "sub2.sql").write_text("sub2")
        (nested / "nested.sql").write_text("nested")
        
        # 재귀적으로 모든 .sql 파일 찾기
        result = find_files_by_extension(tmp_path, [".sql"])
        
        assert len(result) == 4
        assert tmp_path / "root.sql" in result
        assert subdir1 / "sub1.sql" in result
        assert subdir2 / "sub2.sql" in result
        assert nested / "nested.sql" in result
    
    def test_find_files_case_insensitive(self, tmp_path):
        """대소문자 구분 없이 파일 찾기"""
        # 다양한 대소문자 확장자 파일 생성
        (tmp_path / "file1.SQL").write_text("query1")
        (tmp_path / "file2.sql").write_text("query2")
        (tmp_path / "file3.Sql").write_text("query3")
        
        # 소문자 확장자로 검색
        result = find_files_by_extension(tmp_path, [".sql"])
        
        assert len(result) == 3
    
    def test_find_files_sorted_output(self, tmp_path):
        """결과가 정렬되어 반환됨"""
        # 파일을 무작위 순서로 생성
        (tmp_path / "c.sql").write_text("c")
        (tmp_path / "a.sql").write_text("a")
        (tmp_path / "b.sql").write_text("b")
        
        result = find_files_by_extension(tmp_path, [".sql"])
        
        # 파일명으로 정렬되어 있는지 확인
        filenames = [f.name for f in result]
        assert filenames == sorted(filenames)
    
    def test_find_files_empty_directory(self, tmp_path):
        """빈 디렉토리에서 파일 찾기"""
        result = find_files_by_extension(tmp_path, [".sql"])
        
        assert result == []
    
    def test_find_files_no_matching_files(self, tmp_path):
        """일치하는 파일이 없는 경우"""
        (tmp_path / "file1.txt").write_text("text")
        (tmp_path / "file2.md").write_text("markdown")
        
        result = find_files_by_extension(tmp_path, [".sql", ".pls"])
        
        assert result == []
    
    def test_find_files_nonexistent_directory(self):
        """존재하지 않는 디렉토리"""
        nonexistent = Path("/nonexistent/directory")
        
        with pytest.raises(ValueError, match="디렉토리가 존재하지 않습니다"):
            find_files_by_extension(nonexistent, [".sql"])
    
    def test_find_files_not_a_directory(self, tmp_path):
        """디렉토리가 아닌 파일 경로"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        
        with pytest.raises(ValueError, match="디렉토리가 아닙니다"):
            find_files_by_extension(file_path, [".sql"])
    
    def test_find_files_empty_extensions_list(self, tmp_path):
        """빈 확장자 리스트"""
        with pytest.raises(ValueError, match="확장자 리스트가 비어있습니다"):
            find_files_by_extension(tmp_path, [])
    
    def test_find_files_with_dot_in_filename(self, tmp_path):
        """파일명에 점이 여러 개 있는 경우"""
        (tmp_path / "backup.2024.01.15.sql").write_text("backup")
        (tmp_path / "test.data.sql").write_text("test")
        
        result = find_files_by_extension(tmp_path, [".sql"])
        
        assert len(result) == 2
        assert all(f.suffix == ".sql" for f in result)
    
    def test_find_files_ignores_directories_with_extension(self, tmp_path):
        """확장자가 있는 디렉토리는 무시"""
        # .sql이라는 이름의 디렉토리 생성
        dir_with_ext = tmp_path / "folder.sql"
        dir_with_ext.mkdir()
        
        # 실제 .sql 파일 생성
        (tmp_path / "real_file.sql").write_text("query")
        
        result = find_files_by_extension(tmp_path, [".sql"])
        
        # 디렉토리는 제외되고 파일만 포함
        assert len(result) == 1
        assert result[0].name == "real_file.sql"
    
    def test_find_files_with_hidden_files(self, tmp_path):
        """숨김 파일도 찾기"""
        # 숨김 파일 생성 (Unix 스타일)
        (tmp_path / ".hidden.sql").write_text("hidden query")
        (tmp_path / "visible.sql").write_text("visible query")
        
        result = find_files_by_extension(tmp_path, [".sql"])
        
        assert len(result) == 2
        assert tmp_path / ".hidden.sql" in result
        assert tmp_path / "visible.sql" in result
    
    def test_find_files_mixed_case_extensions_input(self, tmp_path):
        """입력 확장자가 대소문자 섞여있는 경우"""
        (tmp_path / "file1.sql").write_text("query1")
        (tmp_path / "file2.SQL").write_text("query2")
        
        # 대문자 확장자로 검색
        result = find_files_by_extension(tmp_path, [".SQL"])
        
        # 대소문자 구분 없이 모두 찾아야 함
        assert len(result) == 2


class TestReadFileWithEncoding:
    """여러 인코딩으로 파일 읽기 테스트"""
    
    def test_read_file_utf8(self, tmp_path):
        """UTF-8 인코딩 파일 읽기"""
        file_path = tmp_path / "utf8.txt"
        content = "안녕하세요 Hello 你好"
        file_path.write_text(content, encoding='utf-8')
        
        result = read_file_with_encoding(file_path)
        
        assert result == content
    
    def test_read_file_latin1(self, tmp_path):
        """Latin-1 인코딩 파일 읽기"""
        file_path = tmp_path / "latin1.txt"
        content = "Café résumé"
        
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        
        result = read_file_with_encoding(file_path)
        
        assert result == content
    
    def test_read_file_cp949(self, tmp_path):
        """CP949 인코딩 파일 읽기"""
        file_path = tmp_path / "cp949.txt"
        content = "한글 테스트 파일입니다"
        
        with open(file_path, 'w', encoding='cp949') as f:
            f.write(content)
        
        # CP949로 명시적으로 읽기
        result = read_file_with_encoding(file_path, encodings=['cp949', 'utf-8'])
        
        assert result == content
    
    def test_read_file_custom_encodings(self, tmp_path):
        """커스텀 인코딩 리스트로 파일 읽기"""
        file_path = tmp_path / "custom.txt"
        content = "Test content"
        file_path.write_text(content, encoding='utf-16')
        
        # UTF-16을 포함한 커스텀 인코딩 리스트
        result = read_file_with_encoding(file_path, encodings=['utf-16', 'utf-8'])
        
        assert result == content
    
    def test_read_file_tries_multiple_encodings(self, tmp_path):
        """여러 인코딩을 순서대로 시도"""
        file_path = tmp_path / "test.txt"
        content = "한글 내용"
        
        # CP949로 저장
        with open(file_path, 'w', encoding='cp949') as f:
            f.write(content)
        
        # CP949를 포함한 인코딩 리스트로 읽기
        result = read_file_with_encoding(file_path, encodings=['cp949', 'utf-8', 'latin-1'])
        
        assert result == content
    
    def test_read_file_nonexistent_file(self):
        """존재하지 않는 파일"""
        nonexistent = Path("/nonexistent/file.txt")
        
        with pytest.raises(FileNotFoundError, match="파일이 존재하지 않습니다"):
            read_file_with_encoding(nonexistent)
    
    def test_read_file_directory_path(self, tmp_path):
        """디렉토리 경로를 파일로 읽으려고 시도"""
        with pytest.raises(ValueError, match="파일이 아닙니다"):
            read_file_with_encoding(tmp_path)
    
    def test_read_file_all_encodings_fail(self, tmp_path):
        """모든 인코딩으로 읽기 실패"""
        file_path = tmp_path / "binary.dat"
        
        # 바이너리 데이터 작성 (텍스트로 읽을 수 없음)
        with open(file_path, 'wb') as f:
            f.write(bytes([0xFF, 0xFE, 0xFD, 0xFC] * 100))
        
        # 일반적인 텍스트 인코딩으로는 읽을 수 없어야 함
        with pytest.raises(IOError, match="모든 인코딩으로 파일 읽기 실패"):
            read_file_with_encoding(file_path, encodings=['utf-8', 'ascii'])
    
    def test_read_file_empty_file(self, tmp_path):
        """빈 파일 읽기"""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        
        result = read_file_with_encoding(file_path)
        
        assert result == ""
    
    def test_read_file_large_file(self, tmp_path):
        """큰 파일 읽기"""
        file_path = tmp_path / "large.txt"
        content = "Line {}\n" * 10000
        content = content.format(*range(10000))
        file_path.write_text(content, encoding='utf-8')
        
        result = read_file_with_encoding(file_path)
        
        assert len(result) > 0
        assert "Line 0" in result
        assert "Line 9999" in result
    
    def test_read_file_with_special_characters(self, tmp_path):
        """특수 문자가 포함된 파일 읽기"""
        file_path = tmp_path / "special.txt"
        content = "Special chars: \n\t©®™€£¥"
        file_path.write_text(content, encoding='utf-8')
        
        result = read_file_with_encoding(file_path)
        
        # 특수 문자가 포함되어 있는지 확인
        assert "Special chars:" in result
        assert "©®™€£¥" in result
    
    def test_read_file_with_mixed_content(self, tmp_path):
        """다양한 언어가 섞인 파일 읽기"""
        file_path = tmp_path / "mixed.txt"
        content = """
English: Hello World
한국어: 안녕하세요
日本語: こんにちは
中文: 你好
Русский: Привет
العربية: مرحبا
        """
        file_path.write_text(content, encoding='utf-8')
        
        result = read_file_with_encoding(file_path)
        
        assert "Hello World" in result
        assert "안녕하세요" in result
        assert "こんにちは" in result
    
    def test_read_file_default_encodings(self, tmp_path):
        """기본 인코딩 리스트 사용"""
        file_path = tmp_path / "default.txt"
        content = "Test with default encodings"
        file_path.write_text(content, encoding='utf-8')
        
        # encodings 파라미터 없이 호출
        result = read_file_with_encoding(file_path)
        
        assert result == content
    
    def test_read_file_preserves_line_endings(self, tmp_path):
        """줄바꿈 문자 보존 (플랫폼 독립적)"""
        file_path = tmp_path / "lines.txt"
        content = "Line 1\nLine 2\nLine 3\n"
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        result = read_file_with_encoding(file_path)
        
        # 줄바꿈이 있는지 확인 (정확한 형식은 플랫폼에 따라 다를 수 있음)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert result.count("\n") >= 3
    
    def test_read_file_with_bom(self, tmp_path):
        """BOM이 있는 UTF-8 파일 읽기"""
        file_path = tmp_path / "bom.txt"
        content = "Content with BOM"
        
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        # UTF-8로 읽으면 BOM이 포함될 수 있음
        result = read_file_with_encoding(file_path, encodings=['utf-8-sig', 'utf-8'])
        
        # BOM 없이 내용만 확인
        assert content in result or result.strip('\ufeff') == content


class TestFileUtilsIntegration:
    """파일 유틸리티 통합 테스트"""
    
    def test_find_and_read_files(self, tmp_path):
        """파일 찾기 후 읽기 워크플로우"""
        # 여러 SQL 파일 생성
        (tmp_path / "query1.sql").write_text("SELECT * FROM users;", encoding='utf-8')
        (tmp_path / "query2.sql").write_text("SELECT * FROM orders;", encoding='utf-8')
        
        # 1. SQL 파일 찾기
        sql_files = find_files_by_extension(tmp_path, [".sql"])
        assert len(sql_files) == 2
        
        # 2. 각 파일 읽기
        contents = []
        for sql_file in sql_files:
            content = read_file_with_encoding(sql_file)
            contents.append(content)
        
        assert "SELECT * FROM users;" in contents
        assert "SELECT * FROM orders;" in contents
    
    def test_find_files_with_different_encodings(self, tmp_path):
        """다양한 인코딩의 파일 찾기 및 읽기"""
        # UTF-8 파일
        utf8_file = tmp_path / "utf8.sql"
        utf8_file.write_text("SELECT '한글';", encoding='utf-8')
        
        # Latin-1 파일
        latin1_file = tmp_path / "latin1.sql"
        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write("SELECT 'Café';")
        
        # 파일 찾기
        sql_files = find_files_by_extension(tmp_path, [".sql"])
        assert len(sql_files) == 2
        
        # 모든 파일 읽기 (자동 인코딩 감지)
        for sql_file in sql_files:
            content = read_file_with_encoding(sql_file)
            assert len(content) > 0
    
    def test_recursive_find_and_read(self, tmp_path):
        """재귀적 파일 찾기 및 읽기"""
        # 중첩된 디렉토리 구조 생성
        subdir = tmp_path / "queries"
        subdir.mkdir()
        
        (tmp_path / "root.sql").write_text("-- Root query", encoding='utf-8')
        (subdir / "sub.sql").write_text("-- Sub query", encoding='utf-8')
        
        # 재귀적으로 찾기
        sql_files = find_files_by_extension(tmp_path, [".sql"])
        assert len(sql_files) == 2
        
        # 모든 파일 읽기
        contents = [read_file_with_encoding(f) for f in sql_files]
        assert any("Root query" in c for c in contents)
        assert any("Sub query" in c for c in contents)
    
    def test_batch_file_processing(self, tmp_path):
        """배치 파일 처리 시나리오"""
        # 여러 타입의 파일 생성
        files_data = {
            "query1.sql": "SELECT 1;",
            "query2.sql": "SELECT 2;",
            "package.pls": "CREATE PACKAGE;",
            "report.out": "Report data",
            "readme.txt": "Readme"
        }
        
        for filename, content in files_data.items():
            (tmp_path / filename).write_text(content, encoding='utf-8')
        
        # SQL과 PLS 파일만 찾기
        target_files = find_files_by_extension(tmp_path, [".sql", ".pls"])
        assert len(target_files) == 3
        
        # 각 파일 처리
        processed = {}
        for file_path in target_files:
            content = read_file_with_encoding(file_path)
            processed[file_path.name] = content
        
        assert "query1.sql" in processed
        assert "query2.sql" in processed
        assert "package.pls" in processed
        assert "readme.txt" not in processed
    
    def test_error_handling_workflow(self, tmp_path):
        """오류 처리 워크플로우"""
        # 정상 파일과 문제가 있는 파일 생성
        good_file = tmp_path / "good.sql"
        good_file.write_text("SELECT 1;", encoding='utf-8')
        
        # 파일 찾기
        sql_files = find_files_by_extension(tmp_path, [".sql"])
        
        # 각 파일 읽기 시도 (오류 처리 포함)
        results = []
        errors = []
        
        for sql_file in sql_files:
            try:
                content = read_file_with_encoding(sql_file)
                results.append((sql_file.name, content))
            except Exception as e:
                errors.append((sql_file.name, str(e)))
        
        assert len(results) == 1
        assert len(errors) == 0
        assert results[0][0] == "good.sql"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
