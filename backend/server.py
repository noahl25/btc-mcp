if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    import os
    load_dotenv()
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=os.getenv("ENV") == "development", reload_excludes=["builds/*", "builds\\*"])