"""
重试机制单元测试
"""

import pytest
import time
from unittest.mock import Mock, patch
from app.utils.retry import retry_with_backoff, retry_with_backoff_async


class TestRetryWithBackoff:
    """测试同步重试装饰器"""

    def test_successful_call_no_retry(self):
        """测试成功调用不重试"""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_failure(self):
        """测试失败时重试"""
        mock_func = Mock(side_effect=[Exception("error"), Exception("error"), "success"])
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        mock_func = Mock(side_effect=Exception("persistent error"))
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception) as exc_info:
            test_func()
        
        assert "persistent error" in str(exc_info.value)
        assert mock_func.call_count == 3  # 初始调用 + 2次重试

    def test_specific_exception_types(self):
        """测试特定异常类型触发重试"""
        mock_func = Mock(side_effect=[ValueError("value error"), "success"])
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"

    def test_non_matching_exception_not_retried(self):
        """测试不匹配异常类型不重试"""
        mock_func = Mock(side_effect=TypeError("type error"))
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
        def test_func():
            return mock_func()
        
        with pytest.raises(TypeError):
            test_func()
        
        assert mock_func.call_count == 1

    def test_on_retry_callback(self):
        """测试重试回调函数"""
        mock_func = Mock(side_effect=[Exception("error"), "success"])
        on_retry_mock = Mock()
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01, on_retry=on_retry_mock)
        def test_func():
            return mock_func()
        
        test_func()
        
        assert on_retry_mock.call_count == 1
        args, kwargs = on_retry_mock.call_args
        assert isinstance(args[0], Exception)
        assert args[1] == 1  # retry count

    def test_delay_increases_with_backoff(self):
        """测试延迟随退避因子增加"""
        delays = []
        
        original_sleep = time.sleep
        def mock_sleep(duration):
            delays.append(duration)
        
        mock_func = Mock(side_effect=[Exception("error"), Exception("error"), "success"])
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0, jitter=False)
        def test_func():
            return mock_func()
        
        with patch('time.sleep', mock_sleep):
            test_func()
        
        # 第二次重试的延迟应该是第一次的两倍
        assert len(delays) == 2
        assert delays[1] == delays[0] * 2.0

    def test_max_delay_respected(self):
        """测试最大延迟限制"""
        delays = []
        
        def mock_sleep(duration):
            delays.append(duration)
        
        mock_func = Mock(side_effect=[Exception("error"), Exception("error"), 
                                      Exception("error"), Exception("error"), "success"])
        
        @retry_with_backoff(max_retries=5, initial_delay=1.0, max_delay=2.0, 
                           backoff_factor=2.0, jitter=False)
        def test_func():
            return mock_func()
        
        with patch('time.sleep', mock_sleep):
            test_func()
        
        # 所有延迟都不应超过 max_delay
        for delay in delays:
            assert delay <= 2.0

    def test_jitter_adds_randomness(self):
        """测试抖动添加随机性"""
        delays = []
        
        def mock_sleep(duration):
            delays.append(duration)
        
        mock_func = Mock(side_effect=[Exception("error"), "success"])
        
        @retry_with_backoff(max_retries=2, initial_delay=1.0, jitter=True)
        def test_func():
            return mock_func()
        
        with patch('time.sleep', mock_sleep):
            test_func()
        
        # 有抖动时，延迟应该在 0.5 * delay 到 1.5 * delay 之间
        assert 0.5 <= delays[0] <= 1.5

    def test_preserves_function_metadata(self):
        """测试保留函数元数据"""
        @retry_with_backoff(max_retries=3)
        def my_function():
            """我的文档字符串"""
            return "result"
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "我的文档字符串"


class TestRetryWithBackoffAsync:
    """测试异步重试装饰器"""

    @pytest.mark.asyncio
    async def test_successful_async_call(self):
        """测试成功的异步调用"""
        mock_func = Mock(return_value="async success")
        
        @retry_with_backoff_async(max_retries=3)
        async def test_async_func():
            return mock_func()
        
        result = await test_async_func()
        
        assert result == "async success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_on_failure(self):
        """测试异步失败重试"""
        mock_func = Mock(side_effect=[Exception("error"), "success"])
        
        @retry_with_backoff_async(max_retries=3, initial_delay=0.01)
        async def test_async_func():
            return mock_func()
        
        result = await test_async_func()
        
        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_async_max_retries_exceeded(self):
        """测试异步超过最大重试"""
        mock_func = Mock(side_effect=Exception("async error"))
        
        @retry_with_backoff_async(max_retries=2, initial_delay=0.01)
        async def test_async_func():
            return mock_func()
        
        with pytest.raises(Exception) as exc_info:
            await test_async_func()
        
        assert "async error" in str(exc_info.value)
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_async_preserves_function_metadata(self):
        """测试异步保留函数元数据"""
        @retry_with_backoff_async(max_retries=3)
        async def my_async_function():
            """我的异步文档字符串"""
            return "result"
        
        assert my_async_function.__name__ == "my_async_function"
        assert my_async_function.__doc__ == "我的异步文档字符串"
