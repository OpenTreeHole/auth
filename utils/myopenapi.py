from typing import Union, Literal, Any, Optional, Type, Callable

from pydantic import BaseModel
from sanic_ext.extensions.openapi.builders import OperationStore


def response(
        status: Union[Literal["default"], int] = "default",
        content: Any = str,
        description: Optional[str] = None,
        **kwargs,
):
    content = {'application/json': content}

    def inner(func):
        OperationStore()[func].response(status, content, description, **kwargs)
        return func

    return inner


def body(content: Any, **kwargs, ):
    content = {'application/json': content}

    def inner(func):
        OperationStore()[func].body(content, **kwargs)
        return func

    return inner


def query(model: Type[BaseModel]):
    def inner(func: Callable):
        for name, field in model.schema()['properties'].items():
            if field['type'] == 'integer':
                type_ = int
            else:
                type_ = str
            OperationStore()[func].parameter(name, type_)
        return func

    return inner
