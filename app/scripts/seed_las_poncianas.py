"""
Script de seed para datos de ejemplo: Hospedaje Las Poncianas de Casma

Este script crea datos de ejemplo para probar las funcionalidades CRUD y RAG.
Incluye información sobre habitaciones, servicios, ubicación y políticas.

Uso:
    python -m app.scripts.seed_las_poncianas --api-key YOUR_API_KEY
"""
import asyncio
import sys
from typing import Dict, Any

# Datos del hospedaje Las Poncianas de Casma
HOSPEDAJE_INFO = {
    "nombre": "Las Poncianas de Casma",
    "tipo": "Hospedaje",
    "ubicacion": {
        "direccion": "Jr. Huaraz 234, Casma",
        "distrito": "Casma",
        "provincia": "Casma",
        "departamento": "Áncash",
        "pais": "Perú",
        "coordenadas": {
            "latitud": -9.4748,
            "longitud": -78.3044
        }
    },
    "contacto": {
        "telefono": "+51 943 123 456",
        "email": "info@lasponcianas.com",
        "whatsapp": "+51 943 123 456",
        "horario_atencion": "24 horas"
    },
    "descripcion": "Hospedaje familiar ubicado en el corazón de Casma, a pocas cuadras de la plaza de armas. Ofrecemos habitaciones cómodas y limpias con todos los servicios necesarios para una estadía placentera. Ideal para turistas y viajeros de negocios."
}

HABITACIONES = [
    {
        "id": "hab_simple_01",
        "nombre": "Habitación Simple",
        "tipo": "Simple",
        "capacidad": 1,
        "precio_noche": 50.00,
        "moneda": "PEN",
        "descripcion": "Habitación acogedora para una persona con cama individual, baño privado y TV cable.",
        "servicios": [
            "Baño privado",
            "TV cable",
            "WiFi gratuito",
            "Agua caliente",
            "Ventilador",
            "Escritorio"
        ],
        "disponible": True
    },
    {
        "id": "hab_doble_01",
        "nombre": "Habitación Doble Estándar",
        "tipo": "Doble",
        "capacidad": 2,
        "precio_noche": 80.00,
        "moneda": "PEN",
        "descripcion": "Habitación espaciosa con cama matrimonial, baño privado, TV cable y minibar.",
        "servicios": [
            "Baño privado",
            "TV cable",
            "WiFi gratuito",
            "Agua caliente",
            "Aire acondicionado",
            "Minibar",
            "Escritorio",
            "Closet"
        ],
        "disponible": True
    },
    {
        "id": "hab_doble_02",
        "nombre": "Habitación Doble Twin",
        "tipo": "Doble Twin",
        "capacidad": 2,
        "precio_noche": 80.00,
        "moneda": "PEN",
        "descripcion": "Habitación con dos camas individuales, ideal para amigos o compañeros de trabajo.",
        "servicios": [
            "Baño privado",
            "TV cable",
            "WiFi gratuito",
            "Agua caliente",
            "Aire acondicionado",
            "Escritorio",
            "Closet"
        ],
        "disponible": True
    },
    {
        "id": "hab_triple_01",
        "nombre": "Habitación Triple",
        "tipo": "Triple",
        "capacidad": 3,
        "precio_noche": 110.00,
        "moneda": "PEN",
        "descripcion": "Habitación amplia con una cama matrimonial y una cama individual, perfecta para familias pequeñas.",
        "servicios": [
            "Baño privado",
            "TV cable",
            "WiFi gratuito",
            "Agua caliente",
            "Aire acondicionado",
            "Minibar",
            "Escritorio",
            "Closet"
        ],
        "disponible": True
    },
    {
        "id": "hab_suite_01",
        "nombre": "Suite Familiar",
        "tipo": "Suite",
        "capacidad": 4,
        "precio_noche": 150.00,
        "moneda": "PEN",
        "descripcion": "Suite espaciosa con sala de estar, dos habitaciones (una con cama matrimonial y otra con dos camas individuales), ideal para familias.",
        "servicios": [
            "Baño privado",
            "TV cable en ambas habitaciones",
            "WiFi gratuito",
            "Agua caliente",
            "Aire acondicionado",
            "Minibar",
            "Sala de estar",
            "Escritorio",
            "Closet amplio",
            "Balcón"
        ],
        "disponible": True
    }
]

