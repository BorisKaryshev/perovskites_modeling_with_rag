from src.common.class_with_creator import ClassWithCreator
from src.common.workers_pool import WorkersPool

from abc import ABC, abstractmethod


import logging

logger = logging.getLogger(__name__)


class AgentBase(ABC, ClassWithCreator, WorkersPool):
    def __init__(self):
        super().__init__()

    @abstractmethod
    async def run(self, prompt):
        pass
