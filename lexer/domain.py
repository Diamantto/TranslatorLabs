from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class LexerData:
    table_of_language_tokens: Dict[str, str]
    table_ident_float_int: Dict[int, str]
    classes: Dict[str, str]
    stf: Dict[Tuple[int, str], int]
    states: Dict[str, Tuple[int]]
    errors_states: Dict[int, str]