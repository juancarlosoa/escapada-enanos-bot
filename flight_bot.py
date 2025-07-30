import json
import logging
import calendar
import os
from datetime import datetime, timedelta
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

# Logging config
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}
DESTINATIONS_FILE = "destinations.json"
BOT_PASSWORD = os.getenv('BOT_PASSWORD')
AUTHORIZED_USERS = set()

# Configuración maestra de destinos disponibles (nombres y valores por defecto)
DESTINATIONS_MASTER = {
    "Country:FR": {"name": "🇫🇷 Francia", "default": True},
    "Country:IT": {"name": "🇮🇹 Italia", "default": True},
    "Country:PT": {"name": "🇵🇹 Portugal", "default": True},
    "Country:GB": {"name": "🇬🇧 Reino Unido", "default": True},
    "Country:DE": {"name": "🇩🇪 Alemania", "default": True},
    "Country:NL": {"name": "🇳🇱 Países Bajos", "default": True},
    "Country:BE": {"name": "🇧🇪 Bélgica", "default": False},
    "Country:CH": {"name": "🇨🇭 Suiza", "default": False},
    "Country:AT": {"name": "🇦🇹 Austria", "default": False},
    "Country:CZ": {"name": "🇨🇿 Rep. Checa", "default": False},
    "Country:PL": {"name": "🇵🇱 Polonia", "default": False},
    "Country:HR": {"name": "🇭🇷 Croacia", "default": False},
    "Country:GR": {"name": "🇬🇷 Grecia", "default": False},
    "Country:HU": {"name": "🇭🇺 Hungría", "default": False},
    "Country:DK": {"name": "🇩🇰 Dinamarca", "default": False},
    "Country:NO": {"name": "🇳🇴 Noruega", "default": False},
    "Country:SE": {"name": "🇸🇪 Suecia", "default": False},
    "Country:FI": {"name": "🇫🇮 Finlandia", "default": False},
    "Country:IS": {"name": "🇮🇸 Islandia", "default": True},
    "Country:IE": {"name": "🇮🇪 Irlanda", "default": False}
}

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite al usuario autenticarse con la contraseña del bot"""
    user_id = update.effective_user.id

    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ Ya estás autenticado.")
        return

    if not context.args:
        await update.message.reply_text("🔐 Usa el comando así: `/login tu_contraseña`", parse_mode="Markdown")
        return

    password = context.args[0]
    if password == BOT_PASSWORD:
        AUTHORIZED_USERS.add(user_id)
        await update.message.reply_text("🔓 Acceso concedido. Ya puedes usar el bot.")
    else:
        await update.message.reply_text("❌ Contraseña incorrecta. Inténtalo de nuevo.")

def require_authentication(handler):
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_USERS:
            await update.effective_message.reply_text("🚫 Necesitas autenticarte con `/login tu_contraseña`.")
            return
        return await handler(update, context, *args, **kwargs)
    return wrapper

def get_available_destinations():
    """Obtiene todos los códigos de destinos disponibles"""
    return list(DESTINATIONS_MASTER.keys())

def get_default_destinations():
    """Obtiene la configuración por defecto de destinos (solo estado activo/inactivo)"""
    return {code: config["default"] for code, config in DESTINATIONS_MASTER.items()}

def get_country_name(code):
    """Obtiene el nombre amigable de un país"""
    return DESTINATIONS_MASTER.get(code, {}).get("name", code.replace("Country:", ""))

def is_valid_destination(code):
    """Verifica si un código de destino es válido"""
    return code in DESTINATIONS_MASTER

def load_destinations():
    """Carga la configuración de destinos desde el archivo JSON"""
    try:
        with open(DESTINATIONS_FILE, "r", encoding='utf-8') as f:
            loaded_data = json.load(f)
            
        # Validar que los datos cargados sean un diccionario
        if not isinstance(loaded_data, dict):
            logging.warning("destinations.json no contiene un diccionario válido. Recreando archivo.")
            default_config = get_default_destinations()
            save_destinations(default_config)
            return default_config.copy()
            
        # Verificar que todas las claves esperadas estén presentes
        default_config = get_default_destinations()
        missing_keys = set(default_config.keys()) - set(loaded_data.keys())
        if missing_keys:
            logging.info(f"Agregando destinos faltantes: {missing_keys}")
            for key in missing_keys:
                loaded_data[key] = default_config[key]
            save_destinations(loaded_data)
            
        # Eliminar claves obsoletas que ya no están en la configuración
        obsolete_keys = set(loaded_data.keys()) - set(default_config.keys())
        if obsolete_keys:
            logging.info(f"Eliminando destinos obsoletos: {obsolete_keys}")
            for key in obsolete_keys:
                del loaded_data[key]
            save_destinations(loaded_data)
            
        return loaded_data
        
    except FileNotFoundError:
        logging.info("destinations.json no encontrado. Creando archivo con configuración por defecto.")
        default_config = get_default_destinations()
        save_destinations(default_config)
        return default_config.copy()
        
    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar destinations.json: {e}")
        logging.info("Recreando archivo con configuración por defecto.")
        default_config = get_default_destinations()
        save_destinations(default_config)
        return default_config.copy()
        
    except Exception as e:
        logging.error(f"Error inesperado al cargar destinations.json: {e}")
        return get_default_destinations().copy()

def save_destinations(data):
    """Guarda la configuración de destinos en el archivo JSON.
    Solo guarda el estado activo/inactivo, no los nombres ni configuración maestra.
    """
    try:
        # Validar que data sea un diccionario
        if not isinstance(data, dict):
            logging.error("Intento de guardar datos no válidos en destinations.json")
            return False
        
        # Filtrar solo destinos válidos y valores booleanos
        filtered_data = {}
        for key, value in data.items():
            if is_valid_destination(key) and isinstance(value, bool):
                filtered_data[key] = value
            elif is_valid_destination(key):
                # Convertir valores no booleanos a False
                filtered_data[key] = False
                logging.warning(f"Convirtiendo valor no booleano a False para {key}")
            else:
                logging.warning(f"Ignorando destino no válido: {key}")
            
        with open(DESTINATIONS_FILE, "w", encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Configuración de destinos guardada: {len(filtered_data)} destinos")
        return True
        
    except Exception as e:
        logging.error(f"Error al guardar destinations.json: {e}")
        return False

def get_selected_destinations():
    """Obtiene solo los destinos activos"""
    config = load_destinations()
    selected = [k for k, v in config.items() if v is True]
    logging.info(f"Destinos activos: {len(selected)} de {len(config)}")
    return selected

def validate_destinations_config():
    """Valida y corrige la configuración de destinos si es necesario"""
    try:
        config = load_destinations()
        corrected = False
        
        # Asegurar que todos los valores sean booleanos
        for key, value in config.items():
            if not isinstance(value, bool):
                logging.warning(f"Corrigiendo valor no booleano para {key}: {value} -> False")
                config[key] = False
                corrected = True
                
        if corrected:
            save_destinations(config)
            
        return config
        
    except Exception as e:
        logging.error(f"Error validando configuración de destinos: {e}")
        return get_default_destinations().copy()

def get_weekends(month: int, year: int):
    """Obtiene todos los fines de semana (viernes-domingo) de un mes"""
    weekends = []
    _, last_day = calendar.monthrange(year, month)
    
    for day in range(1, last_day + 1):
        date = datetime(year, month, day)
        if date.weekday() == 4:  # Viernes
            sunday = date + timedelta(days=2)
            # Solo agregar si el domingo está en el mismo mes
            if sunday.month == month:
                weekends.append((date, sunday))
    
    return weekends

def parse_and_filter_flights(data):
    """Parsea y filtra los vuelos de la respuesta de la API"""
    if not data or "itineraries" not in data:
        return []
    
    filtered = []
    for itinerary in data.get("itineraries", []):
        try:
            outbound_seg = itinerary["outbound"]["sectorSegments"][0]["segment"]
            inbound_seg = itinerary["inbound"]["sectorSegments"][0]["segment"]

            # Parsear fechas
            outbound_dt = datetime.strptime(outbound_seg["source"]["localTime"][:16], "%Y-%m-%dT%H:%M")
            inbound_dt = datetime.strptime(inbound_seg["source"]["localTime"][:16], "%Y-%m-%dT%H:%M")

            # Información del vuelo
            origin = outbound_seg["source"]["station"]["name"]
            destination = outbound_seg["destination"]["station"]["name"]
            price = f"{float(itinerary['price']['amount']):.2f}"
            
            # Aerolíneas
            outbound_carrier = outbound_seg["carrier"]["name"]
            inbound_carrier = inbound_seg["carrier"]["name"]

            # Link de booking
            booking = itinerary.get("bookingOptions", {}).get("edges", [])
            link = "https://www.kiwi.com" + booking[0]["node"]["bookingUrl"] if booking else "https://www.kiwi.com"

            message = (
                f"✈️ *{origin} → {destination}*\n"
                f"🛫 Ida: `{outbound_dt.strftime('%d/%m %H:%M')}` ({outbound_carrier})\n"
                f"🛬 Vuelta: `{inbound_dt.strftime('%d/%m %H:%M')}` ({inbound_carrier})\n"
                f"💰 Precio: *{price} €*\n"
                f"[🔗 Reservar]({link})"
            )
            filtered.append(message)
            
        except (KeyError, ValueError, IndexError) as e:
            logging.warning(f"Error procesando itinerario: {e}")
            continue
    
    return filtered

@require_authentication
async def find(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    """Comando principal para buscar vuelos"""
    send_to = update.callback_query.message if from_callback else update.message

    if not context.args:
        await send_to.reply_text("📅 Usa el comando así: `/find agosto` [opcional: año]", parse_mode="Markdown")
        return

    month_name = context.args[0].lower()
    if month_name not in MONTHS:
        valid_months = ", ".join(MONTHS.keys())
        await send_to.reply_text(f"❌ Mes no reconocido.\n\n**Meses válidos:** {valid_months}", parse_mode="Markdown")
        return

    # Determinar año
    now = datetime.now()
    month = MONTHS[month_name]
    
    if len(context.args) > 1 and context.args[1].isdigit():
        year = int(context.args[1])
    else:
        # Si el mes ya pasó este año, usar el próximo año
        year = now.year + 1 if month < now.month else now.year

    weekends = get_weekends(month, year)
    
    if not weekends:
        await send_to.reply_text(f"❌ No hay fines de semana completos en {month_name.title()} {year}")
        return

    # Verificar destinos activos
    destinations = get_selected_destinations()
    if not destinations:
        await send_to.reply_text(
            "⚠️ No hay destinos activos. Usa `/destinations` para configurarlos.\n\n"
            "💡 Tip: Necesitas activar al menos un destino para buscar vuelos.",
            parse_mode="Markdown"
        )
        return

    # Mostrar información de la búsqueda
    active_countries = [get_country_name(dest) for dest in destinations]
    countries_text = ", ".join(active_countries[:3])
    if len(active_countries) > 3:
        countries_text += f" y {len(active_countries) - 3} más"

    await send_to.reply_text(
        f"🔍 Buscando vuelos desde *viernes a domingo* para *{month_name.title()} {year}* por menos de 150€...\n"
        f"📊 {len(weekends)} fines de semana encontrados\n"
        f"🎯 Destinos: {countries_text}", 
        parse_mode="Markdown"
    )

    total_found = 0
    
    for i, (outbound_date, inbound_date) in enumerate(weekends, 1):
        try:
            # Horarios de búsqueda
            outbound_start = outbound_date.replace(hour=17)
            outbound_end = outbound_date.replace(hour=23, minute=59)
            inbound_start = inbound_date.replace(hour=11)
            inbound_end = inbound_date.replace(hour=23, minute=59)

            params = {
                "source": "Airport:ALC,Airport:RMU",
                "destination": ",".join(destinations),
                "currency": "eur",
                "locale": "es",
                "adults": "1",
                "children": "0",
                "infants": "0",
                "handbags": "1",
                "holdbags": "0",
                "cabinClass": "ECONOMY",
                "applyMixedClasses": "false",
                "enableThrowAwayTicketing": "false",
                "allowReturnFromDifferentCity": "false",
                "allowChangeInboundDestination": "false",
                "allowChangeInboundSource": "false",
                "allowOvernightStopover": "false",
                "enableTrueHiddenCity": "false",
                "enableSelfTransfer": "true",
                "allowDifferentStationConnection": "true",
                "sortBy": "PRICE",
                "sortOrder": "ASCENDING",
                "outboundDepartureDateStart": outbound_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "outboundDepartureDateEnd": outbound_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "inboundDepartureDateStart": inbound_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "inboundDepartureDateEnd": inbound_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "transportTypes": "FLIGHT",
                "limit": "5",
                "priceStart": "0",
                "priceEnd":"150"
            }

            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "kiwi-com-cheap-flights.p.rapidapi.com"
            }

            # Enviar mensaje de progreso
            progress_msg = f"⏳ Procesando fin de semana {i}/{len(weekends)} ({outbound_date.strftime('%d/%m')} - {inbound_date.strftime('%d/%m')})..."
            if from_callback:
                await send_to.reply_text(progress_msg)
            else:
                await update.message.reply_text(progress_msg)

            response = requests.get(
                "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip", 
                headers=headers, 
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            flights = parse_and_filter_flights(response.json())

            if flights:
                weekend_header = f"🗓️ *Fin de semana del {outbound_date.strftime('%d/%m')} - {inbound_date.strftime('%d/%m')}*:"
                await send_to.reply_text(weekend_header, parse_mode="Markdown")
                
                for msg in flights:
                    await send_to.reply_markdown(msg)
                    
                total_found += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"Error de API para {outbound_date.date()}–{inbound_date.date()}: {e}")
            await send_to.reply_text(f"⚠️ Error buscando vuelos para {outbound_date.strftime('%d/%m')} - {inbound_date.strftime('%d/%m')}")
            
        except Exception as e:
            logging.error(f"Error inesperado para {outbound_date.date()}–{inbound_date.date()}: {e}")

    # Mensaje final
    if total_found == 0:
        await send_to.reply_text("❌ No se encontraron vuelos válidos para ningún fin de semana.")
    else:
        await send_to.reply_text(f"✅ Búsqueda completada. Se encontraron vuelos para {total_found}/{len(weekends)} fines de semana.")

@require_authentication
async def destinations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para configurar destinos"""
    # Validar configuración antes de mostrar
    config = validate_destinations_config()
    
    # Ordenar: activos primero, luego por nombre
    sorted_items = sorted(
        config.items(), 
        key=lambda item: (not item[1], get_country_name(item[0]))
    )
    
    # Crear botones en grid de 2 columnas
    buttons = []
    row = []
    
    for key, active in sorted_items:
        display_name = get_country_name(key)
        emoji = "✅" if active else "❌"
        button = InlineKeyboardButton(f"{emoji} {display_name}", callback_data=f"toggle_{key}")
        
        row.append(button)
        
        # Crear nueva fila cada 2 botones
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    # Agregar fila incompleta si existe
    if row:
        buttons.append(row)
    
    # Agregar botones de control
    control_buttons = []
    control_buttons.append([
        InlineKeyboardButton("✅ Activar Todos", callback_data="toggle_all_on"),
        InlineKeyboardButton("❌ Desactivar Todos", callback_data="toggle_all_off")
    ])
    control_buttons.append([
        InlineKeyboardButton("🔄 Restablecer Defecto", callback_data="reset_defaults")
    ])
    
    buttons.extend(control_buttons)
    markup = InlineKeyboardMarkup(buttons)
    
    # Contar destinos activos
    active_count = sum(1 for active in config.values() if active)
    active_names = [get_country_name(k) for k, v in config.items() if v]
    
    status_text = "🛩️ **Configurar Destinos**\n\n"
    status_text += f"📊 Destinos activos: **{active_count}/{len(config)}**\n\n"
    
    if active_count > 0:
        if active_count <= 5:
            status_text += f"🎯 Activos: {', '.join(active_names)}\n\n"
        else:
            status_text += f"🎯 Activos: {', '.join(active_names[:3])} y {active_count - 3} más\n\n"
    
    status_text += "💡 Toca para activar/desactivar:"
    
    await update.effective_message.reply_text(
        status_text,
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def handle_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el toggle de destinos y acciones de control"""
    query = update.callback_query
    await query.answer()
    
    config = load_destinations()
    
    if query.data.startswith("toggle_"):
        action = query.data.replace("toggle_", "")
        
        if action == "all_on":
            # Activar todos los destinos
            for key in config:
                config[key] = True
            save_destinations(config)
            await query.answer("✅ Todos los destinos activados", show_alert=True)
            
        elif action == "all_off":
            # Desactivar todos los destinos
            for key in config:
                config[key] = False
            save_destinations(config)
            await query.answer("❌ Todos los destinos desactivados", show_alert=True)
            
        elif action == "defaults":
            # Restablecer configuración por defecto
            default_config = get_default_destinations()
            save_destinations(default_config)
            await query.answer("🔄 Configuración restablecida", show_alert=True)
            
        else:
            # Toggle individual
            key = action
            if key in config:
                config[key] = not config[key]
                save_destinations(config)
                country_name = get_country_name(key)
                status = "activado" if config[key] else "desactivado"
                await query.answer(f"{country_name} {status}", show_alert=False)
            else:
                await query.answer("❌ Destino no encontrado", show_alert=True)
                return
        
        # Actualizar el mensaje con la nueva configuración
        await destinations(update, context)
    
    elif query.data == "reset_defaults":
        # Restablecer configuración por defecto
        default_config = get_default_destinations()
        save_destinations(default_config)
        await query.answer("🔄 Configuración restablecida a valores por defecto", show_alert=True)
        await destinations(update, context)

@require_authentication
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de inicio con botones de meses en grid"""
    # Validar configuración al inicio
    validate_destinations_config()
    
    month_buttons = []
    row = []
    
    # Crear botones en grid de 3 columnas
    for mes in MONTHS.keys():
        button = InlineKeyboardButton(mes.title(), callback_data=f"find_{mes}")
        row.append(button)
        
        # Nueva fila cada 3 botones
        if len(row) == 3:
            month_buttons.append(row)
            row = []
    
    # Agregar fila incompleta si existe
    if row:
        month_buttons.append(row)
    
    # Botón adicional para configurar destinos
    month_buttons.append([InlineKeyboardButton("⚙️ Configurar Destinos", callback_data="config_destinos")])
    
    markup = InlineKeyboardMarkup(month_buttons)
    
    welcome_text = (
        "🤖 **Bot de Vuelos - Fines de Semana**\n\n"
        "✈️ Busca automáticamente vuelos por menos de 150€ desde Alicante y Murcia para todos los fines de semana de un mes\n\n"
        "📅 **Selecciona un mes:**"
    )
    
    await update.effective_message.reply_text(
        welcome_text,
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los botones inline"""
    query = update.callback_query
    
    if query.data.startswith("find_"):
        # Buscar vuelos para el mes seleccionado
        month = query.data[5:]
        context.args = [month]
        await find(update, context, from_callback=True)
        
    elif query.data == "config_destinos":
        # Mostrar configuración de destinos
        await destinations(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de ayuda"""
    config = load_destinations()
    active_count = sum(1 for v in config.values() if v)
    total_available = len(get_available_destinations())
    
    help_text = (
        "🆘 **Ayuda - Bot de Vuelos**\n\n"
        "**Comandos disponibles:**\n"
        "• `/start` - Menú principal\n"
        "• `/find agosto` - Buscar vuelos para un mes\n"
        "• `/destinations` - Configurar destinos\n"
        "• `/help` - Mostrar esta ayuda\n\n"
        "**¿Cómo funciona?**\n"
        "1. Selecciona un mes con `/start`\n"
        "2. El bot busca automáticamente todos los viernes-domingos\n"
        "3. Te muestra los vuelos más baratos disponibles con un precio máximo de 150€\n\n"
        "**Configuración actual:**\n"
        f"• Destinos activos: {active_count}/{total_available}\n"
        "• Origen: Alicante (ALC) + Murcia(RMU)\n"
        "• Vuelos: Viernes 17:00-23:59 → Domingo 11:00-23:59\n"
        "• Orden: Por precio (más barato primero), con un precio máximo de 150€\n"
        "• Límite: 5 vuelos por fin de semana\n\n"
        "💡 **Tip:** Configura tus destinos preferidos con `/destinations` para personalizar las búsquedas."
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

#####################################

if __name__ == "__main__":
    # Verificar que las variables de entorno estén configuradas
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN no encontrado en variables de entorno")
        print("💡 Crea un archivo .env con: BOT_TOKEN=tu_token_aqui")
        exit(1)
    
    if not RAPIDAPI_KEY:
        print("❌ Error: RAPIDAPI_KEY no encontrado en variables de entorno")
        print("💡 Crea un archivo .env con: RAPIDAPI_KEY=tu_clave_aqui")
        exit(1)

    # Validar configuración al iniciar el bot
    logging.info("🚀 Iniciando bot...")
    logging.info("🔧 Validando configuración de destinos...")
    validate_destinations_config()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("destinations", destinations))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_toggle, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(handle_toggle, pattern="^reset_defaults$"))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(CommandHandler("login", login))

    print("🤖 Bot iniciado ✅ Usa /start")
    app.run_polling()
