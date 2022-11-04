from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, List, Optional


@dataclass(frozen=True)
class KittiLabel:
    type: str
    height: float
    """z方向の幅"""
    width: float
    """y方向の幅"""
    depth: float
    """x方向の幅"""
    x: float
    """底面の中心座標のx成分"""
    y: float
    """底面の中心座標のy成分"""
    z: float
    """底面の中心座標のz成分"""
    yaw: float
    annotation_id: Optional[str]
    ignore_types: ClassVar[List[str]] = ["DontCare"]

    @classmethod
    def decode(cls, line: str) -> Optional["KittiLabel"]:
        fields = [field.strip() for field in line.split(" ")]
        label = KittiLabel(
            fields[0],
            float(fields[8]),
            float(fields[9]),
            float(fields[10]),
            float(fields[11]),
            float(fields[12]),
            float(fields[13]),
            float(fields[14]),
            fields[16] if len(fields) > 16 else None,
        )

        return label if label.type not in cls.ignore_types else None

    @classmethod
    def decode_many(cls, csv: str) -> List["KittiLabel"]:
        lines = csv.split("\n")
        return [label for line in lines if len(line.strip()) > 0 for label in [cls.decode(line)] if label is not None]

    @classmethod
    def decode_path(cls, csv_path: Path) -> List["KittiLabel"]:
        if not csv_path.exists():
            return []
        with csv_path.open("r") as reader:
            return cls.decode_many(reader.read())
