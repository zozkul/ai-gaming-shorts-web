#!/usr/bin/env python3
import os, sys, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_veo3_prompt(clip, game_name):
    title = clip['title']
    description = clip['description']
    emotion = clip.get('emotion', 'excited')
    viral_score = clip.get('viral_score', 8)
    start_time = clip.get('start_time', 0)
    end_time = clip.get('end_time', start_time + 12)
    duration = end_time - start_time

    prompt_request = f"""Create a Veo3 video prompt for a realistic gaming streamer reacting to this {game_name} moment:

CLIP: {title}
DESCRIPTION: {description}
EMOTION: {emotion} | VIRAL SCORE: {viral_score}/10 | DURATION: {duration:.0f}s

STREAMER REQUIREMENTS:
- Young streamer (20-25), casual hoodie/t-shirt, at gaming desk
- Hands ALWAYS on keyboard and mouse, eyes on screen
- Natural reactions - NOT exaggerated, NOT fake wide eyes
- Webcam angle from chest up, RGB background lighting
- Speaks naturally like real Twitch/YouTube streamer

TIMELINE:
- 0-4s: Focused gaming, quiet commentary ("okay okay...", "come on come on...")
- 4-8s: Genuine reaction TO THIS SPECIFIC MOMENT: "{description}"
- 8-13s: Follow-up ("chat did you see that?!", "that was insane!", "let's GO!")

Return JSON:
{{"prompt": "...", "duration": 13, "dialogue": {{"build_up": "0-4s speech", "peak_reaction": "4-8s speech", "aftermath": "8-13s speech"}}}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You create Veo3 prompts for gaming content."},
            {"role": "user", "content": prompt_request}
        ],
        temperature=0.8, max_tokens=1000
    )
    result = response.choices[0].message.content
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].split("```")[0].strip()
    return json.loads(result)

def process_clips(game_name):
    metadata_file = f"games/{game_name}/clips/clips_metadata.json"
    if not os.path.exists(metadata_file):
        print(f"❌ No clips metadata found: {metadata_file}")
        return False

    print("=" * 60)
    print("🎨 VEO3 PROMPT GENERATOR")
    print("=" * 60)

    with open(metadata_file) as f:
        data = json.load(f)

    clips = data['clips']
    print(f"\n📹 Found {len(clips)} clips for {game_name}\n")
    prompts = []

    for i, clip in enumerate(clips, 1):
        clip_num = f"{i:02d}"
        print(f"🎬 Clip {i}/{len(clips)}: {clip['title']}")
        veo3_data = generate_veo3_prompt(clip, game_name)
        dialogue = veo3_data.get('dialogue', {})
        clip['veo3_prompt'] = veo3_data['prompt']
        clip['veo3_dialogue'] = dialogue
        prompts.append({
            'clip_number': i,
            'clip_title': clip['title'],
            'veo3_prompt': veo3_data['prompt'],
            'dialogue': dialogue,
            'output_filename': f"clip_{clip_num}_influencer.mp4"
        })
        print(f"   ✅ Prompt ready ({len(veo3_data['prompt'])} chars)")
        print(f"   🗣️  0-4s:  \"{dialogue.get('build_up', '')}\"")
        print(f"   🗣️  4-8s:  \"{dialogue.get('peak_reaction', '')}\"")
        print(f"   🗣️  8-13s: \"{dialogue.get('aftermath', '')}\"\n")

    prompts_file = f"games/{game_name}/clips/veo3_prompts.json"
    with open(prompts_file, 'w') as f:
        json.dump({'game': game_name, 'total_prompts': len(prompts), 'prompts': prompts}, f, indent=2, ensure_ascii=False)
    with open(metadata_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"✅ {len(prompts)} prompts saved to: {prompts_file}")
    print(f"\nNEXT: python3 AUTOMATION_MASTER.py {game_name} combine")
    print("(after placing influencer videos in games/{game_name}/influencers/)")
    print("=" * 60)
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 2_generate_veo3_prompts.py <game_name>")
        sys.exit(1)
    process_clips(sys.argv[1])
