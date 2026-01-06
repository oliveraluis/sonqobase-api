"""
Event Bus para publicar y suscribirse a eventos de dominio.
Similar a ApplicationEventPublisher de Spring Boot.
"""
from typing import Callable, Dict, List, Type, TypeVar
from collections import defaultdict
import asyncio
import logging

from app.domain.events import DomainEvent

T = TypeVar('T', bound=DomainEvent)

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus para publicar y suscribirse a eventos de dominio.
    
    Características:
    - Suscripción basada en decoradores
    - Listeners asíncronos ejecutados en paralelo
    - Manejo de errores sin afectar otros listeners
    - Type-safe con generics
    """
    
    def __init__(self):
        # Dict[EventType, List[AsyncListener]]
        self._async_listeners: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)
        # Dict[EventType, List[SyncListener]]
        self._sync_listeners: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)
    
    def subscribe(
        self, 
        event_type: Type[T], 
        async_handler: bool = True
    ) -> Callable:
        """
        Decorator para registrar un listener.
        
        Usage:
            @event_bus.subscribe(DocumentReadEvent)
            async def handle_document_read(event: DocumentReadEvent):
                # Procesar evento
                pass
        
        Args:
            event_type: Tipo de evento a escuchar
            async_handler: True para listener asíncrono, False para síncrono
        """
        def decorator(handler: Callable[[T], None]):
            if async_handler:
                self._async_listeners[event_type].append(handler)
                logger.info(f"✅ Registered async listener for {event_type.__name__}")
            else:
                self._sync_listeners[event_type].append(handler)
                logger.info(f"✅ Registered sync listener for {event_type.__name__}")
            return handler
        return decorator
    
    async def publish(self, event: DomainEvent):
        """
        Publicar un evento a todos los listeners registrados.
        Los listeners asíncronos se ejecutan en paralelo.
        Los errores en listeners no afectan la operación principal.
        
        Args:
            event: Evento de dominio a publicar
        """
        event_type = type(event)
        
        # Ejecutar listeners síncronos
        for listener in self._sync_listeners.get(event_type, []):
            try:
                listener(event)
            except Exception as e:
                logger.error(f"❌ Error in sync listener for {event_type.__name__}: {e}")
        
        # Ejecutar listeners asíncronos en paralelo
        async_tasks = []
        for listener in self._async_listeners.get(event_type, []):
            async_tasks.append(self._safe_async_call(listener, event))
        
        if async_tasks:
            await asyncio.gather(*async_tasks, return_exceptions=True)
    
    async def _safe_async_call(self, listener: Callable, event: DomainEvent):
        """Ejecutar listener con manejo de errores"""
        try:
            await listener(event)
        except Exception as e:
            logger.error(f"❌ Error in async listener for {type(event).__name__}: {e}", exc_info=True)
    
    def publish_sync(self, event: DomainEvent):
        """
        Publicar evento de forma síncrona (solo listeners síncronos).
        Útil para contextos no-async.
        
        Args:
            event: Evento de dominio a publicar
        """
        event_type = type(event)
        for listener in self._sync_listeners.get(event_type, []):
            try:
                listener(event)
            except Exception as e:
                logger.error(f"❌ Error in sync listener for {event_type.__name__}: {e}")
    
    def get_listener_count(self, event_type: Type[DomainEvent] = None) -> int:
        """Obtener número de listeners registrados"""
        if event_type:
            return (
                len(self._async_listeners.get(event_type, [])) +
                len(self._sync_listeners.get(event_type, []))
            )
        else:
            total = 0
            for listeners in self._async_listeners.values():
                total += len(listeners)
            for listeners in self._sync_listeners.values():
                total += len(listeners)
            return total


# Singleton global
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Obtener instancia global del event bus"""
    return _event_bus
