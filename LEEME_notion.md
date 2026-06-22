# LEEME — Importar a Notion y Generar Calendario

---

## 1. Importar `guia.md` como página de Notion

1. Abrir Notion y crear una página nueva (clic en `+` en la barra lateral).
2. Hacer clic en los tres puntos `...` de la página → **Import** → **Markdown & CSV**.
3. Seleccionar el archivo `guia.md`.
4. Notion importará el archivo con todos los encabezados, tablas y listas de verificación.
5. Renombrar la página a **Guía China 2027** y moverla al espacio de trabajo deseado.

> Algunas listas de verificación (`- [ ]`) pueden importarse como texto plano. Si es así, convertirlas manualmente a bloques "To-do" en Notion seleccionando el texto y cambiando el tipo de bloque.

---

## 2. Importar `itinerario.csv` como base de datos

1. Crear una página nueva en Notion → **Import** → **CSV**.
2. Seleccionar `itinerario.csv`. Notion crea automáticamente una base de datos con todas las columnas.
3. **Configurar la columna `Fecha`:**
   - Hacer clic en el encabezado `Fecha` → cambiar el tipo de propiedad a **Date**.
   - Formato: `YYYY/MM/DD` o el preferido.
4. **Crear vista Calendario:**
   - En la barra superior de la base de datos clic en `+ Add a view` → seleccionar **Calendar**.
   - Configurar para que use la propiedad `Fecha` como campo de fecha.
5. **Crear vista Timeline (Gantt):**
   - `+ Add a view` → **Timeline**.
   - Start date: `Fecha`. End date: `Fecha`. Agrupar por: `Ciudad`.
6. **Tip útil:** Crear un filtro para ocultar las filas donde `Ciudad` sea "En tránsito" cuando se quiere ver solo las actividades en China.

---

## 3. Importar `hoteles.csv` como base de datos

1. Nueva página → **Import** → **CSV** → seleccionar `hoteles.csv`.
2. Ajustes después de importar:
   - `Noches`: cambiar tipo a **Number**.
   - `Cocina` y `Gym`: cambiar tipo a **Checkbox** (Sí = marcado).

---

## 4. Importar `restaurantes.csv` como base de datos

1. Nueva página → **Import** → **CSV** → seleccionar `restaurantes.csv`.
2. Ajustes después de importar:
   - `Michelin`: cambiar tipo a **Select** con opciones (Bib Gourmand, 1 estrella, Recomendado, No Michelin).
   - `Reserva`: cambiar tipo a **Select** (Sí, No, Sí — URGENTE).
   - `Anticipacion_reserva`: dejar como texto o cambiar a **Select** — contiene el tiempo exacto (ej. "4-6 semanas antes") y también cuándo ir si no se reserva.
   - `Picante` y `Apto_sin_pescado`: cambiar tipo a **Checkbox**.

---

## 5. Calendario .ics — LEER ESTO ANTES DE CORRER EL SCRIPT

> **NO correr `generar_calendario.py` todavía.**
>
> Las fechas y horarios de vuelo en `fechas.config.json` son **TENTATIVOS**.
> El script funcionará, pero los eventos de vuelo aparecerán marcados como `[TENTATIVO]`
> y ocuparán días completos sin hora real.
>
> **Esperar a comprar los boletos de avión antes de generar el calendario definitivo.**

---

### Cuándo y cómo generar el calendario

**Paso 1 — Comprar los boletos de avión y trenes**

Una vez que tengan los boletos comprados (TIJ→PEK, PVG→LAX, TFU→PVG, y los trenes bala), continuar con los siguientes pasos.

**Paso 2 — Editar `fechas.config.json`**

Abrir el archivo `fechas.config.json` con cualquier editor de texto (TextEdit, Notepad, VS Code) y reemplazar **todos los valores que digan `"TENTATIVO"`** con los datos reales:

```json
"hora_salida": "22:30",
"numero_vuelo": "HU7986",
"aerolinea": "Hainan Airlines"
```

Guardar el archivo cuando terminen.

**Paso 3 — Correr el script**

Abrir una terminal (o Command Prompt en Windows) en la carpeta donde están los archivos y ejecutar:

```bash
python3 generar_calendario.py
```

En Windows puede ser necesario usar `python` en lugar de `python3`. Python 3.6 o superior es suficiente — no se necesita instalar ninguna librería adicional.

El script generará el archivo **`viaje.ics`** en la misma carpeta.

**Paso 4 — Importar `viaje.ics` a Google Calendar**

1. Ir a [calendar.google.com](https://calendar.google.com).
2. Hacer clic en el ícono de engrane (⚙) → **Configuración**.
3. En el menú lateral: **Importar y exportar** → **Importar**.
4. Seleccionar el archivo `viaje.ics`.
5. Elegir el calendario de destino (recomendado: crear uno nuevo llamado "Viaje China 2027").
6. Hacer clic en **Importar**.

**Paso 4 (alternativa) — Importar `viaje.ics` a Apple Calendar**

1. Asegurarse de que el archivo `viaje.ics` esté en el Mac o iPhone.
2. Doble clic sobre `viaje.ics`.
3. Apple Calendar abrirá un diálogo preguntando en qué calendario importar.
4. Seleccionar el calendario deseado y confirmar.

---

### Si necesitan regenerar el calendario

Si después de importar descubren un error en las fechas o quieren actualizar algo:

1. Editar `fechas.config.json` con el cambio correcto.
2. Correr `python3 generar_calendario.py` de nuevo — sobrescribirá el `viaje.ics` anterior.
3. En Google Calendar: eliminar primero los eventos anteriores del calendario "Viaje China 2027" y luego volver a importar el nuevo `viaje.ics`.

---

## Resumen de todos los archivos

| Archivo | Para qué | Importar en |
|---|---|---|
| `guia.md` | Guía de referencia completa | Notion (Import → Markdown) |
| `itinerario.csv` | Base de datos día a día | Notion (Import → CSV) → vista Calendario |
| `hoteles.csv` | Base de datos de hoteles | Notion (Import → CSV) |
| `restaurantes.csv` | Base de datos de restaurantes | Notion (Import → CSV) |
| `fechas.config.json` | Fechas y horarios de vuelos | Editar cuando se compren boletos |
| `generar_calendario.py` | Script generador del calendario | Correr con Python 3 después de editar el config |
| `viaje.ics` | Calendario generado | Google Calendar o Apple Calendar |
