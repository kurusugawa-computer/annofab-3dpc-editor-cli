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
        annotation_id_index = 16
        fields = [field.strip() for field in line.split(" ")]
        label = cls(
            type=fields[0],
            height=float(fields[8]),
            width=float(fields[9]),
            depth=float(fields[10]),
            x=float(fields[11]),
            y=float(fields[12]),
            z=float(fields[13]),
            yaw=float(fields[14]),
            annotation_id=(fields[annotation_id_index] if len(fields) > annotation_id_index else None),
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
