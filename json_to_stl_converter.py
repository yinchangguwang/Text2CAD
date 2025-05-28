import json
from vedo import Sphere, Box, Cylinder, Torus, Cone, Ellipsoid, Assembly, merge, settings
import os
import numpy as np
from vedo import Sphere, Box, Cylinder, Torus, Cone, Ellipsoid, merge, write

settings.default_backend = 'vtk' 

def create_stl_from_json_data(json_data: dict, export_path: str = "output.stl"):
    """
    Creates 3D objects from a JSON data dictionary, merges them, and exports to STL.
    This version does NOT show a plot, suitable for backend use.

    Args:
        json_data (dict): A dictionary containing the parts descriptions.
        export_path (str): The path where the STL file will be saved.
    """
    all_objects = []

    parts = json_data.get("parts", [])
    if not parts:
        print("No 'parts' found in JSON data.")
        raise ValueError("No 'parts' found in JSON data to create STL.")


    for i, part_desc in enumerate(parts):
        shape_type = part_desc.get("shape")
        if not shape_type:
            print(f"Warning: Part {i+1} is missing 'shape' information. Skipping.")
            continue

        pos = part_desc.get("position", [0, 0, 0])
        rotation = part_desc.get("rotation", [0, 0, 0]) 
        obj = None
        print(f"Creating part {i+1}: type={shape_type}, position={pos}, rotation={rotation}")

        try:
            if shape_type == "sphere":
                radius = part_desc.get("radius", 1)
                obj = Sphere(r=radius).pos(pos) 
            elif shape_type == "cylinder":
                radius = part_desc.get("radius", 1)
                height = part_desc.get("height", 1)
                obj = Cylinder(r=radius, height=height).pos(pos)
            elif shape_type == "box":
                size = part_desc.get("size", [1, 1, 1])
                if len(size) != 3:
                    raise ValueError(f"Box part {i+1} 'size' must have 3 dimensions [width, depth, height]. Got: {size}")
              
                obj = Box(pos=pos, length=size[0], width=size[1], height=size[2])
            elif shape_type == "cone":
                radius_bottom = part_desc.get("radius_bottom", 1)
                radius_top = part_desc.get("radius_top", 0)
                height = part_desc.get("height", 1)
                obj = Cone(pos=pos, r=radius_bottom, r2=radius_top, height=height)
            elif shape_type == "torus":
                major_radius = part_desc.get("radius", 5)
                tube_radius = part_desc.get("tube", 1) # 假设 "tube" 是管子的半径
                obj = Torus(pos=pos, r=major_radius, thickness=tube_radius) # 使用 thickness 参数
            elif shape_type == "ellipsoid":
                radius_x = part_desc.get("radius_x", 1)
                radius_y = part_desc.get("radius_y", 1)
                radius_z = part_desc.get("radius_z", 1)
               
                obj = Sphere(r=1).scale([radius_x, radius_y, radius_z]).pos(pos)
            else:
                print(f"Warning: Unknown shape type '{shape_type}' for part {i+1}. Skipping.")
                continue

            if obj:
                obj.rotate_x(rotation[0])
                obj.rotate_y(rotation[1])
                obj.rotate_z(rotation[2])
                all_objects.append(obj)
        except Exception as e:
            print(f"Error creating part {i+1} ({shape_type}): {e}")

    if all_objects:
        print(f"Merging {len(all_objects)} objects...")
        if len(all_objects) == 1:
            final_assembly = all_objects[0]
        else:
            final_assembly = Assembly(all_objects)

        if final_assembly: 
            final_assembly.write(export_path)
            print(f"STL successfully exported to {export_path}")
        else:
            print(f"Warning: No final assembly to write to {export_path}. Might be due to errors or empty parts list.")
            raise ValueError("Failed to create final assembly for STL export.")

    else:
        print(f"No valid objects were created. Cannot export STL to {export_path}.")
        raise ValueError("No valid 3D objects were generated to create STL.")
