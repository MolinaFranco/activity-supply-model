-- =============================================================================
-- 1 · MODELO DE DATOS — relación actividad ↔ insumo
-- Ilustrativo: expresa el diseño, no está pensado para correr.
-- =============================================================================
--
--   Actividad                   SPO (SUPPLYOUTPUT)              Inventario
--     item (id, nombre, dosis)    parent_id ──→ actividad
--              ▲                  record (supply_id, cantidad,
--              └──── item_id ─────        item_id)  ──────────→ insumo
--
-- Tres datos nuevos:
--   1. Cada item de una actividad tiene un id.
--   2. El SPO guarda a qué actividad pertenece (o nada, si es suelto).
--   3. Cada record guarda a qué item corresponde.
-- Y una tabla que copia los records a columnas, para consultarlos sin abrir el JSON.
--
-- Se dan por existentes (el enunciado no da su esquema):
--   structured_data (id UUID PK, data JSONB, ...)   una fila por entry: actividades y SPO
--   supplies        (id PK, name, unit)             el inventario


-- -----------------------------------------------------------------------------
-- A · Cambios en los schemas (campos nuevos)
-- -----------------------------------------------------------------------------
--   Fertilizer        + id: UUID
--   Treatment         + id: UUID
--   TreatmentProduct  + id: UUID
--   Details           + genetic_variety_id: UUID   la genética es un campo único: lleva su propio id
--   Record            + item_id: UUID               el item de la actividad al que corresponde
--
-- El id de cada item se genera automáticamente. item_id es opcional:
-- lo ya cargado sigue siendo válido, sin link, igual que hoy.


-- -----------------------------------------------------------------------------
-- B · El SPO guarda a qué actividad pertenece
-- -----------------------------------------------------------------------------
ALTER TABLE structured_data
    ADD COLUMN parent_id  UUID REFERENCES structured_data (id),  -- solo SPO: su actividad. NULL = SPO suelto
    ADD COLUMN deleted_at TIMESTAMPTZ;                             -- baja lógica (agregado propio). NULL = viva

-- ¿Qué SPO tiene esta actividad?  /  El tab Datos lista lo que no tiene padre.
-- Es único: una actividad tiene un solo SPO vivo.
CREATE UNIQUE INDEX uq_structured_data_parent ON structured_data (parent_id)
    WHERE parent_id IS NOT NULL AND deleted_at IS NULL;


-- -----------------------------------------------------------------------------
-- C · Los records, en columnas
-- -----------------------------------------------------------------------------
-- Una fila por cada record de un SPO vivo. Es una copia de lo que el record dice
-- en el JSON: cada vez que se guarda un SPO, sus filas se reescriben completas.
CREATE TABLE supply_output_record (
    supply_output_id  UUID    NOT NULL REFERENCES structured_data (id),
    record_index      INT     NOT NULL CHECK (record_index >= 0),   -- posición del record en el SPO

    supply_id         TEXT    NOT NULL REFERENCES supplies (id),    -- qué insumo
    quantity          NUMERIC NOT NULL,                             -- cuánto
    unit              INT,                                          -- entero derivado del insumo (Record.unit)

    item_id           UUID,   -- item de la actividad al que corresponde. NULL = a ninguno

    PRIMARY KEY (supply_output_id, record_index)
);

-- ¿En qué usos y actividades aparece este insumo?
CREATE INDEX ix_supply_output_record_supply ON supply_output_record (supply_id);

-- Notas:
--   · Un record sin supply_id (el campo es Optional) no genera fila.
--   · item_id no puede ser clave foránea: los items viven dentro del JSON de la actividad.
--   · Al dar de baja un SPO se quitan sus filas: la tabla solo tiene lo vivo.


-- -----------------------------------------------------------------------------
-- Tipo de relación
-- -----------------------------------------------------------------------------
--   Actividad — SPO      uno a uno. El SPO apunta a su actividad (parent_id).
--                        Un SPO suelto no apunta a ninguna.
--   Item — record        uno a uno. El record apunta a su item (item_id).
--   Actividad — insumo   muchos a muchos, a través de los records del SPO.


-- -----------------------------------------------------------------------------
-- Por qué queda consultable sin recorrer el JSON
-- -----------------------------------------------------------------------------

-- Insumos que consumió una actividad, con unidad y cantidad.
SELECT s.name, r.quantity, r.unit, r.item_id
FROM structured_data spo
JOIN supply_output_record r ON r.supply_output_id = spo.id
JOIN supplies s             ON s.id = r.supply_id
WHERE spo.parent_id = :activity_id AND spo.deleted_at IS NULL;

-- Actividades en las que se usó un insumo.
SELECT spo.parent_id AS activity_id, r.quantity, r.unit
FROM supply_output_record r
JOIN structured_data spo ON spo.id = r.supply_output_id
WHERE r.supply_id = :supply_id AND spo.parent_id IS NOT NULL;

-- Tab Datos · la página: todo lo que no es hijo de una actividad.
-- (Se suman los filtros que el feed ya usa hoy: campo, fechas, orden.)
SELECT *
FROM structured_data
WHERE parent_id IS NULL AND deleted_at IS NULL
LIMIT :limit OFFSET :offset;
-- `total` es el COUNT(*) con ese mismo WHERE.

-- Tab Datos · los insumos de todas las actividades de la página, en una consulta.
SELECT spo.parent_id AS activity_id, spo.id AS supply_output_id,
       r.item_id, r.supply_id, s.name, r.quantity, r.unit
FROM structured_data spo
JOIN supply_output_record r ON r.supply_output_id = spo.id
JOIN supplies s             ON s.id = r.supply_id
WHERE spo.parent_id = ANY (:activity_ids_de_la_pagina) AND spo.deleted_at IS NULL
ORDER BY spo.parent_id, r.record_index;
