from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Sampling:
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 512
    stop: tuple[str, ...] = ()
    top_k: int | None = None
    min_p: float | None = None
    repeat_penalty: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    seed: int | None = None

    OPTIONAL_FIELDS = ("top_k", "min_p", "repeat_penalty", "frequency_penalty",
                       "presence_penalty", "seed")

    def with_stops(self, extra: tuple[str, ...]) -> "Sampling":
        return replace(self, stop=tuple(dict.fromkeys(self.stop + tuple(extra))))


DETERMINISTIC = Sampling(temperature=0.0, top_p=1.0, max_tokens=160)
CREATIVE = Sampling(temperature=0.85, top_p=0.95, max_tokens=512)


@dataclass(frozen=True)
class Generation:
    text: str


class LLMClient(ABC):
    @abstractmethod
    def complete(
        self, prompt: str, sampling: Sampling, grammar: str | None = None
    ) -> Generation:
        pass


class LLMUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatTemplate:
    system_open: str = "<|im_start|>system\n"
    system_close: str = "<|im_end|>\n"
    user_open: str = "<|im_start|>user\n"
    user_close: str = "<|im_end|>\n"
    assistant_open: str = "<|im_start|>assistant\n"
    assistant_close: str = "<|im_end|>\n"
    stop: tuple[str, ...] = ("<|im_end|>",)


@dataclass
class PromptBuilder:
    template: ChatTemplate = field(default_factory=ChatTemplate)

    def build(self, *, system: str, history=None, user: str) -> str:
        t = self.template
        parts = [t.system_open, system, t.system_close]
        for turn in (history or []):
            if turn.role == "player":
                parts += [t.user_open, turn.text, t.user_close]
            else:
                parts += [t.assistant_open, turn.text, t.assistant_close]
        parts += [t.user_open, user, t.user_close, t.assistant_open]
        return "".join(parts)

    @property
    def stops(self) -> tuple[str, ...]:
        return self.template.stop


@dataclass
class _Call:
    prompt: str
    sampling: Sampling
    grammar: str | None


class FakeLLMClient(LLMClient):

    def __init__(
        self,
        default_text: str = "The room is quiet. Nothing answers.",
        default_json: str = '{"intent": "dialogue", "detail": ""}',
    ):
        self.default_text = default_text
        self.default_json = default_json
        self._queue: list[str] = []
        self.calls: list[_Call] = []

    def queue(self, *responses: str) -> "FakeLLMClient":
        self._queue.extend(responses)
        return self

    def complete(self, prompt, sampling, grammar=None) -> Generation:
        self.calls.append(_Call(prompt, sampling, grammar))
        if self._queue:
            return Generation(self._queue.pop(0))
        return Generation(self.default_json if grammar else self.default_text)


class _LiveSampling:

    _OVERRIDE_KEYS = ("temperature", "top_p", "max_tokens") + Sampling.OPTIONAL_FIELDS

    def _init_overrides(self) -> None:
        self.overrides: dict = {}

    def set_overrides(self, **kw) -> None:
        self.overrides = {k: v for k, v in kw.items()
                          if k in self._OVERRIDE_KEYS and v is not None}

    def _params(self, sampling: Sampling) -> dict:
        p = {"temperature": sampling.temperature, "top_p": sampling.top_p,
             "max_tokens": sampling.max_tokens}
        for k in Sampling.OPTIONAL_FIELDS:
            v = getattr(sampling, k, None)
            if v is not None:
                p[k] = v
        p.update(self.overrides)
        return p


def _post_json(url: str, body: dict, headers: dict, timeout: float, label: str) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")
        except Exception:
            pass
        raise LLMUnavailable(
            f"Backend at {label} returned HTTP {e.code}. ({detail[:200].strip()})"
        ) from e
    except urllib.error.URLError as e:
        raise LLMUnavailable(
            f"Could not reach backend at {label}. Is it running? ({e})"
        ) from e


_CHATML_TURN = re.compile(r"<\|im_start\|>(\w+)\n(.*?)<\|im_end\|>", re.DOTALL)


def chatml_to_messages(prompt: str) -> list:
    msgs = [{"role": role, "content": content.strip()}
            for role, content in _CHATML_TURN.findall(prompt)]
    return msgs or [{"role": "user", "content": prompt}]


_CONTROL_TOKEN_RE = re.compile(
    r"[<|>]{1,3}\s*im_(?:end|start)\s*[<|>]{0,3}"
    r"|im_(?:end|start)\s*[<|>]{1,3}",
    re.IGNORECASE,
)


