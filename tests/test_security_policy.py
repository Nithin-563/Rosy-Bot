from rosy.security.policy import check_user_request, founder_response, sanitize_output


def test_founder_and_brand_answers():
    assert founder_response("who made you?") == "I Am Made By MakeIt Company."
    assert "Wisee Models" in founder_response("what model powers you?")


def test_destructive_execution_is_blocked():
    decision = check_user_request("delete the server")
    assert decision.blocked is True
    assert "destructive actions" in decision.response


def test_output_redacts_secrets_and_safety_labels():
    text = sanitize_output("token=sk-or-v1-abcdefghijklmnop User Safety: internal")
    assert "sk-or-v1" not in text
    assert "User Safety:" not in text
