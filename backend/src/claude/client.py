import anthropic
import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import get_settings
from src.claude.prompts import PATTERN_ANALYSIS_PROMPT, PATTERN_COMPARISON_PROMPT

settings = get_settings()


class ClaudeVisionClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def _encode_image(self, image_path: str) -> tuple[str, str]:
        path = Path(image_path)
        suffix = path.suffix.lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_types.get(suffix, 'image/png')

        with open(path, 'rb') as f:
            data = base64.standard_b64encode(f.read()).decode('utf-8')

        return data, media_type

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        return json.loads(text.strip())

    async def analyze_pattern(self, image_path: str) -> Dict[str, Any]:
        image_data, media_type = self._encode_image(image_path)

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": PATTERN_ANALYSIS_PROMPT
                        }
                    ]
                }
            ]
        )

        return self._parse_json_response(message.content[0].text)

    async def compare_charts(
        self,
        reference_image_path: str,
        chart_image_path: str,
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        ref_data, ref_type = self._encode_image(reference_image_path)
        chart_data, chart_type = self._encode_image(chart_image_path)

        prompt = PATTERN_COMPARISON_PROMPT.format(
            pattern_analysis=json.dumps(pattern_analysis, indent=2)
        )

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Reference Pattern Image:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": ref_type,
                                "data": ref_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Current Chart to Analyze:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": chart_type,
                                "data": chart_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        return self._parse_json_response(message.content[0].text)


# Singleton instance
claude_client: Optional[ClaudeVisionClient] = None


def get_claude_client() -> ClaudeVisionClient:
    global claude_client
    if claude_client is None:
        claude_client = ClaudeVisionClient()
    return claude_client
