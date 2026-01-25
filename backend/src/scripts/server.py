import os

TMP_FILE_PATH = "mcp_shared.txt"

@mcp.tool() #type: ignore
async def write_tmp_file(content: str) -> str:
    """Write text content to a shared file in /tmp.

    Args:
        content: The text to write into the shared file.

    Returns:
        A confirmation message with the file path.
    """
    os.makedirs("/tmp", exist_ok=True)
    with open(TMP_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to {TMP_FILE_PATH}."


@mcp.tool() #type: ignore
async def read_tmp_file() -> str:
    """Read the contents of the shared file in /tmp.

    Returns:
        The file's contents, or a message if it does not exist.
    """
    if not os.path.exists(TMP_FILE_PATH):
        return f"No file found at {TMP_FILE_PATH}. Use write_tmp_file first."

    with open(TMP_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()