SERVICIOS_GENERALES = {
    "servicios_incluidos": [
        "WiFi gratuito en todas las áreas",
        "Recepción 24 horas",
        "Servicio de despertador",
        "Custodia de equipaje",
        "Información turística",
        "Servicio de taxi",
        "Estacionamiento gratuito (sujeto a disponibilidad)"
    ],
    "servicios_adicionales": [
        {
            "nombre": "Desayuno buffet",
            "precio": 15.00,
            "moneda": "PEN",
            "descripcion": "Desayuno continental con frutas, panes, jugos, café y opciones calientes"
        },
        {
            "nombre": "Lavandería",
            "precio": 10.00,
            "moneda": "PEN",
            "descripcion": "Servicio de lavado y planchado por kilo"
        },
        {
            "nombre": "Transfer aeropuerto",
            "precio": 30.00,
            "moneda": "PEN",
            "descripcion": "Traslado desde/hacia el aeropuerto de Chimbote"
        }
    ]
}

POLITICAS = {
    "check_in": "14:00",
    "check_out": "12:00",
    "cancelacion": "Cancelación gratuita hasta 24 horas antes del check-in. Después se cobra el 50% de la primera noche.",
    "mascotas": "No se permiten mascotas",
    "fumadores": "Prohibido fumar en las habitaciones. Área de fumadores disponible en el patio",
    "ninos": "Los niños menores de 5 años no pagan. De 5 a 12 años pagan el 50% de la tarifa de adulto.",
    "pago": "Aceptamos efectivo, tarjetas Visa y Mastercard, y transferencias bancarias",
    "deposito": "No se requiere depósito para reservas"
}

ATRACCIONES_CERCANAS = [
    {
        "nombre": "Plaza de Armas de Casma",
        "distancia_km": 0.3,
        "tiempo_caminando": "5 minutos",
        "descripcion": "Centro histórico de la ciudad con jardines y monumentos"
    },
    {
        "nombre": "Playa Tortugas",
        "distancia_km": 8.5,
        "tiempo_auto": "15 minutos",
        "descripcion": "Hermosa playa ideal para surf y deportes acuáticos"
    },
    {
        "nombre": "Sitio Arqueológico Sechín",
        "distancia_km": 5.0,
        "tiempo_auto": "10 minutos",
        "descripcion": "Importante complejo arqueológico con más de 3000 años de antigüedad"
    },
    {
        "nombre": "Humedales de Villa María",
        "distancia_km": 12.0,
        "tiempo_auto": "20 minutos",
        "descripcion": "Área natural protegida ideal para observación de aves"
    }
]

