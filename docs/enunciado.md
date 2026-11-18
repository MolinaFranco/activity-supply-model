> Enunciado original del challenge, tal como fue recibido. Las capturas del apéndice no están
> incluidas: en su lugar queda la descripción de cada una.

Challenge técnico · Backend / Modelado de datos

# Modelado de actividades e insumos

Diseñá, desde cero, un modelo de relación explícito entre las actividades a campo y los insumos que consumen — sobre structured data.

**Foco:** diseño de datos **Formato:** diseño en papel **Código:** ilustrativo, no corre **Entregable:** esquema + payloads + README

## Contexto

Trabajamos en una plataforma de gestión agrícola donde los productores registran operaciones a campo. Una operación típica es una **actividad** — una siembra, una fertilización, una pulverización — y cada actividad consume **insumos**: semilla, fertilizante, agroquímico, etc.

Hoy, actividades e insumos viven como *structured data* completamente independientes: no están asociados de ninguna manera. Son dos conjuntos de datos sueltos, sin ningún vínculo entre una entidad y la otra.

El challenge consiste en diseñar e implementar, desde cero, un **modelo de relación explícito** entre estas dos entidades.

## El problema a resolver

Sin una relación, no hay forma de saber qué insumos consumió una actividad, ni de derivar información que dependa de ese vínculo: qué unidad corresponde a cada insumo dentro de la actividad, cuánto se aplicó, o cómo imputar el costo.

Queremos que en structured data la relación entre actividad e insumo sea **explícita, robusta y consultable** — construida desde el modelo de datos, no inferida en tiempo de lectura recorriendo el JSON a mano.

## Qué se linkea en cada actividad

Trabajá solo con estos tipos de actividad. Dentro de cada una, estos son los items que deben tener insumos asociados:

| Actividad | Structure | Items con insumo |
| --- | --- | --- |
| Siembra | `Plantation` | `fertilizers[]` + `details.genetic_variety` (la genética) |
| Fertilización | `Fertilization` | `fertilizers[]` |
| Pulverización | `Pulverization` | `treatments[]` |
| Tratamiento | `TREATMENT` | `products[]` |
| Supply output | `SUPPLYOUTPUT` | `records[]` |

Regla de matching

El link entre un item de la actividad y un insumo existe **únicamente cuando el nombre coincide**: el nombre del item (`source` / `name` / `genetic_variety`) tiene que ser el **mismo** que el del insumo. Si difieren, no hay link.

## Schemas de referencia

Cada entry de structured data (toda actividad, incluido el `SUPPLYOUTPUT`) tiene su propio `id` **UUID** único y distinto. Es todo lo que necesitás saber sobre `BaseStructure` / `BaseModel` — y es la pieza sobre la que vas a colgar la relación.

plantation.py — Plantation (siembra)

```
class Details(BaseModel):
    genetic_variety: Optional[str] = None
    spacing: Optional[float] = None

class Density(BaseModel):
    density: Optional[float] = None
    density_units: Optional[Literal["seeds/ha", "plants/ha", "kg/ha"]] = None

class Fertilizer(BaseModel):
    source: Optional[str] = None
    dosage: Optional[float] = None
    dosage_units: Optional[Literal["L/ha", "kg/ha"]] = None

class Plantation(BaseStructure):
    basic_info: BasicInfo                # record_date, crop_category
    fields: list[FieldRefRequired]       # 1..5 lotes
    details: Optional[Details] = None    # details.genetic_variety = genética
    density: Optional[Density] = None
    fertilizers: list[Fertilizer] = []   # max 5
    contractor: Optional[str] = None
    note: Optional[str] = None
```

fertilization.py — Fertilization

```
class Fertilizer(BaseModel):
    source: str
    dosage: Optional[float] = None
    dosage_units: Optional[Literal["L/ha", "kg/ha"]] = None

class Fertilization(BaseStructure):
    basic_info: BasicInfo
    fields: list[FieldRefRequired]       # 1..5 lotes
    contractor: Optional[str] = None
    fertilizers: list[Fertilizer]        # min 1, max 5
    note: Optional[str] = None
```

pulverization.py — Pulverization

```
class Treatment(BaseModel):
    source: str
    dosage: float
    dosage_units: Literal["L/ha", "g/ha", "kg/ha", "cc/ha"]

class Pulverization(BaseStructure):
    basic_info: BasicInfo
    fields: list[FieldRefRequired]       # 1..5 lotes
    contractor: Optional[str] = None
    treatments: list[Treatment]          # min 1, max 5
    note: Optional[str] = None
```

