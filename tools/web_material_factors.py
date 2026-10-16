"""Encode explicit source material factors unsupported by the node exporter.

Only declared factors are adapted; embedded image/binary buffers are untouched.
Independent verify_web_materials.py still checks the resulting glTF values.
"""
import json,struct

def apply_factors(data,rows):
    n,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
    document=json.loads(data[20:20+n]);tail=data[20+n:];changed=[]
    for material in document.get('materials',[]):
        matches=[r for r in rows if r.get('base_color_factor') is not None and
                 (material['name']==r['export_material'] or material['name'].startswith(r['export_material']+'.'))]
        if not matches:continue
        assert len(matches)==1
        factor=matches[0]['base_color_factor']
        assert len(factor)==4 and all(0<=v<=1 for v in factor)
        material['pbrMetallicRoughness']['baseColorFactor']=factor
        changed.append(material['name'])
    assert len(changed)>=sum(r.get('base_color_factor') is not None for r in rows),'declared factor missing material'
    raw=json.dumps(document,ensure_ascii=False,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
    result=b'glTF'+struct.pack('<II',2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail
    assert result[20+len(raw):]==tail
    return result,changed
