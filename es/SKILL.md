# Escritura técnica en español

Basado en **Norma UNE 157001:2002** (Criterios generales para la elaboración de documentos) y **Guía de Lenguaje Administrativo** del Gobierno de España.

Escribe documentación técnica clara, directa y accesible en español. Este skill aplica principios de lenguaje llano adaptados al contexto técnico hispanohablante.

## Normas de referencia

### Norma UNE 157001:2002
Estándar oficial español para elaboración de documentos técnicos. Publicado por AENOR (Asociación Española de Normalización).

Principios clave:
- **Claridad**: El mensaje debe comprenderse en una primera lectura
- **Concisión**: Usar el mínimo de palabras necesarias
- **Precisión**: Evitar ambigüedades y vaguedades
- **Accesibilidad**: Adaptar el lenguaje al público objetivo

### Guía de Lenguaje Administrativo
Recomendaciones oficiales del Gobierno de España para comunicación clara con ciudadanos.

Disponible en: https://www.administracion.gob.es/pag_Home/atencionCiudadano/catalogo-tramites/lenguaje-claro.html

### Fundéu BBVA
Fundación del Español Urgente, avalada por la Real Academia Española.

Consulta dudas lingüísticas: https://www.fundeu.es/

## Principios fundamentales

### 1. Usa voz activa (UNE 157001, §4.2)
La voz activa clarifica quién realiza la acción.

- **Mal**: El archivo es guardado por el sistema
- **Bien**: El sistema guarda el archivo

- **Mal**: Los datos son procesados automáticamente
- **Bien**: El sistema procesa los datos automáticamente

### 2. Evita frases burocráticas (Guía Lenguaje Claro, §3.1)
Elimina construcciones administrativas innecesarias.

- **Mal**: En el marco de la implementación del sistema
- **Bien**: Al implementar el sistema

- **Mal**: Con el objeto de facilitar la comprensión
- **Bien**: Para facilitar la comprensión

### 3. Sé directo y conciso (UNE 157001, §4.3)
Ve al grano. Elimina palabras de relleno.

- **Mal**: Cabe destacar que es importante mencionar que
- **Bien**: Es importante

- **Mal**: En el mundo de hoy, en la era digital
- **Bien**: (eliminar - no aporta información)

### 4. Usa oraciones cortas (UNE 157001, §4.4)
Máximo 20 palabras por oración. Una idea por oración.

- **Mal**: El administrador debe iniciar sesión en el sistema con sus credenciales antes de poder acceder a las funcionalidades de configuración que permiten modificar los parámetros del sistema.
- **Bien**: El administrador debe iniciar sesión. Luego puede acceder a la configuración para modificar los parámetros.

### 5. Evita nominalizaciones innecesarias (UNE 157001, §4.5)
Usa verbos en lugar de sustantivos derivados.

- **Mal**: La realización de la configuración
- **Bien**: Configurar

- **Mal**: La implementación de la solución
- **Bien**: Implementar la solución

### 6. Usa terminología técnica precisa (Fundéu)
Usa términos técnicos cuando sean necesarios. Evita eufemismos.

- **Mal**: incidencia → problema
- **Mal**: desafío → problema
- **Bien**: error de conexión (específico)

## Estructura del documento (UNE 157001, §5)

### Títulos
- Usa verbos en infinitivo para instrucciones: Instalar, Configurar, Ejecutar
- Usa sustantivos para conceptos: Arquitectura, Configuración, Requisitos
- Máximo 6 niveles de encabezados

### Párrafos
- Máximo 6 oraciones por párrafo
- Un tema por párrafo
- Empieza con la idea principal

### Listas
- Usa para pasos secuenciales
- Usa para opciones o alternativas
- Máximo 7 elementos por lista

## Vocabulario a evitar

### Frases burocráticas (Guía Lenguaje Claro)
- a efectos de → para
- en virtud de → según
- por medio de la presente → (eliminar)
- en el marco de → en
- con el objeto de → para

### Lenguaje de marketing
- innovador → describe qué hace
- revolucionario → (eliminar)
- de vanguardia → (eliminar)
- solución integral → describe qué incluye

### AI slop
- en el mundo de hoy → (eliminar)
- en la era digital → (eliminar)
- cabe destacar → (eliminar)
- es importante destacar → ve al punto

### Palabras de relleno
- básicamente → (eliminar)
- simplemente → (eliminar)
- realmente → (eliminar)
- actualmente → solo si es relevante

## Verificación

Antes de entregar (checklist UNE 157001):
1. ¿Cada oración tiene máximo 20 palabras?
2. ¿Usé voz activa?
3. ¿Eliminé frases burocráticas?
4. ¿El documento es directo y conciso?
5. ¿Los párrafos tienen máximo 6 oraciones?
6. ¿Evité nominalizaciones innecesarias?
7. ¿La terminología es precisa?

Usa el linter:
    python3 es/es-ste-lint.py documento.md

**Score**: violaciones por 100 palabras
- <2.0: Excelente (cumple UNE 157001)
- <5.0: Aceptable
- >10.0: Necesita revisión

## Recursos adicionales

### Estándares oficiales
- **Norma UNE 157001:2002**: https://www.une.org/
- **Guía de Lenguaje Administrativo**: https://www.administracion.gob.es/pag_Home/atencionCiudadano/catalogo-tramites/lenguaje-claro.html

### Referencias lingüísticas
- **Real Academia Española**: https://www.rae.es
- **Fundéu BBVA**: https://www.fundeu.es
- **Diccionario panhispánico de dudas**: https://www.rae.es/dpd/

## Comparación con otros estándares

| Estándar | Idioma | Enfoque |
|----------|--------|---------|
| ASD-STE100 | Inglés | Simplified Technical English |
| ГОСТ Р 58049-2017 | Ruso | Упрощённый технический язык |
| **UNE 157001:2002** | **Español** | **Criterios para documentos técnicos** |

Este skill implementa los principios de UNE 157001 adaptados para documentación técnica moderna.
