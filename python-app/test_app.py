import pytest
# ⚠️ 修改这里：从 utils 导入，而不是从 app 导入
from utils import add 

def test_add_function():
    assert add(1, 1) == 2
    assert add(-1, 1) == 0