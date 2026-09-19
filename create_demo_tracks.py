import os
import wave
import math
import struct


def generate_synth_track(filename: str, duration_sec: float, base_freq: float, title: str):
    """Generates a pleasant melodic synth audio file."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration_sec)
    
    notes = [base_freq, base_freq * 1.25, base_freq * 1.5, base_freq * 1.75, base_freq * 2.0]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = i / sample_rate
            note_idx = int(t * 2) % len(notes)
            freq = notes[note_idx]
            
            # Envelope (soft fade in/out per note)
            note_t = (t * 2) % 1.0
            envelope = math.sin(math.pi * note_t)
            
            sample_l = math.sin(2 * math.pi * freq * t) * envelope * 0.3
            sample_r = math.sin(2 * math.pi * (freq * 1.005) * t) * envelope * 0.3
            
            int_l = int(sample_l * 32767)
            int_r = int(sample_r * 32767)
            
            data = struct.pack('<hh', int_l, int_r)
            wav_file.writeframesraw(data)
    print(f"Generated demo track: {filename}")


if __name__ == "__main__":
    demo_dir = os.path.join(os.path.dirname(__file__), "demo_music")
    os.makedirs(demo_dir, exist_ok=True)
    
    generate_synth_track(os.path.join(demo_dir, "Midnight_Chill_Synth.wav"), 12.0, 261.63, "Midnight Chill Synth")
    generate_synth_track(os.path.join(demo_dir, "Harmonix_Groove_Demo.wav"), 15.0, 329.63, "Harmonix Groove Demo")
    generate_synth_track(os.path.join(demo_dir, "Neon_Horizon_Waves.wav"), 10.0, 392.00, "Neon Horizon Waves")
