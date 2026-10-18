import ast,unittest
from pathlib import Path
tree=ast.parse((Path(__file__).resolve().parents[1]/'jiangnan.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='quay_stone39_target')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'quay39-source','exec'),ns)
class Quay39Scope(unittest.TestCase):
    def test_expected_public_users(self):
        for name in ['JN_桥西补履_接路石坪','JN_北河转水埠_共享青石桥板_01','JN_北河转水埠_共享石凳面_1','JN_北河转水埠_石凳面原型','JN_北河转水埠_亲水踏步_3']:
            self.assertTrue(ns['quay_stone39_target'](name),name)
    def test_non_target_assets_excluded(self):
        for name in ['JN_北河转水埠_西岸北延地基','JN_北河转水埠_共享石凳足_1_1','JN_北河转水埠_灯柱_1','JN_桥西补履_案面','JN_村落民居_01_室内地坪','JN_太湖石_瘦透漏皱']:
            self.assertFalse(ns['quay_stone39_target'](name),name)
