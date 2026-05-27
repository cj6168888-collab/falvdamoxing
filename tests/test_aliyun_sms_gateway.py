import json

import pytest

from scripts import aliyun_sms_gateway


def test_build_send_sms_params_uses_purpose_specific_template(monkeypatch):
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_SECRET", "test-secret")
    monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "测试")
    monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "SMS_DEFAULT")
    monkeypatch.setenv("ALIYUN_SMS_REGISTER_TEMPLATE_CODE", "SMS_REGISTER")
    monkeypatch.setenv("ALIYUN_SMS_REGION_ID", "cn-hangzhou")

    params = aliyun_sms_gateway._build_send_sms_params("13800138000", "123456", "register")

    assert params["Action"] == "SendSms"
    assert params["TemplateCode"] == "SMS_REGISTER"
    assert params["PhoneNumbers"] == "13800138000"
    assert json.loads(params["TemplateParam"]) == {"code": "123456"}
    assert params["Signature"]


def test_build_send_sms_params_requires_credentials(monkeypatch):
    monkeypatch.delenv("ALIYUN_SMS_ACCESS_KEY_ID", raising=False)
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_SECRET", "test-secret")
    monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "测试")
    monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "SMS_DEFAULT")

    with pytest.raises(RuntimeError, match="ALIYUN_SMS_ACCESS_KEY_ID"):
        aliyun_sms_gateway._build_send_sms_params("13800138000", "123456", "register")


def test_send_sms_dry_run_does_not_call_provider(monkeypatch):
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_SECRET", "test-secret")
    monkeypatch.setenv("ALIYUN_SMS_SIGN_NAME", "测试")
    monkeypatch.setenv("ALIYUN_SMS_TEMPLATE_CODE", "SMS_DEFAULT")
    monkeypatch.setenv("ALIYUN_SMS_DRY_RUN", "1")

    def fail_urlopen(*args, **kwargs):
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(aliyun_sms_gateway.request, "urlopen", fail_urlopen)

    assert aliyun_sms_gateway.send_sms("13800138000", "123456", "register")["Code"] == "OK"
