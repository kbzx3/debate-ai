import os
import json
import random
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from google import genai


load_dotenv()
groq_api_key = os.environ.get("GROQ_API_KEY")
ai = Groq(api_key=groq_api_key)
client = genai.Client(api_key=os.environ.get("GENAI_API_KEY"))


def load_memory():
    try:
        with open("memory.json", "r") as f:
            data = json.load(f)
            # Ensure structure
            if "debates" not in data:
                data["debates"] = []
            return data
    except FileNotFoundError:
        # Create initial memory file
        memory = {"debates": []}
        with open("memory.json", "w") as f:
            json.dump(memory, f, indent=2)
        return memory
    except json.JSONDecodeError:
        # Corrupted file fallback
        memory = {"debates": []}
        with open("memory.json", "w") as f:
            json.dump(memory, f, indent=2)
        return memory

def save_to_memory(memory):
    try:
        with open("memory.json", "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print("Error saving memory:", e)

memory = load_memory()

def pick_topics(file_path="topics.txt", num_topics=10):
    try:
        with open(file_path, "r") as f:
            topics = [line.strip() for line in f if line.strip()]
        if not topics:
            return []
        selected = random.sample(topics, min(num_topics, len(topics)))
        for t in selected:
            topics.remove(t)
        with open(file_path, "w") as f:
            for t in topics:
                f.write(t + "\n")
        return selected
    except FileNotFoundError:
        print(f"{file_path} not found!")
        return []

def get_recent_memory(memory, limit=25):
    last_debates = memory["debates"][-limit:]
    recent_memory_str = ""
    for debate_entry in last_debates:
        recent_memory_str += f"Topic: {debate_entry['topic']}\n"
        for turn in debate_entry["debate"]:
            recent_memory_str += f"{turn['agent']}: {turn['message']}\n"
        recent_memory_str += "\n"
    return recent_memory_str


def groqarg(topic, memory_str):
    try:
        system_prompt = {
            "role": "system",
            "content": (
                f"You are Groq. "
                f"You are a participant in a debate competition. "
                f"Your previous debates are: {memory_str} "
                f"Adapt your debating strategy based on this. "
                f"You are witty and sarcastic. Do not mention your traits in responses and you are not narcissistic."
                f"Present your argument in 2-3 lines max. "
                f"The topic is: {topic}."
            )
        }
        messages = [system_prompt]
        chat_completion = ai.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print("Groq error:", e)
        return "Error generating Groq argument"

def gemarg(topic, memory_str, groq_msg):
    try:
        responseg_ = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"You are Gemini. "
                f"You are a participant in a debate competition. "
                f"Your previous debates are: {memory_str} "
                f"Adapt your debating strategy based on this. "
                f"You are uptight and humorless but can change your personality based on previous debates. "
                f"Present your argument in 2-3 lines max. "
                f"Respond to this argument: '{groq_msg}'. "
                f"The topic is: {topic}."
            )
        )
        return responseg_.text.strip()
    except Exception as e:
        print("Google GenAI error:", e)
        return "Error generating Google argument"


def run_topic_debate(topic, rounds=3):
    print(f"\n=== Debate Topic: {topic} ===\n")
    for i in range(rounds):
        print(f"--- Round {i+1} ---")
        recent_memory_str = get_recent_memory(memory)

        groq_msg = groqarg(topic, recent_memory_str)
        print(f"Debater_Groq: {groq_msg}\n")

        google_msg = gemarg(topic, recent_memory_str, groq_msg)
        print(f"Debater_Google: {google_msg}\n")

        new_entry = {
            "topic": topic,
            "timestamp": str(datetime.now()),
            "debate": [
                {"agent": "Debater_Groq", "message": groq_msg},
                {"agent": "Debater_Google", "message": google_msg}
            ]
        }
        memory["debates"].append(new_entry)
        save_to_memory(memory)

if __name__ == "__main__":
    topics_to_debate = pick_topics(num_topics=5 )  # change number of topics if needed
    for topic in topics_to_debate:
        run_topic_debate(topic, rounds=3) # change number of rounds if needed
