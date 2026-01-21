import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("backend")

def get_logger(name: str):
    return logging.getLogger(f"backend.{name}")