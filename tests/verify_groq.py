import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.resume_processor import ResumeProcessor

async def test_groq_integration():
    print("Testing Groq Integration (SDK)...")
    
    # Test initialization
    api_key = "test_key"
    
    # Mock AsyncGroq client
    with patch("services.resume_processor.AsyncGroq") as mock_groq_cls:
        mock_client = AsyncMock()
        mock_groq_cls.return_value = mock_client
        
        processor = ResumeProcessor(api_key)
        
        # Verify client initialization
        mock_groq_cls.assert_called_with(api_key=api_key)
        assert processor.model == "llama-3.3-70b-versatile"
        print("✅ Initialization successful")
        
        # Mock chat completion response
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"skills": ["Python"], "experience": [], "education": [], "projects": []}'
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Test extract_structured_data_with_groq
        print("Testing extract_structured_data_with_groq...")
        result = await processor.extract_structured_data_with_groq("Sample resume text")
        
        assert "skills" in result
        assert result["skills"] == ["Python"]
        print("✅ Extraction logic successful")
        
        # Verify API call arguments
        call_args = mock_client.chat.completions.create.call_args
        kwargs = call_args[1]
        
        assert kwargs["model"] == "llama-3.3-70b-versatile"
        assert kwargs["temperature"] == 0.1
        assert len(kwargs["messages"]) == 2
        print("✅ SDK call arguments verified")

if __name__ == "__main__":
    asyncio.run(test_groq_integration())
