import os
import uuid
import docker
import docker.types
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import ast
import shutil

mcp_server = APIRouter()
client = docker.from_env()

BUILD_DIR = "builds"
os.makedirs(BUILD_DIR, exist_ok=True)

def parse_docstring(docstring: str | None):
    if not docstring:
        return {"description": "", "args": "", "returns": ""}

    lines = docstring.splitlines()
    
    description_lines = []
    args = {}
    returns_lines = []

    current_section = "description"
    for line in lines:
        if len(line) == 0:
            continue

        stripped = line.strip()
        if stripped.startswith("Args:") or stripped.startswith("Arguments:"):
            current_section = "args"
            continue
        elif stripped.startswith("Returns:") or stripped.startswith("Return:"):
            current_section = "returns"
            continue

        if current_section == "description":
            description_lines.append(line)
        elif current_section == "args":
            args[line.split(":")[0].strip()] = line.split(":")[1].strip()
        elif current_section == "returns":
            returns_lines.append(line.strip())

    description = "\n".join(description_lines).strip()
    returns = "\n".join(returns_lines).strip()

    return {"description": description, "args": args, "returns": returns}


@mcp_server.post("/deploy")
async def deploy_mcp(cpu: float, ram: int, tmpfs: int, mcp: UploadFile = File(...), requirements: UploadFile = File(None), env: UploadFile = File(None)):
    unique_id = str(uuid.uuid4())
    server_dir = os.path.join(BUILD_DIR, unique_id)
    os.makedirs(server_dir, exist_ok=True)

    if ram < 128 or ram > 1024 or cpu > 100 or cpu < 1 or tmpfs > 1024 * 5:
        return { "status": "failed", "error": "Invalid configuration." }

    code_path = os.path.join(server_dir, "server.py")
    mcp_file = await mcp.read()
    tree = ast.parse(mcp_file)
    if not all(isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef) for node in tree.body):
        return { "status": "failed", "error": "MCP file must only contain function definitions." }
    with open(code_path, "wb") as f:
        f.write(f"\nfrom mcp.server.fastmcp import FastMCP\nimport uvicorn\nimport os\nmcp=FastMCP(name='{unique_id}',json_response=False,stateless_http=False)\nos.chdir('tmp')\n\n".encode(encoding="utf-8") + mcp_file + "\n\nif __name__=='__main__': uvicorn.run(mcp.streamable_http_app,host='0.0.0.0',port=8080,factory=True,log_level='info')".encode(encoding="utf-8"))

    tools = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            has_mcp_tool = any(
                isinstance(d, ast.Call) and getattr(d.func, 'attr', '') == 'tool'
                or isinstance(d, ast.Attribute) and d.attr == 'tool'
                for d in node.decorator_list
            )
            if has_mcp_tool:
                tool_name = node.name
                docstring = ast.get_docstring(node)
                tools[tool_name] = docstring

    requirements_path = os.path.join(server_dir, "requirements.txt")
    with open(requirements_path, "wb") as f:
        f.write((await requirements.read() if requirements is not None else "".encode(encoding="utf-8")) + "\n\nmcp\nuvicorn[standard]".encode(encoding="utf-8"))

    dockerfile = f"""FROM python:3.12-slim
WORKDIR /app
COPY server.py /app/server.py
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "server.py"]
    """
    dockerfile_path = os.path.join(server_dir, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile)

    image_tag = f"mcp-server:{unique_id}"
    try:
        client.images.build(path=server_dir, tag=image_tag)
        shutil.rmtree(server_dir)
    except Exception as e:
        return JSONResponse({ "error": str(e), "status": "failed" }, status_code=400)\
    
    environment = {}
    if env is not None:
        text = (await env.read()).decode(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                environment[key.strip()] = val.strip()

    try:
        container = client.containers.run(
            image_tag,
            detach=True,
            name=f"mcp-server-{unique_id}",
            ports={ "8000/tcp": ("127.0.0.1", 0) },
            mem_limit=f"{ram}m",
            cpu_count=int(cpu * 10000000),
            network_mode="bridge",
            tmpfs={"/tmp": f"size={tmpfs}m"},
            read_only=True,
            environment=environment,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            pids_limit=64,
            ulimits=[
                docker.types.Ulimit(name="nofile", soft=64, hard=64),
                docker.types.Ulimit(name="nproc", soft=64, hard=64),
            ]
        )
    except Exception as e:
        return JSONResponse({ "error": str(e), "status": "failed" }, status_code=500)

    container.reload()
    port_info = container.attrs['NetworkSettings']['Ports']
    host_port = port_info['8080/tcp'][0]['HostPort']
    endpoint = f"http://localhost:{host_port}"

    return { "status": "success" }
