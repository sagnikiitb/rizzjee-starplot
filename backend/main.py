from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import io
import base64
import json
import ast
import sys
import contextlib
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import traceback
import mpld3

app = FastAPI(title="Plot Server API")

# Configure CORS to allow requests from your Next.js app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your Next.js domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str
    plot_type: str = "2d"  # "2d" or "3d"
    format: str = "interactive"  # "interactive", "png", "svg"
    width: int = 800
    height: int = 600

@app.get("/")
def read_root():
    return {"message": "Plot Server API is running"}

@app.post("/generate-plot")
async def generate_plot(request: CodeRequest):
    try:
        # Safety check - basic validation of Python code
        ast.parse(request.code)
        
        # Prepare output capture
        output_buffer = io.StringIO()
        
        # Setup figure with specified dimensions
        plt.figure(
            figsize=(int(request.width)/100, int(request.height)/100),
            dpi=100,
            facecolor=getattr(request, "facecolor", "lightblue"),
            edgecolor=getattr(request, "edgecolor", "darkblue")
        )

        
        # For 3D plots, explicitly create a 3D axis
        if request.plot_type == "3d":
            ax = plt.axes(projection='3d')
            
        # Execute the code with restricted globals
        plot_globals = {
            'plt': plt,
            'np': np,
            'Axes3D': Axes3D,
            'figure': plt.figure,
            'ax': plt.gca(),
        }
        
        # Redirect stdout/stderr and execute code
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            exec(request.code, plot_globals)
        
        # Get any print output
        output_text = output_buffer.getvalue()
        
        # Generate appropriate response based on format
        if request.format == "interactive":
            # Use mpld3 to convert to interactive HTML/JS
            try:
                plot_html = mpld3.fig_to_html(plt.gcf())
                plt.close()
                return JSONResponse(content={
                    "success": True,
                    "format": "interactive",
                    "plot": plot_html,
                    "output": output_text
                })
            except Exception as e:
                # Fallback to PNG if mpld3 conversion fails
                img_data = render_plot_to_base64()
                plt.close()
                return JSONResponse(content={
                    "success": True,
                    "format": "png",
                    "plot": img_data,
                    "output": output_text,
                    "conversion_error": str(e)
                })
        
        elif request.format == "svg":
            # Generate SVG
            svg_io = io.StringIO()
            plt.savefig(svg_io, format='svg')
            svg_io.seek(0)
            svg_data = svg_io.getvalue()
            plt.close()
            return JSONResponse(content={
                "success": True, 
                "format": "svg",
                "plot": svg_data,
                "output": output_text
            })
        elif request.format == "threejs" and request.plot_type == "3d":
            # Extract surface data from plot_globals
            try:
                X = plot_globals.get("X")
                Y = plot_globals.get("Y")
                Z = plot_globals.get("Z")

                if X is None or Y is None or Z is None:
                    raise ValueError("Variables X, Y, Z (meshgrid) not found in user code.")

                # Flatten and build vertex list
                vertices = []
                faces = []
                rows, cols = X.shape
                for i in range(rows):
                    for j in range(cols):
                        vertices.append([float(X[i, j]), float(Y[i, j]), float(Z[i, j])])
                for i in range(rows - 1):
                    for j in range(cols - 1):
                        a = i * cols + j
                        b = a + 1
                        c = a + cols
                        d = c + 1
                        faces.append([a, b, d])
                        faces.append([a, d, c])

                # Build HTML with embedded three.js
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Three.js 3D Surface</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body style="margin:0">
<canvas id="three-canvas"></canvas>
<script>
    const vertices = {json.dumps(vertices)};
    const faces = {json.dumps(faces)};
    const canvas = document.getElementById("three-canvas");
    const renderer = new THREE.WebGLRenderer({{canvas}});
    renderer.setSize(window.innerWidth, window.innerHeight);
    
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);

    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(10, 10, 10);
    camera.lookAt(0, 0, 0);

    const geometry = new THREE.BufferGeometry();
    const positions = [];
    for (let v of vertices) {{
        positions.push(...v);
    }}
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));

    const indices = [];
    for (let f of faces) {{
        indices.push(...f);
    }}
    geometry.setIndex(indices);
    geometry.computeVertexNormals();

    const material = new THREE.MeshStandardMaterial({{color: 0x3399ff, flatShading: true, side: THREE.DoubleSide}});
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(10, 10, 10);
    scene.add(light);

    function animate() {{
        requestAnimationFrame(animate);
        mesh.rotation.y += 0.005;
        renderer.render(scene, camera);
    }}
    animate();
