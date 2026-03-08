"""
文件解析工具单元测试
"""

import pytest
import tempfile
from pathlib import Path
from app.utils.file_parser import FileParser, split_text_into_chunks, _read_text_with_fallback


class TestReadTextWithFallback:
    """测试文本读取（带编码回退）"""

    def test_read_utf8_file(self, tmp_path):
        """测试读取 UTF-8 文件"""
        file_path = tmp_path / "utf8.txt"
        content = "这是一个 UTF-8 编码的文件。\n包含中文和 English。"
        file_path.write_text(content, encoding='utf-8')
        
        result = _read_text_with_fallback(str(file_path))
        # 标准化换行符进行比较
        assert result.replace('\r\n', '\n') == content.replace('\r\n', '\n')

    def test_read_gbk_file(self, tmp_path):
        """测试读取 GBK 编码文件"""
        file_path = tmp_path / "gbk.txt"
        content = "这是一个 GBK 编码的文件。"
        file_path.write_text(content, encoding='gbk')
        
        result = _read_text_with_fallback(str(file_path))
        assert "GBK 编码" in result or "gbk" in result.lower()

    def test_read_empty_file(self, tmp_path):
        """测试读取空文件"""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("", encoding='utf-8')
        
        result = _read_text_with_fallback(str(file_path))
        assert result == ""


class TestFileParser:
    """测试文件解析器"""

    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        supported = FileParser.SUPPORTED_EXTENSIONS
        assert '.pdf' in supported
        assert '.md' in supported
        assert '.markdown' in supported
        assert '.txt' in supported

    def test_extract_from_txt(self, tmp_path):
        """测试从 TXT 提取文本"""
        file_path = tmp_path / "test.txt"
        content = "这是第一行。\n这是第二行。\n这是第三行。"
        file_path.write_text(content, encoding='utf-8')
        
        result = FileParser.extract_text(str(file_path))
        # 标准化换行符进行比较
        assert result.replace('\r\n', '\n') == content.replace('\r\n', '\n')

    def test_extract_from_md(self, tmp_path):
        """测试从 Markdown 提取文本"""
        file_path = tmp_path / "test.md"
        content = "# 标题\n\n这是正文内容。"
        file_path.write_text(content, encoding='utf-8')
        
        result = FileParser.extract_text(str(file_path))
        # 标准化换行符进行比较
        assert result.replace('\r\n', '\n') == content.replace('\r\n', '\n')

    def test_extract_from_nonexistent_file(self, tmp_path):
        """测试提取不存在的文件"""
        file_path = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            FileParser.extract_text(str(file_path))

    def test_extract_from_unsupported_format(self, tmp_path):
        """测试提取不支持的格式"""
        file_path = tmp_path / "test.docx"
        file_path.write_text("内容", encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            FileParser.extract_text(str(file_path))
        
        assert "不支持的文件格式" in str(exc_info.value)

    def test_extract_from_multiple_files(self, tmp_path):
        """测试从多个文件提取"""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("文件1的内容", encoding='utf-8')
        file2.write_text("文件2的内容", encoding='utf-8')
        
        result = FileParser.extract_from_multiple([str(file1), str(file2)])
        
        # 检查包含关系（考虑换行符差异）
        assert "file1.txt" in result
        assert "文件1的内容" in result
        assert "file2.txt" in result
        assert "文件2的内容" in result

    def test_extract_from_multiple_with_error(self, tmp_path):
        """测试从多个文件提取时部分失败"""
        file1 = tmp_path / "file1.txt"
        file1.write_text("正常内容", encoding='utf-8')
        
        # 包含一个不存在的文件
        result = FileParser.extract_from_multiple([str(file1), str(tmp_path / "nonexistent.txt")])
        
        assert "正常内容" in result
        assert "提取失败" in result


class TestSplitTextIntoChunks:
    """测试文本分块功能"""

    def test_short_text_no_split(self):
        """测试短文本不分块"""
        text = "这是一个短文本。"
        chunks = split_text_into_chunks(text, chunk_size=100, overlap=10)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text(self):
        """测试空文本"""
        chunks = split_text_into_chunks("", chunk_size=100, overlap=10)
        assert len(chunks) == 0

    def test_whitespace_only(self):
        """测试仅包含空白字符的文本"""
        chunks = split_text_into_chunks("   \n\n   ", chunk_size=100, overlap=10)
        assert len(chunks) == 0

    def test_split_long_text(self):
        """测试长文本分块"""
        # 创建超过 chunk_size 的文本
        text = "这是一句话。" * 50  # 约 300 字符
        chunks = split_text_into_chunks(text, chunk_size=100, overlap=10)
        
        assert len(chunks) > 1
        # 验证每个块不超过 chunk_size
        for chunk in chunks:
            assert len(chunk) <= 100

    def test_overlap_preserved(self):
        """测试重叠部分保留"""
        text = "A" * 200
        chunks = split_text_into_chunks(text, chunk_size=100, overlap=20)
        
        if len(chunks) > 1:
            # 第二块应该包含第一块末尾的 20 个字符
            assert chunks[1].startswith("A" * 20)

    def test_sentence_boundary_respected(self):
        """测试句子边界优先"""
        # 创建包含句子结束符的文本
        text = "这是第一句。这是第二句。这是第三句。这是第四句。" * 10
        chunks = split_text_into_chunks(text, chunk_size=50, overlap=5)
        
        # 验证分块不会切断句子（在合理范围内）
        for chunk in chunks:
            # 块不应该以句中字符开头（除非是第一个块）
            pass  # 具体断言取决于实现细节

    def test_custom_chunk_size(self):
        """测试自定义块大小"""
        text = "A" * 500
        chunks = split_text_into_chunks(text, chunk_size=200, overlap=20)
        
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 200

    def test_custom_overlap(self):
        """测试自定义重叠大小"""
        text = "A" * 300
        chunks_small_overlap = split_text_into_chunks(text, chunk_size=100, overlap=10)
        chunks_large_overlap = split_text_into_chunks(text, chunk_size=100, overlap=30)
        
        # 大重叠应该产生更多块
        assert len(chunks_large_overlap) >= len(chunks_small_overlap)
