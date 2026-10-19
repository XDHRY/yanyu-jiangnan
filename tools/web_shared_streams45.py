"""Scoped, bit-exact accessor sharing for eight evaluated workshop legs.

UV differences are NEVER rounded away. No geometry, material, transform or
mesh is merged. Only target attributes with identical metadata/view bytes can
share an accessor. Unrelated unused data is deliberately retained.
"""
import copy
import hashlib
import json
from web_topology import decode, encode

PREFIXES = ('JN_北河修桨作坊_长案腿', 'JN_北河修桨作坊_修桨马凳腿')


def share_workshop_streams(data):
    g, binary = decode(data)
    old = copy.deepcopy(g)
    assert set(g) <= {'asset', 'extensionsUsed', 'extensionsRequired', 'scene',
                      'scenes', 'nodes', 'cameras', 'materials', 'meshes',
                      'textures', 'images', 'accessors', 'bufferViews',
                      'samplers', 'buffers'}, 'unknown accessor consumer'
    assert len(g['buffers']) == 1 and 'uri' not in g['buffers'][0]
    assert not any(n.get('extensions') or 'skin' in n for n in g['nodes'])
    for mesh in g['meshes']:
        assert not mesh.get('extensions') and not mesh.get('weights')
        for p in mesh['primitives']:
            assert not p.get('extensions') and not p.get('targets')
    for a in g['accessors']:
        assert 'sparse' not in a and not a.get('extensions')
    for v in g['bufferViews']:
        assert v.get('buffer', 0) == 0 and not v.get('extensions')
        assert v.get('byteOffset', 0) + v['byteLength'] <= len(binary)
    for image in g.get('images', []):
        assert not image.get('extensions')

    def payload(i):
        v = old['bufferViews'][i]
        s = v.get('byteOffset', 0)
        return binary[s:s + v['byteLength']]

    selected = []
    for prefix in PREFIXES:
        family = [n for n in g['nodes'] if n.get('name', '').startswith(prefix)]
        assert len(family) == 4 and all('mesh' in n for n in family)
        selected.extend(n['mesh'] for n in family)
    assert len(set(selected)) == 8
    # These meshes may not be attached to any unexpected non-target user.
    assert sum(n.get('mesh') in selected for n in g['nodes']) == 8
    seen, replacements, candidates = {}, [], set()
    for mi in selected:
        for p in g['meshes'][mi]['primitives']:
            for semantic, ai in list(p['attributes'].items()):
                a = g['accessors'][ai]
                vi = a['bufferView']
                v = g['bufferViews'][vi]
                # Include byteOffset/stride/normalization/min/max/extras: no
                # lossy interpretation and no material/UV phase substitution.
                ak = {k: x for k, x in a.items() if k != 'bufferView'}
                vk = {k: x for k, x in v.items() if k != 'byteOffset'}
                key = (semantic, json.dumps([ak, vk], sort_keys=True), payload(vi))
                if key not in seen:
                    seen[key] = ai
                elif seen[key] != ai:
                    p['attributes'][semantic] = seen[key]
                    candidates.add(ai)
                    replacements.append({'mesh': mi, 'semantic': semantic,
                                         'from': ai, 'to': seen[key]})
    # Only accessor references supported above exist; indices are retained too.
    used = set()
    for mesh in g['meshes']:
        for p in mesh['primitives']:
            used.update(p['attributes'].values())
            if 'indices' in p:
                used.add(p['indices'])
    dropped = candidates - used
    amap = {i: j for j, i in enumerate(i for i in range(len(g['accessors']))
                                     if i not in dropped)}
    for mesh in g['meshes']:
        for p in mesh['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = amap[p['indices']]
    g['accessors'] = [a for i, a in enumerate(g['accessors']) if i not in dropped]
    candidate_views = {old['accessors'][i]['bufferView'] for i in dropped}
    used_views = {a['bufferView'] for a in g['accessors'] if 'bufferView' in a}
    used_views.update(im['bufferView'] for im in g.get('images', []) if 'bufferView' in im)
    dropped_views = candidate_views - used_views
    vmap = {i: j for j, i in enumerate(i for i in range(len(g['bufferViews']))
                                     if i not in dropped_views)}
    out, kept_views = bytearray(), []
    for i, v in enumerate(g['bufferViews']):
        if i in dropped_views:
            continue
        out.extend(b'\0' * ((-len(out)) % 4))
        v['byteOffset'] = len(out)
        out.extend(payload(i))
        kept_views.append(v)
    for a in g['accessors']:
        if 'bufferView' in a:
            a['bufferView'] = vmap[a['bufferView']]
    for im in g.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = vmap[im['bufferView']]
    g['bufferViews'] = kept_views
    g['buffers'][0]['byteLength'] = len(out)
    result = encode(g, bytes(out))
    for i, j in vmap.items():
        v = g['bufferViews'][j]
        assert bytes(out[v['byteOffset']:v['byteOffset'] + v['byteLength']]) == payload(i)
    for k in ('nodes', 'materials', 'textures', 'samplers', 'cameras', 'scenes'):
        assert g.get(k) == old.get(k)
    return result, {
        'schema': 'jiangnan-scoped-stream-sharing45-v1',
        'policy': 'eight workshop legs only; exact metadata and bytes; no tolerance',
        'target_meshes': selected, 'mesh_entries_before': len(old['meshes']),
        'mesh_entries_after': len(g['meshes']), 'replacements': replacements,
        'removed_accessors': sorted(dropped), 'removed_buffer_views': sorted(dropped_views),
        'preserved_buffer_payloads': len(vmap), 'bytes_before': len(data),
        'bytes_after': len(result), 'binary_bytes_saved': len(binary) - len(out),
        'all_retained_payloads_bit_identical': True,
        'nodes_materials_cameras_unchanged': True,
        'source_sha256': hashlib.sha256(data).hexdigest(),
        'result_sha256': hashlib.sha256(result).hexdigest(),
    }
