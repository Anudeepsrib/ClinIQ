import asyncio
import base64
from unittest.mock import AsyncMock, patch
from PIL import Image
import io

from app.chat.local_llm_adapter import local_llm_adapter
from app.core.config import settings

async def test_hostname_security():
    print("Testing Security (Localhost Restriction)...")
    try:
        local_llm_adapter._validate_localhost("http://malicious.com:11434")
        print("FAIL: Malicious URL allowed")
    except ValueError as e:
        print(f"PASS: {e}")

async def test_image_resizing():
    print("\nTesting Image Optimization (1120x1120)...")
    # Create large dummy image (2000x2000)
    img = Image.new('RGB', (2000, 2000), color='red')
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    resized_b64 = local_llm_adapter._resize_image(img_b64)
    
    # Check size of resized image
    resized_data = base64.b64decode(resized_b64)
    resized_img = Image.open(io.BytesIO(resized_data))
    print(f"Original size: 2000x2000, Optimized size: {resized_img.size}")
    if resized_img.size[0] <= 1120 and resized_img.size[1] <= 1120:
        print("PASS: Image resized correctly")
    else:
        print(f"FAIL: Image too large {resized_img.size}")

async def test_ollama_payload():
    print("\nTesting Ollama Payload Format...")
    settings.LLM_PROVIDER = "ollama"
    
    # Mocking httpx.AsyncClient as a context manager
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Gemma test"}}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await local_llm_adapter.generate_response("hello", "sys")
        
        args, kwargs = mock_client.post.call_args
        payload = kwargs["json"]
        print(f"Ollama Payload Model: {payload['model']}")
        if "images" in payload["messages"][1]:
            print("PASS: Multimodal structure present")
        else:
            print("FAIL: Multimodal structure missing")

if __name__ == "__main__":
    from unittest.mock import MagicMock
    asyncio.run(test_hostname_security())
    asyncio.run(test_image_resizing())
    asyncio.run(test_ollama_payload())
