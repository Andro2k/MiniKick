# Outbound Webhook Delivery Service

* **Author:** Andro2k
* **Date:** 2026-11-10

## Overview

MiniKick is a desktop streaming companion that processes live events from Kick and Twitch. This feature adds an outbound-only HTTP webhook dispatcher that forwards stream events (subscriptions, gift subscriptions, follows, raids, tips/alerts, bot commands, and music track changes) to external systems such as Discord channels, Home Assistant, Node-RED, or custom web services.

The dispatcher operates independently of the PySide6 UI thread on a pure-Python background worker, protecting the responsiveness of chat, audio alerts, and OBS overlay WebSockets. It protects secrets at rest using MiniKick's existing encryption service, sanitizes outbound URLs in application logs to prevent token leakage, and discards high-volume chat events during network backpressure to preserve critical channel alerts.

## Analysis

The review evaluated the concept across architectural boundaries, operational reliability, security, and performance:

1. **Isolation from Qt Runtime:**
   Desktop streaming applications fail when UI loops block on network I/O. The webhook worker runs as a standard Python daemon thread (`threading.Thread`) using an in-memory `queue.Queue`. It interacts with internal MiniKick event producers via lightweight callback subscriptions, keeping the business logic testable without a GUI application context.

2. **Dual-Lane Queue and Drop-on-Saturation:**
   High-frequency chat events create burst volume that can overwhelm outbound HTTP queues or trigger third-party rate limits. The queue is divided into two operational priority lanes:
   * **Critical Lane:** Monetary and milestone events (subscriptions, gifts, follows, raids, donations). These retried with exponential backoff and full jitter across up to 4 attempts.
   * **Ephemeral Lane:** High-volume chat and music updates. When queue capacity reaches an 80% saturation threshold, incoming chat events are dropped immediately with an incremented counter to avoid memory leaks or latency cascading into alerts.

3. **Rate Limits and Jittered Backoff:**
   Remote endpoints (specifically Discord webhook APIs) enforce strict rate limits and return HTTP 429 with `Retry-After`. The dispatcher handles backoff per endpoint:
   $$\text{delay} = \text{random.uniform}(0, \min(30.0, 1.0 \times 2^{\text{attempt}}))$$
   A 429 response on one destination pauses that specific endpoint without stalling deliveries to other configured webhooks.

4. **Security and Secret Scrubbing:**
   Discord webhook URLs embed authentication tokens directly within the URL path (`/api/webhooks/{id}/{token}`). To eliminate credential exposure:
   * Destination URLs and HMAC signing secrets are encrypted at rest using `SecretCipher` and stored in SQLite.
   * A regex scrubbing filter masks webhook tokens and HMAC secrets in `minikick.log` and UI error displays.
   * Custom endpoints receive `X-MiniKick-Event-Id` (UUID for deduplication), `X-MiniKick-Timestamp` (millisecond timestamp), and `X-MiniKick-Signature-256` (`HMAC-SHA256(timestamp + "." + body, secret)`).

5. **Shutdown Lifecycles:**
   When MiniKick exits, the background thread must not hang the application process. The worker implements a shutdown signal with a hard timeout of 1.5 seconds to drain active requests before aborting.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  * Outbound HTTP POST dispatching to one or more user-configured endpoints.
  * Standardized generic JSON formatter envelope `{ schema_version, id, type, platform, timestamp, data }`.
  * Dedicated Discord embed formatter mapping events to styled Discord embeds with color codes.
  * Event filtering per destination by event type and streaming platform (Kick / Twitch).
  * In-memory queue with worker thread, exponential backoff, and full jitter (3-5 retries).
  * Drop-on-saturation policy for optional chat events.
  * Encrypted storage of URLs and signing secrets using `SecretCipher`.
  * Log scrubbing for webhook tokens.
  * Settings view with endpoint management and a "Send Test Ping" validation action.

* **Out-of-Scope Non-Goals:**
  * Inbound webhook receiver or local HTTP listener (avoids NAT, port-forwarding, and firewall complications).
  * Persistent disk queue or dead-letter storage in version 1 (postponed until delivery loss is demonstrated).
  * User-customizable payload templates or script engines (YAGNI; covered by Generic and Discord formatters).
  * Complex content-based filtering rules (e.g., regex matching on chat message text).

## Alternatives Weighed

* **Inbound HTTP Server for Two-Way Webhooks:**
  * *Rejected by author:* Opening an inbound port on a desktop application introduces operating system firewall warnings, NAT traversal issues, and security attack surface. MiniKick already ingests stream events via Pusher and Twitch IRC.
* **Persistent Disk Queue in Version 1:**
  * *Rejected by author:* Adds SQLite write churn and schema overhead for desktop event relay. Deferred behind an `IWebhookQueue` abstraction for v2 if user testing reveals lost events across application restarts.
* **Single Shared FIFO Queue for Alerts and Chat:**
  * *Rejected by review:* A single queue allows chat floods during high-activity raids to backlog critical donation and subscription alerts. Resolved using a dual-lane drop policy.
* **QThread with Qt Network Objects for Backend Workers:**
  * *Rejected by review:* Coupling backend services to Qt modules complicates unit testing and violates clean separation of layers. Resolved using standard Python `threading.Thread` and `urllib`/`requests`.
* **Plaintext URLs and Secrets in TOML Config:**
  * *Rejected by review:* Discord webhook URLs contain secret tokens that grant write access to Discord channels. Storing them in plaintext violates MiniKick credential security standards. Resolved using `SecretCipher`.

## Key Decisions & Staging for Next Steps

* **Decision 1: Strategy Pattern for Payloads (`IPayloadFormatter`):**
  The dispatcher relies on `IPayloadFormatter` implementations (`GenericJsonFormatter` and `DiscordEmbedFormatter`), allowing new destination schemas to be added without modifying the dispatch engine.
* **Decision 2: Non-blocking Worker Loop (`WebhookDeliveryWorker`):**
  Uses pure-Python `threading.Thread` with bounded `queue.Queue`. Adheres to MiniKick's `worker_shutdown` pattern with an explicit 1.5-second termination deadline.
* **Decision 3: Settings UI & Presets:**
  The frontend settings page provides a "Discord Preset" (preselecting the Discord embed formatter) and a "Custom Endpoint Preset" (with automated HMAC key generation and a "Send Test Ping" button).
