"""
Generate English commentary scripts based on analysis
"""
import os
import json
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_commentary(analysis, influencer_name="Nova"):
    """Generate commentary scripts based on analysis"""
    print("💬 Generating commentary scripts...")

    highlights = analysis.get('highlights', [])
    summary = analysis.get('summary', '')
    vibe = analysis.get('overall_vibe', 'action')

    prompt = f"""You are "{influencer_name}", a young, energetic gaming influencer.
You give spontaneous, natural reactions to gameplay videos.

Video summary: {summary}
Overall vibe: {vibe}

{len(highlights)} interesting moments detected in this video:

"""

    for i, h in enumerate(highlights, 1):
        prompt += f"""
{i}. At {h['timestamp']:.1f} seconds:
   - What happened: {h['description']}
   - Why interesting: {h['why_interesting']}
   - Emotion: {h['emotion']}
   - Viral score: {h['viral_score']}/10
"""

    prompt += """

Your task:
1. Create a short intro for the video start (2-3 sentences, build excitement)
2. Natural reaction/comment for each highlight (1-2 sentences)
3. Outro for video end (call-to-action)

Important:
- Speak in casual English gaming slang (but keep it clean)
- Short and dynamic sentences
- You can use emojis (😱 🔥 💯 etc.)
- Natural reactions like "WOAH", "NO WAY", "INSANE", "LET'S GO"
- Talk to the audience ("Did you see that?", "Wait for it!", "Check this out!")

Respond in JSON format:
{
    "intro": "Video intro script",
    "reactions": [
        {
            "timestamp": 12.5,
            "text": "Reaction to this moment",
            "emotion": "surprised",
            "energy_level": 8
        }
    ],
    "outro": "Video outro script"
}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional gaming content writer. You create English content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    result_text = response.choices[0].message.content

    try:
        # JSON parse
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        commentary = json.loads(result_text)
        return commentary
    except json.JSONDecodeError:
        print("⚠️ JSON parse error:")
        print(result_text)
        return None

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python 3_generate_commentary_EN.py <analysis_json_file>")
        sys.exit(1)

    analysis_file = sys.argv[1]

    if not os.path.exists(analysis_file):
        print(f"❌ Analysis file not found: {analysis_file}")
        sys.exit(1)

    # Load analysis
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    # Generate commentary
    commentary = generate_commentary(analysis)

    if commentary:
        # Save
        output_file = analysis_file.replace('_analysis.json', '_commentary.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commentary, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Commentary scripts created!")
        print(f"\n📝 Intro: {commentary['intro'][:100]}...")
        print(f"💬 {len(commentary['reactions'])} reaction scripts")
        print(f"💾 Saved: {output_file}")
    else:
        print("❌ Failed to generate commentary!")

if __name__ == '__main__':
    main()
