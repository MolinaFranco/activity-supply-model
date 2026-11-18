# 3 · Payloads de ejemplo

Parten de los registros del «antes» del enunciado. Cada ejemplo muestra la
actividad y su SPO como quedan guardados. Al final están las filas que generan
en `supply_output_record`.

El «antes» es una muestra incompleta: la siembra y la pulverización tienen
items que consumen insumos, pero no traen su uso cargado. Acá se completan con
el SPO que les corresponde (`sd-supply-775` y `sd-supply-776`).

Convenciones:
- Los `id` están abreviados para leerlos; en la base son UUID.
- Los `supply_id`, los valores de `unit` y las cantidades de los dos SPO
  agregados son ilustrativos: el enunciado no da el inventario, el enum de
  unidades ni esas cantidades.
- El enunciado no define la forma de `FieldRefRequired`; se muestra solo el nombre del lote.
- `parent_id` es una columna de la entry, no parte de su JSON. Se muestra junto
  al `id` para leerlo de corrido.
- Lo nuevo está marcado con `// ←`.

---

## 1. Siembra · `Plantation`

```jsonc
{
  "id": "sd-siembra-001",
  "basic_info": { "record_date": "2026-03-10", "crop_category": "Maíz" },
  "fields": [{ "name": "Lote Norte" }],
  "details": {
    "genetic_variety": "DK7210",
    "genetic_variety_id": "it-dk7210"                    // ← id del item
  },
  "fertilizers": [
    { "id": "it-fosfato", "source": "Fosfato diamónico" }  // ← id del item
  ]
}
```

Su SPO, con un record por item:

```jsonc
{
  "id": "sd-supply-775",
  "parent_id": "sd-siembra-001",                         // ← su actividad
  "basic_info": { "record_date": "2026-03-10", "lote": "Lote Norte" },
  "records": [
    { "supply_id": "sup-dk7210",  "quantity": 20,   "unit": 7, "item_id": "it-dk7210" },   // ← su item
    { "supply_id": "sup-fosfato", "quantity": 1000, "unit": 2, "item_id": "it-fosfato" }   // ← su item
  ]
}
```

---

## 2. Fertilización · `Fertilization`

```jsonc
{
  "id": "sd-fert-002",
  "basic_info": { "record_date": "2026-03-12", "crop_category": "Trigo" },
  "fields": [{ "name": "Lote Sur" }],
  "fertilizers": [
    { "id": "it-urea", "source": "Urea", "dosage": 10, "dosage_units": "kg/ha" }
  ]
}
```

```jsonc
{
  "id": "sd-supply-777",
  "parent_id": "sd-fert-002",
  "basic_info": { "record_date": "2026-03-12", "lote": "Lote Sur" },
  "records": [
    { "supply_id": "sup-urea", "quantity": 100, "unit": 2, "item_id": "it-urea" }
  ]
}
```

El item dice lo que se aplicó: nombre y dosis. El record dice lo que se
consumió: insumo y cantidad. Lo único que comparten es el link.

---

## 3. Pulverización · `Pulverization`

```jsonc
{
  "id": "sd-pulv-003",
  "basic_info": { "record_date": "2026-03-14" },
  "fields": [{ "name": "Lote Sur" }],
  "treatments": [
    { "id": "it-glifo", "source": "Glifosato", "dosage": 2, "dosage_units": "L/ha" }
  ]
}
```

```jsonc
{
  "id": "sd-supply-776",
  "parent_id": "sd-pulv-003",
  "basic_info": { "record_date": "2026-03-14", "lote": "Lote Sur" },
  "records": [
    { "supply_id": "sup-glifo", "quantity": 20, "unit": 1, "item_id": "it-glifo" }
  ]
}
```

---

## 4. Tratamiento · `TREATMENT`

```jsonc
{
  "id": "sd-trat-004",
  "record_date": "2026-03-15",
  "treatment": "Antiparasitario",
  "products": [
    { "id": "it-iver", "name": "Ivermectina" }
  ],
  "animals": [{ "animal_category_name": "Vaquillonas" }]
}
```

```jsonc
{
  "id": "sd-supply-778",
  "parent_id": "sd-trat-004",
  "basic_info": { "record_date": "2026-03-15" },
  "records": [
    { "supply_id": "sup-iver", "quantity": 500, "unit": 5, "item_id": "it-iver" }
  ]
}
```

---

## 5. Uso de insumo · `SUPPLYOUTPUT`

Los cuatro SPO de arriba pertenecen a una actividad. Un SPO también se puede
cargar suelto: es el mismo JSON, sin actividad y sin items.

```jsonc
{
  "id": "sd-supply-779",
  "parent_id": null,                                     // ← suelto
  "basic_info": { "record_date": "2026-03-16" },
  "records": [
    { "supply_id": "sup-urea", "quantity": 50, "unit": 2, "item_id": null }
  ]
}
```

Este último es solo para mostrar la forma: no está en el «antes» ni en el mock
del tab Datos.

---

## Las filas en `supply_output_record`

Una por cada record. Es lo que permite consultar sin abrir el JSON.

| supply_output_id | record_index | supply_id | quantity | unit | item_id |
|---|---|---|---|---|---|
| sd-supply-775 | 0 | sup-dk7210 | 20 | 7 | it-dk7210 |
| sd-supply-775 | 1 | sup-fosfato | 1000 | 2 | it-fosfato |
| sd-supply-776 | 0 | sup-glifo | 20 | 1 | it-glifo |
| sd-supply-777 | 0 | sup-urea | 100 | 2 | it-urea |
| sd-supply-778 | 0 | sup-iver | 500 | 5 | it-iver |
