import json
from vedo import Plotter, Sphere, Box, Cylinder, Torus, Cone, merge, Axes

def render_from_json(json_data, export_path="output.stl"):
    with open(json_data) as f:
        data = json.load(f)
        
    plt = Plotter(bg="white")
    all_objects = []
    
    for part in data.get("parts", []):
        shape = part["shape"]
        pos = part.get("position", [0, 0, 0])
        rotation = part.get("rotation", [0, 0, 0])
        color = part.get("color", "#cccccc")
        opacity = part.get("opacity", 1.0)
        
        if shape == "sphere":
            radius = part.get("radius", 1)
            obj = Sphere(r=radius).pos(*pos).c(color).alpha(opacity)
            
        elif shape == "cylinder":
            r = part.get("radius", 1)
            h = part.get("height", 1)
            obj = Cylinder(r=r, height=h).pos(*pos).c(color).alpha(opacity)
            
        elif shape == "box":
            sx, sy, sz = part.get("size", [1, 1, 1])
            obj = Box(pos=pos, length=sx, width=sy, height=sz).c(color).alpha(opacity)
            
        elif shape == "cone":
            r1 = part.get("radius_bottom", 1)
            r2 = part.get("radius_top", 0)
            h = part.get("height", 1)
            obj = Cone(pos=pos, r=r1, height=h).c(color).alpha(opacity)
            
        elif shape == "torus":
            r = part.get("radius", 5)
            tube = part.get("tube", 1)
            obj = Torus(r1=r, r2=tube).pos(*pos).c(color).alpha(opacity)
            
        elif shape == "ellipsoid":
            rx = part.get("radius_x", 1)
            ry = part.get("radius_y", 1)
            rz = part.get("radius_z", 1)
            obj = Sphere().scale([rx, ry, rz]).pos(*pos).c(color).alpha(opacity)
            
        else:
            print(f"Unknown shape type: {shape}")
            continue
        
        obj.rotate_x(rotation[0], around=pos)
        obj.rotate_y(rotation[1], around=pos)
        obj.rotate_z(rotation[2], around=pos)
        
        plt += obj
        all_objects.append(obj)
        
    axes = Axes(all_objects, xtitle="X", ytitle="Y", ztitle="Z")
    plt += axes
    plt.show(interactive=True)
    
    if all_objects:
        combined = merge(all_objects)
        combined.write(export_path)
        print(f"Exported to {export_path}")
