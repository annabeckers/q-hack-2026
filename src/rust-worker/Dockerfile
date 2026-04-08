# syntax=docker/dockerfile:1

# ── Build (cached deps via cargo-chef pattern) ───
FROM rust:1.82-slim AS planner
WORKDIR /app
RUN cargo install cargo-chef
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM rust:1.82-slim AS builder
WORKDIR /app
RUN cargo install cargo-chef
COPY --from=planner /app/recipe.json recipe.json
# Build deps only (cached unless Cargo.toml changes)
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo chef cook --release --recipe-path recipe.json
# Build app (only source changes trigger this)
COPY . .
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release

# ── Production (minimal image) ───────────────────
FROM debian:bookworm-slim AS prod
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd -r -s /bin/false appuser
COPY --from=builder /app/target/release/hackathon-worker /usr/local/bin/
USER appuser
EXPOSE 8080
CMD ["hackathon-worker"]
