import typing as t


class NotFoundException(Exception):
    pass


class MultipleFoundException(Exception):
    pass


T = t.TypeVar("T")


def findfirst(arr: list[T], condition: t.Callable, strict: bool = False) -> t.Optional[T]:
    """Find the first element in an array that satisfies the given condition.

    Args:
        arr (list): The list to search through.
        condition (Callable[[Any], bool]): A function that takes an element and returns True if it satisfies the condition.
        strict (bool): If true, raises an error if no element is found. Defaults to False.

    Returns:
        Optional[Any]: The first element that satisfies the condition, or None if no such element is found.
    """
    for item in arr:
        if condition(item):
            return item

    if strict:
        raise NotFoundException("No element found that satisfies the condition.")

    return None


def findone(arr: list[T], condition: t.Callable, strict: bool = False) -> t.Optional[T]:
    """Find exactly one element in an array that satisfies the given condition.

    Args:
        arr (list): The list to search through.
        condition (Callable[[Any], bool]): A function that takes an element and returns True if it satisfies the condition.
        strict (bool): If true, raises an error if no element is found or if multiple elements are found. Defaults to False.

    Returns:
        Optional[Any]: The element that satisfies the condition, or None if no such element is found.
    """
    found_items = [item for item in arr if condition(item)]

    if len(found_items) == 1:
        return found_items[0]
    elif len(found_items) == 0:
        if strict:
            raise NotFoundException("No element found that satisfies the condition.")
        return None
    else:
        if strict:
            raise MultipleFoundException("Multiple elements found that satisfy the condition.")
        return None
