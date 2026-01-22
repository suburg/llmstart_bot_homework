"""Простой тест для проверки обработки ошибок LLM API"""
import sys
sys.path.insert(0, 'c:/_Src/llmstart_bot_homework')

import asyncio
import httpx
import openai
from unittest.mock import MagicMock

from src.ai.llm import is_retryable_error


def test_is_retryable_error():
    """Тест функции проверки на повторяемость ошибок"""
    print("=" * 60)
    print("Testing is_retryable_error function")
    print("=" * 60 + "\n")
    
    # 1. Timeout ошибки - должны быть retryable
    print("1. Testing timeout errors...")
    timeout_error = asyncio.TimeoutError()
    assert is_retryable_error(timeout_error), "TimeoutError should be retryable"
    print("   [OK] asyncio.TimeoutError is retryable")
    
    httpx_timeout = httpx.TimeoutException("Request timeout")
    assert is_retryable_error(httpx_timeout), "httpx.TimeoutException should be retryable"
    print("   [OK] httpx.TimeoutException is retryable")
    
    httpx_connect = httpx.ConnectError("Connection failed")
    assert is_retryable_error(httpx_connect), "httpx.ConnectError should be retryable"
    print("   [OK] httpx.ConnectError is retryable")
    
    # 2. Rate limit - должен быть retryable
    print("\n2. Testing rate limit errors...")
    rate_limit = MagicMock(spec=openai.RateLimitError)
    assert is_retryable_error(rate_limit), "RateLimitError should be retryable"
    print("   [OK] RateLimitError is retryable")
    
    # 3. polza.ai специфическая ошибка 400 с временной недоступностью
    print("\n3. Testing polza.ai specific 400 errors...")
    bad_request_temp = MagicMock(spec=openai.BadRequestError)
    bad_request_temp.__str__ = lambda self: "Service is temporarily unavailable"
    assert is_retryable_error(bad_request_temp), "BadRequestError with 'temporarily unavailable' should be retryable"
    print("   [OK] BadRequestError with 'temporarily unavailable' is retryable")
    
    bad_request_llm = MagicMock(spec=openai.BadRequestError)
    bad_request_llm.__str__ = lambda self: "Error: LLM_REQUEST_ERROR"
    assert is_retryable_error(bad_request_llm), "BadRequestError with 'LLM_REQUEST_ERROR' should be retryable"
    print("   [OK] BadRequestError with 'LLM_REQUEST_ERROR' is retryable")
    
    # 4. Обычный BadRequest - НЕ должен быть retryable
    print("\n4. Testing permanent errors...")
    bad_request_normal = MagicMock(spec=openai.BadRequestError)
    bad_request_normal.__str__ = lambda self: "Invalid API key"
    assert not is_retryable_error(bad_request_normal), "BadRequestError with auth error should NOT be retryable"
    print("   [OK] BadRequestError with auth error is NOT retryable")
    
    # 5. AuthenticationError - НЕ должен быть retryable
    auth_error = MagicMock(spec=openai.AuthenticationError)
    assert not is_retryable_error(auth_error), "AuthenticationError should NOT be retryable"
    print("   [OK] AuthenticationError is NOT retryable")
    
    # 6. Server errors (5xx)
    print("\n5. Testing server errors (5xx)...")
    server_error = MagicMock()
    server_error.status_code = 503
    assert is_retryable_error(server_error), "503 error should be retryable"
    print("   [OK] 503 Server Error is retryable")
    
    server_error_500 = MagicMock()
    server_error_500.status_code = 500
    assert is_retryable_error(server_error_500), "500 error should be retryable"
    print("   [OK] 500 Server Error is retryable")
    
    # 7. Client errors (4xx кроме специальных) - НЕ должны быть retryable
    client_error = MagicMock()
    client_error.status_code = 404
    client_error.__str__ = lambda self: "Not found"
    assert not is_retryable_error(client_error), "404 error should NOT be retryable"
    print("   [OK] 404 Client Error is NOT retryable")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)


def test_module_imports():
    """Тест что все модули импортируются без ошибок"""
    print("\n" + "=" * 60)
    print("Testing module imports")
    print("=" * 60 + "\n")
    
    try:
        from src.ai import llm
        print("[OK] src.ai.llm imported successfully")
        
        from src.bot.handlers import messages
        print("[OK] src.bot.handlers.messages imported successfully")
        
        from src.bot.handlers import commands
        print("[OK] src.bot.handlers.commands imported successfully")
        
        from src.story import formatter
        print("[OK] src.story.formatter imported successfully")
        
        from src.config import config
        print("[OK] src.config imported successfully")
        
        # Проверяем наличие новых параметров в конфиге
        assert "llm_timeout" in config, "llm_timeout should be in config"
        assert "llm_max_retries" in config, "llm_max_retries should be in config"
        assert "llm_retry_delay" in config, "llm_retry_delay should be in config"
        print("[OK] New config parameters are present")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All modules imported successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        raise


if __name__ == "__main__":
    try:
        test_module_imports()
        test_is_retryable_error()
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