# Texto completo para ingesta RAG
TEXTO_COMPLETO_RAG = f"""
# Hospedaje Las Poncianas de Casma

## Información General
Las Poncianas de Casma es un hospedaje familiar ubicado en el corazón de Casma, en Jr. Huaraz 234. 
Nos encontramos en el distrito de Casma, provincia de Casma, departamento de Áncash, Perú.

Ofrecemos atención las 24 horas del día y contamos con recepción permanente para atender todas sus necesidades.
Puede contactarnos al teléfono +51 943 123 456, por WhatsApp al mismo número, o por email a info@lasponcianas.com.

## Ubicación
Estamos ubicados a solo 3 cuadras de la Plaza de Armas de Casma, en una zona céntrica y segura.
Nuestras coordenadas son: Latitud -9.4748, Longitud -78.3044.

## Habitaciones Disponibles

### Habitación Simple (S/ 50 por noche)
Habitación acogedora para una persona con cama individual. Incluye baño privado, TV cable, WiFi gratuito,
agua caliente, ventilador y escritorio. Capacidad: 1 persona.

### Habitación Doble Estándar (S/ 80 por noche)
Habitación espaciosa con cama matrimonial. Incluye baño privado, TV cable, WiFi gratuito, agua caliente,
aire acondicionado, minibar, escritorio y closet. Capacidad: 2 personas.

### Habitación Doble Twin (S/ 80 por noche)
Habitación con dos camas individuales, ideal para amigos o compañeros de trabajo. Incluye baño privado,
TV cable, WiFi gratuito, agua caliente, aire acondicionado, escritorio y closet. Capacidad: 2 personas.

### Habitación Triple (S/ 110 por noche)
Habitación amplia con una cama matrimonial y una cama individual, perfecta para familias pequeñas.
Incluye baño privado, TV cable, WiFi gratuito, agua caliente, aire acondicionado, minibar, escritorio
y closet. Capacidad: 3 personas.

### Suite Familiar (S/ 150 por noche)
Suite espaciosa con sala de estar y dos habitaciones: una con cama matrimonial y otra con dos camas individuales.
Ideal para familias de hasta 4 personas. Incluye baño privado, TV cable en ambas habitaciones, WiFi gratuito,
agua caliente, aire acondicionado, minibar, sala de estar, escritorio, closet amplio y balcón.

## Servicios Incluidos
- WiFi gratuito en todas las áreas del hospedaje
- Recepción 24 horas para atenderle en cualquier momento
- Servicio de despertador
- Custodia de equipaje
- Información turística sobre Casma y alrededores
- Servicio de taxi
- Estacionamiento gratuito (sujeto a disponibilidad)

## Servicios Adicionales
- Desayuno buffet: S/ 15 por persona. Incluye frutas, panes, jugos, café y opciones calientes.
- Lavandería: S/ 10 por kilo. Servicio de lavado y planchado.
- Transfer aeropuerto: S/ 30. Traslado desde/hacia el aeropuerto de Chimbote.

## Horarios y Políticas

### Check-in y Check-out
- Check-in: A partir de las 14:00 horas
- Check-out: Hasta las 12:00 horas

### Política de Cancelación
Cancelación gratuita hasta 24 horas antes del check-in. Después de ese plazo se cobra el 50% de la primera noche.

### Otras Políticas
- No se permiten mascotas en el hospedaje
- Prohibido fumar en las habitaciones. Contamos con área de fumadores en el patio
- Niños menores de 5 años no pagan. Niños de 5 a 12 años pagan el 50% de la tarifa de adulto
- Aceptamos efectivo, tarjetas Visa y Mastercard, y transferencias bancarias
- No se requiere depósito para reservas

## Atracciones Cercanas

### Plaza de Armas de Casma
A solo 300 metros (5 minutos caminando). Centro histórico de la ciudad con jardines y monumentos.

### Playa Tortugas
A 8.5 km (15 minutos en auto). Hermosa playa ideal para surf y deportes acuáticos.

### Sitio Arqueológico Sechín
A 5 km (10 minutos en auto). Importante complejo arqueológico con más de 3000 años de antigüedad.
Es uno de los sitios arqueológicos más importantes de la región.

### Humedales de Villa María
A 12 km (20 minutos en auto). Área natural protegida ideal para observación de aves y ecoturismo.

## Preguntas Frecuentes

### ¿Tienen WiFi?
Sí, ofrecemos WiFi gratuito en todas las áreas del hospedaje.

### ¿Incluye desayuno?
El desayuno no está incluido en el precio de la habitación, pero puede agregarlo por S/ 15 por persona.

### ¿Tienen estacionamiento?
Sí, contamos con estacionamiento gratuito sujeto a disponibilidad.

### ¿Aceptan tarjetas de crédito?
Sí, aceptamos tarjetas Visa y Mastercard, además de efectivo y transferencias bancarias.

### ¿Cuál es la habitación más económica?
La habitación simple tiene un costo de S/ 50 por noche.

### ¿Cuál es la habitación más grande?
La Suite Familiar es nuestra habitación más amplia, con capacidad para 4 personas y un costo de S/ 150 por noche.
"""


def print_data_summary():
    """Imprime un resumen de los datos que se van a crear"""
    print("=" * 60)
    print("DATOS DE EJEMPLO: LAS PONCIANAS DE CASMA")
    print("=" * 60)
    print(f"\n📍 Información del Hospedaje:")
    print(f"   Nombre: {HOSPEDAJE_INFO['nombre']}")
    print(f"   Ubicación: {HOSPEDAJE_INFO['ubicacion']['direccion']}")
    print(f"   Teléfono: {HOSPEDAJE_INFO['contacto']['telefono']}")
    
    print(f"\n🏠 Habitaciones: {len(HABITACIONES)}")
    for hab in HABITACIONES:
        print(f"   - {hab['nombre']}: S/ {hab['precio_noche']}/noche (Capacidad: {hab['capacidad']})")
    
    print(f"\n✨ Servicios Incluidos: {len(SERVICIOS_GENERALES['servicios_incluidos'])}")
    print(f"💰 Servicios Adicionales: {len(SERVICIOS_GENERALES['servicios_adicionales'])}")
    print(f"🏖️  Atracciones Cercanas: {len(ATRACCIONES_CERCANAS)}")
    print(f"\n📝 Texto para RAG: {len(TEXTO_COMPLETO_RAG)} caracteres")
    print("=" * 60)


if __name__ == "__main__":
    print_data_summary()
    print("\n💡 Para usar estos datos:")
    print("   1. Crea un proyecto y obtén tu API key")
    print("   2. Usa los endpoints CRUD para insertar los datos")
    print("   3. Usa el endpoint /ingest para cargar el texto RAG")
    print("   4. Prueba consultas como:")
    print("      - ¿Cuánto cuesta la habitación doble?")
    print("      - ¿Qué servicios incluye el hospedaje?")
    print("      - ¿Dónde está ubicado Las Poncianas?")
    print("      - ¿Qué atracciones turísticas hay cerca?")
