import speech_recognition as sr
import webbrowser as op
import requests
import yt_dlp
import time
import joblib
import re
import gradio as gr
import os

PASSWORD = 'Sairam@970#'
def verify_password(pswd):
    if pswd == PASSWORD:
        return(
            gr.update(visible=True),
            gr.update(visible=True),
            'Access Granted !',
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    else:
        return(
            gr.update(visible=False),
            gr.update(visible=False),
            'Invalid Credentials ! Please Login with correct credentials',
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )

def open_website(link):
    op.open(link)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|∩╜£]','',name)

def playing_music_download(song_name,progress=gr.Progress()):
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str','0%')
            progress(percent.strip())
    options = {
        'format':'best[ext=mp4]/best',
        'quiet':True,
        'default_search':'ytsearch1',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist':True,
        'progress_hooks':[progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(song_name,download=True)
            entry = info['entries'][0] if 'entries' in info else info
            filename = sanitize_filename(ydl.prepare_filename(entry))
            title = entry['title']  
        
        return filename

    except Exception as e:
        print('Error:',e)
        print('Sorry, Our music library is limited...Please Choose another song !')

        return None   
def fetching_news():
    api_key = '904716fee400b0ccd9210e82f10353fb'
    url = f'https://api.mediastack.com/v1/news?access_key={api_key}&countries=in'
    response = requests.get(url,timeout = 10)
    news = response.json() if response.status_code==200 else {'data':[]}
    headlines = []
    for i in news.get('data',[]):
        headline = i.get('title','No Title')
        source = i.get('source','Unknown Source')
        headlines.append(f'{source}--->{headline}')
    return headlines
    
def recognition(audio):
    r = sr.Recognizer()
    if audio is None:
        return None
    try:
        with sr.AudioFile(audio) as source:
            audio_data = r.record(source)
            user = r.recognize_google(audio_data)
            return user
    except Exception:
        return 'Your Voice is not Recognized by Chitti'

def extract_website(sentence):
    doc = sentence.lower()
    site_pattern = r"(https?://\S+|www\.\S+|\w+\.(com|in|org|net|io))"
    match = re.search(site_pattern,doc)
    if match:
        return match.group(0)
    verb_pattern = r'(open|visit|search|go to|launch)\s+(\w+)'
    match = re.search(verb_pattern,doc)
    if match:
        return match.group(2)
    words = doc.split()
    for i in words:
        if i.isalpha() and len(i)>2:
            return i
    return None

def model_activation(history,state,audio,code_text):
    user = None
    if code_text and code_text.strip() != '':
        user = code_text.lower()
    elif audio is not None:
        user = recognition(audio)
        if user:
            user = user.lower()
    if not user:
        history.append({'role':'assistant',
                        'content':'Code word is needed to activate Chitti....'})
        return history,gr.update(value=None),history,gr.update(interactive=False),gr.update(),gr.update()
    if 'chitti' not in user:
        warning = 'Warning: The Chitti cannot be activated without the Code Word'
        history.append({"role": "assistant", "content": warning})
        return history,gr.update(value=None),history,gr.update(interactive=False),gr.update(),gr.update()
    
    response = 'speak.......How can i help you ?'
    history.append({'role':'user','content':user})
    history.append({'role':'assistant','content':response})
    return history,gr.update(value=None,visible=True),history.copy(),gr.update(interactive=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=True)

try:
    model = joblib.load('intent_based_model.pkl')
except Exception as e:
    print('Model Loading Failed:',e)
    model = None
    
def find_intent(audio1):
    command = recognition(audio1)
    if not command:
        return 'Unknown',''
    command = command.lower()
    intent = model.predict([command])[0] if model else 'Unknown'
    return intent,command

def command_processing(audio1,history,command_text):
    file_path = None
    if command_text and command_text.strip() != '':
        command = command_text.lower()
        intent = model.predict([command])[0] if model else 'Unknown'
    elif audio1 is not None:
        intent,command = find_intent(audio1)
    else:
        history.append({'role':'assistant',
                        'content':'Please provide a voice or typed command'})
        return history,history.copy(),gr.update(value=file_path,visible=True),gr.update(value=None)
    if intent == 'music':
        history.append({'role':'user','content':command})
        history.append({'role':'assistant','content':'Downloading Video.....Please Wait..'})
        file_path = playing_music_download(command)
        if file_path:
            return history,history,gr.update(value=file_path,visible=True)
        else:
            response = 'Download Failed'
            history.append({'role':'assistant','content':response})
            return history,history.copy(),gr.update(visible=False),gr.update(value=None)
    elif intent == 'news':
        headlines = fetching_news()
        response = (
            'Chitti: Here is the latest news for you......\n\n'
            + '\n'.join(headlines[:20])
            ) if headlines else 'Chitti: No News Found !'
        histroy.append({'role':'assistant','content':response})
        return history, history.copy(), gr.update(value=file_path, visible=True),gr.update(value=None)
    elif intent == 'website':
        site = extract_website(command)
        if site:
            link = f'http://{site}.com'
            response = f'Chitti: Just wait, i will open the {site} for you.....click this link {link}...'
        else:
            response = 'Chitti: Sorry, i could not understand this.....'
    history.append({'role':'user','content':command})
    history.append({'role':'assistant','content':response})
    return history,gr.update(value=None),history.copy(),gr.update(interactive=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=True)

with gr.Blocks(theme = gr.themes.Monochrome()) as demo:
    gr.Markdown("""
        <div align="center">
          <h1 style="font-size: 42px; color: #2c3e50;">
                    Chitti - The AI Bot
          </h1>
        </div>
        """)
    password = gr.Textbox(label='Password',type='password',placeholder='Enter Your Password')
    auth_message = gr.Textbox(label='Status',interactive=False)
    chatbot_box = gr.Chatbot(visible=False)
    code_text = gr.Textbox(
        label = 'Or Type Code Word Here',
        placeholder = "Type 'chitti' to activate......",
        visible = False)
    command_text = gr.Textbox(
        label = 'Or Type Command Here',
        placeholder = 'Type your command',
        visible = False
    )
    video_player = gr.Video(label= 'Now Playing.....',visible=False)
    msg = gr.Textbox('Wake Up The Chitti with the Code Word !',visible=False)
    progress_box = gr.Textbox(
        label = 'Download Status',
        interactive = False,
        visible = False
    )
    state = gr.State([])
    audio = gr.Audio(sources='microphone',type='filepath',visible=False)
    send_audio = gr.Button('Send CODE WORD!',visible=False)
    send_command = gr.Button('Send Command',interactive=False)
    password.submit(verify_password,
                    inputs = password,
                    outputs = [chatbot_box,msg,auth_message,audio,send_audio,code_text])
    send_audio.click(model_activation,
                 inputs = [chatbot_box,state,audio,code_text],
                 outputs = [chatbot_box,audio,state,send_command,send_audio,code_text,command_text])
    send_command.click(command_processing,
                       inputs = [audio,state,command_text],
                       outputs = [chatbot_box,state,video_player,audio])
    

port = int(os.environ.get('PORT',7860))
demo.launch(server_name = '0.0.0.0',
            server_port = port)

















