from pathlib import Path

from loguru import logger


def configure_logging() -> None:
    logs_dir = Path(__file__).resolve().parents[1] / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(lambda msg: print(msg, end=''), level='INFO')
    logger.add(
        logs_dir / 'app.log',
        rotation='10 MB',
        retention='10 days',
        level='INFO',
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
