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
            [],
            gr.update(value = [],visible=True),
            gr.update(value = 'Wake Up The Chitti With The Code Word !',visible=True),
            gr.update(value='Access Granted !'),
            gr.update(value=None,visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    else:
        return(
            [],
            gr.update(value=[],visible=False),
            gr.update(visible=False),
            'Invalid Credentials ! Please Login with correct credentials',
            gr.update(value =None,visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )

def get_youtube(song_name):
    options = {
        'quiet':True,
        'default_search':'ytsearch1',
        'noplaylist':True
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(song_name,download=True)
        entry = info['entries'][0] if 'entries' in info else info
        return entry ['webpage_url']
        
def extract_id(url):
    match = re.search(r'(?:v=|youtu\.be/)([^&]+)', url)
    return match.group(1) if match else None
  
def fetching_news():
    api_key = '904716fee400b0ccd9210e82f10353fb'
    url = f'https://api.mediastack.com/v1/news?access_key={api_key}&countries=in'
    response = requests.get(url,timeout = 10)
    news = response.json() if response.status_code==200 else {}
    headlines = []
    for i in news.get('data',[]):
        headline = i.get('title','No Title')
        source = i.get('source','Unknown Source')
        headlines.append(f'{source}--->{headline}')
    return headlines if headlines else ['No Latest News Available Right Now']
    
def recognition(audio):
    r = sr.Recognizer()
    if audio is None:
        return ''
    try:
        with sr.AudioFile(audio) as source:
            audio_data = r.record(source)
            user = r.recognize_google(audio_data)
            return user.strip().lower()
    except Exception:
        return 'Your Voice is not Recognized by Chitti'

def extract_website(sentence):
    doc = sentence.lower()
    site_pattern = r"(https?://\S+|www\.\S+|\w+\.(com|in|org|net|io))"
    match = re.search(site_pattern,doc)
    if match:
        url = match.group(0)
        return url if url.startswith('http') else f'http://{url}'
    verb_pattern = r'(open|visit|search|go to|launch)\s+(\w+)'
    match = re.search(verb_pattern,doc)
    if match:
        return f'http://www.{match.group(2)}.com'
    words = doc.split()
    for i in words:
        if i.isalpha() and len(i)>2:
            return f'http://www.{i}.com'
    return None

def model_activation(history,audio,code_text):
    if history is None:
        history = []
    user = None
    if code_text and code_text.strip() != '':
        user = code_text.lower()
    elif audio is not None:
        user = recognition(audio)
        if user:
            user = user.lower()
    if not user:
        history.append({'role':'assistant', 'content':'Code word is needed to activate Chitti....'})
        return history,gr.update(value=None),history,gr.update(interactive=False),gr.update(visible=True),gr.update(visible=True),gr.update(visible=False)
    if 'chitti' not in user:
        warning = 'Warning: The Chitti cannot be activated without the Code Word'
        history.append({"role": "assistant", "content": warning})
        return history,gr.update(value=None),history,gr.update(interactive=False),gr.update(visible=True),gr.update(visible=True),gr.update(visible=False)
    
    response = 'speak.......How can i help you ?'
    history.append({'role':'user','content':user})
    history.append({'role':'assistant','content':response})
    return history,gr.update(value=None),history.copy(),gr.update(interactive=True,visible=True),gr.update(visible=False),gr.update(visible=False),gr.update(visible=True)

try:
    model = joblib.load('intent_based_model.pkl')
except Exception as e:
    print('Model Loading Failed:',e)
    model = None
    
def find_intent(audio1):
    command = recognition(audio1).strip() if audio1 else ''
    if not command:
        return 'Unknown',""
    command = command.lower()
    intent = model.predict([command])[0] if model is not None else 'Unknown'
    return intent,command

def command_processing(audio1,history,command_text):
    file_path = None
    if command_text and command_text.strip() != '':
        command = command_text.lower()
        intent = model.predict([command])[0] if model else 'Unknown'
    elif audio1 is not None:
        intent,command = find_intent(audio1)
    else:
        content = 'Please provide a voice or typed command'
        history.append({'role':'assistant', 'content':'Please provide a voice or typed command'})
        return history,history.copy(),gr.update(visible=False),gr.update(value=None),gr.update(interactive=True),gr.update(),gr.update()
    if intent == 'music':
        history.append({'role':'user','content':command})
        history.append({'role':'assistant','content':'Downloading Video.....Please Wait..'})
        try:
            url = get_youtube(command)
            id = extract_id(url)
            embed_html = f"""
        <iframe width="100%" height="400"
        src="https://www.youtube.com/embed/{video_id}?autoplay=1"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen>
        </iframe>
        """
            history.append({'role':'assistant','content':'Playing Your Song Below.....'})
            return history,history.copy(),gr.update(value=embed_html,visible=True),gr.update(value=None),gr.update(interactive=True),gr.update(),gr.update()
        except Exception as e:
            history.append({'role':'assistant','content':f'Error fetching video: {str(e)}'})
            return history,history.copy(),gr.update(visible=False),gr.update(value=None),gr.update(interactive=True),gr.update(),gr.update()
        
    elif intent == 'news':
        headlines = fetching_news()
        response = (
            'Chitti: Here is the latest news for you......\n\n'
            + '\n'.join(headlines[:20])
            ) if headlines else 'Chitti: No News Found !'
        history.append({'role':'assistant','content':response})
        return history, history.copy(), gr.update(visible=False),gr.update(value=None),gr.update(interactive=True),gr.update(),gr.update()
    elif intent == 'website':
        site = extract_website(command)
        if site:
            link = site
            response = f'Chitti: Just wait, i will open the {site} for you.....click this link {link}...'
        else:
            response = 'Chitti: Sorry, i could not understand this.....'
    history.append({'role':'user','content':command})
    history.append({'role':'assistant','content':response})
    return history,history.copy(),gr.update(visible=False),gr.update(value=None),gr.update(interactive=True),gr.update(visible=False),gr.update(visible=False)

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
    video_player = gr.HTML(visible=False)
    msg = gr.Textbox('Wake Up The Chitti with the Code Word !',visible=False)
    progress_box = gr.Textbox(
        label = 'Download Status',
        interactive = False,
        visible = False
    )
    state = gr.State([])
    audio = gr.Audio(sources='microphone',type='filepath',visible=False)
    send_audio = gr.Button('Send CODE WORD!',visible=False)
    send_command = gr.Button('Send Command',interactive=False,visible=False)
    password.submit(verify_password,
                    inputs = password,
                    outputs = [state,chatbot_box,msg,auth_message,audio,send_audio,code_text])
    send_audio.click(model_activation,
                 inputs = [state,audio,code_text],
                 outputs = [chatbot_box,audio,state,send_command,send_audio,code_text,command_text])
    send_command.click(command_processing,
                       inputs = [audio,state,command_text],
                       outputs = [chatbot_box,state,video_player,audio,send_command,send_audio,code_text])
    

port = int(os.environ.get('PORT',7860))
demo.launch(server_name = '0.0.0.0',
            server_port = port)


























