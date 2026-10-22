import ast,copy,importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('palette53',ROOT/'tools/procedural_palette53.py')
palette=importlib.util.module_from_spec(spec);spec.loader.exec_module(palette)

class ProceduralPalette53(unittest.TestCase):
    def fixture(self):
        g={'materials':[],'nodes':[],'meshes':[]};rows=[]
        for i,(name,(colour,rough,count)) in enumerate(palette.PALETTE.items()):
            g['materials'].append({'name':name+'__WEB','pbrMetallicRoughness':{'baseColorFactor':list(colour),'roughnessFactor':rough,'metallicFactor':0}})
            g['meshes'].append({'primitives':[{'material':i}]})
            g['nodes'].extend({'name':name+str(j),'mesh':i} for j in range(count))
            rows.append({'source_material':name,'source_images':[],'base_color_factor':list(colour)})
        return g,rows
    def test_all_13_colours_and_322_users(self):
        g,rows=self.fixture();self.assertEqual(len(palette.verify_palette(g,rows)),13)
    def test_reject_any_white_fallback(self):
        g,rows=self.fixture();g['materials'][4]['pbrMetallicRoughness'].pop('baseColorFactor')
        with self.assertRaises(AssertionError):palette.verify_palette(g,rows)
    def test_reject_lost_user(self):
        g,rows=self.fixture();g['nodes'].pop()
        with self.assertRaises(AssertionError):palette.verify_palette(g,rows)
    def test_reject_image_alias_or_double_tint(self):
        g,rows=self.fixture();g['materials'][0]['normalTexture']={'index':0}
        with self.assertRaises(AssertionError):palette.verify_palette(g,rows)
    def test_reject_partial_source_declaration(self):
        g,rows=self.fixture()
        with self.assertRaises(AssertionError):palette.verify_palette(g,rows[:-1])
    def test_native_declaration_only_adds_metadata(self):
        import json
        tree=ast.parse((ROOT/'jiangnan.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='declare_procedural_palette53')
        mats={}
        class Mat(dict):pass
        for name,(colour,_,_) in palette.PALETTE.items():
            m=Mat();m.diffuse_color=colour;m.name=name;m.use_nodes=True
            m.node_tree=SimpleNamespace(nodes=[SimpleNamespace(type='TEX_NOISE')]);mats[name]=m
        scope={'bpy':SimpleNamespace(data=SimpleNamespace(materials=mats)),'PREFIX':'JN_','S':{},'json':json}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<isolated-source>','exec'),scope)
        scope['declare_procedural_palette53']()
        self.assertEqual(sum('JN_web_base_color_factor' in m for m in mats.values()),12)
        self.assertTrue(all(m.diffuse_color==palette.PALETTE[name][0] and m.node_tree.nodes[0].type=='TEX_NOISE' for name,m in mats.items()))
