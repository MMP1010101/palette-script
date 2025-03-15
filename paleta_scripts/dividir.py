import os
import argparse
from PIL import Image
import numpy as np

def cargar_imagen(ruta_imagen):
    """Carga una imagen desde una ruta especificada."""
    try:
        imagen = Image.open(ruta_imagen)
        if imagen.mode != "RGBA" and "A" in imagen.getbands():
            imagen = imagen.convert("RGBA")
        return imagen
    except Exception as e:
        print(f"Error al cargar la imagen: {e}")
        return None

def detectar_sprites_horizontal(imagen):
    """Detecta los límites horizontales de cada sprite en una imagen."""
    datos = np.array(imagen)
    altura, anchura = datos.shape[:2]
    
    # Buscar columnas que tienen píxeles no transparentes
    columnas_no_vacias = []
    inicio_sprite = None
    
    for x in range(anchura):
        # Comprueba si hay píxeles no transparentes en esta columna
        columna = datos[:, x, 3]  # Canal alpha
        if np.any(columna > 0):  # Hay píxeles no transparentes
            if inicio_sprite is None:
                inicio_sprite = x
        elif inicio_sprite is not None:
            # Hemos encontrado el final de un sprite
            columnas_no_vacias.append((inicio_sprite, x))
            inicio_sprite = None
    
    # Comprobar si hay un sprite que llega hasta el borde derecho
    if inicio_sprite is not None:
        columnas_no_vacias.append((inicio_sprite, anchura))
    
    return columnas_no_vacias

def detectar_sprites_vertical(imagen):
    """Detecta los límites verticales de cada sprite en una imagen."""
    datos = np.array(imagen)
    altura, anchura = datos.shape[:2]
    
    # Buscar filas que tienen píxeles no transparentes
    filas_no_vacias = []
    inicio_sprite = None
    
    for y in range(altura):
        # Comprueba si hay píxeles no transparentes en esta fila
        fila = datos[y, :, 3]  # Canal alpha
        if np.any(fila > 0):  # Hay píxeles no transparentes
            if inicio_sprite is None:
                inicio_sprite = y
        elif inicio_sprite is not None:
            # Hemos encontrado el final de un sprite
            filas_no_vacias.append((inicio_sprite, y))
            inicio_sprite = None
    
    # Comprobar si hay un sprite que llega hasta el borde inferior
    if inicio_sprite is not None:
        filas_no_vacias.append((inicio_sprite, altura))
    
    return filas_no_vacias

def detectar_sprites(imagen):
    """Detecta los límites de cada sprite en una imagen, tanto horizontal como verticalmente."""
    limites_horizontales = detectar_sprites_horizontal(imagen)
    limites_verticales = detectar_sprites_vertical(imagen)
    
    sprites = []
    limites = []
    
    for x_inicio, x_fin in limites_horizontales:
        for y_inicio, y_fin in limites_verticales:
            sprite = imagen.crop((x_inicio, y_inicio, x_fin, y_fin))
            sprites.append(sprite)
            limites.append((x_inicio, y_inicio, x_fin, y_fin))
    
    return sprites, limites

def recortar_sprites(imagen, modo='horizontal'):
    """Recorta los sprites individuales de la imagen."""
    if modo == 'horizontal':
        limites = detectar_sprites_horizontal(imagen)
        sprites = [imagen.crop((x_inicio, 0, x_fin, imagen.height)) for x_inicio, x_fin in limites]
    else:  # vertical
        limites = detectar_sprites_vertical(imagen)
        sprites = [imagen.crop((0, y_inicio, imagen.width, y_fin)) for y_inicio, y_fin in limites]
    
    return sprites, limites

def dividir_sprites_fijos(imagen, ancho, alto):
    """Divide una imagen en sprites de tamaño fijo."""
    sprites = []
    limites = []
    
    imagen_ancho, imagen_alto = imagen.size
    
    # Calcula cuántos sprites caben en la imagen
    num_sprites_x = imagen_ancho // ancho
    num_sprites_y = imagen_alto // alto
    
    for y in range(num_sprites_y):
        for x in range(num_sprites_x):
            left = x * ancho
            upper = y * alto
            right = left + ancho
            lower = upper + alto
            
            sprite = imagen.crop((left, upper, right, lower))
            sprites.append(sprite)
            limites.append((left, upper, right, lower))
    
    return sprites, limites

