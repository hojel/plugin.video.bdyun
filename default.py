#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import os, sys, re, json 

from lib.resource import get_auth, pcs, utils, cnkeyboard, myplayer
from xbmcswift2 import Plugin

plugin = Plugin()
dialog = xbmcgui.Dialog()


@plugin.route('/')
def main_menu():
    user_info = get_user_info()
    if user_info is None:
        items = [{
        'label': u'登入',
        'path': plugin.url_for('login_dialog'),
        'is_playable': False
        }]
    else:
        user_pcs = plugin.get_storage('user_pcs', TTL=60*12)
        PcsInfo = user_pcs.get('PcsInfo')
        if PcsInfo is None:
            user_pcs = plugin.get_storage('user_pcs', TTL=60*12)
            pcs_info = pcs.get_pcs_info(user_info['cookie'], user_info['tokens'])
            if pcs_info:
                user_pcs['PcsInfo'] = pcs_info
                avatar_url = pcs_info['avatar_url']
            else:
                avatar_url = ''
                dialog.ok('Error',u'请重新登录',u'点击当前帐号，再点击登出')
        else:
            avatar_url = PcsInfo['avatar_url']
        items = [{
        'label': u'## 当前帐号: %s' %user_info['username'],
        'path': plugin.url_for('accout_setting'),
        'is_playable': False,
        'icon': avatar_url
        },{
        'label': u'## 搜索视频或音频',
        'path': plugin.url_for('search'),
        'is_playable': False
        },{
        'label': u'## 刷新',
        'path': plugin.url_for('refresh'),
        'is_playable': False
        }]

        if avatar_url:
            homemenu = plugin.get_storage('homemenu')
            if homemenu.get('item_list'):
                item_list = homemenu.get('item_list')
            else:
                item_list = menu_cache(user_info['cookie'], user_info['tokens'])
            items.extend(item_list)

    return plugin.finish(items, update_listing=True)


