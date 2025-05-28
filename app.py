from flask import Flask, request, jsonify, send_file,render_template 
from openai import OpenAI
import json
import os
import uuid 
import re
import math
from openai import APIConnectionError  
import time

from json_to_stl_converter import create_stl_from_json_data

app = Flask(__name__)

API_KEY = "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"  # Set your OpenAI API key here
system_prompt = """
You are a CAD model generator assistant.

Given a natural language description of a 3D structure, your task is to return a JSON object that describes a list of geometric parts and their parameters. 

Each part must include:
- `"shape"`: one of "box", "cylinder", "sphere", "cone", "torus", "ellipsoid"
- `"position"`: [x, y, z] float values
- `"rotation"`: [x_angle, y_angle, z_angle] float values in degrees (optional, default is [0, 0, 0])
- `"operation"`: "new", "union", or "cut"
- (Optional) `"color"`: Hex color string (e.g. "#ff0000")
- (Optional) `"opacity"`: A float value between 0.0 (completely transparent) and 1.0 (completely opaque)

Shape-specific parameters:
- For `"box"`: add `"size"` as [width, depth, height]
- For `"cylinder"`: add `"radius"` and `"height"`
- For `"sphere"`: add `"radius"`
- For `"cone"`: add `"radius_top"`, `"radius_bottom"`, `"height"`
- For `"torus"`: add `"radius"` and `"tube"` (donut shape)
- For `"ellipsoid"`: add `"radius_x"`, `"radius_y"`, `"radius_z"` (semi-axes lengths along x, y, z)

Please strictly return a JSON object following this format, **no extra text**, no explanation, only valid parsable JSON.

Here is an example:

```json
{
  "parts": [
    {
      "shape": "cylinder",
      "radius": 5,
      "height": 10,
      "position": [0, 0, 0],
      "rotation": [0, 0, 45],
      "operation": "new"
      "color": "#ff0000",
      "opacity": 0.8
    },
    {
      "shape": "box",
      "size": [10, 5, 3],
      "position": [15, 0, 0],
      "rotation": [0, 0, 0],
      "operation": "union"
    }
  ]
}
```

notice: you should not include the beginning ```json and ending ``` in the output, just return the JSON object directly.
Now generate the JSON structure for the following description:
"""

