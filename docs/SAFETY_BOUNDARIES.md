# Safety boundaries

All H.E.L.M. experiments must use synthetic data, synthetic credentials, local
fixtures, simulated tools, deterministic containment, and a complete audit trail.

The project prohibits:

- Production systems, operational networks, and FAA systems.
- Unrestricted shell or network access from agents.
- Real credentials, sensitive data, or autonomous external action.
- Unreviewed tool invocation.
- Self-modifying runtime policy, self-granted permissions, role promotion, and spawning.

The runtime contains no shell, HTTP client, model client, dynamic plugin loader, or
external execution adapter. An `ALLOW` result records a simulated action only.
`TOOL_REQUEST` always requires review unless a stricter deny applies; Phase 0 offers
no approval bypass or tool executor. A future reviewed tool integration requires
a new design and separate authorization.

Containment allows only `LOCAL_REASONING` for a valid known identity when policy
allows it. Global actions, external actions, memory access, messages, spawning,
role changes, escalation, delegation, and policy mutation are blocked. Audit and
human review remain required even for allowed local reasoning.

Containment cannot be released inside a run. A human must examine the report,
restore trusted configuration, and explicitly start a new experiment. This also
resets replay tracking; credentials and claims must never be reused across runs
in a future persistent implementation. Phase 0 is intentionally isolated per run.

These are application rules in a trusted Python process, not hostile-code isolation.
Agents currently exist only as fixture declarations. Never execute untrusted Python
inside this process. Public fixture signing material demonstrates deterministic
legitimacy checks but provides no real-world authentication.

Repository setup, package installation, Git, and CI are developer operations outside
the simulated agent plane. They do not grant these capabilities to experiment agents.
