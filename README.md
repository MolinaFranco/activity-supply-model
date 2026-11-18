# activity-supply-model

Diseño de un modelo de relación explícito entre las actividades a campo de una
plataforma agrícola (siembra, fertilización, pulverización, tratamiento) y los
insumos que consumen.

Es la respuesta a un challenge técnico de modelado de datos. El challenge es de
diseño: el código es ilustrativo, expresa el criterio y no está pensado para correr.

| # | Entregable | Archivo |
|---|---|---|
| 1 | Modelo de datos | [`entregable/1_modelo.sql`](entregable/1_modelo.sql) |
| 2 | Código ilustrativo del CRUD | [`entregable/2_crud.py`](entregable/2_crud.py) |
| 3 | Payloads de los 5 tipos | [`entregable/3_payloads.md`](entregable/3_payloads.md) |
| 4 | Respuesta nueva del tab Datos | [`entregable/4_tab_datos_after.json`](entregable/4_tab_datos_after.json) |
| 5 | Decisiones y trade-offs | este README |

Además:

- [`docs/enunciado.md`](docs/enunciado.md): el enunciado original.
- [`docs/presentacion.html`](docs/presentacion.html): la solución en formato de
  presentación. Se abre en el navegador.
- [`docs/proceso/`](docs/proceso/README.md): cómo se llegó a este diseño, con las
  alternativas que se consideraron y se descartaron.

---

## La idea

```
Actividad                   SPO (SUPPLYOUTPUT)              Inventario
  item (id, nombre, dosis)    parent_id ──→ actividad
           ▲                  record (insumo, cantidad,
           └──── item_id ─────        item_id)  ──────────→ insumo
```

| Palabra | Qué es |
|---|---|
| Actividad | Un registro de Siembra, Fertilización, Pulverización o Tratamiento |
| Item | Un renglón de una actividad: nombre del producto y dosis |
| SPO | Un registro `SUPPLYOUTPUT`: un uso de insumo |
| Record | Un renglón de un SPO: id de un insumo y cantidad |
| Insumo | Un producto del inventario |

El enunciado cuenta al SPO como el quinto tipo de actividad. Lo trato como una
actividad que puede cargarse sola, o como parte de otra que la necesita para
realizarse: toda siembra, fertilización, pulverización o tratamiento consume
insumos, y ese consumo es un SPO.

Hoy cada record ya dice qué insumo es, pero nada dice a qué actividad pertenece
ese SPO ni a qué item corresponde cada record. La solución agrega esas dos
referencias.

## El modelo

Tres datos nuevos:

1. **Cada item tiene un id.** Antes un item era solo una posición en una lista.
2. **El SPO guarda a qué actividad pertenece** (`parent_id`). Vacío si es suelto.
3. **Cada record guarda a qué item corresponde** (`item_id`).

Y una tabla, `supply_output_record`, con **una fila por cada record**: el
insumo, la cantidad, la unidad y el item, en columnas. Es una copia de lo que
el record dice en el JSON, y se reescribe cada vez que se guarda el SPO.

La copia existe porque respeto los tipos del enunciado, que guardan los records
dentro del JSON. No es lo que haría con libertad total: ver «Sin datos
repetidos» en las mejoras.

**Por qué queda consultable sin recorrer el JSON:** la actividad de un SPO es
una columna con índice, y el insumo y la cantidad de cada record también son
columnas. «Qué insumos consumió esta actividad, en qué unidad y cuánto» es
buscar su SPO por `parent_id` y leer sus filas. «En qué actividades se usó este
insumo» es un filtro por `supply_id`. Con la cantidad y el insumo en columnas
queda la base para imputar el costo.

## Cuándo hay link

| Situación | Qué pasa |
|---|---|
| El usuario elige un insumo del inventario al cargar la actividad | Se crean el item y su record, y el record guarda el id del item |
| Un SPO que ya existía se asocia a una actividad | Regla del enunciado: hay link solo si el nombre del item es el mismo que el del insumo |
| El producto es texto libre, sin insumo elegido | No hay record. No hay link |

