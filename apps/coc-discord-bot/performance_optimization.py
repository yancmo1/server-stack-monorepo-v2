# Minimal stub for development and production

def get_performance_optimizer():
    return None

def performance_decorator(arg=None):
    def decorator(func):
        return func
    if callable(arg):
        # Used as @performance_decorator with no args
        return decorator(arg)
    # Used as @performance_decorator("some_name")
    return decorator

