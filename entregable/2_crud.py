"""
2 · CRUD — qué pasa con la relación al crear, actualizar y borrar.

Ilustrativo: firmas + cuerpo esquemático. No compila ni corre.
`sd_repo`, `record_repo`, `inventory` y `transaction` representan el acceso a datos.

Criterio:
  · Los links son datos, no cálculos. El SPO guarda su actividad (`parent_id`) y
    cada record guarda su item (`item_id`). Al editar no se recalcula nada.
  · La actividad es la fuente de verdad sobre sus items. El SPO lo es sobre lo
    consumido. Lo único que comparten es el link.
  · Hay un solo camino para escribir un SPO (`save_supply_output`), sea suelto o
    de una actividad. Ese camino mantiene la tabla `supply_output_record`.
  · Todo se escribe en una transacción.
  · Baja lógica (agregado propio): se marca `deleted_at`, no se borra.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ItemSupply(BaseModel):
    """Un «Descontar del inventario» del form: un producto de la actividad
    para el que el usuario eligió un insumo y una cantidad."""
    item_id: UUID          # el item de la actividad
    supply_id: str         # el insumo elegido
    quantity: float


# --------------------------------------------------------------------------- #
# CREAR
# --------------------------------------------------------------------------- #
def create_activity(structure: "BaseStructure",
                    supplies: Optional[list[ItemSupply]] = None) -> UUID:
    with transaction():
        activity_id = sd_repo.insert(structure)      # cada item ya trae su id

        if supplies:
            spo = build_supply_output(structure, supplies)   # un record por insumo, con su item_id
            save_supply_output(spo, parent_id=activity_id)

        return activity_id


def create_supply_output(spo: "SUPPLYOUTPUT") -> UUID:
    """Un SPO suelto, cargado sin actividad."""
    with transaction():
        return save_supply_output(spo, parent_id=None)


def save_supply_output(spo: "SUPPLYOUTPUT", parent_id: Optional[UUID],
                       spo_id: Optional[UUID] = None) -> UUID:
    """Único camino para escribir un SPO. Guarda la entry y copia sus records."""
    if spo_id is None:
        spo_id = sd_repo.insert(spo, parent_id=parent_id)
    else:
        sd_repo.update(spo_id, spo, parent_id=parent_id)

    record_repo.delete_by_supply_output(spo_id)
    record_repo.insert_many(
        row(spo_id, index, record)                   # supply_id, quantity, unit, item_id
        for index, record in enumerate(spo.records)
        if record.supply_id is not None              # sin insumo no hay fila
    )
    return spo_id


# --------------------------------------------------------------------------- #
# ACTUALIZAR
# --------------------------------------------------------------------------- #
def update_activity(activity_id: UUID, structure: "BaseStructure",
                    supplies: Optional[list[ItemSupply]] = None) -> None:
    """Guarda la actividad. Sobre su SPO:
      · supplies = lista → el form mandó los insumos: reemplazan a los anteriores.
      · supplies = None  → no los mandó: el SPO queda como está, salvo los records
                            de items que ya no existen.
    """
    with transaction():
        sd_repo.update(activity_id, structure)
        spo_id, spo = sd_repo.supply_output_of(activity_id)   # por parent_id; puede no haber

        if supplies is not None:
            records = records_from(supplies)
        elif spo is not None:
            alive = item_ids(structure)
            records = [r for r in spo.records
                       if r.item_id is None or r.item_id in alive]
        else:
            return

        if records:
            spo = with_records(spo or new_supply_output(structure), records)
            save_supply_output(spo, parent_id=activity_id, spo_id=spo_id)
        elif spo_id:
            delete_supply_output(spo_id)             # no quedó nada que descontar


def update_supply_output(spo_id: UUID, spo: "SUPPLYOUTPUT") -> None:
    """Editar un SPO: por ejemplo, corregir una cantidad.
    Conserva su actividad, y los `item_id` viajan en los records. No se recalcula nada."""
    with transaction():
        parent_id = sd_repo.parent_of(spo_id)
        save_supply_output(spo, parent_id=parent_id, spo_id=spo_id)


def attach_supply_output(spo_id: UUID, activity_id: UUID) -> None:
    """Asociar a una actividad un SPO que ya existía, sin pasar por el form.

    Es el único lugar donde se usa la regla del enunciado: un record se linkea
    a un item solo si el nombre del item es el mismo que el del insumo.
    """
    with transaction():
        spo = sd_repo.get(spo_id)
        activity = sd_repo.get(activity_id)

        for record in spo.records:
            item = find_item_by_name(activity, inventory.name_of(record.supply_id))
            record.item_id = item.id if item else None      # si difieren, no hay link

        if not any(r.item_id for r in spo.records):
            raise NoMatchingItem                             # ningún nombre coincide: no se asocia

        save_supply_output(spo, parent_id=activity_id, spo_id=spo_id)


# --------------------------------------------------------------------------- #
# BORRAR — baja lógica (agregado propio)
# --------------------------------------------------------------------------- #
def delete_activity(activity_id: UUID) -> None:
    """Da de baja la actividad y su SPO."""
    with transaction():
        spo_id, _ = sd_repo.supply_output_of(activity_id)
        if spo_id:
            delete_supply_output(spo_id)
        sd_repo.mark_deleted(activity_id)


def delete_supply_output(spo_id: UUID) -> None:
    """Da de baja un SPO, suelto o de una actividad.
    Su JSON queda guardado; sus filas se quitan, porque la tabla solo tiene lo vivo."""
    sd_repo.mark_deleted(spo_id)
    record_repo.delete_by_supply_output(spo_id)


# --------------------------------------------------------------------------- #
# Auxiliares (solo firmas)
# --------------------------------------------------------------------------- #
def build_supply_output(structure, supplies: list[ItemSupply]) -> "SUPPLYOUTPUT":
    """Arma el SPO de una actividad: misma fecha, un record por insumo."""

def records_from(supplies: list[ItemSupply]) -> list["Record"]:
    """Un record por insumo: supply_id, quantity, unit del insumo, item_id."""

def item_ids(structure) -> set[UUID]:
    """Los ids de todos los items de la actividad, incluida la genética."""

def find_item_by_name(activity, supply_name: str):
    """El item cuyo source / name / genetic_variety es exactamente ese nombre.
    Si hay más de uno, el primero."""
