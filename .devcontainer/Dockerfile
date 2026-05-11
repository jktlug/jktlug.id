# Development container for tlug.jp Hakyll website
# Based on Debian Bookworm for compatibility with Stack's system deps
FROM debian:bookworm-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Install system dependencies required by Stack, Haskell builds, and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    gnupg \
    pkg-config \
    sudo \
    zlib1g-dev \
    libgmp-dev \
    libffi-dev \
    libncurses-dev \
    make \
    python3 \
    python3-pip \
    build-essential \
    dpkg-dev \
    && rm -rf /var/lib/apt/lists/*



# Create a non-root user for development
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && mkdir -p /home/$USERNAME/.local/bin \
    && chown -R $USER_UID:$USER_GID /home/$USERNAME \
    && chsh -s /bin/bash $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Install Haskell Stack (pinned version)
ENV STACK_VERSION=3.1.1
RUN curl -sSL https://github.com/commercialhaskell/stack/releases/download/v${STACK_VERSION}/stack-${STACK_VERSION}-linux-x86_64.tar.gz \
    | tar xz --wildcards --strip-components=1 -C /usr/local/bin '*/stack'



# Ensure tools are in PATH
ENV PATH="/home/${USERNAME}/.local/bin:/usr/local/bin:${PATH}"

# Set default shell for RUN commands going forward
SHELL ["/bin/bash", "-c"]

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER $USERNAME

# Install nvm, Node.js 22, and Pi Coding Agent as non-root user
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash \
    && export NVM_DIR="$HOME/.nvm" \
    && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" \
    && nvm install 22 \
    && nvm alias default 22 \
    && npm install -g @earendil-works/pi-coding-agent \
    && ln -sf "$(which node)" "$HOME/.local/bin/node" \
    && ln -sf "$(which npm)" "$HOME/.local/bin/npm" \
    && ln -sf "$(which pi)" "$HOME/.local/bin/pi"

# Configure bash profile
RUN echo '# Source .bashrc if it exists' > /home/${USERNAME}/.bash_profile \
    && echo 'if [ -f "$HOME/.bashrc" ]; then' >> /home/${USERNAME}/.bash_profile \
    && echo '    . "$HOME/.bashrc"' >> /home/${USERNAME}/.bash_profile \
    && echo 'fi' >> /home/${USERNAME}/.bash_profile

# Verify installations
RUN stack --version
RUN pi --version

# Default command - login shell so profiles are loaded
CMD ["/bin/bash", "-l"]