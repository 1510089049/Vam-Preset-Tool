from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Preset:
    name: str
    vap_path: str
    fav_path: Optional[str]
    img_path: Optional[str]
    dependencies: List[str]

@dataclass
class VarPackage:
    name: str
    full_path: str