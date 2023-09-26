import asyncio
import inspect
import sys
from functools import wraps


def exc_handler(on_error_obj_method_name=None, handled_exceptions=None):
    handled_exceptions = tuple(handled_exceptions) if handled_exceptions else (Exception,)

    def exc_handler_decorator(funct):
        if asyncio.iscoroutinefunction(funct):
            @wraps(funct)
            async def _wrapper(obj, *args, **kwarg):
                result = None
                try:
                    result = await funct(obj, *args, **kwarg)
                except handled_exceptions:
                    try:
                        on_error = (
                            getattr(obj, on_error_obj_method_name)
                            if on_error_obj_method_name else (lambda *x, **y: None)
                        )
                        result = (
                            on_error(*args, **kwarg)
                            if not asyncio.iscoroutinefunction(on_error)
                            else await on_error(*args, **kwarg)
                        )
                    except Exception:
                        print(sys.exc_info())
                return result

            return _wrapper
        elif inspect.isasyncgenfunction(funct):
            @wraps(funct)
            async def _wrapper(obj, *args, **kwarg):
                try:
                    async for yield_ in funct(obj, *args, **kwarg):
                        yield yield_
                except handled_exceptions:
                    try:
                        on_error = (
                            getattr(obj, on_error_obj_method_name)
                            if on_error_obj_method_name else (lambda *x, **y: None)
                        )
                        if asyncio.iscoroutinefunction(on_error):
                            yield await on_error(*args, **kwarg)
                        elif inspect.isasyncgenfunction(on_error):
                            async for yield_ in on_error(*args, **kwarg):
                                yield yield_
                        else:
                            yield on_error(*args, **kwarg)
                    except Exception:
                        print(sys.exc_info())

            return _wrapper
        else:
            @wraps(funct)
            def _wrapper(obj, *args, **kwarg):
                result = None
                try:
                    result = funct(obj, *args, **kwarg)
                except handled_exceptions:
                    try:
                        on_error = (
                            getattr(obj, on_error_obj_method_name)
                            if on_error_obj_method_name else (lambda *x, **y: None)
                        )
                        result = on_error(*args, **kwarg)
                    except Exception:
                        print(sys.exc_info())
                return result

            return _wrapper

    return exc_handler_decorator
