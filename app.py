import eventlet
eventlet.monkey_patch()
print('Patched eventlet!')

from flask import Flask, redirect, send_file
from flask_socketio import SocketIO
import requests, zipfile, re, os, threading, traceback
from io import BytesIO
from db import initialize_database, store_file, get_file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(16).hex()

socketio = SocketIO(app, async_mod='eventlet')
print('Started socketio!')

initialize_database()

@app.route('/')
def index():
    return send_file('index.html')

@app.errorhandler(404)
def handle_404(_):
    return redirect('/')

@app.route('/query/<username>')
def getUser(username):
    return _getUser(username)

def _getUser(username):
    try:
        assert len(username) > 0
        req = requests.get('https://viblo.asia/api/users/' + username).json()
        assert 'data' in req
        ret = {key: req['data'][key] for key in ['name', 'username', 'avatar', 'posts_count']}
    except AssertionError:
        ret = {'error': "Invalid username! Try again."}
    except Exception as e:
        traceback.format_exc()
        ret = {'error': 'Something went wrong... I blame Viblo ¯\_(ツ)_/¯'}
    return ret

@app.route('/download/<ticket>')
def getDownload(ticket):
    try:
        username, content = get_file(ticket)
        return send_file(
            BytesIO(content),
            download_name=username + '.zip',
            as_attachment=True
        )
    except Exception as e:
        print(traceback.format_exc())
        return redirect('/')

@app.route('/request/<username>')
def getTicket(username):
    try:
        posts_count = _getUser(username)['posts_count']
    except Exception as e:
        traceback.format_exc()
        return redirect('/')
    ticket = os.urandom(8).hex()
    threading.Thread(target=prepDownload, args=(username, posts_count, ticket)).start()
    return {'ticket': ticket}, 202

def prepDownload(username, posts_count, ticket):
    # 'title', 'slug', 'contents', 'transliterated'
    req = requests.get('https://viblo.asia/api/users/' + username + '/posts?limit=' + str(posts_count)).json()['data']
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for count, post in enumerate(req):
            socketio.send({'current': count, 'total': len(req)}, namespace='/'+ticket)

            prefix = post['transliterated'] + '-' + post['slug']
            replacements = {}
            for match in re.finditer(r'!\[[^\]]*\]\(([^\)]+)\)', post['contents']):
                url = match.group(1)
                if url in replacements:
                    continue
                fname = url.rsplit('/', 1)[-1]
                if fname in replacements.values():
                    fname_, ext_ = fname.rsplit('.', 1)
                    idx = 0
                    while fname in replacements.values():
                        idx += 1
                        fname = fname_ + '_' + str(idx) + '.' + ext_
                try:
                    zf.writestr(prefix + '_files/' + fname, requests.get(url, stream=True).raw.data)
                    replacements[url] = fname
                except:
                    # if unable to fetch image, leave as-is
                    pass
            for k, v in replacements.items():
                re.sub(
                    r'!\[([^\]]*)\]\(' + re.escape(k) + r'\)',
                    r'!\[\g<1>\]\(' + re.escape(prefix + '_files/' + v) + r'\)',
                    post['contents']
                )
            zf.writestr(prefix + '.md', post['contents'])
            
    memory_file.seek(0)
    store_file(ticket, username, memory_file.read())
    socketio.send({'current': len(req), 'total': len(req)}, namespace='/'+ticket)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
