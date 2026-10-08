from pathlib import Path
from PIL import Image
import base64, io, json, re, sys
root=Path(sys.argv[1])
html=(root/'index.html').read_text(encoding='utf-8')
app=(root/'app.bundle.js').read_text(encoding='utf-8')
model=(root/'jiangnan-town.glb').read_bytes()
manifest=json.loads((root/'diagnostics'/'manifest.json').read_text(encoding='utf-8'))
diags=[]
for v in manifest['views']:
    p=root/'diagnostics'/v['file']
    with Image.open(p) as im:
        im=im.convert('RGB'); im.thumbnail((640,400),Image.Resampling.LANCZOS)
        b=io.BytesIO(); im.save(b,'JPEG',quality=78,optimize=True)
    diags.append({'title':v['file'].replace('.png','')+' · '+v.get('question',''),'src':'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()})
bootstrap='<script>window.JIANGNAN_GLB_BASE64="'+base64.b64encode(model).decode()+'";window.JIANGNAN_DIAGNOSTICS='+json.dumps(diags,ensure_ascii=False,separators=(',',':'))+';</script>'
html=html.replace('<script src="./app.bundle.js"></script>',bootstrap+'<script>'+app+'</script>')
(root/'jiangnan-town-standalone.html').write_text(html,encoding='utf-8')
print(json.dumps({'standalone_bytes':(root/'jiangnan-town-standalone.html').stat().st_size,'glb_bytes':len(model),'diagnostics':len(diags)},ensure_ascii=False))
