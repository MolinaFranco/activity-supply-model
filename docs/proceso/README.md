# Cómo se llegó a este diseño

La solución final está en el [README del repo](../../README.md). Esta carpeta
guarda el camino: lo que se leyó primero, las opciones que se compararon y por
qué el modelo fue cambiando.

| Archivo | Qué es |
|---|---|
| [`analisis_inicial.md`](analisis_inicial.md) | Primera lectura del enunciado: requisitos, puntos finos, opciones y preguntas |
| [`opciones.html`](opciones.html) | Comparación de las cuatro opciones iniciales, con sus preguntas. Se abre en el navegador |
| [`modelos_base.py`](modelos_base.py) | Los schemas del enunciado, extraídos tal cual como punto de partida |

Los dos primeros son documentos de trabajo y quedaron como estaban. Describen
modelos que después se descartaron.

## Las tres preguntas que definieron todo

**1. ¿Qué es «insumo» en la relación actividad ↔ insumo?**
El enunciado admite dos lecturas: el producto del inventario, o el uso de
insumo (`SUPPLYOUTPUT`). La primera lleva a linkear cada item directo contra el
inventario. La segunda pone al `SUPPLYOUTPUT` en el medio. Se eligió la segunda:
el enunciado dice que la relación se cuelga del UUID de cada entry de
structured data, y el insumo del inventario no es una entry.

**2. ¿Cómo se identifica un item?**
Los items de una actividad son elementos de una lista dentro de un JSON, sin
identificador. Se probó con la posición en la lista y con el nombre. Las dos
se rompen: la posición cambia si se reordena, y el nombre no es único. Se
terminó agregando un id a cada item.

**3. ¿Qué hacer con la regla de matching por nombre?**
El enunciado pide link únicamente cuando el nombre coincide. Es frágil para un
sistema grande y no deja escribir un nombre distinto al del inventario. Se
reemplazó por ids, y la regla por nombre quedó para asociar un uso que ya
existía.

## Cómo fue cambiando el modelo

| Etapa | Modelo | Por qué se cambió |
|---|---|---|
| 1 | Tabla de links item → insumo, con match por nombre al guardar | El nombre como criterio era frágil |
| 2 | El item guarda el id del insumo; el link es por id | El insumo quedaba en dos lugares: en el item y en el uso |
| 3 | Dos estructuras: una fila por item para los cinco tipos, más una referencia del uso a su actividad | Era más de lo que pedía el problema, y mezclaba dosis y cantidad en filas distintas |
| 4 | Una sola tabla que unía un item con un record, emparejados por nombre | Exigía recalcular los links en cada edición, y editar un uso podía romperlos |
| 5 | **Final.** Tres datos (id del item, actividad del uso, item del record) y una tabla con los records en columnas | Los links pasan a ser datos: editar no recalcula nada |

## Opciones generales que se compararon al principio

| Opción | Idea | Por qué no |
|---|---|---|
| Referencia embebida en el JSON | Guardar los ids dentro del documento y consultarlos con índices sobre el JSON | Sin claves foráneas, y un índice por cada consulta |
| Proyección por eventos | Un proceso aparte arma los links después de cada cambio | Consistencia eventual y más infraestructura, para un problema que se resuelve al guardar |
| Tabla genérica de relaciones | Una tabla de aristas para cualquier vínculo entre entries | Cantidad y unidad terminan en un campo sin tipar: vuelve al problema original |
| Tabla de links (elegida) | Persistir la relación en columnas, al guardar | Es la base de la solución final |

## Lo que se probó y quedó afuera

- **Un casillero «descontado» en el uso.** Servía para registrar un uso sin
  mover el stock. Se sacó: el challenge no pide manejar stock.
- **Un uso por lote.** Se llegó a repartir la cantidad entre lotes por
  hectáreas. Se sacó: el enunciado no pide separar el consumo por lote. Quedó
  como punto a tener en cuenta.
- **Control de concurrencia.** Fuera de alcance para un diseño que se pedía simple.
- **Reemplazar el JSON por tablas.** Es lo que se haría con libertad total.
  Quedó como la mejora principal, porque cambia los tipos que da el enunciado.

## Revisión

Antes de cerrar, el diseño se revisó contra el enunciado desde tres ángulos:
como lo haría quien corrige el challenge, como revisión técnica del esquema y
del CRUD, y con una lectura a ciegas del enunciado para comparar
interpretaciones. De ahí salieron la simplificación de la etapa 5, la consulta
del feed y la garantía de un solo uso por actividad.
