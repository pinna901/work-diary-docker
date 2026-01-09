import pytest
from app import add

# 这是一个测试用例
def test_add_function():
    # 我们断言：1 + 1 必须等于 2
    assert add(1, 1) == 2
    # 我们断言：-1 + 1 必须等于 0
    assert add(-1, 1) == 0

# 如果这里写 assert add(1, 1) == 3，测试就会失败