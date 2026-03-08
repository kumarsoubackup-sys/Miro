"""
文本处理服务单元测试
"""

import pytest
from unittest.mock import Mock, patch
from app.services.text_processor import TextProcessor


class TestTextProcessor:
    """测试文本处理器"""

    def test_extract_from_files(self, tmp_path):
        """测试从文件提取文本"""
        # 创建测试文件
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("内容1", encoding='utf-8')
        file2.write_text("内容2", encoding='utf-8')
        
        result = TextProcessor.extract_from_files([str(file1), str(file2)])
        
        assert "内容1" in result
        assert "内容2" in result

    @patch('app.services.text_processor.FileParser.extract_from_multiple')
    def test_extract_from_files_calls_parser(self, mock_extract):
        """测试提取文本调用解析器"""
        mock_extract.return_value = "提取的内容"
        
        result = TextProcessor.extract_from_files(["/path/to/file.txt"])
        
        assert result == "提取的内容"
        mock_extract.assert_called_once_with(["/path/to/file.txt"])

    def test_split_text(self):
        """测试分割文本"""
        text = "A" * 1000
        chunks = TextProcessor.split_text(text, chunk_size=200, overlap=20)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 200

    @patch('app.services.text_processor.split_text_into_chunks')
    def test_split_text_calls_utility(self, mock_split):
        """测试分割文本调用工具函数"""
        mock_split.return_value = ["chunk1", "chunk2"]
        
        result = TextProcessor.split_text("some text", chunk_size=100, overlap=10)
        
        assert result == ["chunk1", "chunk2"]
        mock_split.assert_called_once_with("some text", 100, 10)

    def test_preprocess_text_normalizes_newlines(self):
        """测试预处理标准化换行"""
        text = "line1\r\nline2\rline3"
        result = TextProcessor.preprocess_text(text)
        
        assert "\r\n" not in result
        assert "\r" not in result
        assert "line1\nline2\nline3" in result

    def test_preprocess_text_removes_extra_blank_lines(self):
        """测试预处理移除多余空行"""
        text = "line1\n\n\n\nline2"
        result = TextProcessor.preprocess_text(text)
        
        # 最多保留两个换行
        assert "\n\n\n" not in result

    def test_preprocess_text_strips_whitespace(self):
        """测试预处理去除行首行尾空白"""
        text = "  line1  \n  line2  "
        result = TextProcessor.preprocess_text(text)
        
        lines = result.split('\n')
        for line in lines:
            assert not line.startswith(' ') or not line.endswith(' ')

    def test_preprocess_text_empty_input(self):
        """测试预处理空输入"""
        result = TextProcessor.preprocess_text("")
        assert result == ""

    def test_preprocess_text_whitespace_only(self):
        """测试预处理仅空白字符"""
        result = TextProcessor.preprocess_text("   \n\n   ")
        assert result == ""

    def test_get_text_stats(self):
        """测试获取文本统计"""
        text = "Hello world\n这是第二行\n这是第三行"
        stats = TextProcessor.get_text_stats(text)
        
        assert stats["total_chars"] == len(text)
        assert stats["total_lines"] == 3
        assert stats["total_words"] >= 3  # 取决于分词

    def test_get_text_stats_empty(self):
        """测试空文本统计"""
        stats = TextProcessor.get_text_stats("")
        
        assert stats["total_chars"] == 0
        assert stats["total_lines"] == 1  # 空字符串 split 后有一个元素
        assert stats["total_words"] == 0

    def test_get_text_stats_single_line(self):
        """测试单行文本统计"""
        text = "单行文本"
        stats = TextProcessor.get_text_stats(text)
        
        assert stats["total_chars"] == 4
        assert stats["total_lines"] == 1

    def test_integration_extract_and_split(self, tmp_path):
        """测试提取和分割集成"""
        # 创建大文本文件
        file_path = tmp_path / "large.txt"
        content = "A" * 5000
        file_path.write_text(content, encoding='utf-8')
        
        # 提取
        extracted = TextProcessor.extract_from_files([str(file_path)])
        assert len(extracted) >= 5000
        
        # 分割
        chunks = TextProcessor.split_text(extracted, chunk_size=1000, overlap=100)
        assert len(chunks) >= 4  # 5000 / 1000 = 5 块左右

    def test_integration_preprocess_and_stats(self):
        """测试预处理和统计集成"""
        text = "  Line 1  \r\n\n\n\n  Line 2  \r\n"
        
        # 预处理
        processed = TextProcessor.preprocess_text(text)
        
        # 统计
        stats = TextProcessor.get_text_stats(processed)
        
        assert stats["total_lines"] <= 3  # 预处理后空行减少
