ROUND17 has been revised. The old taskbook guess "Security Center → Command Security → Program Blacklist" was unsupported and is withdrawn.

Read and follow:
https://github.com/hhdy/matepad11-dby-w09-agent-reports/blob/main/firmware-analysis/round17/AGENT_TASK.md

Do NOT invoke wsl.exe again yet. First passively identify the exact local Agent product/version and the command-execution policy layer that emitted the prior sandbox block message. Do not assume Defender, Windows Security Center, Codex, VS Code, or any specific endpoint product. Use only existing app metadata, logs already available, visible UI/help and official docs for the identified product. If identity cannot be established without running blocked commands, stop and ask the user for the local Agent name/version and screenshot of the block message.

No retries, alternate shells, script wrappers, copies, renames, UAC bypass, security changes or installation attempts. Do not launch the Agent elevated preemptively. Elevation is only considered if a specific later official step requires it and the user approves.

Preserve the existing C: Ubuntu unchanged. Fixed future plan is a separate Ubuntu-24.04 at D:\WSL\Ubuntu-24.04, once normal WSL execution is authorized. Continue the kernel-only official manifest + ACK pin procedure only after the policy gate is legitimately cleared. Do not patch or compile in ROUND17.
