import os
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any

from .services.comparator import Comparator
from .utils.helpers import format_response, load_env_file
from .config import AVAILABLE_MODELS

# Load environment variables
load_env_file()

app = FastAPI(
    title="Multi-AI",
    description="Compare responses from multiple LLM providers",
    version="0.1.0",
)

# Set up static files and templates
app.mount("/static", StaticFiles(directory="multi_ai/static"), name="static")
templates = Jinja2Templates(directory="multi_ai/templates")

# Initialize the comparator
comparator = Comparator()
# Create a second instance for blending
blending_comparator = Comparator(use_blending=True)


class CompareRequest(BaseModel):
    prompt: str = Field(..., description="The prompt to send to the models")
    models: Optional[Dict[str, str]] = Field(
        None, description="Optional mapping of provider to model names"
    )
    blend: bool = Field(
        False, description="Whether to blend responses instead of selecting one"
    )
    include_details: bool = Field(
        False,
        description="Whether to include detailed evaluation information in the response",
    )


class CompareResponse(BaseModel):
    result: str = Field(..., description="The selected or blended response")
    success: bool = Field(..., description="Whether the comparison was successful")
    explanation: Optional[str] = Field(
        None, description="Explanation of the judge's decision or blending process"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Optional detailed evaluation information"
    )

    # Allow additional fields to be included in the response
    model_config = ConfigDict(extra="allow")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the HTML frontend"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/models")
async def list_models():
    """List all available models by provider"""
    return {"models": AVAILABLE_MODELS}


@app.post("/compare", response_model=CompareResponse)
async def compare_models(request: CompareRequest = Body(...)):
    """
    Compare responses from multiple LLM providers and return the best one
    or a blended response based on the judge's evaluation
    """
    try:
        # Select the appropriate comparator based on blend option
        selected_comparator = blending_comparator if request.blend else comparator

        # Execute the comparison
        result = await selected_comparator.compare(request.prompt, request.models)

        # Format the response
        formatted = format_response(result, request.include_details)

        # Ensure explanation is at top level if it exists in the original result
        if (
            request.include_details
            and "explanation" in result
            and "explanation" not in formatted
        ):
            formatted["explanation"] = result.get("explanation")

        return formatted

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
