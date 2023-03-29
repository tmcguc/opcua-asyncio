from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from asyncua import Server, ua
from asyncua.ua import uatypes

TEST_DIR = Path(__file__).parent


class ExampleEnum(IntEnum):
    EnumVal1 = 0
    EnumVal2 = 1
    EnumVal3 = 2


import asyncua.ua

setattr(asyncua.ua, 'ExampleEnum', ExampleEnum)


@dataclass
class ExampleStruct:
    IntVal1: uatypes.Int16 = 0
    EnumVal: ExampleEnum = ExampleEnum(0)


async def add_server_custom_enum_struct(server: Server):
    # import some nodes from xml
    await server.import_xml(TEST_DIR / "enum_struct_test_nodes.xml")
    ns = await server.get_namespace_index('http://yourorganisation.org/struct_enum_example/')
    uatypes.register_extension_object('ExampleStruct', ua.NodeId(5001, ns), ExampleStruct)
    val = ua.ExampleStruct()
    val.IntVal1 = 242
    val.EnumVal = ua.ExampleEnum.EnumVal2
    myvar = server.get_node(ua.NodeId(6009, ns))
    await myvar.write_value(val)
