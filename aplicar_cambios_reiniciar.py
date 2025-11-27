#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar los cambios necesarios para la funcionalidad de reiniciar canción
"""

# Leer el archivo
with open('static/player.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar las líneas y hacer los cambios
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # CAMBIO 1: Agregar variables globales después de "let autoplayTimer = null;"
    if 'let autoplayTimer = null;' in line and i > 0 and '// Variables para el autoplay' in lines[i-1]:
        output_lines.append(line)
        output_lines.append('        \r\n')
        output_lines.append('        // Variables para rastrear el video actual (necesarias para reiniciar)\r\n')
        output_lines.append('        let currentVideoId = null;\r\n')
        output_lines.append('        let currentVideoDuration = 0;\r\n')
        i += 1
        continue
    
    # CAMBIO 2: Agregar guardar video en playVideo
    if 'function playVideo(videoId, duration = 0) {' in line:
        output_lines.append(line)
        # Siguiente línea es el console.log
        i += 1
        output_lines.append(lines[i])
        # Siguiente línea es una línea en blanco
        i += 1
        output_lines.append(lines[i])
        # Agregar el código para guardar el video
        output_lines.append('            // Guardar el video actual para poder reiniciarlo\r\n')
        output_lines.append('            currentVideoId = videoId;\r\n')
        output_lines.append('            currentVideoDuration = duration;\r\n')
        output_lines.append('\r\n')
        i += 1
        continue
    
    # CAMBIO 3 y 4: Agregar manejador restart_song y modificar el else
    if 'setTimeout(() => emoji.remove(), 6000); // Limpiar el emoji del DOM' in line:
        output_lines.append(line)
        # Siguiente línea es el cierre del if de reaction
        i += 1
        output_lines.append(lines[i])  # }
        # Saltar el "} else {" original
        i += 1
        # Agregar el nuevo código
        output_lines.append('                \r\n')
        output_lines.append('                // --- NUEVO: Escuchar el evento de reiniciar canción ---\r\n')
        output_lines.append('                if (data.type === ' + "'restart_song'" + ') {\r\n')
        output_lines.append('                    console.log(' + "'🔄 Recibida orden de reiniciar canción'" + ');\r\n')
        output_lines.append('                    if (currentVideoId) {\r\n')
        output_lines.append('                        console.log(`🔄 Reiniciando video: ${currentVideoId}`);\r\n')
        output_lines.append('                        playVideo(currentVideoId, currentVideoDuration);\r\n')
        output_lines.append('                    } else {\r\n')
        output_lines.append('                        console.warn(' + "'⚠️ No hay video actual para reiniciar'" + ');\r\n')
        output_lines.append('                    }\r\n')
        output_lines.append('                }\r\n')
        output_lines.append('                \r\n')
        output_lines.append('                // Si no es un tipo específico, asumimos que es la actualización de la cola\r\n')
        output_lines.append('                if (![' + "'play_song', 'song_finished', 'notification', 'reaction', 'restart_song'" + '].includes(data.type)) {\r\n')
        # Siguiente línea es el comentario que vamos a saltar
        i += 1
        # Siguiente línea es updateQueueUI
        i += 1
        output_lines.append(lines[i])  # updateQueueUI(data);
        # Siguiente línea es el cierre del else
        i += 1
        output_lines.append(lines[i])  # }
        i += 1
        continue
    
    output_lines.append(line)
    i += 1

# Guardar el archivo
with open('static/player.html', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("✅ Cambios aplicados exitosamente!")
print("")
print("Cambios realizados:")
print("1. ✓ Agregadas variables globales currentVideoId y currentVideoDuration")
print("2. ✓ Modificada función playVideo para guardar el video actual")
print("3. ✓ Agregado manejador para el evento restart_song")
print("4. ✓ Modificado el else final para no procesar restart_song como actualización de cola")
print("")
print("El botón de 'Reiniciar canción' ahora debería funcionar correctamente.")
