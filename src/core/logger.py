import logging

logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s {%(name)s} [%(levelname)s] %(message)s",
    handlers=[console_handler],
)

logger = logging.getLogger(__name__)
