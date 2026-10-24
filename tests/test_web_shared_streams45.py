"""Lossless sharing must preserve even tiny UV differences and unrelated data."""
import copy
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from web_shared_streams45 import PREFIXES, share_workshop_streams
from web_topology import decode, encode


class SharedStreams45(unittest.TestCase):
    def fixture(self):
        g = {'asset': {'version': '2.0'}, 'buffers': [{}], 'bufferViews': [],
             'accessors': [], 'meshes': [], 'nodes': [], 'materials': [{'name': 'wood'}],
             'images': [], 'scenes': [{'nodes': list(range(9))}], 'scene': 0}
        b = bytearray()
        def stream(raw, kind, count, component=5126):
            b.extend(b'\0' * ((-len(b)) % 4))
            v = len(g['bufferViews']); a = len(g['accessors'])
            g['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw)})
            b.extend(raw)
            g['accessors'].append({'bufferView': v, 'componentType': component, 'type': kind, 'count': count})
            return a
        for i in range(9):
            pos = stream(struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0), 'VEC3', 3)
            normal = stream(struct.pack('<9f', *([0,0,1] * 3)), 'VEC3', 3)
            uv = stream(struct.pack('<6f', 0,0, 1,0, 0,1), 'VEC2', 3)
            index = stream(struct.pack('<3H', 0,1,2), 'SCALAR', 3, 5123)
            g['meshes'].append({'name': str(i), 'primitives': [{'attributes': {'POSITION': pos, 'NORMAL': normal, 'TEXCOORD_0': uv}, 'indices': index, 'material': 0}]})
            name = PREFIXES[i // 4] + ('.%03d' % (i % 4)) if i < 8 else 'untouched'
            g['nodes'].append({'name': name, 'mesh': i, 'translation': [i,0,0]})
        # An unrelated unused stream must survive; no broad garbage collection.
        stream(b'UNUSED!!', 'SCALAR', 8, 5121)
        g['buffers'][0]['byteLength'] = len(b)
        return encode(g, bytes(b))

    def test_exact_streams_share_but_meshes_nodes_materials_do_not(self):
        raw = self.fixture(); out, r = share_workshop_streams(raw)
        g,b = decode(out); old,_ = decode(raw)
        self.assertEqual(len(r['removed_accessors']), 21)
        self.assertEqual(len(g['meshes']), 9)
        for k in ('nodes', 'materials', 'scenes'): self.assertEqual(g[k], old[k])
        self.assertIn(b'UNUSED!!', b)
        self.assertLess(len(out), len(raw))

    def test_one_bit_uv_difference_not_rounded(self):
        g,b = decode(self.fixture()); b = bytearray(b)
        ai = g['meshes'][1]['primitives'][0]['attributes']['TEXCOORD_0']
        v = g['bufferViews'][g['accessors'][ai]['bufferView']]
        struct.pack_into('<f', b, v['byteOffset'], 1e-20)
        out,r = share_workshop_streams(encode(g, bytes(b)))
        self.assertNotIn(ai, r['removed_accessors'])

    def test_normalized_metadata_difference_not_shared(self):
        g,b = decode(self.fixture()); ai = g['meshes'][1]['primitives'][0]['attributes']['NORMAL']
        g['accessors'][ai]['extras'] = {'keep': True}
        _,r = share_workshop_streams(encode(g,b))
        self.assertNotIn(ai, r['removed_accessors'])

    def test_shared_with_non_target_consumer_retained(self):
        g,b = decode(self.fixture()); ai = g['meshes'][1]['primitives'][0]['attributes']['POSITION']
        g['meshes'][8]['primitives'][0]['attributes']['POSITION'] = ai
        _,r = share_workshop_streams(encode(g,b))
        self.assertNotIn(ai, r['removed_accessors'])

    def test_animation_accessors_and_target_survive_remap(self):
        g,b=decode(self.fixture())
        g['animations']=[{'name':'lantern','samplers':[{'input':0,'output':1,'interpolation':'LINEAR'}],
            'channels':[{'sampler':0,'target':{'node':0,'path':'rotation'}}]}]
        out,r=share_workshop_streams(encode(g,b));n,_=decode(out)
        self.assertEqual(len(n['animations']),1);self.assertEqual(r['animation_clips_preserved'],1)
        sampler=n['animations'][0]['samplers'][0]
        self.assertGreaterEqual(sampler['input'],0);self.assertGreaterEqual(sampler['output'],0)
        self.assertEqual(n['animations'][0]['channels'][0]['target'],{'node':0,'path':'rotation'})

    def test_sparse_and_extensions_rejected(self):
        for key in ('sparse', 'extensions'):
            g,b = decode(self.fixture()); g['accessors'][0][key] = {'unsafe': 1}
            with self.assertRaises(AssertionError): share_workshop_streams(encode(g,b))

    def test_idempotent_and_missing_family_rejected(self):
        once,_ = share_workshop_streams(self.fixture())
        self.assertEqual(once, share_workshop_streams(once)[0])
        g,b = decode(self.fixture()); g['nodes'][0]['name'] = 'not-target'
        with self.assertRaises(AssertionError): share_workshop_streams(encode(g,b))
