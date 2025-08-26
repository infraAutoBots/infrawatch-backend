import os
import logging
import asyncio
from dotenv import load_dotenv
from pysnmp.hlapi.v3arch.asyncio import SnmpEngine



load_dotenv()


# Configuração de logging otimizada
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# Configuração de logging otimizada
logger = logging.getLogger(__name__)


# Pool melhorado de engines SNMP com auto-renovação
class SNMPEnginePool:
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.engines = asyncio.Queue(maxsize=max_size)
        self.engines_created = 0
        self.lock = asyncio.Lock()
        # Rastreamento de engines problemáticas
        self.faulty_engines = set()

    async def get_engine(self, force_new: bool = False):
        """Obtém uma engine do pool ou cria uma nova"""
        async with self.lock:
            if force_new:
                return self._create_new_engine()
                
            try:
                engine = self.engines.get_nowait()
                # Verifica se a engine não está marcada como defeituosa
                if id(engine) in self.faulty_engines:
                    await self._dispose_engine(engine)
                    return await self._get_or_create_engine()
                return engine
            except asyncio.QueueEmpty:
                return await self._get_or_create_engine()

    async def _get_or_create_engine(self):
        """Obtém ou cria uma engine"""
        if self.engines_created < self.max_size:
            return self._create_new_engine()
        else:
            # Espera por uma engine disponível
            engine = await self.engines.get()
            if id(engine) in self.faulty_engines:
                await self._dispose_engine(engine)
                return self._create_new_engine()
            return engine
    
    def _create_new_engine(self):
        """Cria uma nova engine"""
        engine = SnmpEngine()
        self.engines_created += 1
        logger.debug(f"Nova SNMP engine criada. Total: {self.engines_created}")
        return engine
    
    async def return_engine(self, engine, is_faulty: bool = False):
        """Retorna uma engine ao pool"""
        async with self.lock:
            if is_faulty:
                self.faulty_engines.add(id(engine))
                await self._dispose_engine(engine)
                logger.debug(f"Engine marcada como defeituosa e descartada")
            else:
                try:
                    self.engines.put_nowait(engine)
                except asyncio.QueueFull:
                    await self._dispose_engine(engine)
    
    async def _dispose_engine(self, engine):
        """Descarta uma engine defeituosa"""
        try:
            if hasattr(engine, 'transport_dispatcher'):
                engine.transport_dispatcher.close_dispatcher()
            self.engines_created -= 1
            self.faulty_engines.discard(id(engine))
        except Exception as e:
            logger.error(f"Erro ao descartar engine: {e}")
    
    async def refresh_all_engines(self):
        """Força a renovação de todas as engines"""
        async with self.lock:
            logger.info("Renovando todas as engines SNMP...")
            # Marca todas as engines como defeituosas
            while not self.engines.empty():
                try:
                    engine = self.engines.get_nowait()
                    await self._dispose_engine(engine)
                except asyncio.QueueEmpty:
                    break
            self.faulty_engines.clear()
            logger.info("Todas as engines SNMP foram renovadas")

