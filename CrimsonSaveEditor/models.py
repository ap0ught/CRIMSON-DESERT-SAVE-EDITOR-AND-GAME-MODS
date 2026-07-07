from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


_ITEM_DIFF_FIELDS = (
    ("item_no", "ItemNo"),
    ("item_key", "ItemKey"),
    ("slot_no", "Slot"),
    ("stack_count", "Stack"),
    ("enchant_level", "Enchant"),
    ("endurance", "Endurance"),
    ("sharpness", "Sharpness"),
)


class QuestState(IntEnum):
    LOCKED           = 0x0D01
    AVAILABLE        = 0x0902
    AVAILABLE_PLUS   = 0x0903
    IN_PROGRESS      = 0x0905
    IN_PROGRESS_PLUS = 0x1102
    COMPLETED        = 0x1105
    SIDE_CONTENT     = 0x1502
    FULLY_COMPLETED  = 0x1905


@dataclass
class SaveItem:
    offset: int = 0
    item_no: int = 0
    item_key: int = 0
    slot_no: int = 0
    stack_count: int = 0
    enchant_level: int = 0
    endurance: int = 0
    sharpness: int = 0

    @property
    def actual_endurance(self) -> int:
        return self.endurance & 0xFF

    @property
    def socket_count_from_endurance(self) -> int:
        return (self.endurance >> 8) & 0xFF
    has_enchant: bool = False
    is_equipment: bool = False
    source: str = "Inventory"
    bag: str = ""
    section: int = 0
    name: str = ""
    category: str = "Misc"
    block_size: int = 0
    field_offsets: dict = field(default_factory=dict)
    parc_parsed: bool = False
    _original_values: dict = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.mark_original()

    def mark_original(self) -> None:
        self._original_values = {
            attr: getattr(self, attr)
            for attr, _label in _ITEM_DIFF_FIELDS
        }

    def original_value(self, attr: str):
        return self._original_values.get(attr, getattr(self, attr))

    @property
    def is_modified(self) -> bool:
        return bool(self.modified_fields())

    def modified_fields(self) -> dict:
        return {
            label: (self._original_values.get(attr), getattr(self, attr))
            for attr, label in _ITEM_DIFF_FIELDS
            if self._original_values.get(attr) != getattr(self, attr)
        }

    def proposed_diff_summary(self, **proposed_values: int) -> str:
        changes = []
        for attr, label in _ITEM_DIFF_FIELDS:
            if attr not in proposed_values:
                continue
            current = getattr(self, attr)
            proposed = proposed_values[attr]
            if current != proposed:
                changes.append(f"{label}: {current} -> {proposed}")
        return "; ".join(changes)

    def diff_summary(self) -> str:
        return "; ".join(
            f"{label}: {old} -> {new}"
            for label, (old, new) in self.modified_fields().items()
        )


@dataclass
class SaveData:
    raw_header: bytes = b""
    decompressed_blob: bytearray = field(default_factory=bytearray)
    original_compressed_size: int = 0
    original_decompressed_size: int = 0
    file_path: str = ""
    is_raw_stream: bool = False


@dataclass
class ItemInfo:
    item_key: int = 0
    name: str = ""
    internal_name: str = ""
    category: str = "Misc"
    max_stack: int = 0


@dataclass
class UndoEntry:
    description: str = ""
    offset: int = 0
    old_bytes: bytes = b""
    new_bytes: bytes = b""
    patches: list = field(default_factory=list)
