import os, json, sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def fix_pronunciation(text):
    """Fix common TTS pronunciation issues"""
    replacements = {
        'NO WAY': 'no way',
        'WOAH': 'woah',
        'INSANE': 'insane',
        'YOOO': 'yo',
        'NOO': 'no',
        'NOOO': 'nooo',
        'OMG': 'oh my god',
        'WTF': 'what the',
        'GG': 'good game',
        'LFG': "let's go",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_commentary(analysis):
    print("💬 Generating English commentary...")
    highlights = analysis.get('highlights', [])
    summary = analysis.get('summary', '')
    vibe = analysis.get('overall_vibe', 'action')

    prompt = f"""You are Nova, an energetic gaming influencer.

Video: {summary}
Vibe: {vibe}
{len(highlights)} highlights found.

Create commentary in JSON format:
{{
    "intro": "2-3 sentences, hype and exciting opener",
    "reactions": [
        {{
            "timestamp": {highlights[0]['timestamp'] if highlights else 10},
            "text": "1-2 sentences reaction. Use natural spelling for better TTS: 'woah' not 'WOAH', 'no way' not 'NO WAY'",
            "display_text": "Text with caps/emojis for on-screen display: WOAH! 🔥",
            "emotion": "excited",
            "energy_level": 8
        }}
    ],
    "outro": "call-to-action"
}}

IMPORTANT for TTS:
- Write reactions in LOWERCASE or sentence case (not ALL CAPS)
- Spell out abbreviations: "oh my god" not "OMG"
- Use natural spelling: "woah" not "WOAHHH"
- Keep emojis in display_text only, not in text field

Style: Energetic, casual English gaming slang, clean language."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You create English gaming content with proper TTS-friendly text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    result = response.choices[0].message.content
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].split("```")[0].strip()

    commentary = json.loads(result)

    # Fix pronunciation in text field
    commentary['intro'] = fix_pronunciation(commentary['intro'])
    commentary['outro'] = fix_pronunciation(commentary['outro'])
    for reaction in commentary['reactions']:
        reaction['text'] = fix_pronunciation(reaction['text'])

    return commentary

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 3_generate_commentary_EN_v2.py input/video_analysis.json")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        analysis = json.load(f)

    commentary = generate_commentary(analysis)
    output = sys.argv[1].replace('_analysis.json', '_commentary_v2.json')

    with open(output, 'w') as f:
        json.dump(commentary, f, indent=2)

    print(f"✅ Done! Saved: {output}")
