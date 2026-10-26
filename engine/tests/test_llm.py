import io
import json
import sys
import pathlib
import urllib.request
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from engine.llm import (OpenAIClient, LlamaServerClient, FakeLLMClient, Sampling,
                        client_from_connection, chatml_to_messages, _openai_base)


class _Capture:
    def __init__(self, response: dict):
        self.response = response
        self.req = None
        self.body = None

    def __call__(self, req, timeout=None):
        self.req = req
        self.body = json.loads(req.data.decode("utf-8"))
        self.timeout = timeout
        return io.BytesIO(json.dumps(self.response).encode("utf-8"))


def _patched(response: dict):
    cap = _Capture(response)
    return cap


def _run(client, prompt, sampling, response):
    cap = _patched(response)
    orig = urllib.request.urlopen
    urllib.request.urlopen = cap
    try:
        out = client.complete(prompt, sampling)
    finally:
        urllib.request.urlopen = orig
    return out, cap


CHATML = ("<|im_start|>system\nYou narrate.<|im_end|>\n"
          "<|im_start|>user\nI open the door.<|im_end|>\n"
          "<|im_start|>assistant\n")


def test_openai_base_normalizes_variants():
    assert _openai_base("http://127.0.0.1:5000/v1/completions") == "http://127.0.0.1:5000"
    assert _openai_base("http://127.0.0.1:5000/v1/chat/completions") == "http://127.0.0.1:5000"
    assert _openai_base("http://h:8080/v1/") == "http://h:8080"
    assert _openai_base("https://api.openai.com/v1") == "https://api.openai.com"
    assert _openai_base("http://h:8080") == "http://h:8080"


def test_chatml_to_messages_roundtrips_roles():
    msgs = chatml_to_messages(CHATML)
    assert msgs == [{"role": "system", "content": "You narrate."},
                    {"role": "user", "content": "I open the door."}]
    assert chatml_to_messages("just text")[0]["role"] == "user"


def test_completions_endpoint_sends_raw_prompt():
    client = OpenAIClient("http://127.0.0.1:5000", endpoint="completions", model="m1")
    out, cap = _run(client, CHATML, Sampling(temperature=0.3, top_p=0.9, max_tokens=64),
                    {"choices": [{"text": "  The door groans open.  "}]})
    assert cap.req.full_url == "http://127.0.0.1:5000/v1/completions"
    assert cap.body["prompt"] == CHATML
    assert "messages" not in cap.body
    assert cap.body["model"] == "m1" and cap.body["temperature"] == 0.3 and cap.body["max_tokens"] == 64
    assert out.text == "The door groans open."


def test_chat_endpoint_sends_messages_and_parses_message_content():
    client = OpenAIClient("http://host/v1", endpoint="chat", model="gpt-x")
    out, cap = _run(client, CHATML, Sampling(),
                    {"choices": [{"message": {"role": "assistant", "content": "You step through."}}]})
    assert cap.req.full_url == "http://host/v1/chat/completions"
    assert "prompt" not in cap.body
    assert cap.body["messages"][0]["role"] == "system"
    assert cap.body["messages"][-1]["content"] == "I open the door."
    assert out.text == "You step through."


def test_api_key_sets_bearer_header():
    client = OpenAIClient("http://host", api_key="sk-secret")
    _, cap = _run(client, CHATML, Sampling(), {"choices": [{"text": "ok"}]})
    assert cap.req.get_header("Authorization") == "Bearer sk-secret"
    client2 = OpenAIClient("http://host")
    _, cap2 = _run(client2, CHATML, Sampling(), {"choices": [{"text": "ok"}]})
    assert cap2.req.get_header("Authorization") is None


def test_live_sampling_override_wins():
    client = OpenAIClient("http://host")
    client.set_overrides(temperature=0.0, top_p=1.0, max_tokens=8)
    _, cap = _run(client, CHATML, Sampling(temperature=0.85, top_p=0.95, max_tokens=512),
                  {"choices": [{"text": "ok"}]})
    assert cap.body["temperature"] == 0.0 and cap.body["max_tokens"] == 8


class _FailThenOK:
    def __init__(self, detail: str, response: dict):
        self.detail = detail
        self.response = response
        self.bodies = []

    def __call__(self, req, timeout=None):
        self.bodies.append(json.loads(req.data.decode("utf-8")))
        if len(self.bodies) == 1:
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
                                         io.BytesIO(self.detail.encode("utf-8")))
        return io.BytesIO(json.dumps(self.response).encode("utf-8"))


def test_fixed_temperature_backend_retries_at_allowed_value():
    client = OpenAIClient("http://strict.example/api", model="m", endpoint="chat")
    stub = _FailThenOK('{"error":{"message":"invalid temperature: only 1 is allowed for this model"}}',
                       {"choices": [{"message": {"content": "narrated."}}]})
    orig = urllib.request.urlopen
    urllib.request.urlopen = stub
    try:
        out = client.complete(CHATML, Sampling(temperature=0.0, top_p=1.0, max_tokens=16))
    finally:
        urllib.request.urlopen = orig
    assert out.text == "narrated."
    assert stub.bodies[0]["temperature"] == 0.0
    assert stub.bodies[1]["temperature"] == 1.0
    assert client.force_temperature == 1.0
    _, cap = _run(client, CHATML, Sampling(temperature=0.85),
                  {"choices": [{"message": {"content": "again."}}]})
    assert cap.body["temperature"] == 1.0


