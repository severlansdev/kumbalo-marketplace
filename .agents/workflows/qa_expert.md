---
description: Ejecutar el Agente Experto en QA y Diseño Web
---

# Agente Experto en QA y Diseño Web

Este workflow ejecuta una auditoría completa de calidad (QA) y diseño en el sitio web interactuando como un agente experto. Evalúa:
- Aspectos visuales y estética premium
- Ortografía y gramática
- Responsividad (Mobile y Desktop)
- Navegación entre páginas (enlaces rotos, UX)
- Animaciones y transiciones (fluidez de GSAP)
- Funcionalidad general (formularios, botones, modales)

## Pasos de Ejecución

1. **Iniciar Servidor Local**
   Inicia un servidor local en el directorio del frontend para que el subagente pueda navegar sin bloqueos del protocolo `file://`. Puedes usar Python o Node.
   ```bash
   // turbo
   python -m http.server 8080
   ```

2. **Lanzar Browser Subagent de QA**
   Ejecuta la herramienta `browser_subagent` asignándole la siguiente instrucción precisa:
   *Task:* "Eres un Agente Experto en QA y Diseño Web. Navega a http://localhost:8080. Realiza una auditoría exhaustiva: 1. Verifica la estética visual (contraste, modo oscuro 'Ferrari', alineación). 2. Revisa la tipografía y ortografía en la página principal y páginas vinculadas. 3. Redimensiona la ventana para probar la responsividad (vista móvil). 4. Navega por todos los enlaces principales para asegurar que la navegación funciona y no hay errores 404. 5. Evalúa las animaciones de scroll y hover. 6. Verifica la funcionalidad de botones y formularios. Genera un reporte detallado con las fallas encontradas y áreas de mejora."

3. **Análisis de Resultados**
   Una vez que el subagente termine, revisa minuciosamente sus capturas de pantalla y su reporte de hallazgos. 

4. **Crear Artefacto de Reporte y Ejecutar Correcciones**
   Genera un artefacto llamado `qa_report.md` con los resultados. Inmediatamente después, asume la responsabilidad y cambia al modo EXECUTION para corregir proactivamente todos los fallos detectados en el HTML, CSS y JS, asegurando una calidad impecable.
