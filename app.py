import speech_recognition as sr
import webbrowser as op
import requests
import yt_dlp
import time
import joblib
import spacy
import re
import gradio as gr

PASSWORD = 'Sairam@970#'
def verify_password(pswd):
    if pswd == PASSWORD:
        return [],[],'Access Granted !'
    else:
        return [],[],'Invalid Credentials ! Please Login with correct credentials'

def open_website(link):
    op.open(link)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|∩╜£]','',name)

def playing_music_download(song_name):
    options = {
        'format':'bestvideo+bestaudio/best',
        'quiet':True,
        'default_search':'ytsearch1',
        'outtmpl': '%(title)s.%(ext)s',
        'compat_opts':['js-runtime'],
        'noplaylist':True,
        'remote_components':'ejs:github',
        'postprocessors':[{
            'key':'FFmpegVideoConvertor',
            'preferedformat':'mp4'
        }],
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
    
def playing_music(song_name):
    options = {
        'format':'bestvideo+bestaudio/best',
        'quiet':True,
        'default_search':'ytsearch1',
        'outtmpl': '%(title)s.%(ext)s',
        'compat_opts':['js-runtime'],
        'noplaylist':True,
        'remote_components':'ejs:github',
        'postprocessors':[{
            'key':'FFmpegVideoConvertor',
            'preferedformat':'mp4'
        }]
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(song_name,download=False)
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

try:
    nlp = spacy.load('en_core_web_md')
except OSError:
    spacy.cli.download('en_core_web_md')
    nlp = spacy.load('en_core_web_md')

def extract_website(sentence):
    doc = nlp(sentence.lower())
    for i in doc.ents:
        if i.label_ in ['ORG','PRODUCT']:
            site = i.text.lower()
            return site
    for i in doc:
        if i.dep_ in ('dobj','obj') and i.head.pos_ == 'VERB':
            return i.text.lower()
    for i in doc:
        if i.pos_ in ['NOUN','PROPN']:
            return i.text.lower()
    return None

model = joblib.load('intent_based_model.pkl')

def model_activation(message,history,state,audio):
    if audio is None:
        history.append({
            'role':'assistant',
            'content':'No audio detected. Please say the code word.'
        })
        return history, gr.update(value=None), history,gr.update(interactive=True)
    user = recognition(audio)
    if user:
        user = user.lower()
    if not user:
        history.append({'role':'assistant',
                        'content':'Code word is needed to activate Chitti....'})
        return history,gr.update(value=None),history,gr.update(interactive=False)
    if 'chitti' not in user:
        warning = 'Warning: The Chitti cannot be activated without the Code Word'
        history.append({"role": "assistant", "content": warning})
        return history,gr.update(value=None),history,gr.update(interactive=False)
    
    response = 'speak.......How can i help you ?'
    history.append({'role':'user','content':user})
    history.append({'role':'assistant','content':response})
    return history,gr.update(value=None),history,gr.update(interactive=True)

model = joblib.load('intent_based_model.pkl')
def find_intent(audio1):
    command = recognition(audio1)
    if not command:
        return 'Unknown',''
    command = command.lower()
    intent = model.predict([command])[0] if command.strip() else 'Unknown'
    return intent,command

def command_processing(audio1,history):
    if audio1 is None:
        history.append({'role':'assistant',
                        'content':'No audio was detected, please record your command'})
        return history,history
    intent,command = find_intent(audio1)
    if not command:
        return history,history
    if intent == 'music':
        file_path = playing_music_download(command)
        response = 'Chitti: I will play the song for you...\nChitti: if you want to download just say true otherwise false'
        history.append({'role':'user','content':command})
        history.append({'role':'assistant','content':response})
        return history,history,file_path
    elif intent == 'news':
        headlines = fetching_news()
        response = (
            'Chitti: Here is the latest news for you......\n\n'
            + '\n'.join(headlines[:20])
            ) if headlines else 'Chitti: No News Found !'
    elif intent == 'website':
        site = extract_website(command)
        if site:
            link = f'http://{site}.com'
            response = f'Chitti: Just wait, i will open the {site} for you.....click this link {link}...'
        else:
            response = 'Chitti: Sorry, i could not understand this.....'
    history.append({'role':'user','content':command})
    history.append({'role':'assistant','content':response})
    return history,history

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
    chatbot_box = gr.Chatbot()
    music_player = gr.Audio(label= 'Now Playing.....',interactive=False)
    msg = gr.Textbox(label = '''Initialising Chitti..........\n
                     Wake Up The Chitti with the Code Word !''',visible=True)
    state = gr.State([])
    password.submit(verify_password,
                    inputs = password,
                    outputs = [chatbot_box,msg,auth_message])
    
    audio = gr.Audio(sources='microphone',type='filepath')
    send_audio = gr.Button('Send CODE WORD!')
    send_command = gr.Button('Send Command',interactive=False)
    send_audio.click(model_activation,
                 inputs = [msg,chatbot_box,state,audio],
                 outputs = [chatbot_box,audio,state,send_command])
    send_command.click(command_processing,
                       inputs = [audio,state],
                       outputs = [chatbot_box,state,music_player])
    
demo.launch(share=True)