def detectar_sprites_por_numero(imagen, num_horizontal, num_vertical):
    """Detecta los límites de cada sprite en una imagen basado en el número de sprites horizontal y verticalmente."""
    imagen_ancho, imagen_alto = imagen.size
    ancho_sprite = imagen_ancho // num_horizontal
    alto_sprite = imagen_alto // num_vertical
    
    sprites = []
    limites = []
    
    for y in range(num_vertical):
        for x in range(num_horizontal):
            left = x * ancho_sprite
            upper = y * alto_sprite
            right = left + ancho_sprite
            lower = upper + alto_sprite
            
            sprite = imagen.crop((left, upper, right, lower))
            sprites.append(sprite)
            limites.append((left, upper, right, lower))
    
    return sprites, limites

def guardar_sprites(sprites, directorio_salida, nombre_base):
    """Guarda los sprites recortados como archivos individuales."""
    os.makedirs(directorio_salida, exist_ok=True)
    
    for i, sprite in enumerate(sprites):
        nombre_archivo = f"{nombre_base}_{i+1}.png"
        ruta_completa = os.path.join(directorio_salida, nombre_archivo)
        sprite.save(ruta_completa)
        print(f"Sprite guardado: {ruta_completa}")

def main():
    parser = argparse.ArgumentParser(description="Divide una hoja de sprites en sprites individuales.")
    parser.add_argument("imagen", help="Ruta de la imagen a procesar")
    parser.add_argument("--modo", choices=["horizontal", "vertical", "fijo", "auto", "numero"], default="fijo",
                        help="Modo de división: 'horizontal', 'vertical', 'fijo', 'auto' o 'numero' (predeterminado: fijo)")
    parser.add_argument("--salida", default="sprites_recortados",
                        help="Directorio donde guardar los sprites (predeterminado: 'sprites_recortados')")
    parser.add_argument("--nombre", default="sprite",
                        help="Nombre base para los sprites guardados (predeterminado: 'sprite')")
    parser.add_argument("--ancho", type=int, default=0,
                        help="Ancho en píxeles de cada sprite (para modo 'fijo')")
    parser.add_argument("--alto", type=int, default=0,
                        help="Alto en píxeles de cada sprite (para modo 'fijo')")
    parser.add_argument("--num_horizontal", type=int, default=0,
                        help="Número de sprites horizontalmente (para modo 'numero')")
    parser.add_argument("--num_vertical", type=int, default=0,
                        help="Número de sprites verticalmente (para modo 'numero')")
    
    args = parser.parse_args()
    
    imagen = cargar_imagen(args.imagen)
    if imagen:
        if args.modo == "fijo":
            # Verificar que se proporcionaron ancho y alto
            if args.ancho <= 0 or args.alto <= 0:
                print("Error: Para el modo 'fijo', debe proporcionar un ancho y alto válidos (mayores que 0).")
                return
                
            sprites, limites = dividir_sprites_fijos(imagen, args.ancho, args.alto)
            print(f"Se han generado {len(sprites)} sprites con dimensiones {args.ancho}x{args.alto} píxeles.")
            for i, limite in enumerate(limites):
                left, upper, right, lower = limite
                print(f"Sprite {i+1}: Coordenadas (x1={left}, y1={upper}, x2={right}, y2={lower})")
        elif args.modo == "auto":
            sprites, limites = detectar_sprites(imagen)
            print(f"Se han detectado {len(sprites)} sprites.")
            for i, limite in enumerate(limites):
                print(f"Sprite {i+1}: Coordenadas (x1={limite[0]}, y1={limite[1]}, x2={limite[2]}, y2={limite[3]})")
        elif args.modo == "numero":
            # Verificar que se proporcionaron num_horizontal y num_vertical
            if args.num_horizontal <= 0 or args.num_vertical <= 0:
                print("Error: Para el modo 'numero', debe proporcionar un número válido de sprites horizontal y verticalmente (mayores que 0).")
                return
                
            sprites, limites = detectar_sprites_por_numero(imagen, args.num_horizontal, args.num_vertical)
            print(f"Se han generado {len(sprites)} sprites con {args.num_horizontal}x{args.num_vertical} divisiones.")
            for i, limite in enumerate(limites):
                left, upper, right, lower = limite
                print(f"Sprite {i+1}: Coordenadas (x1={left}, y1={upper}, x2={right}, y2={lower})")
        else:
            sprites, limites = recortar_sprites(imagen, args.modo)
            print(f"Se han detectado {len(sprites)} sprites.")
            for i, limite in enumerate(limites):
                if args.modo == "horizontal":
                    print(f"Sprite {i+1}: Desde x={limite[0]} hasta x={limite[1]}")
                else:
                    print(f"Sprite {i+1}: Desde y={limite[0]} hasta y={limite[1]}")
        
        guardar_sprites(sprites, args.salida, args.nombre)
        print("Proceso completado con éxito.")

if __name__ == "__main__":
    main()
    