"""Code to download the transcripts from YouTube."""
from pytube import Playlist
import json
from youtube_transcript_api import YouTubeTranscriptApi


def get_playlist_info(url):
    playlist = Playlist(url)

    # Dict to hold title-ID pairs
    video_dict = {}

    for video in playlist.videos:
        video_dict[video.title] = video.video_id
        # print(video.title, video.video_id)

    return video_dict


def download_transcript(video_title, video_id, output_file):
    try:
        # Download transcript with youtube_transcript_api
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])

        # Save transcript to a JSON file
        with open(output_file, 'w', encoding='utf-8') as file:
            # Put the title and the video ID at the top of the JSON file and then dump the transcript
            json.dump({
                'title': video_title,
                'video_id': video_id,
                'transcript': transcript}, file, ensure_ascii=False, indent=4)

        print(f'Transcript has been saved to {output_file}')

    except Exception as e:
        print('An error occurred:', str(e))


def download_playlist(url):
    video_id_dict = get_playlist_info(url)

    for i, (video_title, video_id) in enumerate(video_id_dict.items()):
        output_file = 'Episode_' + str(i + 1) + '.json'
        download_transcript(video_title, video_id, output_file)


def create_chunked_data(file, max_chunk_size, min_overlap_size):
    with open(file, 'r') as f:
        json_file = json.load(f)

    # Replace \n with a space
    for segment in json_file['transcript']:
        segment['text'] = segment['text'].replace('\n', ' ')

    segment_lengths = [len(json_file['transcript'][segment]['text']) for segment in range(len(json_file['transcript']))]

    # Split the transcript into chunks
    chunks_indices = []

    current_beginning_index = 0
    current_ending_index = 0
    current_chunk_size = 0

    for current_index, segment_length in enumerate(segment_lengths):
        if current_chunk_size + segment_length + 1 < max_chunk_size:
            current_chunk_size += segment_length + 1
            current_ending_index = current_index
            continue
        chunks_indices.append((current_beginning_index, current_ending_index))
        current_chunk_size += segment_length
        current_ending_index = current_index

        while current_chunk_size > max_chunk_size - min_overlap_size:
            current_chunk_size -= segment_lengths[current_beginning_index] + 1
            current_beginning_index += 1
        current_chunk_size += 1

    # Now that we have the chunk indices, we can create the chunks
    chunks = [{
        'text': ' '.join(
            [segment['text'] for segment in json_file['transcript'][chunk_index[0]:chunk_index[1] + 1]]),
        'start': json_file['transcript'][chunk_index[0]]['start'],
        'duration': sum(
            [segment['duration'] for segment in json_file['transcript'][chunk_index[0]:chunk_index[1] + 1]])}
        for chunk_index in chunks_indices]

    return chunks
