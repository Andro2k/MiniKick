# backend\workers\worker_utils.py

import logging

def stop_provider_chat_worker(worker, provider, logger: logging.Logger, worker_tag: str, target: str) -> None:
    logger.info("[%s] Stopping chat worker for '%s'...", worker_tag, target)
    worker._is_stopped = True
    worker.requestInterruption()
    if provider and hasattr(provider, "stop_chat"):
        provider.stop_chat()
    worker.quit()
