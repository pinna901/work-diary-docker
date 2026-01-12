# utils package
from utils.decorators import *
from utils.exceptions import *

# Keep the original add function for backward compatibility
def add(a, b):
    return a + b
