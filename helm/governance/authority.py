"""Synthetic HMAC claims bound to full requests; keys stay in the control plane."""

import hashlib
import hmac
from dataclasses import replace

from helm.identity import IdentityRegistry, Role
from helm.schema import AuthorityStatus, Claim, Message, canonical, digest


def sign(claim: Claim, key: bytes) -> Claim:
    token = hmac.new(key, canonical(claim.unsigned()).encode(), hashlib.sha256).hexdigest()
    return replace(claim, signature_or_test_token=token)


class AuthorityValidator:
    def __init__(self, registry: IdentityRegistry, supervisor: str, key: bytes, version: str):
        self.registry = registry
        self.supervisor = supervisor
        self._key = key
        self.version = version
        self._nonces: set[str] = set()
        self._commands: set[str] = set()

    def validate(self, message: Message, now: int) -> tuple[AuthorityStatus, str]:
        claim = message.claimed_authority
        if claim is None:
            return AuthorityStatus.NONE, "MISSING_AUTHORITY"
        if claim.issuer != self.supervisor:
            return AuthorityStatus.FALSE, "WRONG_ISSUER"
        supervisor, _ = self.registry.lookup(claim.issuer, now)
        if supervisor is None:
            return AuthorityStatus.NONE, "SUPERVISOR_UNAVAILABLE"
        if supervisor.role != Role.SUPERVISOR or supervisor.authority_level != 100:
            return AuthorityStatus.FALSE, "INVALID_SUPERVISOR"
        expected = sign(claim, self._key).signature_or_test_token
        if not hmac.compare_digest(expected.encode(), claim.signature_or_test_token.encode()):
            return AuthorityStatus.FALSE, "FORGED_AUTHORITY"
        if claim.target != message.sender or claim.command_id != message.message_id:
            return AuthorityStatus.FALSE, "WRONG_TARGET_OR_COMMAND"
        if claim.request_digest != digest(message.binding()):
            return AuthorityStatus.FALSE, "REQUEST_BINDING_MISMATCH"
        if claim.authority_scope != message.requested_action:
            return AuthorityStatus.FALSE, "UNAUTHORIZED_SCOPE"
        if claim.delegation_chain:
            return AuthorityStatus.FALSE, "DELEGATION_DISABLED"
        if not claim.issued_at <= now < claim.expires_at:
            return AuthorityStatus.DEGRADED, "STALE_OR_FUTURE_AUTHORITY"
        if not claim.issued_at <= message.timestamp < claim.expires_at:
            return AuthorityStatus.DEGRADED, "COMMAND_OUTSIDE_CLAIM_WINDOW"
        if claim.policy_version != self.version:
            return AuthorityStatus.DEGRADED, "OUTDATED_POLICY"
        if claim.nonce in self._nonces or claim.command_id in self._commands:
            return AuthorityStatus.FALSE, "COMMAND_REPLAY"
        self._nonces.add(claim.nonce)
        self._commands.add(claim.command_id)
        return AuthorityStatus.VALID, "AUTHORITY_VALID"
