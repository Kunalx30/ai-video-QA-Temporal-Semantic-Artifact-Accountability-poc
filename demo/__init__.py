"""Demo and UI workbench package."""

def __getattr__(name: str):
    if name == "create_demo":
        from demo.gradio_app import create_demo
        return create_demo
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["create_demo"]
