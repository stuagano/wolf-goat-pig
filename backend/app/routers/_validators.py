"""Reusable Pydantic field-validation primitives for router request models."""

from typing import Annotated

from pydantic import AfterValidator


def non_blank(v: str) -> str:
    """Strip surrounding whitespace and reject empty/whitespace-only strings.

    Raised ValueError is wrapped by Pydantic into a 422 response.
    """
    v = v.strip()
    if not v:
        raise ValueError("must not be blank")
    return v


# A `str` that is stripped and guaranteed non-empty after validation.
NonBlankStr = Annotated[str, AfterValidator(non_blank)]
