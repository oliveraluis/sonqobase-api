"""
Strategy Pattern para ingesta de contenido (texto, PDF, etc.)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4

from app.domain.entities import User, Plan


class IngestStrategy(ABC):
    """
    Estrategia base para ingesta de contenido.
    Cada tipo de contenido (texto, PDF, Word, etc.) implementa esta interfaz.
    """
    
    @abstractmethod
    async def validate(self, user: User, plan: Plan, source: Any) -> None:
        """
        Validar que el contenido cumpla con los límites del plan.
        
        Args:
            user: Usuario que realiza la ingesta
            plan: Plan del usuario
            source: Fuente de datos (texto, archivo, etc.)
        
        Raises:
            ValueError: Si excede límites del plan
        """
        pass
    
    @abstractmethod
    async def process(
        self,
        user_id: str,
        project_id: str,
        collection: str,
        source: Any,
        document_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        chunk_size: int = 500,
    ) -> str:
        """
        Procesar el contenido y generar embeddings.
        
        Args:
            user_id: ID del usuario
            project_id: ID del proyecto
            collection: Nombre de la colección
            source: Fuente de datos
            document_id: ID del documento (para ingesta progresiva)
            metadata: Metadatos adicionales
            chunk_size: Tamaño de chunks en tokens
        
        Returns:
            job_id: ID del trabajo de procesamiento
        """
        pass
    
    def _generate_job_id(self) -> str:
        """Generar ID único para el trabajo"""
        return f"job_{uuid4().hex[:12]}"
    
    def _generate_document_id(self, document_id: Optional[str] = None) -> str:
        """Generar o usar document_id existente"""
        return document_id or f"doc_{uuid4().hex[:12]}"
