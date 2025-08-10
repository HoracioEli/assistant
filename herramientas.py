import re

def VERIFICAR_CUIT(cuit_str):
    """
    Verifica si un CUIT es válido según las reglas establecidas.
    
    Args:
        cuit_str (str): String con el CUIT a verificar
        
    Returns:
        bool: True si el CUIT es válido, False en caso contrario
    """
    # Quitar espacios del principio y fin
    cuit = cuit_str.strip()
    
    # Si el string tiene exactamente 11 dígitos, formatear automáticamente
    if len(cuit) == 11 and cuit.isdigit():
        # Insertar guiones: xx-xxxxxxxx-x
        cuit = cuit[:2] + '-' + cuit[2:10] + '-' + cuit[10]
    
    # Verificar que comience con 2 o 3
    if not (cuit.startswith('2') or cuit.startswith('3')):
        return False
    
    # Verificar formato xx-xxxxxxxx-x usando expresión regular
    patron = r'^[23]\d-\d{8}-\d$'
    
    if not re.match(patron, cuit):
        return False

    # Extraer los números para calcular el dígito verificador
    # Remover los guiones y convertir a lista de enteros
    numeros = [int(d) for d in cuit.replace('-', '')]
    
    # Los primeros 10 dígitos son para el cálculo
    digitos_calculo = numeros[:10]
    digito_verificador_dado = numeros[10]
    
    # Coeficientes para el cálculo del dígito verificador
    coeficientes = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    
    # Calcular la suma ponderada
    suma = sum(digito * coef for digito, coef in zip(digitos_calculo, coeficientes))
    
    # Calcular el resto de la división por 11
    resto = suma % 11
    
    # Determinar el dígito verificador correcto
    if resto < 2:
        digito_verificador_correcto = resto
    else:
        digito_verificador_correcto = 11 - resto
    
    # Verificar si el dígito verificador coincide
    return digito_verificador_dado == digito_verificador_correcto


# Ejemplos de uso y pruebas
if __name__ == "__main__":
    # Casos de prueba
    casos_prueba = [
        "34-50004533-9",    # Con espacios y 11 dígitos
        "30123456747",        # 11 dígitos sin guiones
        "20123456743",        # 11 dígitos sin guiones
        "30-12345674-7",      # CUIT válido con guiones
        "20-12345674-3",      # CUIT válido con guiones
        "10123456743",        # No comienza con 2 o 3 (11 dígitos)
        "10-12345674-3",      # No comienza con 2 o 3 (con guiones)
        "20-1234567-3",       # Formato incorrecto (faltan dígitos)
        "20-12345674-5",      # Dígito verificador incorrecto
        "2a123456743",        # Contiene letra (11 caracteres)
        "2a-12345674-3",      # Contiene letra (con guiones)
        "20-12345674",        # Formato incorrecto (sin dígito verificador)
        "2012345674",         # Solo 10 dígitos
        "201234567435",       # 12 dígitos
    ]
    
    print("Pruebas de la función VERIFICAR_CUIT:")
    print("-" * 40)
    
    for cuit in casos_prueba:
        resultado = VERIFICAR_CUIT(cuit)
        print(f"CUIT: '{cuit}' -> {resultado}")