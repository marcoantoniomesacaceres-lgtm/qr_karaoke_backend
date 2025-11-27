#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar updateQueueUI(data) en el if - versión robusta
"""

# Leer el archivo
with open('static/player.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar la línea y agregar updateQueueUI
output_lines = []
for i, line in enumerate(lines):
    output_lines.append(line)
    # Si encontramos el if con la lista de tipos de eventos
    if "if (!['play_song', 'song_finished', 'notification', 'reaction', 'restart_song'].includes(data.type))" in line:
        # La siguiente línea debería ser una línea en blanco
        # Agregar updateQueueUI antes del cierre del if
        output_lines.append('                    updateQueueUI(data);\r\n')

# Guardar el archivo
with open('static/player.html', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("✅ Agregada llamada a updateQueueUI(data)")
