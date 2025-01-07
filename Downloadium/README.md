# Downloadium

Downloadium é um software de download de vídeos do YouTube, desenvolvido inicialmente em Python com uma interface gráfica utilizando Tkinter. Este projeto é voltado para fornecer funcionalidades avançadas de download de vídeos, áudio e outros recursos de mídia de forma simples e eficiente.

## Funcionalidades

- **Download de vídeos individuais**: Baixe vídeos diretamente do YouTube com facilidade.
- **Download de playlists**: Obtenha todos os vídeos de uma playlist de uma só vez.
- **Download de canais**: Extraia todos os vídeos de um canal específico.
- **Escolha de resolução**: Selecione entre diferentes resoluções disponíveis.
- **Conversão para áudio**: Baixe apenas o áudio dos vídeos no formato desejado.
- **Download de thumbnails**: Baixe a imagem de capa do vídeo separadamente ou junto ao vídeo.
- **Legendas**: Suporte para download de legendas em diversos idiomas, como arquivo separado ou embutido no vídeo.
- **Múltiplas faixas de áudio**: Suporte para vídeos com múltiplos canais de áudio.


## Requisitos

- Python 3.9+
- Dependências listadas em `requirements.txt`

## Como Usar

1. Clone este repositório:
   ```bash
   git clone https://github.com/usuario/downloadium.git
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o programa:
   ```bash
   python main.py
   ```

## Contribuindo

Contribuições são bem-vindas! Por favor, siga os passos abaixo:

1. Faça um fork deste repositório.
2. Crie uma branch para suas alterações:
   ```bash
   git checkout -b minha-nova-feature
   ```
3. Dê Commit em suas alterações:
   ```bash
   git commit -m "Adicionei uma nova feature"
   ```
4. Envie suas alterações:
   ```bash
   git push origin minha-nova-feature
   ```
5. Abra um Pull Request.

## Testes

Para rodar os testes:
```bash
python -m unittest discover -s tests
```