def test_fixed_top_p_backend_retries_at_allowed_value():
    client = OpenAIClient("http://strict.example/api", model="m", endpoint="chat")
    stub = _FailThenOK('{"error":{"message":"invalid top_p: only 0.95 is allowed for this model"}}',
                       {"choices": [{"message": {"content": "ok."}}]})
    orig = urllib.request.urlopen
    urllib.request.urlopen = stub
    try:
        out = client.complete(CHATML, Sampling(temperature=1.0, top_p=1.0, max_tokens=16))
    finally:
        urllib.request.urlopen = orig
    assert out.text == "ok."
    assert stub.bodies[0]["top_p"] == 1.0
    assert stub.bodies[1]["top_p"] == 0.95
    assert client.forced["top_p"] == 0.95
    _, cap = _run(client, CHATML, Sampling(top_p=0.8),
                  {"choices": [{"message": {"content": "again."}}]})
    assert cap.body["top_p"] == 0.95


def test_rejected_field_is_dropped_and_retried():
    client = OpenAIClient("http://strict.example/api", endpoint="chat")
    stub = _FailThenOK('{"error":{"message":"unsupported parameter: presence_penalty"}}',
                       {"choices": [{"message": {"content": "ok."}}]})
    orig = urllib.request.urlopen
    urllib.request.urlopen = stub
    try:
        client.complete(CHATML, Sampling(presence_penalty=0.5))
    finally:
        urllib.request.urlopen = orig
    assert "presence_penalty" in stub.bodies[0]
    assert "presence_penalty" not in stub.bodies[1]
    assert "presence_penalty" in client.dropped
    _, cap = _run(client, CHATML, Sampling(presence_penalty=0.5),
                  {"choices": [{"message": {"content": "again."}}]})
    assert "presence_penalty" not in cap.body


def test_known_host_profile_pins_and_drops_up_front():
    client = OpenAIClient("https://api.kimi.com/coding", model="kimi", endpoint="chat")
    _, cap = _run(client, CHATML,
                  Sampling(temperature=0.85, top_p=0.7, frequency_penalty=0.5,
                           presence_penalty=0.5, seed=42, max_tokens=16),
                  {"choices": [{"message": {"content": "ok."}}]})
    assert cap.body["temperature"] == 1.0 and cap.body["top_p"] == 0.95
    for f in ("frequency_penalty", "presence_penalty", "seed"):
        assert f not in cap.body
    assert cap.body["max_tokens"] == 1024


def test_reasoning_profile_forces_chat_endpoint():
    client = OpenAIClient("https://api.kimi.com/coding", model="kimi")
    assert client.endpoint == "chat"


def test_chat_reasoning_content_used_when_content_empty():
    client = OpenAIClient("http://host", endpoint="chat")
    out, _ = _run(client, CHATML, Sampling(),
                  {"choices": [{"message": {"content": "", "reasoning_content": "  pong  "}}]})
    assert out.text == "pong"
    out2, _ = _run(client, CHATML, Sampling(),
                   {"choices": [{"message": {"content": "answer", "reasoning_content": "musing"}}]})
    assert out2.text == "answer"


def test_local_openai_backend_sends_penalties_and_seed():
    client = OpenAIClient("http://127.0.0.1:5000", endpoint="chat")
    _, cap = _run(client, CHATML,
                  Sampling(frequency_penalty=0.3, presence_penalty=0.2, seed=7),
                  {"choices": [{"message": {"content": "ok."}}]})
    assert cap.body["frequency_penalty"] == 0.3 and cap.body["presence_penalty"] == 0.2
    assert cap.body["seed"] == 7


def test_non_temperature_400_is_not_retried():
    from engine.llm import LLMUnavailable
    client = OpenAIClient("http://host", endpoint="chat")
    stub = _FailThenOK('{"error":{"message":"model not found"}}', {"choices": []})
    orig = urllib.request.urlopen
    urllib.request.urlopen = stub
    try:
        raised = False
        try:
            client.complete(CHATML, Sampling())
        except LLMUnavailable:
            raised = True
    finally:
        urllib.request.urlopen = orig
    assert raised and len(stub.bodies) == 1 and client.force_temperature is None


def test_empty_or_malformed_choices_returns_empty_string():
    client = OpenAIClient("http://host", endpoint="chat")
    out, _ = _run(client, CHATML, Sampling(), {"choices": []})
    assert out.text == ""


def test_factory_builds_each_kind():
    assert isinstance(client_from_connection({"kind": "llama-cpp"}), LlamaServerClient)
    oc = client_from_connection({"kind": "openai", "base_url": "http://h/v1",
                                 "endpoint": "chat", "model": "m", "api_key": "k"})
    assert isinstance(oc, OpenAIClient) and oc.endpoint == "chat" and oc.api_key == "k"
    sentinel = FakeLLMClient()
    assert client_from_connection({"kind": "canned"}, fake=sentinel) is sentinel
    assert isinstance(client_from_connection(None), FakeLLMClient)


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for t in ALL:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(ALL) - failed}/{len(ALL)} passed")
    raise SystemExit(1 if failed else 0)
