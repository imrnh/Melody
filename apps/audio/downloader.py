from pytube import YouTube
from pydub import AudioSegment
import os, uuid


class MusicDownloader:
    def download_youtube_video(self, url, output_path):
        try:
            yt = YouTube(url)

            video_stream = yt.streams.filter(file_extension='mp4').first()

            random_filename = str(uuid.uuid4())
            video_filename = f"{random_filename}.mp4"
            video_stream.download(output_path, filename=video_filename)

            print(f"Video downloaded successfully to: {output_path}/{video_filename}")

            return video_filename

        except Exception as e:
            print(f"Error from download_youtube_video: {e}")

    def convert_video_to_wav(self, input_file, output_file, channels=1):

        audio = AudioSegment.from_file(input_file, format="mp4")
        print(audio)
        audio = audio.set_channels(channels)
        audio.export(output_file, format="wav")

        print(f"Audio converted to: {output_file}")

        # except Exception as e:
        #     print(f"Error from convert_video_to_wav: {e}")

    def remove_video(self, video_file):
        try:
            os.remove(video_file)
            print(f"Original video file removed: {video_file}")
        except Exception as e:
            print(f"Error from remove_video: {e}")

    def download_and_convert(self, video_url):
        video_url = video_url
        temporary_directory = "assets/tmp"
        audio_output_directory = "assets/audio"

        video_file = self.download_youtube_video(video_url, temporary_directory)
        video_file_path = f"{temporary_directory}/{video_file}"

        output_wav_file = f"{audio_output_directory}/{video_file.replace('.mp4', '.wav')}"
        self.convert_video_to_wav(video_file_path, output_wav_file, channels=1)
        self.remove_video(video_file_path)

        return output_wav_file
