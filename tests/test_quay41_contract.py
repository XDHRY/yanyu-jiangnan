"""Scope the Web repair to exactly two existing quay procedural materials."""
import ast,unittest
from pathlib import Path
TREE=ast.parse((Path(__file__).resolve().parents[1]/'jiangnan.py').read_text())
class QuayFallback41(unittest.TestCase):
    def test_only_two_declared_source_fallbacks_in_boat_phase(self):
        fn=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='town_phase18_quay_boat_gear')
        declarations=[]
        for n in ast.walk(fn):
            if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Subscript):
                t=n.targets[0]
                if isinstance(t.slice,ast.Constant) and t.slice.value=='JN_web_base_color_factor':
                    declarations.append(t.value.id)
                    self.assertEqual(ast.unparse(n.value),f'list({t.value.id}.diffuse_color)')
        self.assertEqual(sorted(declarations),['boatwood','rainwet'])
    def test_source_colours_and_roughness_unchanged(self):
        fn=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='town_phase18_quay_boat_gear')
        wanted={'转水埠旧船木':((.24,.105,.038),.55,4),'转水埠桥面雨湿':((.19,.25,.22),.28,3)}
        got={}
        for n in ast.walk(fn):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='material' and ast.literal_eval(n.args[0]) in wanted:
                got[ast.literal_eval(n.args[0])]=tuple(ast.literal_eval(v) for v in n.args[1:])
        self.assertEqual(got,wanted)
