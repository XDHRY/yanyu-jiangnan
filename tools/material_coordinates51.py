"""Metre-coordinate contract; BOX blend/endgrain/tangent bake remain pending."""
def validate_axes(axes):
    axes=tuple(axes)
    if len(axes)!=3 or any(type(i) is not int for i in axes) or set(axes)!={0,1,2}:
        raise ValueError('coordinate axes must be a permutation of 0,1,2')
    return axes

def object_uv(co,normal,scale,axes=(0,1,2)):
    axes=validate_axes(axes)
    dominant=max(range(3),key=lambda i:abs(normal[axes[i]]))
    a,b=[i for i in range(3) if i!=dominant]
    return co[axes[a]]*scale[a],co[axes[b]]*scale[b]
