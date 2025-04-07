# Criando o Executável

Para criar o executável, execute o comando:
''sh
pyinstaller --onefile --windowed downloadium.py
''
O executável será criado dentro da pasta dist

Personalização (Opcional)
Se você quiser personalizar o ícone do executável, adicione o parâmetro --icon ao comando:

''sh
pyinstaller --onefile --windowed --icon=icone.ico downloadium.py
''

Substitua icone.ico pelo caminho do arquivo de ícone que você deseja usar.
