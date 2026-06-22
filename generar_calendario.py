"""
generar_calendario.py
Lee itinerario.csv + fechas.config.json y genera viaje.ics importable a Google Calendar.

IMPORTANTE: No correr hasta tener los boletos de avion comprados.
Pasos: 1) Editar fechas.config.json con horarios reales  2) python3 generar_calendario.py  3) Importar viaje.ics
"""
import csv
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone


BLOQUES_HORA = {
    "Manana": (9, 0),
    "Tarde": (15, 0),
    "Noche": (19, 0),
}

# Normaliza el nombre del bloque quitando acentos para comparar
def _normalizar_bloque(bloque):
    return (bloque.strip()
            .replace("ñ", "n")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U"))


def tz_fijo(offset_horas):
    return timezone(timedelta(hours=offset_horas))


def escape_ics(texto):
    """Escapa caracteres especiales para valores de texto en RFC 5545."""
    texto = str(texto)
    texto = texto.replace("\\", "\\\\")
    texto = texto.replace(";", "\\;")
    texto = texto.replace(",", "\\,")
    texto = texto.replace("\n", "\\n")
    texto = texto.replace("\r", "")
    return texto


def plegar_linea(linea):
    """RFC 5545: lineas > 75 octetos se doblan con CRLF + espacio."""
    codificada = linea.encode("utf-8")
    if len(codificada) <= 75:
        return linea

    partes = []
    pos = 0
    limite = 75
    while pos < len(codificada):
        fin = pos + limite
        if fin >= len(codificada):
            partes.append(codificada[pos:].decode("utf-8"))
            break
        # No cortar en medio de un caracter UTF-8 multi-byte
        while fin > pos and (codificada[fin] & 0xC0) == 0x80:
            fin -= 1
        partes.append(codificada[pos:fin].decode("utf-8"))
        pos = fin
        limite = 74  # las lineas de continuacion llevan un espacio inicial

    return "\r\n ".join(partes)


def formato_dt_utc(dt):
    """Convierte datetime aware a UTC y formatea como YYYYMMDDTHHMMSSZ."""
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y%m%dT%H%M%SZ")


def crear_vevent(resumen, dt_inicio, dt_fin, descripcion="", ubicacion=""):
    uid = str(uuid.uuid4()) + "@viaje-china-2027"
    ahora = formato_dt_utc(datetime.now(timezone.utc))
    lineas = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{ahora}",
        f"DTSTART:{formato_dt_utc(dt_inicio)}",
        f"DTEND:{formato_dt_utc(dt_fin)}",
        f"SUMMARY:{escape_ics(resumen)}",
    ]
    if descripcion:
        lineas.append(f"DESCRIPTION:{escape_ics(descripcion)}")
    if ubicacion:
        lineas.append(f"LOCATION:{escape_ics(ubicacion)}")
    lineas.append("END:VEVENT")
    return "\r\n".join(plegar_linea(l) for l in lineas)


def leer_config(ruta):
    if not os.path.exists(ruta):
        print(f"ERROR: No se encontro {ruta}", file=sys.stderr)
        print("  Asegurate de que fechas.config.json este en la misma carpeta que este script.", file=sys.stderr)
        sys.exit(1)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def leer_itinerario(ruta):
    if not os.path.exists(ruta):
        print(f"ERROR: No se encontro {ruta}", file=sys.stderr)
        print("  Asegurate de que itinerario.csv este en la misma carpeta que este script.", file=sys.stderr)
        sys.exit(1)
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def es_tentativo(valor):
    return not valor or "TENTATIVO" in str(valor).upper()


def parsear_fecha_hora(fecha_str, hora_str, tzinfo):
    """Parsea 'YYYY-MM-DD' y 'HH:MM' y devuelve un datetime aware."""
    ano, mes, dia = map(int, fecha_str.strip().split("-"))
    h, m = map(int, hora_str.strip().split(":"))
    return datetime(ano, mes, dia, h, m, tzinfo=tzinfo)


def eventos_itinerario(filas, tz_china):
    eventos = []
    advertencias = 0
    for fila in filas:
        fecha_str = fila.get("Fecha", "").strip()
        bloque = fila.get("Bloque", "").strip()
        actividad = fila.get("Actividad", "").strip()
        lugar = fila.get("Lugar", "").strip()
        transporte = fila.get("Transporte", "").strip()
        tipo = fila.get("Tipo", "").strip()
        reserva = fila.get("Reserva", "").strip()
        notas = fila.get("Notas", "").strip()

        if not fecha_str or not actividad:
            continue

        try:
            ano, mes, dia = map(int, fecha_str.split("-"))
        except ValueError:
            print(f"ADVERTENCIA: Fecha invalida '{fecha_str}' — fila omitida.")
            advertencias += 1
            continue

        clave_bloque = _normalizar_bloque(bloque)
        hora, minuto = BLOQUES_HORA.get(clave_bloque, (9, 0))
        if clave_bloque not in BLOQUES_HORA:
            print(f"ADVERTENCIA: Bloque desconocido '{bloque}' en {fecha_str} — usando 09:00.")
            advertencias += 1

        dt_inicio = datetime(ano, mes, dia, hora, minuto, tzinfo=tz_china)
        dt_fin = dt_inicio + timedelta(hours=1)

        resumen = f"[{bloque}] {actividad}"
        descripcion = f"Transporte: {transporte} | Tipo: {tipo} | Reserva: {reserva}"
        if notas:
            descripcion += f"\nNotas: {notas}"

        eventos.append(crear_vevent(resumen, dt_inicio, dt_fin, descripcion, lugar))

    return eventos, advertencias


