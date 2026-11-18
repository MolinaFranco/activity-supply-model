"""
Modelos de referencia extraídos TAL CUAL de challenge2.md.
Es la base que nos dan y que hay que respetar: no se modifican acá.

Lo que el enunciado NO define y asumimos solo como stub (marcado con # STUB):
  - BaseStructure / BaseModel: lo único que sabemos es que cada entry de
    structured data tiene un `id` UUID único (actividades y SUPPLYOUTPUT).
  - BasicInfo (agro): solo sabemos que tiene record_date y crop_category.
  - FieldRefRequired / FieldRefNoHectares: referencia a lote, con y sin hectáreas.
  - La entidad "insumo de inventario" (Supply) NO tiene schema en el enunciado:
    solo sabemos por las capturas que tiene nombre, foto y unidad
    (Litros, Kilos, Metros, Rollos...) y que es por campo.
"""
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


# --------------------------------------------------------------------------- #
# STUBS (no vienen en el enunciado, solo lo mínimo que se deduce)
# --------------------------------------------------------------------------- #
class BaseStructure(BaseModel):  # STUB
    id: UUID  # único y distinto por entry de structured data. "Acá se cuelga la relación".


class BasicInfo(BaseModel):  # STUB — usado por Plantation/Fertilization/Pulverization
    record_date: str
    crop_category: Optional[str] = None


class FieldRefRequired(BaseModel):  # STUB — lote con hectáreas
    field_id: str
    name: Optional[str] = None
    hectares: float  # necesario para pasar dosis/ha -> cantidad total


class FieldRefNoHectares(BaseModel):  # STUB — lote sin hectáreas (hacienda)
    field_id: str
    name: Optional[str] = None


class Supply(BaseModel):  # STUB — insumo de inventario, deducido de las capturas
    id: str
    name: str
    unit: int  # enum (Litros, Kilos, Metros, Rollos...). Record.unit es int "derivado del supply"


# --------------------------------------------------------------------------- #
# plantation.py — Plantation (siembra)
# Items con insumo: fertilizers[].source + details.genetic_variety
# --------------------------------------------------------------------------- #
class Details(BaseModel):
    genetic_variety: Optional[str] = None
    spacing: Optional[float] = None


class Density(BaseModel):
    density: Optional[float] = None
    density_units: Optional[Literal["seeds/ha", "plants/ha", "kg/ha"]] = None


class PlantationFertilizer(BaseModel):  # en el original se llama `Fertilizer`
    source: Optional[str] = None
    dosage: Optional[float] = None
    dosage_units: Optional[Literal["L/ha", "kg/ha"]] = None


class Plantation(BaseStructure):
    basic_info: BasicInfo                # record_date, crop_category
    fields: list[FieldRefRequired]       # 1..5 lotes
    details: Optional[Details] = None    # details.genetic_variety = genética
    density: Optional[Density] = None
    fertilizers: list[PlantationFertilizer] = []   # max 5
    contractor: Optional[str] = None
    note: Optional[str] = None


# --------------------------------------------------------------------------- #
# fertilization.py — Fertilization
# Items con insumo: fertilizers[].source
# --------------------------------------------------------------------------- #
class FertilizationFertilizer(BaseModel):  # en el original se llama `Fertilizer`
    source: str                          # acá es obligatorio (en Plantation es Optional)
    dosage: Optional[float] = None
    dosage_units: Optional[Literal["L/ha", "kg/ha"]] = None


class Fertilization(BaseStructure):
    basic_info: BasicInfo
    fields: list[FieldRefRequired]       # 1..5 lotes
    contractor: Optional[str] = None
    fertilizers: list[FertilizationFertilizer]  # min 1, max 5
    note: Optional[str] = None


# --------------------------------------------------------------------------- #
# pulverization.py — Pulverization
# Items con insumo: treatments[].source
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# cattle.py — TREATMENT (tratamiento hacienda)
# Items con insumo: products[].name
# Ojo: dosis absolutas (ml, cc, g, kg, L), no por hectárea; lotes sin hectáreas.
# --------------------------------------------------------------------------- #
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
    record_date: str                     # ojo: NO usa basic_info
    treatment: str
    products: Optional[list[TreatmentProduct]] = None    # 0..5
    animals: Optional[list[TreatmentAnimalRef]] = None   # 0..5
    fields: Optional[list[FieldRefNoHectares]] = None    # 0..5 lotes, sin hectáreas
    note: Optional[str] = None


# --------------------------------------------------------------------------- #
# supplies.py — SUPPLYOUTPUT (uso de insumo)
# Items con insumo: records[] (ya tiene supply_id, pero NO tiene nombre)
# --------------------------------------------------------------------------- #
class SupplyBasicInfo(BaseModel):  # en el original se llama `BasicInfo` (choca con el de agro)
    record_date: str
    lote: Optional[str] = None


class Record(BaseModel):
    supply_id: Optional[str]             # ref al insumo de inventario
    quantity: float
    unit: Optional[int] = None           # no editable, derivado del supply


class SUPPLYOUTPUT(BaseStructure):
    basic_info: SupplyBasicInfo
    records: list[Record] = []           # min 1, max 20
    note: Optional[str] = None


# --------------------------------------------------------------------------- #
# Mapa "qué se linkea" (tabla del enunciado), útil para un extractor genérico
# --------------------------------------------------------------------------- #
LINKABLE_ITEMS = {
    "PLANTATION":    [("fertilizers[]", "source"), ("details", "genetic_variety")],
    "FERTILIZATION": [("fertilizers[]", "source")],
    "PULVERIZATION": [("treatments[]", "source")],
    "TREATMENT":     [("products[]", "name")],
    "SUPPLYOUTPUT":  [("records[]", "supply_id")],  # matchea por id -> nombre del supply
}
