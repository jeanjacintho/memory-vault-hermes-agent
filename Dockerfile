# Memory Vault's own image: the fleet's pinned base, this agent's persona
# and skills. The agent-index usage reporter is the base's own.
#
# Pinned by digest, exactly like the fleet's own runtime/stack.json and the
# sibling agents' Dockerfiles: a mutable tag would re-resolve on every pull
# and change a large unreviewed surface under a running agent that holds live
# credentials.
FROM public.ecr.aws/e1h7x4a2/plow-cloud-agents:base-67021a7029e33e80bcb27899be6515a5a0e9b37b@sha256:0c3892e93c1a001c61fb7106396e0a4b7e0219008184fd90719caa84a3390ff0

# Boot recomposes $HOME/SOUL.md from this seed. COPY to the home is
# shadowed by the volume and then overwritten; the vault identity has
# to live here or the generic "Plow assistant" seed wins.
COPY runtime/SOUL.md /opt/hermes/plow-seed/SOUL.md

# plow-init seeds an absent home from plow-seed/config.yaml. Copying
# runtime/config.yaml only into /var/lib/hermes is not enough (agent-home
# shadows it): holographic memory, Latch, group sessions and the
# toolset-minus-web have to be stamped onto the seed.
COPY runtime/config.yaml /tmp/mv-runtime-config.yaml
COPY image/merge_mv_seed_config.py /opt/plow/merge_mv_seed_config.py
RUN /opt/hermes/.venv/bin/python3 /opt/plow/merge_mv_seed_config.py \
      /opt/hermes/plow-seed/config.yaml /tmp/mv-runtime-config.yaml \
 && grep -q 'provider: holographic' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'latch:' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'group_sessions_per_user: false' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'interim_assistant_messages: false' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'disabled_toolsets:' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'context_file_max_chars: 40000' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'anthropic/claude-sonnet-5' /opt/hermes/plow-seed/config.yaml \
 && grep -q 'default: anthropic/claude-sonnet-5' /opt/hermes/plow-seed/config.yaml

# Identity and skills. Home COPY is the first-boot volume fill; first boot
# re-asserts root ownership, which is what the trailing chmod answers.
# Skills land at /opt/hermes/skills so the base runtime reconciles them
# into whichever home this image boots — a COPY under /var/lib/hermes/skills
# is shadowed by the agent-home volume after first create.
COPY runtime/SOUL.md /var/lib/hermes/SOUL.md
COPY runtime/config.yaml /var/lib/hermes/config.yaml
COPY LICENSE /usr/share/doc/memory-vault/
COPY mv-ingest/ /opt/hermes/skills/mv-ingest/
COPY mv-recall/ /opt/hermes/skills/mv-recall/
COPY mv-act/    /opt/hermes/skills/mv-act/
COPY mv-learn/  /opt/hermes/skills/mv-learn/

RUN find /opt/hermes/skills -mindepth 1 -type d -exec chmod 0755 {} + \
 && find /opt/hermes/skills -mindepth 1 -type f ! -perm -u+x -exec chmod 0644 {} + \
 && find /opt/hermes/skills -mindepth 1 -type f -perm -u+x -exec chmod 0755 {} + \
 && chmod 0644 /var/lib/hermes/SOUL.md /var/lib/hermes/config.yaml \
      /opt/hermes/plow-seed/SOUL.md

COPY image/cont-init.d/02-copy-plow-credentials /etc/cont-init.d/02-copy-plow-credentials
RUN chmod 0755 /etc/cont-init.d/02-copy-plow-credentials

# Hermes' billing wall concatenates the HTTP body, the provider name, a
# billing URL and `/model`. Pin one user-facing line and fail the build if
# the base digest moved those functions.
COPY image/hermes/billing_user_message.py /opt/hermes/agent/billing_user_message.py
COPY image/hermes/patch_billing_user_message.py /opt/plow/patch_billing_user_message.py
RUN /opt/hermes/.venv/bin/python3 /opt/plow/patch_billing_user_message.py \
      /opt/hermes/agent/conversation_loop.py \
 && chmod 0644 /opt/hermes/agent/billing_user_message.py