El enunciado pide link únicamente cuando el nombre coincide. Cambié esa regla
porque no me parecía útil en un sistema grande: para que escale hace falta
trabajar con ids. Además, así queda la libertad de poner otros nombres en los
items (por ejemplo «Urea3» para el insumo «Urea»): el nombre queda en el item y
el id del insumo en el record, sin duplicar nada.

**Un item sin SPO no tiene link**, aunque su nombre coincida con el de un
insumo. Sin SPO no hay consumo registrado: no hay cantidad ni unidad que
relacionar. El modelo los deja a la vista: son los items a los que ningún
record apunta.

## Criterio de CRUD

Los links son datos, no cálculos. Por eso editar no recalcula nada.

- **Crear una actividad.** En una transacción se guarda la actividad y, si se eligieron
  insumos del inventario, su SPO: con la actividad en `parent_id` y un
  record por insumo, cada uno con su `item_id`.
- **Actualizar una actividad.** Se guarda. Si el form manda los insumos,
  reemplazan a los anteriores. Si no los manda, el SPO queda como está, salvo
  los records de items que ya no existen.
- **Actualizar un SPO.** Se guarda, y conserva su actividad y sus items.
- **Crear un SPO suelto.** El mismo camino, sin actividad.
- **Borrar.** Dar de baja una actividad da de baja su SPO.

**¿La actividad es fuente de verdad sobre sus insumos?** Sí sobre sus items: lo
que se aplicó y a qué dosis. El SPO lo es sobre lo consumido: qué insumo y
cuánto. No hay información repetida entre los dos; lo único que comparten es el
link. Por eso se puede corregir la cantidad de un SPO sin contradecir a la
actividad.

Hay un solo camino para escribir un SPO, y ese camino es el que mantiene la
tabla.

## Tab «Datos»

- Cada actividad conserva todos sus campos y suma `supply_output`: su uso de
  insumos, con cada insumo ya resuelto (nombre, cantidad, unidad y el item al
  que corresponde).
- **Un SPO que pertenece a una actividad deja de ser una fila propia**, para no
  mostrarlo dos veces. La página lista todo lo que no tiene `parent_id`, y
  `total` cuenta lo mismo: pasa de 6 a 4.
- Los insumos de todas las actividades de la página salen de una sola consulta.
- **Un SPO suelto sigue como fila propia**, igual que hoy. El apéndice lo
  muestra («Se utilizó el insumo Maíz»); en el «antes» no queda ninguno.
- El «antes» es una muestra incompleta: la siembra y la pulverización tienen
  items que consumen insumos pero no traen su uso. En el «después» aparecen con
  su SPO, como quedan al crearlas con este modelo. Sus cantidades son ilustrativas.

## Decisiones y trade-offs

| Decisión | Qué gano | Qué cuesta | Alternativa descartada |
|---|---|---|---|
| El SPO guarda su actividad | Una sola referencia, en un solo lugar. El feed filtra directo | Una columna nueva en structured data | Guardarla en cada record: permite un SPO a medio linkear |
| Cada item tiene un id | El link no se rompe si se reordena o se borra un item | Un campo nuevo en cada item | Identificar el item por su posición en la lista |
| El record guarda su item | El link es un dato: editar no recalcula nada | Un campo nuevo en el record | Emparejar por nombre al leer: se rompe con «Urea3» / «Urea» |
| Copiar los records a una tabla | Consultas por actividad y por insumo, sin abrir el JSON | El record queda en dos lugares. Es el precio de respetar los tipos del enunciado; lo cubre el único camino de escritura | Reemplazar el JSON por tablas: es lo que haría con libertad total, pero cambia los tipos dados (ver mejoras) |
| Un solo SPO por actividad, con índice único en `parent_id` | Lo garantiza la base, no el código: ni un error ni dos guardados a la vez dejan dos SPO | Hoy no admite varios SPO por actividad. Es fácil de cambiar: se quita el índice y el resto del modelo queda igual | Controlarlo solo en el código: nada impide que queden dos |
| El id del insumo está solo en el record | El item guarda lo que escribió el usuario; no hay datos repetidos | Un item sin SPO no tiene insumo asociado | Agregar el insumo también al item: dos lugares que pueden contradecirse |

