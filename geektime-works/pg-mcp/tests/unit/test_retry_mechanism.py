"""重试机制单元测试.

测试覆盖：
- 指数退避策略
- 随机抖动
- 最大重试次数限制
- 可重试异常分类
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from pg_mcp.resilience.retry import RetryConfig, retry_with_backoff, RetryableError


class TestRetryConfig:
    """测试 RetryConfig 配置."""

    def test_default_config(self) -> None:
        """测试默认配置."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True

    def test_custom_config(self) -> None:
        """测试自定义配置."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            backoff_factor=3.0,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.backoff_factor == 3.0
        assert config.jitter is False


class TestRetryableError:
    """测试可重试异常."""

    def test_retryable_error_creation(self) -> None:
        """测试创建可重试异常."""
        error = RetryableError("Temporary failure")
        assert str(error) == "Temporary failure"
        assert isinstance(error, Exception)


class TestRetryWithBackoff:
    """测试异步重试函数."""

    @pytest.mark.asyncio
    async def test_successful_operation_no_retry(self) -> None:
        """测试成功的操作不重试."""
        config = RetryConfig(max_attempts=3)
        mock_func = AsyncMock(return_value="success")

        result = await retry_with_backoff(mock_func, config)
        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self) -> None:
        """测试在可重试异常时重试."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        mock_func = AsyncMock(side_effect=[RetryableError("Fail 1"), RetryableError("Fail 2"), "success"])

        result = await retry_with_backoff(mock_func, config)
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_specific_exception(self) -> None:
        """测试在指定异常时重试."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        mock_func = AsyncMock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), "success"])

        result = await retry_with_backoff(mock_func, config, retryable_errors=(ValueError,))
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self) -> None:
        """测试在不可重试异常时不重试."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        mock_func = AsyncMock(side_effect=RuntimeError("Fatal error"))

        with pytest.raises(RuntimeError, match="Fatal error"):
            await retry_with_backoff(mock_func, config, retryable_errors=(RetryableError,))

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_exhaust_retries(self) -> None:
        """测试耗尽所有重试次数."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        mock_func = AsyncMock(side_effect=[RetryableError("Fail 1"), RetryableError("Fail 2"), RetryableError("Fail 3")])

        with pytest.raises(RetryableError):
            await retry_with_backoff(mock_func, config)

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff(self) -> None:
        """测试指数退避."""
        config = RetryConfig(
            max_attempts=4,
            base_delay=0.01,
            backoff_factor=2.0,
            jitter=False,  # 禁用抖动以便精确测试
        )

        call_times = []
        mock_func = AsyncMock(side_effect=[RetryableError("Fail")] * 3 + ["success"])

        async def timed_call():
            import time
            call_times.append(time.time())
            return await mock_func()

        await retry_with_backoff(timed_call, config)

        # 验证延迟递增
        assert mock_func.call_count == 4
        assert len(call_times) == 4

        delays = [call_times[i + 1] - call_times[i] for i in range(3)]
        assert delays[0] >= 0.01  # 第一次重试延迟
        assert delays[1] >= 0.02  # 第二次重试延迟（指数增长）
        assert delays[2] >= 0.04  # 第三次重试延迟

    @pytest.mark.asyncio
    async def test_max_delay_cap(self) -> None:
        """测试最大延迟上限."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=2.0,
            backoff_factor=10.0,
            jitter=False,
        )

        call_times = []
        mock_func = AsyncMock(side_effect=[RetryableError("Fail")] * 4 + ["success"])

        async def timed_call():
            import time
            call_times.append(time.time())
            return await mock_func()

        await retry_with_backoff(timed_call, config)

        # 验证延迟被 max_delay 限制
        delays = [call_times[i + 1] - call_times[i] for i in range(4)]
        assert all(d <= 2.1 for d in delays)  # 所有延迟不超过 2.0 秒

    @pytest.mark.asyncio
    async def test_jitter_variation(self) -> None:
        """测试随机抖动增加变化."""
        config = RetryConfig(
            max_attempts=10,
            base_delay=0.01,
            backoff_factor=1.5,
            jitter=True,
        )

        call_times = []
        mock_func = AsyncMock(side_effect=[RetryableError("Fail")] * 9 + ["success"])

        async def timed_call():
            import time
            call_times.append(time.time())
            return await mock_func()

        await retry_with_backoff(timed_call, config)

        delays = [call_times[i + 1] - call_times[i] for i in range(9)]

        # 有抖动时，延迟应该有变化
        unique_delays = set(round(d, 4) for d in delays)
        assert len(unique_delays) > 1  # 不应该所有延迟都相同


class TestRetryIntegration:
    """集成测试."""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self) -> None:
        """测试重试与熔断器集成."""
        from pg_mcp.resilience.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=3)
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        async def operation_with_check():
            if not breaker.allow_request():
                raise RuntimeError("Circuit is open")
            breaker.record_failure()
            raise RetryableError("Operation failed")

        # 重试应该触发熔断器
        with pytest.raises(RetryableError):
            await retry_with_backoff(operation_with_check, config)

        # 熔断器应该打开
        assert breaker.state.name == "OPEN"


class TestRetryPerformance:
    """性能测试."""

    @pytest.mark.asyncio
    async def test_retry_overhead(self) -> None:
        """测试重试机制的性能开销."""
        config = RetryConfig(max_attempts=3, base_delay=0.001)

        mock_func = AsyncMock(side_effect=[RetryableError("Fail"), "success"])

        import time

        start = time.perf_counter()
        result = await retry_with_backoff(mock_func, config)
        elapsed = time.perf_counter() - start

        assert result == "success"
        # 重试开销应该很小
        assert 0.001 <= elapsed < 0.1

    @pytest.mark.asyncio
    async def test_concurrent_retries(self) -> None:
        """测试并发重试操作."""
        config = RetryConfig(max_attempts=2, base_delay=0.01)

        async def operation_with_id(op_id: int):
            mock_func = AsyncMock(side_effect=[RetryableError(f"Fail {op_id}"), f"Success {op_id}"])
            return await retry_with_backoff(mock_func, config)

        # 并发执行多个重试操作
        tasks = [operation_with_id(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for i, result in enumerate(results):
            assert result == f"Success {i}"
