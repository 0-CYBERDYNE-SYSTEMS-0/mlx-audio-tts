#!/usr/bin/env python3
"""
Example agent using TTS integration
"""

from scripts.agent_integration import initialize_tts, speak

def main():
    print("Initializing TTS...")
    tts = initialize_tts(auto_start=True)

    print("Generating speech...")
    audio = speak("Hello! I am an AI assistant with voice capabilities.")

    print(f"Generated {len(audio)} bytes of audio")

    # Here you would:
    # 1. Play the audio through speakers
    # 2. Or save it to a file
    # 3. Or stream it to a client

    # Example: Save to file
    with open("output.wav", "wb") as f:
        f.write(audio)
    print("Audio saved to output.wav")

if __name__ == "__main__":
    main()