def eventos_vuelos(config, tz_china, tz_mexico):
    eventos = []
    vuelos_cfg = config.get("vuelos", {})

    definiciones = [
        ("salida_tijuana",             "Vuelo TIJ -> PEK (Hainan Airlines)",    tz_mexico, "hora_salida"),
        ("vuelo_interno_chengdu_shanghai", "Vuelo TFU -> PVG (domestico)",      tz_china,  "hora_salida"),
        ("salida_shanghai_pvg",        "Vuelo PVG -> LAX (regreso a casa)",      tz_china,  "hora_salida"),
    ]

    for clave, etiqueta, tzinfo, campo_hora in definiciones:
        v = vuelos_cfg.get(clave, {})
        fecha = v.get("fecha", "")
        hora_str = v.get(campo_hora, "")
        duracion = float(v.get("duracion_horas", 2))
        aerolinea = v.get("aerolinea", "")
        numero = v.get("numero_vuelo", "")
        clase = v.get("clase", "")

        if not fecha:
            continue

        if es_tentativo(hora_str):
            # Evento de marcador tentativo: ocupa todo el dia
            try:
                ano, mes, dia = map(int, fecha.split("-"))
            except ValueError:
                continue
            dt_inicio = datetime(ano, mes, dia, 0, 0, tzinfo=tzinfo)
            dt_fin = dt_inicio + timedelta(hours=23, minutes=59)
            desc = "Horario TENTATIVO. Actualizar fechas.config.json con el horario real y volver a correr el script."
            eventos.append(crear_vevent(f"[TENTATIVO] {etiqueta}", dt_inicio, dt_fin, desc))
            continue

        try:
            dt_inicio = parsear_fecha_hora(fecha, hora_str, tzinfo)
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo procesar vuelo '{clave}': {e}")
            continue

        dt_fin = dt_inicio + timedelta(hours=duracion)
        desc = f"Aerolinea: {aerolinea} | Vuelo: {numero} | Clase: {clase} | Duracion: {duracion}h"
        eventos.append(crear_vevent(etiqueta, dt_inicio, dt_fin, desc))

    return eventos


def eventos_trenes(config, tz_china):
    eventos = []
    trenes_cfg = config.get("trenes", {})

    definiciones = [
        ("beijing_xian", "Tren bala — Beijing -> Xi'an"),
        ("xian_chengdu", "Tren bala — Xi'an -> Chengdu"),
    ]

    for clave, etiqueta in definiciones:
        t = trenes_cfg.get(clave, {})
        fecha = t.get("fecha", "")
        hora_str = t.get("hora_salida", "")
        duracion = float(t.get("duracion_horas", 4))
        origen = t.get("estacion_origen", "")
        destino = t.get("estacion_destino", "")
        tren = t.get("tren", "")

        if not fecha:
            continue

        if es_tentativo(hora_str):
            try:
                ano, mes, dia = map(int, fecha.split("-"))
            except ValueError:
                continue
            dt_inicio = datetime(ano, mes, dia, 9, 0, tzinfo=tz_china)
            dt_fin = dt_inicio + timedelta(hours=duracion)
            desc = "Horario TENTATIVO. Reservar en 12306.cn o Trip.com ~30 dias antes y actualizar fechas.config.json."
            eventos.append(crear_vevent(f"[TENTATIVO] {etiqueta}", dt_inicio, dt_fin, desc, origen))
            continue

        try:
            dt_inicio = parsear_fecha_hora(fecha, hora_str, tz_china)
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo procesar tren '{clave}': {e}")
            continue

        dt_fin = dt_inicio + timedelta(hours=duracion)
        desc = f"Tren: {tren} | De: {origen} | A: {destino} | Duracion: {duracion}h"
        eventos.append(crear_vevent(etiqueta, dt_inicio, dt_fin, desc, origen))

    return eventos


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    ruta_config = os.path.join(base, "fechas.config.json")
    ruta_itinerario = os.path.join(base, "itinerario.csv")
    ruta_salida = os.path.join(base, "viaje.ics")

    config = leer_config(ruta_config)
    filas = leer_itinerario(ruta_itinerario)

    offset_china = config.get("utc_offset_china", 8)
    offset_mexico = config.get("utc_offset_mexico_verano", -7)
    tz_china = tz_fijo(offset_china)
    tz_mexico = tz_fijo(offset_mexico)

    todos_eventos = []

    ev_itinerario, advertencias = eventos_itinerario(filas, tz_china)
    todos_eventos.extend(ev_itinerario)

    todos_eventos.extend(eventos_vuelos(config, tz_china, tz_mexico))
    todos_eventos.extend(eventos_trenes(config, tz_china))

    cabecera = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Viaje China 2027//Nadia y Roberto//ES\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "X-WR-CALNAME:Viaje China 2027\r\n"
        "X-WR-TIMEZONE:Asia/Shanghai\r\n"
    )
    pie = "END:VCALENDAR\r\n"
    cuerpo = "\r\n".join(todos_eventos)
    contenido = cabecera + cuerpo + "\r\n" + pie

    with open(ruta_salida, "w", encoding="utf-8", newline="") as f:
        f.write(contenido)

    print(f"viaje.ics generado con {len(todos_eventos)} eventos.")
    if advertencias:
        print(f"  ({advertencias} advertencias — revisar la salida arriba)")
    print(f"  Archivo: {ruta_salida}")
    print()
    print("Para importar a Google Calendar:")
    print("  calendar.google.com -> Configuracion (engrane) -> Importar -> seleccionar viaje.ics")
    print()
    print("Para importar a Apple Calendar:")
    print("  Doble clic sobre viaje.ics -> confirmar en el dialogo")


if __name__ == "__main__":
    main()
