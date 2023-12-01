from pydub import AudioSegment


def m4a_to_wav(original_file_name):
    wav_filename = f"assets/torec/{original_file_name}.wav"

    sound = AudioSegment.from_file("assets/torec/" + original_file_name, format="m4a")
    sound = sound.set_channels(1)
    sound.export(wav_filename, format="wav")