@plugin.route('/login_dialog/')
def login_dialog():
    username = dialog.input(u'用户名:', type=xbmcgui.INPUT_ALPHANUM)
    password = dialog.input(u'密码:', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if username and password:
        cookie,tokens = get_auth.run(username,password)
        if tokens:
            save_user_info(username,password,cookie,tokens)
            dialog.ok('',u'登录成功',u'请耐心等待')
            xbmc.executebuiltin('Container.Refresh')
            return None
    else:
        dialog.ok('Error',u'用户名或密码不能为空')
    return None


@plugin.route('/accout_setting/')
def accout_setting():
    user_info = get_user_info()
    items = [{
    'label': u'登出和清除缓存',
    'path': plugin.url_for('clear_cache'),
    'is_playable': False
    },{
    'label': 'setting',
    'is_playable': False
    }]
    if user_info:
        return plugin.finish(items)
    else:
        return


@plugin.route('/accout_setting/clear_cache/')
def clear_cache():
    info = plugin.get_storage('info')
    homemenu = plugin.get_storage('homemenu')
    pcs_info = plugin.get_storage('pcs_info')
    info.clear()
    homemenu.clear()
    pcs_info.clear()
    dialog.ok('',u'清理完毕')
    return


@plugin.route('/search/')
def search():
    user_info = get_user_info()
    user_cookie = user_info['cookie']
    user_tokens = user_info['tokens']
    key = cnkeyboard.keyboard(heading=u'输入文件名/关键词')
    if key:
        s = pcs.search(user_cookie, user_tokens, key)
        items = []
        if len(s['list']) == 1:
            for result in s['list']:
                if result['isdir'] == 1:
                    item = {
                            'label': result['server_filename'],
                            'path': plugin.url_for('directory', path=result['path'].encode('utf-8')),
                            'is_playable': False 
                            }
                    items.append(item)
                elif result['category'] == 1:
                    if 'thumbs' in result and 'url2' in result['thumbs']:   
                        ThumbPath = result['thumbs']['url2']
                        item = {
                                'label': result['server_filename'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False, 
                                'icon': ThumbPath,
                                }
                    else:
                        item = {
                                'label': result['server_filename'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False, 
                                }
                    items.append(item)
                elif result['category'] == 2:
                    item = {
                             'label': result['server_filename'],
                             'path': plugin.url_for('play_music', filepath=result['path'].encode('utf-8')),
                             'is_playable': False,
                            }
                    items.append(item)
            if items:
                return plugin.finish(items)
            else:
                dialog.ok('',u'搜素的文件不属于文件夹、视频或音频')

        elif s['list']:
            for result in s['list']:
                if result['isdir'] == 1:
                    item = {
                            'label': result['path'],
                            'path': plugin.url_for('directory', path=result['path'].encode('utf-8')),
                            'is_playable': False 
                            }
                    items.append(item)
                elif result['category'] == 1:
                    if 'thumbs' in result and 'url2' in result['thumbs']:   
                        ThumbPath = result['thumbs']['url2']
                        item = {
                                'label': result['path'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False, 
                                'icon': ThumbPath,
                                }
                    else:
                        item = {
                                'label': result['path'],
                                'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                                'is_playable': False,
                                }
                    items.append(item)
                elif result['category'] == 2:
                    item = {
                             'label': result['path'],
                             'path': plugin.url_for('play_music', filepath=result['path'].encode('utf-8')),
                             'is_playable': False,
                            }
                    items.append(item)
            if items:
                return plugin.finish(items)
            else:
                dialog.ok('',u'搜素的文件不属于文件夹、视频或音频')

        else:
            dialog.ok('',u'没有找到文件')
            return None

    return 


@plugin.route('/directory/<path>')
def directory(path):
    user_info = get_user_info()
    user_cookie = user_info['cookie']
    user_tokens = user_info['tokens']
    dir_files = pcs.list_dir_all(user_info['cookie'], user_info['tokens'], path.decode('utf-8'))
    item_list = MakeList(dir_files)

    previous_path = os.path.dirname(path)
    if previous_path == '/':
        item_list.insert(0,{
                'label': u'返回首页',
                'path': plugin.url_for('main_menu')
            })
    else:
        item_list.insert(0,{
                'label': u'<< 返回上一层',
                'path': plugin.url_for('directory', path=previous_path),
            })

    return plugin.finish(item_list, update_listing=True)


@plugin.route('/refresh/')
def refresh():
    homemenu = plugin.get_storage('homemenu')
    homemenu.clear()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/quality/<filepath>')
def quality(filepath):
    stream_type = ['M3U8_AUTO_480','M3U8_AUTO_720']
    choice = dialog.select(u'请选择画质', [u'流畅480P(推荐)',u'高清720P',u'原画(不转码)'])
    if choice < 0:
        return

    elif choice == 0 or choice == 1:
        stream = stream_type[choice]
        video_path = playlist_path(filepath.decode('utf-8'), stream)

    elif choice == 2:
        rep = dialog.yesno(u'注意',u'原画没有经过转码,需要很高的带宽',u'继续使用原画吗？')
        if rep:
            video_path = playlist_path(filepath, stream=False)
        else:
            return

    name = os.path.basename(filepath.decode('utf-8'))
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo(type='Video', infoLabels={'Title': name})

    player = myplayer.Player()
    player.play(video_path, listitem, windowed=False)


@plugin.route('/play_music/<filepath>')
def play_music(filepath):
    url = playlist_path(filepath, stream=False)
    name = os.path.basename(filepath.decode('utf-8'))
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo(type='Music', infoLabels={'Title': name})
    player = myplayer.Player()
    player.play(url,listitem,windowed=True)


# cache the output of content menu
def menu_cache(cookie, tokens):
    pcs_files = pcs.list_dir_all(cookie, tokens, path='/')
    item_list = MakeList(pcs_files)
    homemenu = plugin.get_storage('homemenu', TTL=60)
    homemenu['item_list'] = item_list
    return item_list


def get_user_info():
    info = plugin.get_storage('info')
    user_info = info.get('user_info')
    return user_info


def save_user_info(username, password, cookie, tokens):
    info = plugin.get_storage('info')
    user_info = info.setdefault('user_info',{})
    user_info['username'] = username
    user_info['password'] = password
    user_info['cookie'] = cookie
    user_info['tokens'] = tokens
    info.sync()


def MakeList(pcs_files):
    item_list = []
    for result in pcs_files:
        if result['isdir'] == 1:
            item = {
                    'label': result['server_filename'],
                    'path': plugin.url_for('directory', path=result['path'].encode('utf-8')),
                    'is_playable': False 
                    }
            item_list.append(item)
        elif result['category'] == 1:
            if 'thumbs' in result and 'url2' in result['thumbs']:   
                ThumbPath = result['thumbs']['url2']
                item = {
                        'label': result['server_filename'],
                        'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                        'is_playable': False, 
                        'icon': ThumbPath,
                        }
            else:
                item = {
                        'label': result['server_filename'],
                        'path': plugin.url_for('quality', filepath=result['path'].encode('utf-8')),
                        'is_playable': False,
                        }
            item_list.append(item)
        elif result['category'] == 2:
            item = {
                    'label': result['server_filename'],
                    'path': plugin.url_for('play_music', filepath=result['path'].encode('utf-8')),
                    'is_playable': False,
                    }
            item_list.append(item)
    return item_list
    

def playlist_path(pcs_file_path, stream):
    user_info = get_user_info()
    user_name = user_info['username']
    user_cookie = user_info['cookie']
    user_tokens = user_info['tokens']

    if stream:
        playlist_data = pcs.get_streaming_playlist(user_cookie, pcs_file_path, stream)
        if playlist_data:
            raw_dir = os.path.dirname(pcs_file_path)
            m = re.search('\/(.*)', raw_dir)
            dirname = m.group(1)
            basename = os.path.basename(pcs_file_path)
            r = re.search('(.*)\.(.*)$', basename)
            filename = ''.join([r.group(1), stream, '.m3u8'])
            dirpath = os.path.join(utils.data_dir(), user_name, dirname)
            if not xbmcvfs.exists(dirpath):
                xbmcvfs.mkdir(dirpath)
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'w') as f:
                f.write(playlist_data)
            return filepath
        else:
            return None
    else:
        url = pcs.get_download_link(user_cookie, user_tokens, pcs_file_path)
        return url


if __name__ == '__main__':
    plugin.run()


