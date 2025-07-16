"""
Threading utilities for AI Investment Tool
Provides async wrappers for CPU-intensive tasks
"""
import asyncio
import functools
from typing import Any, Callable, TypeVar
from fastapi import Request

T = TypeVar('T')

async def run_in_thread_pool(request: Request, func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run a CPU-intensive function in the application's thread pool
    
    Args:
        request: FastAPI request object to access app state
        func: The function to run in thread pool
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        The result of the function execution
    """
    loop = asyncio.get_event_loop()
    thread_pool = getattr(request.app.state, 'thread_pool', None)
    
    if thread_pool is None:
        # Fallback to default thread pool if not available
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    
    return await loop.run_in_executor(
        thread_pool, 
        functools.partial(func, *args, **kwargs)
    )

async def run_cpu_intensive_task(request: Request, task_func: Callable[..., T], *args, **kwargs) -> T:
    """
    Convenience wrapper for running CPU-intensive tasks
    
    This is useful for:
    - Data analysis and calculations
    - Technical indicator computations
    - AI model inference
    - PDF generation
    - Large data processing
    
    Args:
        request: FastAPI request object
        task_func: The CPU-intensive function to execute
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the task execution
    """
    return await run_in_thread_pool(request, task_func, *args, **kwargs)

def cpu_intensive(func: Callable[..., T]) -> Callable:
    """
    Decorator to mark functions as CPU-intensive and automatically
    run them in thread pool when called from async context
    
    Usage:
        @cpu_intensive
        def heavy_calculation(data):
            # CPU-intensive work here
            return result
            
        # In async route:
        result = await heavy_calculation(request, data)
    """
    @functools.wraps(func)
    async def async_wrapper(request: Request, *args, **kwargs) -> T:
        return await run_in_thread_pool(request, func, *args, **kwargs)
    
    # Keep original function available as .sync for synchronous calls
    async_wrapper.sync = func
    return async_wrapper 