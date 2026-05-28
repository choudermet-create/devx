from ast import literal_eval

from pydantic import ValidationError


def format_validation_errors(error: ValidationError) -> list[str]:
    return [
        format_validation_error(error_detail)
        for error_detail in error.errors(include_url=False)
    ]


def format_validation_error(error_detail: dict) -> str:
    column_name = format_location(error_detail.get("loc", []))
    input_value = error_detail.get("input")
    valid_values = get_valid_values(error_detail)
    valid_range = get_valid_range(error_detail)

    if valid_values:
        return (
            f"Input value {input_value!r} for '{column_name}' is not valid. "
            f"Valid values are: {valid_values}."
        )

    if valid_range:
        return (
            f"Input value {input_value!r} for '{column_name}' is not valid. "
            f"Valid range is: {valid_range}."
        )

    return (
        f"Input value {input_value!r} for '{column_name}' is not valid. "
        f"{error_detail.get('msg', 'Please check the workbook value.')}"
    )


def format_location(location) -> str:
    if isinstance(location, (list, tuple)):
        return " -> ".join(str(item) for item in location)

    return str(location)


def get_valid_values(error_detail: dict) -> str | None:
    context = error_detail.get("ctx") or {}

    if "expected" in context:
        return context["expected"]

    error = context.get("error")
    if error is None:
        return None

    message = str(error)
    marker = "Allowed values:"
    if marker not in message:
        return None

    return format_allowed_values(message.split(marker, 1)[1].strip())


def get_valid_range(error_detail: dict) -> str | None:
    context = error_detail.get("ctx") or {}
    minimum = context.get("ge")
    maximum = context.get("le")

    if minimum is not None and maximum is not None:
        return f"{minimum}-{maximum}"

    if minimum is not None:
        return f"{minimum} or greater"

    if maximum is not None:
        return f"{maximum} or lower"

    return None


def format_allowed_values(value: str) -> str:
    try:
        parsed_value = literal_eval(value)
    except (SyntaxError, ValueError):
        return value

    if isinstance(parsed_value, list):
        return ", ".join(repr(item) for item in parsed_value)

    return value
