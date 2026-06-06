FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# ---------------------------------------------------------------------------
# Minimal image: only tools the agent actually invokes.
# Full list verified from tools/kali_tools.py tool definitions.
# Removed: john, wpscan, enum4linux, masscan, theharvester,
#          metasploit-framework (saves ~1.5 GB image, ~1 GB RAM)
# Web pentesting stack: amass, hashcat, dalfox, arjun, jwt_tool,
#                       corsy, crlfuzz, kiterunner, smuggler, nuclei
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    curl \
    wget \
    git \
    bash \
    # --- Core pentesting tools (used by kali_tools.py) ---
    nmap \
    gobuster \
    dirb \
    sqlmap \
    hydra \
    whatweb \
    ffuf \
    wfuzz \
    # --- Utilities (DNS, file inspection, networking) ---
    dnsutils \
    file \
    xxd \
    jq \
    netcat-openbsd \
    socat \
    binutils \
    # --- Recon & cracking ---
    amass \
    hashcat \
    # --- Go (required for dalfox, crlfuzz, kiterunner, nuclei) ---
    golang-go \
    && rm -rf /var/lib/apt/lists/*

ENV GOPATH=/root/go
ENV PATH=$PATH:/root/go/bin

# Optional Kali packages that may vary by mirror/release.
RUN apt-get update && \
    for pkg in subfinder mcp-kali-server; do \
      apt-get install -y --no-install-recommends "$pkg" || echo "[WARN] optional package unavailable: $pkg"; \
    done && \
    rm -rf /var/lib/apt/lists/*

# --- exploitdb (searchsploit): try apt, fallback to git clone ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends exploitdb && \
    rm -rf /var/lib/apt/lists/* || \
    (echo "[INFO] exploitdb not in apt, installing from git..." && \
     git clone --depth 1 https://gitlab.com/exploit-database/exploitdb.git /opt/exploitdb && \
     ln -sf /opt/exploitdb/searchsploit /usr/local/bin/searchsploit && \
     sed -i 's|/opt/exploitdb-papers|/opt/exploitdb/exploitdb-papers|g; s|/opt/exploitdb\b|/opt/exploitdb|g' /opt/exploitdb/.searchsploit_rc)

# --- Nuclei: guaranteed install (try Go module, fallback to apt) ---
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest || \
    (apt-get update && apt-get install -y --no-install-recommends nuclei && rm -rf /var/lib/apt/lists/*) || \
    echo "[WARN] nuclei unavailable"

# --- Go-based web tools: dalfox (XSS), crlfuzz (CRLF) ---
RUN go install github.com/hahwul/dalfox/v2@latest && \
    go install github.com/dwisiswant0/crlfuzz/cmd/crlfuzz@latest

# --- kiterunner (API path fuzzing) — build from source (go module path changed in v1.0.2) ---
RUN git clone --depth 1 https://github.com/assetnote/kiterunner.git /opt/kiterunner && \
    cd /opt/kiterunner && \
    go build -o /root/go/bin/kr ./cmd/kiterunner/ || echo "[WARN] kiterunner build failed"

# --- Python web tools: arjun (hidden parameter discovery) ---
RUN pip3 install --no-cache-dir --break-system-packages arjun

# --- Script-based tools: jwt_tool, corsy, smuggler ---
RUN git clone --depth 1 https://github.com/ticarpi/jwt_tool.git /opt/jwt_tool && \
    pip3 install --no-cache-dir --break-system-packages \
        -r /opt/jwt_tool/requirements.txt && \
    chmod +x /opt/jwt_tool/jwt_tool.py && \
    ln -sf /opt/jwt_tool/jwt_tool.py /usr/local/bin/jwt_tool

RUN git clone --depth 1 https://github.com/s0md3v/Corsy.git /opt/corsy && \
    pip3 install --no-cache-dir --break-system-packages requests && \
    chmod +x /opt/corsy/corsy.py && \
    ln -sf /opt/corsy/corsy.py /usr/local/bin/corsy

RUN git clone --depth 1 https://github.com/defparam/smuggler.git /opt/smuggler && \
    chmod +x /opt/smuggler/smuggler.py && \
    ln -sf /opt/smuggler/smuggler.py /usr/local/bin/smuggler

# Tools not consistently available via apt.
RUN curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
    | sh -s -- -b /usr/local/bin

RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin

# Prowler for cloud audits in an isolated venv.
RUN python3 -m venv /opt/prowler-venv && \
    /opt/prowler-venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/prowler-venv/bin/pip install --no-cache-dir prowler && \
    ln -sf /opt/prowler-venv/bin/prowler /usr/local/bin/prowler

# Fallback: if kali package binary is unavailable, keep official source as runtime fallback.
RUN if ! command -v kali-server-mcp >/dev/null 2>&1; then \
      git clone --depth 1 https://gitlab.com/kalilinux/packages/mcp-kali-server.git /opt/mcp-kali-server || true; \
      if [ -f /opt/mcp-kali-server/requirements.txt ]; then \
        pip3 install --no-cache-dir --break-system-packages -r /opt/mcp-kali-server/requirements.txt; \
      fi; \
    fi

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 5000

CMD ["/entrypoint.sh"]