def _sanitize(text: str) -> str:
    return _CONTROL_TOKEN_RE.sub("", text or "").strip()


_SAMPLER_FIELDS = ("temperature", "top_p", "top_k", "min_p", "max_tokens",
                   "repeat_penalty", "frequency_penalty", "presence_penalty", "seed")
_FORCED_PARAM_RE = re.compile(
    r"invalid\s+(\w+)\s*:?\s*only\s+([0-9]*\.?[0-9]+)\s+is\s+allowed", re.IGNORECASE)
_FIXED_VALUE_RE = re.compile(r"only\s+([0-9]*\.?[0-9]+)\s+is\s+allowed", re.IGNORECASE)
_REJECTED_FIELD_RE = re.compile(
    r"(?:unsupported|unknown|unexpected|unrecognized)\s+(?:sampling\s+)?"
    r"(?:parameter|field|argument|property|key)s?\s*[:=]?\s*['\"]?(\w+)", re.IGNORECASE)


def _forced_param(err_msg: str) -> tuple[str, float] | None:
    m = err_msg or ""
    if "http 400" not in m.lower():
        return None
    hit = _FORCED_PARAM_RE.search(m)
    if hit and hit.group(1).lower() in _SAMPLER_FIELDS:
        return hit.group(1).lower(), float(hit.group(2))
    if "temperature" in m.lower():
        bare = _FIXED_VALUE_RE.search(m)
        return "temperature", float(bare.group(1)) if bare else 1.0
    return None


def _rejected_field(err_msg: str) -> str | None:
    m = err_msg or ""
    if "http 400" not in m.lower():
        return None
    hit = _REJECTED_FIELD_RE.search(m)
    if hit and hit.group(1).lower() in _SAMPLER_FIELDS:
        return hit.group(1).lower()
    return None


def _openai_base(url: str) -> str:
    u = (url or "").rstrip("/")
    for suffix in ("/v1/chat/completions", "/v1/completions", "/chat/completions",
                   "/completions", "/completion", "/v1"):
        if u.endswith(suffix):
            u = u[: -len(suffix)]
            break
    return u.rstrip("/")


WEB_API_PROFILES: dict[str, dict] = {
    "kimi.com":  {"pin": {"temperature": 1.0, "top_p": 0.95},
                  "drop": ("frequency_penalty", "presence_penalty", "seed"),
                  "min_tokens": 1024, "endpoint": "chat"},
    "moonshot":  {"pin": {"temperature": 1.0, "top_p": 0.95},
                  "drop": ("frequency_penalty", "presence_penalty", "seed"),
                  "min_tokens": 1024, "endpoint": "chat"},
    "x.ai":      {"pin": {},
                  "drop": ("frequency_penalty", "presence_penalty", "seed")},
}


def web_api_profile(base_url: str) -> dict | None:
    host = _openai_base(base_url).split("://")[-1].split("/")[0].lower()
    for needle, profile in WEB_API_PROFILES.items():
        if needle in host:
            return profile
    return None


class LlamaServerClient(_LiveSampling, LLMClient):

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.grammar_ok = True
        self._init_overrides()

    def complete(self, prompt, sampling, grammar=None) -> Generation:
        use_grammar = grammar if self.grammar_ok else None
        p = self._params(sampling)
        body = {
            "prompt": prompt,
            "temperature": p["temperature"],
            "top_p": p["top_p"],
            "n_predict": p["max_tokens"],
            "stop": list(sampling.stop),
            "cache_prompt": True,
        }
        for key in ("top_k", "min_p", "repeat_penalty", "frequency_penalty",
                    "presence_penalty", "seed"):
            if key in p:
                body[key] = p[key]
        if use_grammar:
            body["grammar"] = use_grammar
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/completion",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            if use_grammar is not None and ("grammar" in detail.lower() or e.code == 400):
                if self.grammar_ok:
                    self.grammar_ok = False
                    sys.stderr.write(
                        "[llm] llama-server rejected the GBNF grammar; continuing without "
                        "grammar-constrained decoding (classification still works, just unconstrained).\n"
                    )
                return self.complete(prompt, sampling, grammar=None)
            raise LLMUnavailable(
                f"llama-server at {self.base_url} returned HTTP {e.code}. ({detail[:200].strip()})"
            ) from e
        except urllib.error.URLError as e:
            raise LLMUnavailable(
                f"Could not reach llama-server at {self.base_url}. Is it running? ({e})"
            ) from e
        return Generation(_sanitize(payload.get("content", "")))