</script>
</body>
</html>
"""
                plt.close()
                return JSONResponse(content={
                    "success": True,
                    "format": "threejs",
                    "plot": html_content,
                    "output": output_text
                })

            except Exception as e:
                plt.close()
                return JSONResponse(status_code=400, content={
                    "success": False,
                    "error": f"Three.js generation failed: {str(e)}",
                    "traceback": traceback.format_exc(),
                    "output": output_text
                })



        
            
        else:  # Default to PNG
            img_data = render_plot_to_base64()
            plt.close()
            return JSONResponse(content={
                "success": True,
                "format": "png", 
                "plot": img_data,
                "output": output_text
            })
            
    except Exception as e:
        plt.close()
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "traceback": traceback_str,
                "output": output_buffer.getvalue() if 'output_buffer' in locals() else ""
            }
        )

def render_plot_to_base64():
    """Convert the current matplotlib plot to base64 PNG."""
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return img_data

@app.get("/examples")
def get_examples():
    """Return a list of example plots with code."""
    examples = [
        {
            "title": "Basic Line Plot",
            "code": """
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 10, 100)
y = np.sin(x)
plt.plot(x, y)
plt.title('Sine Wave')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
""",
            "plot_type": "2d",
            "description": "A simple sine wave line plot"
        },
        {
            "title": "Scatter Plot",
            "code": """
import numpy as np
import matplotlib.pyplot as plt

# Generate random data
np.random.seed(42)
x = np.random.rand(50)
y = np.random.rand(50)
colors = np.random.rand(50)
sizes = 1000 * np.random.rand(50)

plt.scatter(x, y, c=colors, s=sizes, alpha=0.5)
plt.colorbar(label='Color Value')
plt.title('Scatter Plot with Random Data')
plt.xlabel('X Value')
plt.ylabel('Y Value')
""",
            "plot_type": "2d",
            "description": "A scatter plot with random data points"
        },
        {
            "title": "3D Surface Plot",
            "code": """
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Create data
x = np.linspace(-5, 5, 50)
y = np.linspace(-5, 5, 50)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

# Plot surface
surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

ax.set_title('3D Surface Plot')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
""",
            "plot_type": "3d",
            "description": "A 3D surface plot showing a ripple pattern"
        },
        {
            "title": "Multiple Subplots",
            "code": """
import numpy as np
import matplotlib.pyplot as plt

# Create a figure with 2x2 subplots
fig, axs = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('Multiple Subplots Example')

# Subplot 1: Line plot
x1 = np.linspace(0, 10, 100)
axs[0, 0].plot(x1, np.sin(x1))
axs[0, 0].set_title('Sine Wave')

# Subplot 2: Scatter plot
x2 = np.random.rand(50)
y2 = np.random.rand(50)
axs[0, 1].scatter(x2, y2, c='red', alpha=0.5)
axs[0, 1].set_title('Random Scatter')

# Subplot 3: Bar chart
categories = ['A', 'B', 'C', 'D']
values = [3, 7, 2, 5]
axs[1, 0].bar(categories, values)
axs[1, 0].set_title('Bar Chart')

# Subplot 4: Histogram
data = np.random.normal(0, 1, 1000)
axs[1, 1].hist(data, bins=30)
axs[1, 1].set_title('Histogram')

plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout
""",
            "plot_type": "2d",
            "description": "Four different plot types in subplots"
        }
    ]
    return {"examples": examples}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
