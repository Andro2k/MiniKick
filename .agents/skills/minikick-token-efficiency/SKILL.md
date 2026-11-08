---
name: minikick-token-efficiency
description: Reglas para trabajar en MiniKick gastando pocos tokens. Úsala al inicio de cualquier tarea de código, revisión de logs, pruebas o documentación en este repositorio, y cuando el usuario diga que le quedan pocos tokens.
---

# MiniKick — Eficiencia de tokens

Objetivo: resolver la tarea con la menor cantidad de lectura, llamadas y texto, sin bajar la calidad ni saltarse verificaciones.

## 1. Antes de empezar
- Pregunta como máximo una cosa, y solo si sin ella no se puede avanzar. Si hay una opción razonable, asúmela y dilo en una línea.
- Clasifica la tarea: pequeña (1 archivo, hasta 3 llamadas), mediana (hasta 10) o grande (más de 10: propón un plan de pasos antes de ejecutar).
- Haz `git pull` una sola vez al inicio y anota el hash. Si el remoto cambia durante la tarea, rebasa una vez, no repitas el análisis.

## 2. Leer poco
- Nunca abras un archivo completo para buscar algo. Localiza con `rg -n`/`Select-String`, mide con `wc -l` y lee solo rangos (`sed -n 120,170p`).
- Recorta toda salida: `| head -40`, `| tail -5`, `cut -c1-160`. Para listas largas, cuenta primero (`| wc -l`).
- No releas ni vuelvas a mostrar un archivo ya leído ni uno que acabas de editar; confía en el resultado de la herramienta y vuelve a leer solo si falló.
- Los logs se analizan con filtros y conteos (nivel, ventana de tiempo, `grep -c`), nunca se pegan completos.

## 3. Cambiar poco
- Haz el cambio mínimo que cumple lo pedido. No agregues refactors, opciones, archivos o documentos que nadie pidió.
- Para cambios repetitivos usa un solo script de reemplazo con verificación (el texto antiguo debe aparecer exactamente una vez) en vez de muchas ediciones.
- Si una idea no está pedida, menciónala en una línea al final y no la implementes.

## 4. Verificar sin derrochar
- Ejecuta solo las pruebas de los archivos tocados (`pytest archivo -q --tb=line | tail -5`), no la suite completa. Si la suite completa se cae por Qt, corre cada archivo por separado una sola vez.
- Corre `resources/tools/project_quality_suite.py --quick` una vez, al final.
- Reporta conteos (`N aprobadas, M fallidas`) y solo el nombre de lo que falla. Si una falla ya existía antes del cambio, compruébalo una vez y anótalo.
- Para cambios de estilos, compara una foto de valores y del QSS antes y después en lugar de leer el QSS.

## 5. Entregar corto
- Cambios de código: entrega un patch (`git diff`) verificado con `git apply --check` sobre el HEAD remoto, no código pegado en el chat.
- Documentación: solo si se pide. Un walkthrough por tema, siguiendo `minikick-walkthrough-manager`; no lo reescribas cuando solo cambia un dato.
- Respuesta final: qué cambió, en qué archivos, resultado de las pruebas y riesgos. Sin repetir el contenido del patch ni de los documentos, sin recapitular turnos anteriores y sin tablas si una línea basta.

## 6. Delegar a otra IA
Cuando la tarea sea grande o los tokens se acaben, entrega un prompt de traspaso con estas secciones: Contexto (repo, rama, hash, qué se sabe y qué no), Objetivo, Tareas numeradas, Reglas del proyecto, Entrega (patch, walkthrough, resumen de comandos). Indica qué fallas son conocidas para que no se pierdan tokens investigándolas.

## 7. Para la persona usuaria
- Abre un chat nuevo por tarea: en una conversación larga el historial completo se reprocesa en cada mensaje y consume mucho más.
- Adjunta solo los archivos relevantes y menciona rama y commit.
- Pide primero un diagnóstico corto y luego el cambio, en lugar de pedirlo todo junto.
- Al cerrar una tarea, guarda en las notas del proyecto lo que debe recordarse y empieza la siguiente en un chat aparte.
