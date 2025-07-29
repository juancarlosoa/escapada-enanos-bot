# 🤖 Bot de Vuelos - Fines de Semana

Un bot de Telegram que automatiza la búsqueda de vuelos económicos desde Alicante y Murcia para todos los fines de semana de un mes específico.

## 📖 Descripción

Este bot permite a los usuarios buscar automáticamente vuelos de fin de semana (viernes a domingo) desde el aeropuerto de Alicante y Murcia hacia múltiples destinos europeos. Los usuarios pueden personalizar qué países quieren incluir en sus búsquedas y recibir los resultados organizados por fecha y precio.

## ✨ Características

- 🔍 **Búsqueda automática**: Encuentra todos los fines de semana de un mes
- ⚙️ **Destinos configurables**: 20 países europeos disponibles
- 💰 **Ordenado por precio**: Resultados más económicos primero
- 📅 **Horarios optimizados**: Viernes 17:00-23:59 → Domingo 11:00-23:59
- 🎯 **Interfaz intuitiva**: Botones interactivos y comandos simples
- 💾 **Configuración persistente**: Tus destinos favoritos se guardan automáticamente

## 🛠️ Tecnologías

- **Python 3.8+**
- **python-telegram-bot**: Framework para bots de Telegram
- **python-dotenv**: Manejo de variables de entorno
- **Requests**: Cliente HTTP para llamadas a la API
- **JSON**: Almacenamiento de configuración local

## 🌐 API Utilizada

**Kiwi.com Cheap Flights API** (via RapidAPI): Flights scanner. Build app like kiwi.com, skyscanner, etc

- **Proveedor**: RapidAPI
- **Endpoint**: `kiwi-com-cheap-flights.p.rapidapi.com/round-trip`
- **Funcionalidad**: Búsqueda de vuelos de ida y vuelta
- **Límite**: 5 vuelos por consulta (optimizado para mejores precios)

## 🚀 Instalación

1. **Clona el repositorio**:

   ```bash
   git clone <repository-url>
   cd flight-bot
   ```

2. **Instala las dependencias**:

   ```bash
   pip install python-telegram-bot python-dotenv requests
   ```

3. **Configura las variables de entorno**:

   Crea un archivo `.env` en la raíz del proyecto:

   ```env
   BOT_TOKEN=tu_token_de_telegram_aqui
   RAPIDAPI_KEY=tu_clave_de_rapidapi_aqui
   ```

   - Obtén un token de bot desde [@BotFather](https://t.me/botfather)
   - Regístrate en [RapidAPI](https://rapidapi.com) y suscríbete a "Kiwi.com Cheap Flights"

4. **Ejecuta el bot**:
   ```bash
   py flight_bot.py
   ```

## 📋 Comandos Disponibles

| Comando         | Descripción                           |
| --------------- | ------------------------------------- |
| `/start`        | Menú principal con selección de meses |
| `/find agosto`  | Buscar vuelos para un mes específico  |
| `/destinations` | Configurar países de destino          |
| `/help`         | Mostrar ayuda y configuración actual  |

## 🎯 Destinos Disponibles

El bot incluye 20 destinos europeos:

🟢 **Activos por defecto**: Francia, Italia, Portugal, Reino Unido, Alemania, Países Bajos, Islandia

⚪ **Disponibles**: Bélgica, Suiza, Austria, Rep. Checa, Polonia, Croacia, Grecia, Hungría, Dinamarca, Noruega, Suecia, Finlandia, Irlanda

## 📁 Estructura del Proyecto

```
flight-bot/
├── flight_bot.py          # Código principal del bot
├── destinations.json      # Configuración de destinos del usuario
├── .env                   # Variables de entorno (no incluir en Git)
└── README.md             # Este archivo
```

## ⚙️ Configuración

### destinations.json

Archivo generado automáticamente que almacena las preferencias del usuario:

```json
{
  "Country:FR": true,
  "Country:IT": true,
  "Country:PT": false,
  ...
}
```

### Parámetros de Búsqueda

- **Origen**: Alicante (ALC) + Murcia (RMU)
- **Tipo**: Ida y vuelta obligatorio
- **Clase**: Económica
- **Pasajeros**: 1 adulto
- **Equipaje**: 1 equipaje de mano incluido
- **Ordenación**: Por precio ascendente

## 🔧 Personalización

### Agregar nuevos destinos

Para agregar nuevos destinos al bot:

1. **Modifica `DESTINATIONS_MASTER`** en el código:

   ```python
   DESTINATIONS_MASTER = {
       "Country:XX": {"name": "🏳️ Nuevo País", "default": False},
       # ... resto de destinos existentes
   }
   ```

2. **Reinicia el bot**: Los nuevos destinos se sincronizarán automáticamente al archivo `destinations.json` del usuario con el valor por defecto especificado.

3. **Los usuarios existentes** verán el nuevo destino disponible en `/destinations` automáticamente.

### Variables de entorno

Crea un archivo `.env` para documentar las variables necesarias:

```env
# Token del bot de Telegram (obtener desde @BotFather)
BOT_TOKEN=

# Clave de RapidAPI para Kiwi.com Cheap Flights
RAPIDAPI_KEY=
```

⚠️ **Importante**: Nunca subas el archivo `.env` a Git. Agrégalo a `.gitignore`.

## 📝 Logs

El bot incluye logging detallado para debugging:

- Operaciones de carga/guardado de configuración
- Errores de API y recuperación

## 🤝 Contribuir

1. Fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## ⚠️ Disclaimers

- Los precios y disponibilidad están sujetos a cambios
- El bot requiere conexión a internet activa
- Las claves de API tienen límites de uso según el plan contratado
- Los vuelos mostrados son enlaces directos a Kiwi.com para completar la reserva

---

**¿Problemas o sugerencias?** Abre un issue en GitHub o contacta al desarrollador.
