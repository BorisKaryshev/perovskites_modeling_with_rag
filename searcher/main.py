from src.entry_points import EntryPoint

import asyncio
import logging

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    entry_point = EntryPoint.create()

    try:
        asyncio.run(entry_point.run())
    except Exception as ex:
        logger.error(ex)
        raise