## Supuestos

Lo que el enunciado no define y tomé como dado:

- El inventario tiene, por cada insumo, un id, un nombre y una unidad.
- Al cargar una actividad, cada producto elegido del inventario genera un
  record en su SPO. El apéndice lo muestra para la pulverización; lo extiendo a
  los otros tipos.
- **Una actividad tiene un solo SPO**, con un record por producto. En el «antes»
  y en el apéndice también es uno solo.
- El id de cada item se genera automáticamente.
- «Mismo nombre» es igualdad exacta.

## Puntos a tener en cuenta

- **El lote.** Lo único que podría pedir más de un SPO por actividad es el lote:
  el SPO tiene un solo `lote` y una actividad puede tener hasta 5. Pero ese
  campo es opcional, y el enunciado no pide separar el consumo por lote. Si
  hiciera falta, se quita la unicidad de `parent_id` y el resto no cambia.
- **Otros caminos de escritura.** La tabla es correcta mientras todo SPO se
  guarde por el mismo camino. Una importación que escriba el JSON directo
  tendría que pasar por ahí.

## Agregado mío: baja lógica

El enunciado no la pide. La sumo porque dar de baja una actividad arrastra su
SPO, y prefiero que esos datos no se pierdan.

- Se marca `deleted_at` en la entry, sea actividad o SPO. No se borra.
- La marca vive en un solo lugar. La tabla de records solo tiene lo vivo: al dar
  de baja un SPO se quitan sus filas, y su JSON queda guardado.
- No hay una operación para deshacer. Recuperar algo es un trabajo manual.

---

## Posibles mejoras (fuera de lo pedido)

### Sin datos repetidos: tablas en lugar de JSON

En el challenge respeto los tipos que nos dieron: los items viven dentro del
JSON de la actividad y los records dentro del JSON del SPO. Por eso hace falta
una copia de los records para poder consultarlos.

Si pudiera organizar el almacenamiento a mi criterio, sacaría esas listas del
JSON y las pasaría a tablas propias:

| Tabla | Qué guarda | Reemplaza a |
|---|---|---|
| `activity_item` | Un item: su actividad, de qué tipo es, nombre, dosis y unidad | `fertilizers[]`, `treatments[]`, `products[]` y la genética |
| `supply_output_record` | Un record: su SPO, el insumo, la cantidad, la unidad y su item | `records[]` |

El JSON de cada registro se quedaría solo con lo propio: fecha, lotes, nota.

- **Qué se gana.** Cada dato está en un solo lugar y no hay copia que mantener.
  `item_id` pasa a ser una clave foránea real, cosa que hoy no puede ser porque
  el item vive dentro de un JSON. La relación muchos a muchos entre actividades
  e insumos queda resuelta con tablas intermedias de verdad.
- **Qué cuesta.** Cambia los cinco tipos del enunciado, hay que migrar todo lo
  ya cargado, y cambia todo lo que hoy lee `fertilizers[]` o `records[]` del JSON.
- **Por qué no lo hago acá.** El enunciado da esos tipos como base y pide
  construir la relación sobre structured data. El modelo que entrego es el paso
  previo: los ids de item y las referencias ya son los que usarían esas tablas.

### Otras

- **Linkear lo ya cargado.** Una migración única que recorre los SPO existentes
  y los asocia con la regla por nombre.
- **Sugerir insumos parecidos.** Si el usuario escribe «Urea 3», mostrarle los
  insumos del inventario con nombre más cercano para que elija uno.
- **Crear el insumo si no existe.** Ofrecer crearlo en el momento, desde el form.
- **Costo por actividad.** La cantidad de cada record por el costo unitario del insumo.
- **Stock.** Cada SPO descuenta stock; el challenge no pide manejarlo.