cattle.py — TREATMENT (tratamiento hacienda)

```
class TreatmentProduct(BaseModel):
    name: Optional[str] = None
    dosage: Optional[float] = None
    dosage_units: Optional[Literal["ml", "cc", "g", "kg", "L"]] = None

class TreatmentAnimalRef(BaseModel):
    animal_category_id: Optional[int] = None
    animal_category_name: Optional[str] = None
    head_count: Optional[int] = None
    weight: Optional[float] = None
    herd_id: Optional[str] = None

class TREATMENT(BaseStructure):
    record_date: str
    treatment: str
    products: Optional[list[TreatmentProduct]] = None    # 0..5
    animals: Optional[list[TreatmentAnimalRef]] = None   # 0..5
    fields: Optional[list[FieldRefNoHectares]] = None    # 0..5 lotes, sin hectáreas
    note: Optional[str] = None
```

supplies.py — SUPPLYOUTPUT (uso de insumo)

```
class BasicInfo(BaseModel):
    record_date: str
    lote: Optional[str] = None

class Record(BaseModel):
    supply_id: Optional[str]             # ref al insumo de inventario
    quantity: float
    unit: Optional[int] = None           # no editable, derivado del supply

class SUPPLYOUTPUT(BaseStructure):
    basic_info: BasicInfo
    records: list[Record] = []           # min 1, max 20
    note: Optional[str] = None
```

## Lo que pedimos

Diseñá e implementá un modelo de relación entre actividades e insumos sobre structured data, considerando:

### Relación consultable

El modelo tiene que poder consultarse de forma eficiente, **sin recorrer el JSON de structured data a mano**. Pensá qué necesitás persistir para que eso sea posible.

### Criterio de CRUD

Qué ocurre con la relación cuando se **crea** una actividad, cuando se **actualiza** (¿la actividad es fuente de verdad sobre sus insumos?), y cuando se **borra**.

## Capa BFF — el tab «Datos»

La web tiene un tab **Datos**: un feed cronológico y paginado de todo lo que se cargó en un campo. Cada fila es un *record summary*. El endpoint devuelve una lista plana; el front la renderiza tal cual.

Así respondía el endpoint **ANTES** del linkeo: una fila por cada actividad, y al final los `SUPPLYOUTPUT` (los usos de insumo). Todas **filas independientes**, sin nada que las vincule entre sí:

GET /record-summaries — respuesta ANTES

```
{
  "data": [
    {
      "record_locator": "sd-siembra-001",
      "table_name": "structured_data",
      "detail": "PLANTATION",
      "record_date": "2026-03-10",
      "summary": "Siembra — Lote Norte — Maíz DK7210",
      "structure": {
        "name": "Siembra",
        "lote_names": ["Lote Norte"],
        "keys": { "Cultivo": "Maíz", "Genética": "DK7210", "Fertilizante": "Fosfato diamónico" }
      }
    },
    {
      "record_locator": "sd-fert-002",
      "table_name": "structured_data",
      "detail": "FERTILIZATION",
      "record_date": "2026-03-12",
      "summary": "Fertilización — Lote Sur — Urea 10 kg/ha",
      "structure": {
        "name": "Fertilización",
        "lote_names": ["Lote Sur"],
        "keys": { "Cultivo": "Trigo", "Fertilizante": "Urea", "Dosis": "10 kg/ha" }
      }
    },
    {
      "record_locator": "sd-pulv-003",
      "table_name": "structured_data",
      "detail": "PULVERIZATION",
      "record_date": "2026-03-14",
      "summary": "Pulverización — Lote Sur — Glifosato 2 L/ha",
      "structure": {
        "name": "Pulverización",
        "lote_names": ["Lote Sur"],
        "keys": { "Producto": "Glifosato", "Dosis": "2 L/ha" }
      }
    },
    {
      "record_locator": "sd-trat-004",
      "table_name": "structured_data",
      "detail": "TREATMENT",
      "record_date": "2026-03-15",
      "summary": "Tratamiento — Vaquillonas — Ivermectina",
      "structure": {
        "name": "Tratamiento",
        "keys": { "Tratamiento": "Antiparasitario", "Producto": "Ivermectina", "Categoría": "Vaquillonas" }
      }
    },

    // --- usos de insumo (SUPPLYOUTPUT): hoy son filas sueltas ---
    {
      "record_locator": "sd-supply-777",
      "table_name": "structured_data",
      "detail": "SUPPLYOUTPUT",
      "record_date": "2026-03-12",
      "summary": "Uso de insumos — Urea 100 kg",
      "structure": {
        "name": "Uso de Insumos",
        "lote_names": ["Lote Sur"],
        "keys": { "Insumo": "Urea", "Cantidad": "100 kg" }
      }
    },
    {
      "record_locator": "sd-supply-778",
      "table_name": "structured_data",
      "detail": "SUPPLYOUTPUT",
      "record_date": "2026-03-15",
      "summary": "Uso de insumos — Ivermectina 500 ml",
      "structure": {
        "name": "Uso de Insumos",
        "keys": { "Insumo": "Ivermectina", "Cantidad": "500 ml" }
      }
    }
  ],
  "total": 6,
  "new_records": 0
}
```

