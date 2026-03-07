# Logseq: [[TTA.dev/Platform_tta_dev/Components/Serena/Core/Test/Resources/Repos/Python/Test_repo/Test_repo/Complex_types]]
from typing import TypedDict

a: list[int] = [1]


class CustomListInt(list[int]):
    def some_method(self):
        pass


class CustomTypedDict(TypedDict):
    a: int
    b: str


class Outer2:
    class InnerTypedDict(TypedDict):
        a: int
        b: str


class ComplexExtension(Outer2.InnerTypedDict, total=False):
    c: bool
