from rosy.ai.base import AIProviderError
from rosy.core.errors import safe_user_message
from rosy.security.policy import founder_response
from rosy.tools import build_default_registry

def test_provider_error_keeps_status_code():
    exc=AIProviderError("x", provider="openrouter", status_code=402)
    assert exc.status_code == 402
    assert "credits" in safe_user_message(exc).lower()

def test_founder_name_is_available_in_founder_variants():
    responses = [founder_response(q) for q in (
        "who made you?", "who is your founder?", "who created you?", "who powers you?"
    )]
    assert any("Nithin" in (r or "") for r in responses)
    assert any("MakeIt Company" in (r or "") for r in responses)

def test_new_tools_registered_without_privileged_access():
    reg=build_default_registry(http=None, files=None)
    names={s.name for s in reg.specs()}
    assert {"math","current_time","json_format","text_hash","random_number","roll_dice","url_encode","random_choice","base64_encode","regex_test"} <= names
