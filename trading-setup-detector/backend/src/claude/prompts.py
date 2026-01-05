PATTERN_ANALYSIS_PROMPT = """Analyze this trading chart image and identify the chart pattern shown.

Please provide your analysis in the following JSON format:
{
    "pattern_identified": "Name of the chart pattern (e.g., Ascending Triangle, Double Top, Head and Shoulders)",
    "key_characteristics": [
        "List of key visual characteristics that define this pattern",
        "e.g., 'Higher lows forming ascending support line'",
        "e.g., 'Horizontal resistance at the top'"
    ],
    "entry_conditions": [
        "Conditions that would signal a valid entry",
        "e.g., 'Breakout above resistance with increased volume'",
        "e.g., 'Candle close above the pattern boundary'"
    ],
    "exit_conditions": [
        "Conditions for taking profit or exiting",
        "e.g., 'Target equal to pattern height projected from breakout'",
        "e.g., 'Break below the ascending support line'"
    ],
    "risk_level": "Low/Medium/High",
    "typical_duration": "How long this pattern typically takes to form/play out",
    "success_indicators": [
        "Signs that the pattern is playing out as expected",
        "e.g., 'Increasing volume on breakout'",
        "e.g., 'Clean retest of breakout level'"
    ],
    "failure_indicators": [
        "Signs that the pattern has failed",
        "e.g., 'Break below support with volume'",
        "e.g., 'False breakout with immediate reversal'"
    ],
    "additional_notes": "Any other relevant observations about this pattern"
}

Respond ONLY with valid JSON, no additional text."""


PATTERN_COMPARISON_PROMPT = """You are a professional technical analyst. Compare the current chart with the reference pattern to determine if there's a match.

Reference Pattern Analysis:
{pattern_analysis}

Instructions:
1. Examine both images carefully
2. Compare the current chart's price action with the reference pattern
3. Look for similar:
   - Price structure and shape
   - Key support/resistance levels forming
   - Trend line angles and convergence
   - Overall pattern formation stage

Respond with JSON in this exact format:
{{
    "is_match": true/false,
    "confidence_score": 0.0 to 1.0,
    "reasoning": "Detailed explanation of why this is or isn't a match",
    "pattern_stage": "early/forming/complete/broken",
    "key_similarities": ["List of matching characteristics"],
    "key_differences": ["List of differences from the reference"],
    "action_suggestion": "wait/prepare/ready to trade/avoid"
}}

Be conservative - only mark as a match if the pattern is clearly forming or complete.
Respond ONLY with valid JSON, no additional text."""
