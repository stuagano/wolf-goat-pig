from app.agent import _generate_config
from app.config import Settings


def _tools():
    return _generate_config(Settings()).tools


def test_model_serves_the_computer_use_tool():
    """General-purpose models 400 with 'computer use is not supported ... in this region'."""
    assert Settings().computer_use_model == "gemini-2.5-computer-use-preview-10-2025"


def test_no_predefined_actions_are_excluded():
    computer_use_tools = [t for t in _tools() if t.computer_use is not None]
    assert len(computer_use_tools) == 1
    assert not computer_use_tools[0].computer_use.excluded_predefined_functions


def test_custom_function_declarations_are_registered():
    declared = {
        decl.name for tool in _tools() if tool.function_declarations for decl in tool.function_declarations
    }
    assert declared == {
        "request_confirmation",
        "enter_foretees_credentials",
        "report_booking_result",
    }
