from openai import OpenAI
import json
import cadquery as cq

API_KEY = "your_key"  # Set your OpenAI API key here

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
            "solution": "a 1 * 1 lego brick consists of two parts: 1. a shape box has a size of [1, 1, 0.3] (width, depth, height) and is positioned at the origin [0, 0, 0]; 2. a shape cylinder has a radius of 0.2 and height of 0.3, positioned at [0, 0, 0.3].",
        },
        {
            "problem": "A spiral staircase with three steps, slightly rotating around the central axis between each two steps, and the height difference between the two steps is consistent",
            "solution": """A spiral staircase with three steps can be represented as follows: 
                1. The central rotation axis coincides with the Z-axis.
                2. Each step can be represented as a box with a size of [5, 1, 0.5].
                3. The rotation angle between each two steps is 30°.
                4. The height difference between the two steps is 1.
                5. Each step's center is 3 units away from the Z-axis, 
                    so the first step's x = 3, y = 0, z = 0,
                    the second step's x = 3 * cos(30°), y = 3 * sin(30°), z = 1,
                    the third step's x = 3 * cos(60°), y = 3 * sin(60°), z = 2.
            so we can create three boxes with the following parameters:
                - Step 1: shape: "box", size: [5, 1, 0.5], position: [3, 0, 0], rotation: [0, 0, 0]
                - Step 2: shape: "box", size: [5, 1, 0.5], position: [2.6, 1.5, 1], rotation: [0, 0, 30]
                - Step 3: shape: "box", size: [5, 1, 0.5], position: [1.5, 2.6, 2], rotation: [0, 0, 60]
            """,
        },
    ]
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
    for example in EXAMPLES:
        messages.append({"role": "user", "content": example["problem"]})
        messages.append({"role": "assistant", "content": example["solution"]})
    messages.append({"role": "user", "content": problem_description})
    
    chat_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages, 
        # temperature=0.5,
        # top_p=0.8,
        # max_tokens=2048,
        # extra_body={"repetition_penalty": 1.05},
    )
    return chat_response.choices[0].message.content

system_prompt = """
You are a CAD model generator assistant.

Given a natural language description of a 3D structure(There is some data, but it may not be complete), your task is to return a JSON object that describes a list of geometric parts and their parameters. 

If the input description is not within the following requirements, you need to strictly redesign the 3D structure data according to the following requirements.

Each part must include:
- `"shape"`: one of "box", "cylinder", "sphere", "cone", "torus", "ellipsoid"
- `"position"`: [x, y, z] float values
- `"rotation"`: [x_angle, y_angle, z_angle] float values in degrees (optional, default is [0, 0, 0])
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
      "color": "#ff0000",
      "opacity": 0.8
    },
    {
      "shape": "box",
      "size": [10, 5, 3],
      "position": [15, 0, 0],
      "rotation": [0, 0, 0],
    }
  ]
}
```

notice: you should not include the beginning ```json and ending ``` in the output, just return the JSON object directly.
Now generate the JSON structure for the following description:
"""

# ========== 可选：调用 OpenAI API 生成 JSON ==========
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
    try:
        return json.loads(output)
    except:
        print("LLM output not valid JSON:")
        print(output)
        raise

def text2json(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        prompt = f.read()
        
    print(f"Computing structure data ...")
    math_prompt = generate_math_prompt(prompt)
    
    print(math_prompt)

    print("Generating structure from LLM...")
    structure = call_llm(math_prompt)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2)
    print(f"Saved structure to {output_path}")