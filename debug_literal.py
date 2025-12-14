from pathlib import Path

p = Path('Downloadium/tests/test_utils.py')
src = p.read_text()
start = src.find('"path/to\\file"')
print('raw snippet:', src[start-20:start+20])
# extract raw literal
lit = '"path/to\\file"'
print('literal source:', lit)
# now evaluate literal via python eval to see actual string value
val = eval(lit)
print('repr of evaluated:', repr(val))
print('ordinals:', [ord(c) for c in val])
