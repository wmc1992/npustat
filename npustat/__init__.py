"""
The npustat module.
"""

__version__ = "0.0.1"

from .ascend_dmi import GetCardStatusWithAscendDmi
from .cli import main, print_atlas_stat, loop_atlas_stat
from .core import AtlasCardCollection, AtlasCard
from .npu_smi import GetEntryCardListV1, GetCardStatusWithNpuSmi

__all__ = (
    "__version__",
    "AtlasCardCollection", "AtlasCard",
    "GetCardStatusWithAscendDmi",
    "GetEntryCardListV1", "GetCardStatusWithNpuSmi",
    "main", "print_atlas_stat", "loop_atlas_stat",
)
