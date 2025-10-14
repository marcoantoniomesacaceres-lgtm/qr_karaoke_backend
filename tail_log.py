from collections import deque
p = 'karaoke_debug.log'
try:
    with open(p, 'r', encoding='utf-8', errors='replace') as f:
        lines = deque(f, maxlen=200)
    print('\n'.join(lines))
except Exception as e:
    print('ERROR reading log:', e)