def generate_math_prompt(problem_description: str) -> str:
    client = OpenAI(api_key=API_KEY)
    SYSTEM_MESSAGE = """
    You are a mathematical assistant. 

    Given a natural language description of a 3D structure(maybe ambiguous), your task is to calculate the necessary numerical parameters for the structure. 
    
    Please provide a detailed step-by-step solution to the problem, explain your approach step by step, and finally provide an answer.
    
    You need to ensure that all the data obtained from the final calculation are real numbers.
    
    If specific data is not provided in the required 3D structure, you need to choose a reasonable data for calculation, and cannot write unknown variables such as x, y, z into the final calculation result.
    
    Some representations of trigonometric functions must also be converted to real numbers.
    """
    EXAMPLES = [
        {
            "problem": "a 1 * 1 lego brick",
            "solution": "A 1 * 1 lego brick consists of two parts: \n1. A box with size [1, 1, 0.3] (width, depth, height) at position [0, 0, 0], rotation [0, 0, 0]. \n2. A cylinder with radius 0.2 and height 0.3 at position [0, 0, 0.3], rotation [0, 0, 0]."
        },
        {
            "problem": "A spiral staircase with three steps, slightly rotating around the central axis between each two steps, and the height difference between the two steps is consistent",
            "solution": """
            A spiral staircase with three steps can be represented as follows: 
            1. The central rotation axis coincides with the Z-axis. 
            2. Each step is a box with size [6, 1, 0.5] (width, depth, height) to ensure overlap. 
            3. The rotation angle between each step is 30 degrees. 
            4. The height difference between steps is 0.4 units (slightly less than step height to ensure overlap in Z). 
            5. Radius from the center is 2 units (reduced to bring steps closer). 
            - Step 1: shape 'box', size [6, 1, 0.5], position [2.0000, 0.0000, 0], rotation [0, 0, 0]. 
            - Step 2: shape 'box', size [6, 1, 0.5], position [2*cos(30 degrees), 2*sin(30 degrees), 0.4], rotation [0, 0, 30]. 
            - Step 3: shape 'box', size [6, 1, 0.5], position [2*cos(60 degrees), 2*sin(60 degrees), 0.8], rotation [0, 0, 60]. 
            After converting degrees to radians (degrees * pi/180) and computing:
            - cos(30 degrees) = cos(30 * pi/180) = 0.8660, sin(30 degrees) = 0.5000
            - cos(60 degrees) = 0.5000, sin(60 degrees) = 0.8660
            Final positions:
            - Step 1: shape 'box', size [6, 1, 0.5], position [2.0000, 0.0000, 0], rotation [0, 0, 0]. 
            - Step 2: shape 'box', size [6, 1, 0.5], position [1.7321, 1.0000, 0.4], rotation [0, 0, 30]. 
            - Step 3: shape 'box', size [6, 1, 0.5], position [1.0000, 1.7321, 0.8], rotation [0, 0, 60].
            """
        },
        
        
    ]
    
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
    for example in EXAMPLES:
        messages.append({"role": "user", "content": example["problem"]})
        messages.append({"role": "assistant", "content": example["solution"]})
    messages.append({"role": "user", "content": problem_description})
    
    
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            chat_response = client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            return chat_response.choices[0].message.content
        except APIConnectionError as e:
            print(f"API连接错误 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                raise RuntimeError(f"API连接失败，请检查网络或OpenAI服务状态") from e
        except Exception as e:
            print(f"生成数学提示时出错: {e}")
            raise
    

def text2json(text_description: str) -> dict:
    print("Computing structure data via math assistant...")
    math_prompt = generate_math_prompt(text_description)
    print(f"Math assistant output:\n{math_prompt}")
    
    print("Generating structure from LLM with enhanced prompt...")
    structure = call_llm(math_prompt)
    print(f"Generated JSON structure: {structure}")
    return structure


def call_llm(prompt: str) -> dict:
    client = OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    output = response.choices[0].message.content
    print(f"Raw LLM output:\n{output}")

    # 1. 处理三角函数表达式
    def evaluate_trig_expression(match):
        expr = match.group(0)
        angle_match = re.search(r'(\d+\.?\d*)\*Math\.PI/180', expr)
        if angle_match:
            angle_degrees = float(angle_match.group(1))
            angle_radians = math.radians(angle_degrees)
            if 'Math.cos' in expr:
                return f"{math.cos(angle_radians):.4f}"
            elif 'Math.sin' in expr:
                return f"{math.sin(angle_radians):.4f}"
        return expr

    processed_output = re.sub(
        r'3\*Math\.(cos|sin)\(\d+\.?\d*\*Math\.PI/180\)',
        evaluate_trig_expression,
        output
    )
    
    # 2. 处理算术表达式
    def evaluate_arithmetic_expression(match):
        expr = match.group(0)
        try:
            # 安全计算表达式
            result = eval(expr)
            return f"{result:.4f}"
        except:
            return expr
    
    # 首先处理整个输出中的算术表达式
    processed_output = re.sub(
        r'[-+]?\d*\.?\d+[*/+\-][-+]?\d*\.?\d+', 
        evaluate_arithmetic_expression, 
        processed_output
    )
    
    # 3. 处理位置数组中的表达式
    def process_position(match):
        position_str = match.group(1)
        # 再次处理算术表达式
        processed_position = re.sub(
            r'[-+]?\d*\.?\d+[*/+\-][-+]?\d*\.?\d+', 
            evaluate_arithmetic_expression, 
            position_str
        )
        return f"[{processed_position}]"
    
    processed_output = re.sub(
        r'\[([^\]]+)\]', 
        process_position, 
        processed_output
    )
    
    print(f"Fully processed output:\n{processed_output}")

    try:
        return json.loads(processed_output)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Processed output: {processed_output}")
        raise

def generate_json_from_text(text_prompt: str) -> dict:
    print("Generating structure from LLM...")
    structure = call_llm(text_prompt)
    return structure

    
def generate_stl_from_json_data(json_data: dict, output_stl_path: str):
    try:
        create_stl_from_json_data(json_data, output_stl_path)
    except ValueError as ve: 
        print(f"ValueError during STL creation: {ve}")
        raise
    except Exception as e:
        print(f"Unexpected error during STL creation: {e}")
        import traceback
        traceback.print_exc() 
        raise

    if not os.path.exists(output_stl_path):
        raise FileNotFoundError(f"STL file was not generated at {output_stl_path} by create_stl_from_json_data.")
    print(f"Generated STL file at: {output_stl_path}")
    
    
@app.route('/') 
def serve_index():
    return render_template('index.html') 


STL_OUTPUT_DIR = "generated_stls"
os.makedirs(STL_OUTPUT_DIR, exist_ok=True)

@app.route('/generate_cad', methods=['POST'])
def generate_cad_endpoint():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    text_description = data.get('text')

    if not text_description:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    try:
        print(f"Received text: {text_description}")
        # 1. Text to JSON
        json_structure = text2json(text_description)
        print(f"Generated JSON: {json_structure}")

        # 2. JSON to STL
        unique_filename = f"model_{uuid.uuid4()}.stl"
        output_stl_path = os.path.join(STL_OUTPUT_DIR, unique_filename)

        generate_stl_from_json_data(json_structure, output_stl_path)

        # 3. 返回STL文件
        return send_file(output_stl_path, as_attachment=True, mimetype='application/sla')
      

    except ValueError as ve: 
         print(f"ValueError: {ve}")
         return jsonify({"error": str(ve)}), 500
    except FileNotFoundError as fnfe:
        print(f"FileNotFoundError: {fnfe}")
        return jsonify({"error": "Failed to generate STL file on server."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred."}), 500




if __name__ == '__main__':
    app.run(debug=True, port=5000) 