from django.shortcuts import render, HttpResponse
from django.core.files.storage import FileSystemStorage
from youtube_search import YoutubeSearch
from pytube import YouTube
import os
import pytube
from pydub import AudioSegment
from django.conf import settings
from django.core.mail  import EmailMessage
import sys 
import shutil

# AudioSegment.converter = "C:/ffmpeg/bin/ffmpeg.exe"

def searchtube(artist, songNumber,folderpath):
    print("int search tube")
    results = YoutubeSearch(artist, max_results=songNumber).to_dict()
    s = 'www.youtube.com'
    urls = []
    for value in results:
        urls.append(s+value['url_suffix'])

    for url in urls:
        audio = YouTube(url)
        video_length = audio.length
        if video_length is not None:
            video_length = int(video_length)
        else:
            video_length = 0
        if video_length > 300 and video_length==0:  # 300 seconds = 5 minutes
            continue
        try:
            audio_stream = audio.streams.filter(only_audio=True).first()
        except pytube.exceptions.LiveStreamError as e:
            print("The video is currently streaming live and cannot be loaded.")
        if int(audio_stream.filesize) > 10 * 1024 * 1024:  # 10 MB
            continue
        if audio_stream.is_live:
            continue
        out_file = audio_stream.download(output_path=folderpath)
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)

def extract_and_merge_audio(folder_path, extract_seconds, output_file):
    audio_segments = []
    # Traverse through all the audio files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3") or filename.endswith(".wav"):
            file_path = os.path.join(folder_path, filename).replace('\\','/')
            print(file_path)
            audio = AudioSegment.from_file(file_path)
            
            # Extract the specified number of seconds from the audio
            start = 0
            end = start + extract_seconds * 1000
            extracted_audio = audio[start:end]
            audio_segments.append(extracted_audio)

   #Merge all the extracted audio clips into a single audio
    merged_audio = sum(audio_segments)
    merged_audio.export(output_file, format="mp3")


# Create your views here.
def index(request):
    if request.method == 'POST':
        singer_name = request.POST['singer-name']
        number_of_songs = int(request.POST['number-of-songs'])
        number_of_seconds = int(request.POST['number-of-seconds'])
        print(type(number_of_seconds))
        email = request.POST['email']
        folderpath='./media/ytvd' #check
        outputfilepath='./media/output.mp3' #check

        searchtube(singer_name,number_of_songs,folderpath)
        extract_and_merge_audio(folderpath,number_of_seconds,outputfilepath )

        subject = 'MASHUP CREATED'
        message = 'Result audio for your input'
        email_from = settings.EMAIL_HOST_USER
        recipient_list =[email]
        email = EmailMessage(subject, message, email_from, recipient_list)
        email.attach_file('./media/output.mp3')
        email.send()
        print("MAIL SENT")
        os.remove('./media/output.mp3')
        # filesPath = './media/ytvd/*'
        # for f in filesPath:
        shutil.rmtree('./media/ytvd')




    return render(request,'index.html')

