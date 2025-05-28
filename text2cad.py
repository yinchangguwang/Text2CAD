import sys
from text2json import text2json
from json_to_vedo import render_from_json

def text2cad(path):
    txt_path = path + ".txt"
    json_path = path + ".json"
    stl_path = path + ".stl"
    text2json(txt_path, json_path)
    render_from_json(json_path, stl_path)
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python text2cad.py <path_without_extension>")
        sys.exit(1)
    input_path = sys.argv[1]
    text2cad(input_path)