class OpenAIClient(_LiveSampling, LLMClient):

    def __init__(self, base_url: str, *, api_key: str | None = None, model: str = "local-model",
                 endpoint: str = "completions", timeout: float = 120.0):
        self.base_url = _openai_base(base_url)
        self.api_key = api_key or None
        self.model = model or "local-model"
        self.endpoint = "chat" if str(endpoint).startswith("chat") else "completions"
        self.timeout = timeout
        self.forced: dict = {}
        self.dropped: set = set()
        self.min_tokens: int = 0
        prof = web_api_profile(self.base_url)
        if prof:
            self.forced.update(prof.get("pin", {}))
            self.dropped.update(prof.get("drop", ()))
            self.min_tokens = prof.get("min_tokens", 0)
            if prof.get("endpoint") == "chat":
                self.endpoint = "chat"
        self._init_overrides()

    @property
    def force_temperature(self) -> float | None:
        return self.forced.get("temperature")

    @force_temperature.setter
    def force_temperature(self, value: float | None) -> None:
        if value is None:
            self.forced.pop("temperature", None)
        else:
            self.forced["temperature"] = value

    def _build_body(self, prompt: str, sampling: Sampling) -> dict:
        p = self._params(sampling)
        body = {"model": self.model, "temperature": p["temperature"], "top_p": p["top_p"],
                "max_tokens": max(p["max_tokens"], self.min_tokens)}
        for key in ("frequency_penalty", "presence_penalty"):
            if key in p:
                body[key] = p[key]
        if p.get("seed", -1) != -1:
            body["seed"] = p["seed"]
        for key in self.dropped:
            body.pop(key, None)
        body.update(self.forced)
        if sampling.stop:
            body["stop"] = list(sampling.stop)
        if self.endpoint == "chat":
            body["messages"] = chatml_to_messages(prompt)
        else:
            body["prompt"] = prompt
        return body

    def _adapt_and_should_retry(self, err_msg: str) -> bool:
        forced = _forced_param(err_msg)
        if forced is not None:
            field, val = forced
            if self.forced.get(field) != val:
                self.forced[field] = val
                sys.stderr.write(
                    f"[llm] backend pinned '{field}' to {val} for this connection "
                    f"(this model allows only one value); retrying.\n")
                return True
        dropped = _rejected_field(err_msg)
        if dropped is not None and dropped not in self.dropped:
            self.dropped.add(dropped)
            sys.stderr.write(
                f"[llm] backend rejected the '{dropped}' parameter; dropping it for this "
                f"connection and retrying.\n")
            return True
        return False

    def complete(self, prompt, sampling, grammar=None) -> Generation:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = (f"{self.base_url}/v1/chat/completions" if self.endpoint == "chat"
               else f"{self.base_url}/v1/completions")
        payload = None
        for _ in range(len(_SAMPLER_FIELDS) + 2):
            try:
                payload = _post_json(url, self._build_body(prompt, sampling), headers,
                                     self.timeout, self.base_url)
                break
            except LLMUnavailable as exc:
                if not self._adapt_and_should_retry(str(exc)):
                    raise
        try:
            choice = payload["choices"][0]
            if self.endpoint == "chat":
                msg = choice.get("message") or {}
                text = msg.get("content") or msg.get("reasoning_content") or ""
            else:
                text = choice.get("text", "")
        except (KeyError, IndexError, TypeError):
            text = ""
        return Generation(_sanitize(text or ""))


def client_from_connection(conn: dict | None, *, fake: LLMClient | None = None) -> LLMClient:
    kind = (conn or {}).get("kind", "canned")
    timeout = _conn_timeout(conn)
    if kind == "llama-cpp":
        return LlamaServerClient(base_url=(conn.get("base_url") or "http://127.0.0.1:8080"),
                                 timeout=timeout)
    if kind == "openai":
        return OpenAIClient(base_url=conn.get("base_url", ""),
                            api_key=conn.get("api_key") or None,
                            model=conn.get("model") or "local-model",
                            endpoint=conn.get("endpoint", "completions"),
                            timeout=timeout)
    return fake if fake is not None else FakeLLMClient()


def _conn_timeout(conn: dict | None, default: float = 120.0) -> float:
    try:
        secs = float((conn or {}).get("timeout"))
    except (TypeError, ValueError):
        return default
    return secs if secs > 0 else default