Nada en `sd-supply-777` dice que pertenece a `sd-fert-002`, ni `sd-supply-778` a `sd-trat-004`. Para el front son todos eventos sueltos.

Lo que pedimos

Proponé cómo debería ser el **after**: un mock de la respuesta nueva donde la actividad padre venga con sus insumos **ya resueltos**, lista para que el front la consuma sin reconstruir la relación. Con el JSON y una breve justificación alcanza.

## Qué evaluamos

- **Diseño del modelo de datos** — claridad y solidez del esquema de relación.
- **Criterio de CRUD** — qué pasa al crear, actualizar y borrar una actividad.
- **Criterio de producto** — que entiendas *por qué* se modela así y puedas defender los trade-offs.

## Entregable

Este challenge es de **diseño**. Queremos ver **código como forma de expresar ese diseño**, pero **no tiene que correr** (sin repo, sin setup): definiciones de esquema, modelos, firmas de funciones y snippets ilustrativos que dejen el criterio explícito.

1. **El modelo de datos** de la relación actividad↔insumo, como esquema/modelos: tabla(s), campos, tipo de relación, claves, índices. Qué se persiste y por qué queda consultable sin recorrer el JSON.
2. **Código ilustrativo del CRUD** — firmas + cuerpo esquemático de qué pasa al crear y actualizar una actividad (cómo se escribe/reconcilia la relación). No hace falta que compile.
3. **Payloads de ejemplo** que muestren el modelo sobre los 5 tipos de actividad.
4. **El mock de la respuesta nueva del tab Datos**, partiendo del «antes» que te damos.
5. **Un README** con las decisiones de diseño y los trade-offs.

No buscamos cobertura completa ni una solución pulida de punta a punta: nos interesa el **criterio de diseño** y cómo razonás los trade-offs.

---

No buscamos que cubras todos los tipos ni una solución de punta a punta. Nos interesa el criterio y el razonamiento.

## Apéndice — capturas de la web

Contexto visual de cómo se ve hoy en la web la carga de una pulverización con un producto del inventario, y cómo aparece después en el tab «Datos».

> _Captura (no incluida en este repo):_ Formulario de Pulverización vacío, con el link «Seleccionar de inventario» dentro del campo Producto.

A.1 · Formulario de pulverizaciónAl cargar un dato de Pulverización, el campo **Producto** acepta texto libre o un insumo elegido con «Seleccionar de inventario».

> _Captura (no incluida en este repo):_ Desplegable con los insumos del inventario, cada uno con foto y unidad (Litros, Kilos, Metros, etc.).

A.2 · Selector de inventarioEl desplegable lista los insumos del campo con su unidad (Litros, Kilos, Metros, Rollos…).

> _Captura (no incluida en este repo):_ Producto 2,4-d con dosis 2 L/ha y el bloque «Descontar del inventario de insumos» marcado con 50 Litros.

A.3 · Descontar del inventarioElegido el insumo (`2,4-d`, 2 L/ha), aparece «Descontar del inventario de insumos» con la cantidad total a descontar (50 Litros).

> _Captura (no incluida en este repo):_ Tab Datos: la pulverización en el potrero Corral con una fila hija «Se utilizó el siguiente insumo en el potrero Corral: 2,4-d (50 Litros)».

A.4 · Tab «Datos»La pulverización aparece en el feed y, debajo, el uso de insumo asociado como fila hija: «Se utilizó el siguiente insumo en el potrero Corral: 2,4-d (50 Litros)». El resto de los `SUPPLYOUTPUT` (por ejemplo, «Se utilizó el insumo Maíz») siguen como filas sueltas.