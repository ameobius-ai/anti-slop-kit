# Escritura técnica en español

Escribe documentación técnica clara y directa en español.

## Principios fundamentales

### 1. Usa voz activa
- Mal: El archivo es guardado por el sistema
- Bien: El sistema guarda el archivo

### 2. Evita frases burocráticas
- Mal: En el marco de la implementación del sistema
- Bien: Al implementar el sistema

### 3. Sé directo y conciso
- Mal: Cabe destacar que es importante mencionar que
- Bien: Es importante

### 4. Usa oraciones cortas
- Máximo 20 palabras por oración
- Una idea por oración

### 5. Evita nominalizaciones innecesarias
- Mal: La realización de la configuración
- Bien: Configurar

## Vocabulario a evitar

### Frases burocráticas
- a efectos de → para
- en virtud de → según
- en el marco de → en
- con el objeto de → para

### Lenguaje de marketing
- innovador → describe qué hace
- revolucionario → eliminar
- de vanguardia → eliminar

### AI slop
- en el mundo de hoy → eliminar
- cabe destacar → eliminar
- es importante destacar → ve al punto

## Verificación

Antes de entregar:
1. Cada oración tiene máximo 20 palabras
2. Usé voz activa
3. Eliminé frases burocráticas
4. El documento es directo y conciso

Usa el linter:
    python3 es/es-ste-lint.py documento.md
