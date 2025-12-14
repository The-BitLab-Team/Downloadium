from utils import sanitize_filename
from re import sub

s = "path/to\\file"
print('repr:', repr(s))
print('chars:', [c for c in s])
print('sanitized (func):', sanitize_filename(s))
print('sanitized (re):', sub(r'[<>:"/\\|?*\x00-\x1F]','_',s))
