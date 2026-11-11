import ipaddress
import re
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class GuardrailFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    detector: str


class Guardrails:
    """Deterministic detectors for prompt attacks and sensitive values."""

    _phrase_patterns: ClassVar[dict[str, re.Pattern[str]]] = {
        "direct_injection": re.compile(
            r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|system|your)\s+instructions\b"
            r"|\bforget\s+(?:the\s+)?system prompt\b"
            r"|\bignore\s+(?:all\s+)?(?:your|the)\s+instructions\b"
            r"|\b(?:reveal|print|expose|disclose)\s+(?:your\s+)?(?:hidden\s+)?(?:system prompt|developer message|chain of thought|internal policies)\b"
            r"|\boverride\s+(?:your\s+)?(?:safety|security)\s+(?:rules|instructions)\b",
            re.IGNORECASE,
        ),
        "jailbreak": re.compile(
            r"\b(?:DAN\s+mode|do anything now|developer mode|unrestricted mode|rogue assistant)\b"
            r"|\b(?:without restrictions|no safety rules|bypass all safety filters)\b",
            re.IGNORECASE,
        ),
        "indirect_injection": re.compile(
            r"\b(?:embedded instruction|assistant:\s*disregard|document says:.*(?:ignore|override|reveal))\b",
            re.IGNORECASE,
        ),
        "tool_abuse": re.compile(
            r"\b(?:bypass approval|execute an arbitrary webhook|dump the response|print credentials)\b"
            r"|\b(?:run|execute)\s+(?:arbitrary\s+)?(?:shell|system)\s+commands\b",
            re.IGNORECASE,
        ),
        "resource_exhaustion": re.compile(
            r"\b(?:infinite loop|forever without stopping|recursively call tools forever|without a limit)\b"
            r"|\brepeat\b.{0,50}\bforever\b"
            r"|\b(?:generate|produce)\s+\d{5,}\s+(?:tokens|words|results)\b",
            re.IGNORECASE,
        ),
    }
    _email_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE
    )
    _ssn_pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    _card_pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
    _api_key_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~-]{16,})\b"
    )
    _host_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:localhost(?:\.localdomain)?|metadata\.google\.internal|169\.254\.169\.254)\b",
        re.IGNORECASE,
    )
    _ipv4_pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    @classmethod
    def scan(cls, text: str) -> list[GuardrailFinding]:
        findings: list[GuardrailFinding] = []
        for detector, pattern in cls._phrase_patterns.items():
            if pattern.search(text):
                findings.append(GuardrailFinding(detector=detector))

        if cls._host_pattern.search(text):
            findings.append(GuardrailFinding(detector="ssrf"))
        for address in cls._ipv4_pattern.findall(text):
            try:
                ip = ipaddress.ip_address(address)
            except ValueError:
                continue
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                findings.append(GuardrailFinding(detector="ssrf"))
                break

        if cls._ssn_pattern.search(text) or cls._card_pattern.search(text) or cls._email_pattern.search(text):
            findings.append(GuardrailFinding(detector="pii"))
        if cls._api_key_pattern.search(text):
            findings.append(GuardrailFinding(detector="api_key"))
        return findings

    @classmethod
    def redact_sensitive_text(cls, text: str) -> str:
        redacted = cls._ssn_pattern.sub("[REDACTED]", text)
        redacted = cls._card_pattern.sub("[REDACTED]", redacted)
        redacted = cls._email_pattern.sub("[REDACTED]", redacted)
        return cls._api_key_pattern.sub("[REDACTED]", redacted)
