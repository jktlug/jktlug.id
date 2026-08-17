# Multi-stage Dockerfile for JKTLUG.jp
# Builds the static site inside Docker, then serves with Nginx.
# Uses BuildKit cache mounts to persist Stack/GHC between builds.

# ---------------------------------------------------------------------------
# Stage 1: Build
# ---------------------------------------------------------------------------
FROM debian:trixie AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Install system dependencies for Stack / GHC builds
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

# Install Stack
ENV STACK_VERSION=3.1.1
RUN curl -sSL https://github.com/commercialhaskell/stack/releases/download/v${STACK_VERSION}/stack-${STACK_VERSION}-linux-x86_64.tar.gz \
    | tar xz --wildcards --strip-components=1 -C /usr/local/bin '*/stack'

WORKDIR /build

# Copy dependency files first for better layer caching
COPY stack.yaml stack.yaml.lock jktlug-website.cabal LICENSE.md README.md ./

# Install GHC and build dependencies, cached via BuildKit mount
# The cache mount persists /root/.stack so GHC + compiled deps survive between builds
RUN --mount=type=cache,target=/root/.stack \
    stack setup --no-terminal && \
    stack build --dependencies-only --no-terminal

# Copy source code
COPY app/ ./app/
COPY src/ ./src/
COPY template/ ./template/
COPY docroot/ ./docroot/
COPY wiki/ ./wiki/

# Build project and site, reusing the cached /root/.stack
RUN --mount=type=cache,target=/root/.stack \
    stack build --no-terminal && \
    stack exec site-compiler rebuild

# ---------------------------------------------------------------------------
# Stage 2: Serve
# ---------------------------------------------------------------------------
FROM debian:trixie

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

RUN rm -rf /var/www/html/*

COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Copy compiled static site from builder
COPY --from=builder /build/_site /var/www/html

RUN chown -R www-data:www-data /var/www/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
