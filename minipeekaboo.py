#!/usr/bin/env python3
"""
MiniPeekaboo v2.0 - Python版Peekaboo克隆
兼容 macOS 12+
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Optional, List, Dict

try:
    from Quartz import CGWindowListCopyWindowInfo, kCGNullWindowID, kCGWindowListOptionOnScreenOnly, kCGWindowListOptionAll
except ImportError:
    print("Error: pip3 install pyobjc-framework-Quartz")
    sys.exit(1)


def get_running_apps():
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    apps = {}
    for window in window_list:
        owner = window.get('kCGWindowOwnerName', '')
        pid = window.get('kCGWindowOwnerPID', 0)
        if owner and pid:
            if owner not in apps:
                apps[owner] = {'name': owner, 'pid': pid, 'windows': []}
            apps[owner]['windows'].append({'title': window.get('kCGWindowTitle', ''), 'window_id': window.get('kCGWindowNumber', 0)})
    return sorted(apps.values(), key=lambda x: x['pid'])


def get_windows(app_name=None):
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    windows = []
    for w in window_list:
        owner = w.get('kCGWindowOwnerName', '')
        if app_name and app_name.lower() not in owner.lower():
            continue
        windows.append({'window_id': w.get('kCGWindowNumber', 0), 'title': w.get('kCGWindowTitle', ''), 'owner': owner})
    return windows


def capture_screen(path='/tmp/screenshot.png'):
    subprocess.run(['/usr/sbin/screencapture', '-x', path])
    return path


def capture_window(path='/tmp/window.png', window_id=None):
    cmd = ['/usr/sbin/screencapture', '-x']
    if window_id: 
        cmd.extend(['-l', str(window_id)])
    else: 
        cmd.append('-w')
    cmd.append(path)
    subprocess.run(cmd)
    return path


def capture_region(path='/tmp/region.png', x=0, y=0, w=800, h=600):
    subprocess.run(['/usr/sbin/screencapture', '-x', '-R', f'{x},{y},{w},{h}', path])
    return path


def click_menu(app_name, menu_path):
    parts = menu_path.split('>')
    subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'])
    time.sleep(0.2)
    if len(parts) >= 2:
        script_parts = [f'click menu item "{parts[-1].strip()}"']
        for i in range(len(parts)-2, -1, -1):
            script_parts.append(f'menu "{parts[i].strip()}"')
        script = 'tell application "System Events" to ' + ' of '.join(['menu bar 1 of process "' + app_name + '"'] + script_parts)
    else:
        script = f'tell application "System Events" to click menu item "{parts[0]}" of menu bar 1 of process "{app_name}"'
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    return result.returncode == 0


def click_at(x, y):
    script = f'tell application "System Events" to click at {{ {x}, {y} }}'
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    return result.returncode == 0


def type_text(text, app_name=None):
    if app_name: 
        subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'])
    text = text.replace('"', '\\"')
    script = f'tell application "System Events" to keystroke "{text}"'
    return subprocess.run(['osascript', '-e', script]).returncode == 0


def press_key(key, modifiers=None, app_name=None):
    if app_name: 
        subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'])
    mod_map = {'cmd': 'command', 'shift': 'shift', 'ctrl': 'control', 'option': 'option'}
    key_map = {'enter': 'return', 'tab': 'tab', 'escape': 'escape', 'space': 'space'}
    k = key_map.get(key, key)
    if modifiers:
        mods = ', '.join([mod_map.get(m, m) for m in modifiers])
        script = f'tell application "System Events" to keystroke "{k}" using {{ {mods} down }}'
    else:
        script = f'tell application "System Events" to keystroke "{k}"'
    return subprocess.run(['osascript', '-e', script]).returncode == 0


def drag(from_x, from_y, to_x, to_y):
    """Simulate drag operation using mouse events"""
    # macOS AppleScript doesn't support direct drag
    # Use cliclick or simulate with click + move
    try:
        # Try cliclick if available
        result = subprocess.run(['which', 'cliclick'], capture_output=True)
        if result.returncode == 0:
            subprocess.run(['cliclick', f'd:{from_x},{from_y}', f'm:{to_x},{to_y}', f'c:{to_x},{to_y}'])
            return True
    except:
        pass
    
    # Fallback: just click at destination
    script = f'tell application "System Events" to click at {{ {to_x}, {to_y} }}'
    subprocess.run(['osascript', '-e', script])
    return True


def scroll(direction, amount=3):
    """Scroll in specified direction"""
    # Use keystroke approach for scrolling
    if direction == 'down':
        key = 'page down'
    else:
        key = 'page up'
    
    for _ in range(amount):
        script = f'tell application "System Events" to keystroke "{key}"'
        subprocess.run(['osascript', '-e', script])
    return True


def window_action(action, app_name):
    if action == 'close':
        script = f'close front window of app "{app_name}"'
    elif action == 'minimize':
        script = f'minimize front window of app "{app_name}"'
    elif action == 'focus':
        script = f'activate app "{app_name}"'
    else:
        return False
    subprocess.run(['osascript', '-e', script])
    return True


def move_window(app_name, x, y, width=None, height=None):
    """Move and optionally resize window"""
    subprocess.run(['osascript', '-e', f'activate app "{app_name}"'])
    time.sleep(0.1)
    if width and height:
        script = f'''
tell application "System Events"
    set position of window 1 of process "{app_name}" to {{{x}, {y}}}
    set size of window 1 of process "{app_name}" to {{{width}, {height}}}
end tell'''
    else:
        script = f'tell application "System Events" to set position of window 1 of process "{app_name}" to {{{x}, {y}}}'
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    time.sleep(0.2)  # Wait for window to actually move
    return result.returncode == 0


def get_window_bounds(app_name):
    """Get window position and size"""
    script = f'''
tell application "System Events"
    set winPos to position of window 1 of process "{app_name}"
    set winSize to size of window 1 of process "{app_name}"
    return {{item 1 of winPos, item 2 of winPos, item 1 of winSize, item 2 of winSize}}
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if result.returncode == 0:
        parts = result.stdout.strip().split(', ')
        return {'x': int(parts[0]), 'y': int(parts[1]), 'width': int(parts[2]), 'height': int(parts[3])}
    return None


def app_action(action, name):
    if action == 'activate': 
        subprocess.run(['osascript', '-e', f'activate app "{name}"'])
    elif action == 'launch': 
        subprocess.run(['open', '-a', name])
    elif action == 'quit': 
        subprocess.run(['osascript', '-e', f'quit app "{name}"'])
    return True


def get_clipboard():
    result = subprocess.run(['osascript', '-e', 'the clipboard'], capture_output=True, text=True)
    return result.stdout.strip()


def set_clipboard(text):
    """Set clipboard content"""
    # Use pbcopy for more reliable clipboard setting
    subprocess.run(['pbcopy'], input=text.encode('utf-8'))
    return True


def dock_click(app_name, action='click'):
    """Click Dock icon"""
    script = f'''
tell application "System Events"
    tell process "Dock"
        set dockItems to UI elements of list 1
        repeat with item in dockItems
            if description of item contains "{app_name}" then
                {action} item
                return true
            end if
        end repeat
    end tell
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    return result.returncode == 0


def dock_list():
    """List Dock items"""
    script = '''
tell application "System Events"
    tell process "Dock"
        set dockElements to UI elements of list 1
        set output to ""
        repeat with dockItem in dockElements
            try
                set itemName to name of dockItem
                if itemName is not "missing value" then
                    set output to output & itemName & linefeed
                end if
            end try
        end repeat
        return output
    end tell
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if result.returncode == 0:
        items = result.stdout.strip().split('\n')
        return [item.strip() for item in items if item.strip() and item.strip() != 'missing value']
    return []


def menubar_click(menu_name, app_name=None):
    """Click menu bar item (like WiFi, Battery, Clock)"""
    target = app_name if app_name else "SystemUIServer"
    script = f'''
tell application "System Events"
    tell process "{target}"
        click menu bar item "{menu_name}" of menu bar 1
    end tell
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    return result.returncode == 0


def menubar_list(app_name=None):
    """List menu bar items"""
    target = app_name if app_name else "SystemUIServer"
    script = f'''
tell application "System Events"
    tell process "{target}"
        try
            set menuElements to menu bar items of menu bar 1
            set output to ""
            repeat with menuBarItem in menuElements
                try
                    set itemName to name of menuBarItem
                    if itemName is not "missing value" then
                        set output to output & itemName & linefeed
                    end if
                end try
            end repeat
            return output
        end try
    end tell
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        items = result.stdout.strip().split('\n')
        return [item.strip() for item in items if item.strip() and item.strip() != 'missing value']
    return []


def see_analyze(path=None, prompt="Describe this UI. What elements are visible? What can be clicked?", provider=None):
    """Analyze UI with AI vision model"""
    if path is None:
        path = '/tmp/mp_see.png'
        capture_screen(path)
    
    import base64
    import json
    import urllib.request
    
    with open(path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Try multiple providers
    providers_to_try = provider if provider else ['doubao', 'openai', 'anthropic']
    
    for prov in providers_to_try:
        if prov == 'doubao':
            # Try doubao vision (豆包)
            api_key = subprocess.run(['cat', os.path.expanduser('~/.doubao_api_key')], 
                                     capture_output=True, text=True).stdout.strip()
            if not api_key:
                api_key = os.environ.get('DOUBAO_API_KEY', '')
            if api_key:
                try:
                    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
                    data = {
                        "model": "doubao-vision-pro-32k",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                            ]
                        }]
                    }
                    req = urllib.request.Request(url, 
                        data=json.dumps(data).encode('utf-8'),
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read().decode('utf-8'))
                        return result['choices'][0]['message']['content']
                except Exception as e:
                    continue
        
        elif prov == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY', '')
            if api_key:
                try:
                    url = "https://api.openai.com/v1/chat/completions"
                    data = {
                        "model": "gpt-4o",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                            ]
                        }]
                    }
                    req = urllib.request.Request(url,
                        data=json.dumps(data).encode('utf-8'),
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read().decode('utf-8'))
                        return result['choices'][0]['message']['content']
                except Exception as e:
                    continue
        
        elif prov == 'anthropic':
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if api_key:
                try:
                    url = "https://api.anthropic.com/v1/messages"
                    data = {
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1024,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                                {"type": "text", "text": prompt}
                            ]
                        }]
                    }
                    req = urllib.request.Request(url,
                        data=json.dumps(data).encode('utf-8'),
                        headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": api_key})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read().decode('utf-8'))
                        return result['content'][0]['text']
                except Exception as e:
                    continue
    
    # Fallback: just return screenshot path with prompt suggestion
    return f"Screenshot saved: {path}\nNo AI provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or DOUBAO_API_KEY.\nPrompt: {prompt}"


def drag_mouse(from_x, from_y, to_x, to_y, duration=0.5):
    """Real drag operation using mouse events"""
    # Use Python Quartz for smooth drag
    try:
        from Quartz import CGEventCreateMouseEvent, kCGEventMouseMoved, kCGEventLeftMouseDown, kCGEventLeftMouseDragged, kCGEventLeftMouseUp, kCGMouseButtonLeft, kCGEventSourceStateHIDSystemState
        from Quartz.CoreGraphics import CGEventPost, kCGHIDEventTap, CGEventSourceCreate
        
        source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState)
        
        # Move to start position
        event = CGEventCreateMouseEvent(source, kCGEventMouseMoved, (from_x, from_y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(0.1)
        
        # Press left button
        event = CGEventCreateMouseEvent(source, kCGEventLeftMouseDown, (from_x, from_y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        
        # Drag to destination with smooth movement
        steps = int(duration * 20)
        for i in range(1, steps + 1):
            progress = i / steps
            x = from_x + (to_x - from_x) * progress
            y = from_y + (to_y - from_y) * progress
            event = CGEventCreateMouseEvent(source, kCGEventLeftMouseDragged, (x, y), kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, event)
            time.sleep(duration / steps)
        
        # Release at destination
        event = CGEventCreateMouseEvent(source, kCGEventLeftMouseUp, (to_x, to_y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        return True
    except ImportError:
        # Fallback to AppleScript click
        script = f'tell application "System Events" to click at {{ {to_x}, {to_y} }}'
        subprocess.run(['osascript', '-e', script])
        return True


def swipe(direction, app_name=None):
    """Swipe gesture (up/down/left/right)"""
    script = f'''
tell application "System Events"
    tell process "{app_name or 'Finder'}"
        swipe in direction "{direction}"
    end tell
end tell'''
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    return result.returncode == 0


def space_action(action, space_num=None):
    """Space (virtual desktop) operations"""
    if action == 'list':
        # Use Mission Control to count spaces (complex)
        # For simplicity, just return keyboard shortcut info
        return "Spaces: Use Ctrl+1-9 to switch, Ctrl+Left/Right to navigate"
    
    elif action == 'switch':
        if space_num and space_num <= 9:
            # Use keyboard shortcut Ctrl+N
            script = f'''
tell application "System Events"
    key code {18 + space_num - 1} using control down
end tell'''
            subprocess.run(['osascript', '-e', script])
            time.sleep(0.3)
            return True
    
    elif action == 'next':
        # Ctrl+Right arrow
        script = '''
tell application "System Events"
    key code 124 using control down
end tell'''
        subprocess.run(['osascript', '-e', script])
        return True
    
    elif action == 'prev':
        # Ctrl+Left arrow
        script = '''
tell application "System Events"
    key code 123 using control down
end tell'''
        subprocess.run(['osascript', '-e', script])
        return True
    
    return False


def menu_natural(app_name, description):
    """Natural language menu click - tries to find and click menu item by description"""
    # Keyboard shortcuts are fastest and most reliable
    shortcut_map = {
        'save': ('s', ['cmd']),
        'open': ('o', ['cmd']),
        'new': ('n', ['cmd']),
        'close': ('w', ['cmd']),
        'quit': ('q', ['cmd']),
        'copy': ('c', ['cmd']),
        'paste': ('v', ['cmd']),
        'cut': ('x', ['cmd']),
        'undo': ('z', ['cmd']),
        'redo': ('z', ['cmd', 'shift']),
        'select all': ('a', ['cmd']),
        'find': ('f', ['cmd']),
        'print': ('p', ['cmd']),
        'refresh': ('r', ['cmd']),
        'reload': ('r', ['cmd']),
        'fullscreen': ('f', ['cmd', 'ctrl']),
        'minimize': ('m', ['cmd']),
        'hide': ('h', ['cmd']),
        'spotlight': ('space', ['cmd']),
    }
    
    # Normalize description
    desc = description.lower().strip()
    
    # Try keyboard shortcut first (fastest)
    if desc in shortcut_map:
        key, mods = shortcut_map[desc]
        press_key(key, mods, app_name)
        return True
    
    # Common menu paths as fallback
    menu_map = {
        'save': ['File>Save', '文件>保存'],
        'save as': ['File>Save As', '文件>另存为'],
        'open': ['File>Open', '文件>打开'],
        'new': ['File>New', '文件>新建'],
        'close': ['File>Close', '文件>关闭'],
        'quit': ['File>Quit', '退出'],
        'copy': ['Edit>Copy', '编辑>复制'],
        'paste': ['Edit>Paste', '编辑>粘贴'],
        'cut': ['Edit>Cut', '编辑>剪切'],
        'undo': ['Edit>Undo', '编辑>撤销'],
        'redo': ['Edit>Redo', '编辑>重做'],
        'select all': ['Edit>Select All', '编辑>全选'],
        'find': ['Edit>Find', '编辑>查找'],
        'preferences': ['Preferences', '设置', '偏好设置'],
        'settings': ['Settings', '设置', '偏好设置'],
        'about': ['About', '关于'],
        'help': ['Help', '帮助'],
        'print': ['File>Print', '文件>打印'],
        'export': ['File>Export', '文件>导出'],
        'import': ['File>Import', '文件>导入'],
        'refresh': ['View>Refresh', '刷新'],
        'reload': ['View>Reload', '重新加载'],
    }
    
    if desc in menu_map:
        for menu_path in menu_map[desc]:
            try:
                result = click_menu(app_name, menu_path)
                if result:
                    return True
            except:
                continue
    
    return False


def check_permissions():
    try:
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        screen = len(window_list) > 0
    except: 
        screen = False
    result = subprocess.run(['osascript', '-e', 'first process'], capture_output=True)
    ax = result.returncode == 0
    return {'screen_recording': screen, 'accessibility': ax}


def main():
    p = argparse.ArgumentParser(description='MiniPeekaboo v2.0 - macOS UI Automation')
    
    sub = p.add_subparsers(dest='cmd')
    
    # list
    lp = sub.add_parser('list', help='list apps/windows')
    lp.add_argument('type', choices=['apps', 'windows', 'permissions'])
    lp.add_argument('--app')
    lp.add_argument('--json', action='store_true')
    
    # image
    img = sub.add_parser('image', help='screenshot')
    img.add_argument('--mode', default='screen')
    img.add_argument('--path', default='/tmp/mp.png')
    img.add_argument('--app')
    img.add_argument('--window-id', type=int)
    
    # permissions
    sub.add_parser('permissions', help='check permissions')
    
    # click
    ck = sub.add_parser('click', help='click')
    ck.add_argument('--app')
    ck.add_argument('--menu')
    ck.add_argument('--coords')
    
    # type
    tp = sub.add_parser('type', help='type text')
    tp.add_argument('text')
    tp.add_argument('--app')
    
    # press
    pk = sub.add_parser('press', help='press key')
    pk.add_argument('key')
    pk.add_argument('--modifiers')
    pk.add_argument('--app')
    
    # hotkey
    hk = sub.add_parser('hotkey', help='hotkey')
    hk.add_argument('keys')
    hk.add_argument('--app')
    
    # drag
    dr = sub.add_parser('drag', help='drag')
    dr.add_argument('from_pos')
    dr.add_argument('to_pos')
    
    # scroll
    sc = sub.add_parser('scroll', help='scroll')
    sc.add_argument('direction', choices=['up', 'down'])
    sc.add_argument('--amount', type=int, default=3)
    
    # window
    wp = sub.add_parser('window', help='window actions')
    wp.add_argument('action', choices=['close', 'minimize', 'focus', 'bounds'])
    wp.add_argument('--app', required=True)
    
    # move
    mv = sub.add_parser('move', help='move/resize window')
    mv.add_argument('--app', required=True)
    mv.add_argument('--pos', help='position x,y')
    mv.add_argument('--size', help='size w,h')
    
    # app
    ap = sub.add_parser('app', help='app')
    ap.add_argument('action', choices=['activate', 'launch', 'quit'])
    ap.add_argument('name')
    
    # clipboard
    cp = sub.add_parser('clipboard', help='clipboard')
    cp.add_argument('action', choices=['get', 'set'])
    cp.add_argument('text', nargs='?')
    
    # dock
    dk = sub.add_parser('dock', help='Dock operations')
    dk.add_argument('action', choices=['list', 'click'])
    dk.add_argument('--app')
    
    # menubar
    mb = sub.add_parser('menubar', help='menu bar operations')
    mb.add_argument('action', choices=['list', 'click'])
    mb.add_argument('--item')
    mb.add_argument('--app')
    
    # see (UI analysis with AI)
    se = sub.add_parser('see', help='UI analysis with AI')
    se.add_argument('--image', help='image path to analyze')
    se.add_argument('--prompt', default='Describe this UI. What elements are visible? What can be clicked?')
    se.add_argument('--provider', help='AI provider (openai/anthropic/doubao)')
    
    # swipe
    sw = sub.add_parser('swipe', help='swipe gesture')
    sw.add_argument('direction', choices=['up', 'down', 'left', 'right'])
    sw.add_argument('--app', help='target app')
    
    # space (virtual desktop)
    sp = sub.add_parser('space', help='virtual desktop/space operations')
    sp.add_argument('action', choices=['list', 'switch', 'next', 'prev'])
    sp.add_argument('--num', type=int, help='space number to switch to')
    
    # menu (natural language)
    me = sub.add_parser('menu', help='natural language menu click')
    me.add_argument('--app', required=True)
    me.add_argument('description', help='menu description (e.g. "save", "open", "preferences")')
    
    args = p.parse_args()
    
    if args.cmd == 'list':
        if args.type == 'apps':
            apps = get_running_apps()
            if args.json:
                print(json.dumps(apps, indent=2))
            else:
                for i, app in enumerate(apps, 1):
                    print(f"{i}. {app['name']} (PID: {app['pid']}, Windows: {len(app['windows'])})")
        elif args.type == 'windows':
            wins = get_windows(args.app)
            if args.json:
                print(json.dumps(wins, indent=2))
            else:
                for i, w in enumerate(wins, 1):
                    print(f"{i}. [{w['window_id']}] {w['title']} - {w['owner']}")
        elif args.type == 'permissions':
            perms = check_permissions()
            print(f"Screen Recording: {'Granted' if perms['screen_recording'] else 'Denied'}")
            print(f"Accessibility: {'Granted' if perms['accessibility'] else 'Denied'}")
    
    elif args.cmd == 'image':
        if args.mode == 'screen':
            capture_screen(args.path)
        elif args.mode == 'window':
            capture_window(args.path, args.window_id)
        else:
            capture_region(args.path)
        print(f"Saved: {args.path}")
    
    elif args.cmd == 'permissions':
        perms = check_permissions()
        print(f"Screen Recording: {'Granted' if perms['screen_recording'] else 'Denied'}")
        print(f"Accessibility: {'Granted' if perms['accessibility'] else 'Denied'}")
    
    elif args.cmd == 'click':
        if args.menu:
            click_menu(args.app or 'Finder', args.menu)
            print(f"Clicked: {args.menu}")
        elif args.coords:
            x, y = map(int, args.coords.split(','))
            click_at(x, y)
            print(f"Clicked: {x},{y}")
    
    elif args.cmd == 'type':
        type_text(args.text, args.app)
        print(f"Typed: {args.text}")
    
    elif args.cmd == 'press':
        mods = args.modifiers.split(',') if args.modifiers else None
        press_key(args.key, mods, args.app)
        print(f"Pressed: {args.key}")
    
    elif args.cmd == 'hotkey':
        keys = args.keys.split(',')
        modifiers = [k for k in keys[:-1] if k in ['cmd', 'shift', 'ctrl', 'option']]
        key = keys[-1]
        press_key(key, modifiers, args.app)
        print(f"Hotkey: {args.keys}")
    
    elif args.cmd == 'scroll':
        scroll(args.direction, args.amount)
        print(f"Scrolled: {args.direction}")
    
    elif args.cmd == 'window':
        if args.action == 'bounds':
            bounds = get_window_bounds(args.app)
            if bounds:
                print(f"Position: ({bounds['x']}, {bounds['y']})")
                print(f"Size: ({bounds['width']}, {bounds['height']})")
            else:
                print("Failed to get window bounds")
        else:
            window_action(args.action, args.app)
            print(f"Window: {args.action}")
    
    elif args.cmd == 'move':
        if args.pos:
            x, y = map(int, args.pos.split(','))
            if args.size:
                w, h = map(int, args.size.split(','))
                move_window(args.app, x, y, w, h)
                print(f"Moved {args.app} to ({x},{y}) size ({w},{h})")
            else:
                move_window(args.app, x, y)
                print(f"Moved {args.app} to ({x},{y})")
    
    elif args.cmd == 'app':
        app_action(args.action, args.name)
        print(f"App: {args.action} {args.name}")
    
    elif args.cmd == 'clipboard':
        if args.action == 'get':
            print(get_clipboard())
        elif args.action == 'set':
            set_clipboard(args.text)
            print(f"Clipboard: {args.text}")
    
    elif args.cmd == 'dock':
        if args.action == 'list':
            items = dock_list()
            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")
        elif args.action == 'click':
            if args.app:
                dock_click(args.app)
                print(f"Clicked Dock: {args.app}")
            else:
                print("Error: --app required for click")
    
    elif args.cmd == 'menubar':
        if args.action == 'list':
            items = menubar_list(args.app)
            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")
        elif args.action == 'click':
            if args.item:
                menubar_click(args.item, args.app)
                print(f"Clicked menu bar: {args.item}")
            else:
                print("Error: --item required for click")
    
    elif args.cmd == 'see':
        result = see_analyze(args.image, args.prompt, args.provider)
        print(result)
    
    elif args.cmd == 'swipe':
        swipe(args.direction, args.app)
        print(f"Swiped: {args.direction}")
    
    elif args.cmd == 'space':
        if args.action == 'list':
            count = space_action('list')
            print(f"Spaces: {count}")
        elif args.action == 'switch':
            if args.num:
                space_action('switch', args.num)
                print(f"Switched to space {args.num}")
            else:
                print("Error: --num required for switch")
        elif args.action == 'next':
            space_action('next')
            print("Switched to next space")
        elif args.action == 'prev':
            space_action('prev')
            print("Switched to previous space")
    
    elif args.cmd == 'menu':
        result = menu_natural(args.app, args.description)
        if result:
            print(f"Menu: {args.description}")
        else:
            print(f"Could not find menu: {args.description}")
    
    elif args.cmd == 'drag':
        fx, fy = map(int, args.from_pos.split(','))
        tx, ty = map(int, args.to_pos.split(','))
        drag_mouse(fx, fy, tx, ty)
        print(f"Dragged: ({fx},{fy}) -> ({tx},{ty})")
    
    else:
        p.print_help()


if __name__ == '__main__':
    main()