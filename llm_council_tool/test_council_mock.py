
import asyncio
from unittest.mock import MagicMock, patch
import pytest
from llm_council import Tools

# Mock response data
MOCK_STAGE_1_RESPONSES = {
    "llama3:latest": "Response from Llama3: The sky is blue due to Rayleigh scattering.",
    "gpt-4o": "Response from GPT-4o: Blue light is scattered more than other colors because it travels as shorter, smaller waves.",
}

MOCK_STAGE_2_RANKINGS = {
    "llama3:latest": "FINAL RANKING:\n1. Response B\n2. Response A",
    "gpt-4o": "FINAL RANKING:\n1. Response A\n2. Response B",
}

MOCK_CHAIRMAN_RESPONSE = "Final Synthesis: Both models agree on Rayleigh scattering. The sky is blue."

MOCK_AVAILABLE_MODELS = {
    "data": [
        {"id": "llama3:latest", "object": "model"},
        {"id": "gpt-4o", "object": "model"},
        {"id": "mistral:latest", "object": "model"}
    ]
}

def mock_requests_get(url, headers, timeout):
    mock_resp = MagicMock()
    if "/models" in url:
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_AVAILABLE_MODELS
        return mock_resp
    return mock_resp

def mock_requests_post(url, headers, json, timeout):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    
    model = json.get("model")
    messages = json.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    
    content = ""
    
    # Simple heuristic to determine stage
    if "FINAL RANKING:" in last_msg: 
        content = MOCK_STAGE_2_RANKINGS.get(model, "FINAL RANKING:\n1. Response A")
    elif "Chairperson" in last_msg:
        content = MOCK_CHAIRMAN_RESPONSE
    else:
        content = MOCK_STAGE_1_RESPONSES.get(model, f"Response from {model}")

    mock_resp.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": content}}]
    }
    return mock_resp

@pytest.mark.asyncio
async def test_consult_council():
    tools = Tools()
    # Request a mix of valid and invalid models
    tools.valves.council_models = "llama3:latest,gpt-4o,invalid-model" 
    tools.valves.chairperson_model = "gpt-4o"
    tools.valves.openwebui_api_key = "test-key"

    mock_emitter = MagicMock()
    async def async_emitter(x):
        mock_emitter(x)

    with patch("requests.post", side_effect=mock_requests_post) as mock_post, \
         patch("requests.get", side_effect=mock_requests_get) as mock_get:
        
        result = await tools.consult_council("Why is the sky blue?", __event_emitter__=async_emitter)
        
        print(f"\nResult: {result}")
        
        assert result == MOCK_CHAIRMAN_RESPONSE
        
        # Verification:
        # 1. GET /models called once
        mock_get.assert_called_once()
        
        # 2. Check that 'invalid-model' was NOT queried in Stage 1
        # Extract all models called in POST requests
        called_models = [call.kwargs['json']['model'] for call in mock_post.mock_calls]
        assert "invalid-model" not in called_models
        assert "llama3:latest" in called_models
        assert "gpt-4o" in called_models 
        
if __name__ == "__main__":
    # Manually running the async test if executed as script
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    from unittest.mock import AsyncMock
    
    # Patch requests.post globally for this simple run
    with patch("requests.post", side_effect=mock_requests_post), \
         patch("requests.get", side_effect=mock_requests_get):
        t = Tools()
        t.valves.council_models = "llama3:latest,gpt-4o"
        t.valves.chairperson_model = "gpt-4o"
        t.valves.openwebui_api_key = "test-key-manual"  # Added API Key
        
        async def run():
            print("Running Consult Council...")
            res = await t.consult_council("Test Topic")
            print("Final Result:", res)
            
        loop.run_until_complete(run())
