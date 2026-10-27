# Brief — LFG de rol de mesa (nombre por definir)

> **Proyecto en dos etapas:** v1 es una demo de portafolio con datos ficticios. Se diseña desde el inicio para crecer a un producto real con usuarios, cuentas y moderación.

## Recomendación

Construir un "looking for group" para **rol de mesa (TTRPG)** en español, con foco en Chile. El sitio hace **el match entre personas**: la logística (comuna, plataforma, anfitrión, mesa pagada) es parte del match. Una vez que hacen match, coordinan entre ellos.

**Stack:** Django + PostgreSQL (base alojada en Supabase), con la app desplegada en Render.

**El match se calcula en tres capas:**
1. **Filtro duro de logística:** si pueden jugar juntos.
2. **Similitud de estilo:** sliders de 1 a 5.
3. **Bloqueo por seguridad:** si la línea de uno es el tema favorito del otro, ese match no se muestra.

Las líneas son privadas: nunca aparecen en el perfil público y se muestran automáticamente cuando hay interés mutuo. Ese es el diferencial frente a los LFG que solo preguntan día y hora.

## Problema

Los grupos de rol se arman por logística (día, hora, plataforma) y se desarman a la tercera sesión porque nadie preguntó por gustos ni por límites. Un jugador que odia el gore termina en una mesa grimdark; un táctico termina en una mesa 100% narrativa.

## Público

- **Jugadores:** buscan mesa. Pueden ser nuevos, intermedios o veteranos, en Santiago y regiones u online.
- **Másters:** buscan jugadores afines para su campaña o one-shot.

## El perfil: cinco capas

### 1. Logística (filtro duro)
- **Modalidad:** presencial, online o ambas.
  - Presencial: comunas donde puede jugar.
  - Online: plataformas (Roll20, Foundry, Discord, Owlbear).
- **Disponibilidad ("mi mes"):** un calendario con **las próximas 4 semanas reales**, donde marca bloques de 2 horas (por ejemplo, viernes 20–22 y 22–24).
  - Atajos: "repetir esta semana" y "repetir semana por medio".
  - La frecuencia (semanal, quincenal…) y la duración de sesión salen solas de lo que marca.
  - Sirve para turnos rotativos (por ejemplo 7x7), custodia compartida o "solo el primer sábado".
  - Cada mes el sitio pregunta: "¿Tu disponibilidad sigue igual?".
- **Compromiso:** one-shot, campaña corta o campaña larga.
- **Rol:** jugador, máster o ambos.
- **Idioma:** uno o varios.
- **Anfitrión:** si puede recibir la mesa en su casa.
- **Mesa pagada:** si acepta pagar por una mesa (jugador) o si cobra (máster), y el precio.

**Edad:** se pide la fecha de nacimiento **solo para comprobar que es mayor de 18**. Nunca se muestra, no se puede filtrar ni buscar por edad, y no forma parte del match.

### 2. Sistemas y experiencia
- **Sistemas:** los que conoce y los que quiere probar. D&D 5e/2024, Pathfinder, Call of Cthulhu, Vampiro, PbtA, Blades in the Dark, OSR…
- **Experiencia:** nuevo, intermedio o veterano.
- **Novatos:** si le acomoda enseñar a novatos o prefiere mesas con experiencia.

### 3. Estilo de juego (base del match)

**Seis atributos, asignados con dados.** La persona "tira los dados" y siempre salen los mismos valores (15, 14, 13, 12, 10 y 8, el *standard array*). Luego los reparte entre los seis atributos, como al crear un personaje. Esto obliga a priorizar: no se puede poner todo al máximo.
- Combate
- Exploración
- Interpretación
- Misterio e intriga
- Estrategia
- Humor

Accesibilidad: además de arrastrar, cada atributo tiene un selector para elegir su valor con teclado o lector de pantalla, y la animación respeta "reducir movimiento".

**Seis ejes con dos extremos (sliders de 1 a 5):**
- **Enfoque:** narrativo ↔ táctico.
- **Mundo:** sandbox ↔ lineal.
- **Reglas:** RAW estricto ↔ regla de lo genial.
- **Ritmo:** ágil (acción, escenas cortas) ↔ pausado (escenas largas, conversaciones).
- **Profundidad de interpretación:** ligera (describe lo que hace su personaje) ↔ inmersiva (voces, drama, actuación).
- **Intensidad emocional:** aventura liviana ↔ drama que deja pensando.

**Letalidad** (slider de 1 a 5): de "mi personaje no muere" a "puede morir sin drama".

Selección múltiple:
- **Tono:** épico, grimdark, humor o terror.
- **Arquetipo:** actor, táctico, explorador, coleccionista de loot, el que hace reír u optimizador.
- **Ambientaciones:** fantasía clásica, sci-fi, steampunk, horror cósmico o western.

### 4. Contenido y seguridad: Líneas y Velos
- **Checklist por tema** con cuatro estados: **lo busco**, OK, velo o línea. Temas, entre otros:
  - Arañas, fobias, adicciones, suicidio, racismo, religión, esclavitud, PvP, daño a niños, tortura gráfica y gore.
  - Tres temas sexuales por separado:
    - **Romance entre personajes** (besos, relaciones).
    - **Contenido sexual explícito** (descrito en escena).
    - **Violencia sexual**, que viene marcada como línea por defecto.
- **Herramientas que espera en la mesa:** X-Card, Sesión Cero y pausas.
- **Comportamientos que no tolera:** celulares en la mesa, metagaming, "es lo que haría mi personaje"…
- **Privacidad:** las líneas nunca aparecen en el perfil público. Cuando dos personas marcan interés mutuo, se muestran automáticamente a ambas.

### 5. Social y vibra
- **Ambiente:** de serio/enfocado a casual "con chela".
- **En la mesa:** alcohol, comida, tabaco.
- **Amistad:** si quiere hacer amigos o solo jugar.
- **Campo libre:** "Mi personaje favorito" o "la mejor sesión que he tenido".

## Cómo funciona el match

1. **Filtro duro:** modalidad compatible (una comuna en común si es presencial, una plataforma en común si es online), bloques de horario en común en las próximas 4 semanas, compromiso e idioma. La edad no participa. Mesa pagada: solo se cruza a quien cobra con quien acepta pagar. Si algo no calza, la persona no aparece.
2. **Bloqueo por seguridad:** si un tema es *línea* para una persona y la otra lo marcó como contenido central de su mesa, el match se oculta. No aparece como "baja compatibilidad"; simplemente no se muestra.
3. **Puntaje de afinidad (0–100):** cercanía en los atributos (dados) y los ejes de estilo, más coincidencias de sistemas, tono y arquetipos.
4. **Explicación del puntaje:** "Coinciden en: mucha exploración, tono oscuro, D&D 5e. Difieren en: letalidad."

## Alcance v1 (demo de portafolio)

- **Landing** que explique el problema y las tres capas.
- **Perfil de jugador:** onboarding en pasos (las cinco capas) y página pública del perfil. Las líneas no se muestran en la página pública.
- **Explorar:** personas compatibles, con filtros y puntaje explicado.
- **Interés mutuo:** "Me interesa" en un perfil. Si ambos lo marcan, se muestran automáticamente sus líneas y el contacto que cada uno eligió compartir (Discord o correo), y desde ahí coordinan.
- **Datos semilla:** 20–30 perfiles ficticios, claramente marcados como demo.

## Decisiones tomadas

- **Match:** persona ↔ persona. Todos tienen el mismo perfil; el rol (jugador, máster o ambos) solo cambia el orden de los resultados.
- **Líneas:** privadas; se muestran automáticamente con el interés mutuo.
- **Cuentas:** login real desde la v1 (correo y Discord).
- **Edad:** solo mayores de 18; la fecha de nacimiento es oculta y no se puede buscar ni filtrar por edad.
- **Disponibilidad:** calendario de las próximas 4 semanas con bloques de 2 horas.
- **Estilo:** 6 atributos asignados con dados (standard array) + 6 ejes + letalidad.
- **Stack:** Django + plantillas + HTMX; PostgreSQL alojado en Supabase (solo como base de datos); login con django-allauth (correo y Discord); app en Render.

## Decisiones tomadas

- **Nombre:** Terrenar ("el reino donde se juntan los roleros"). Bestiario pasa a ser el nombre de la skin medieval.
- **Dirección visual:** "Bestiario rubricado" (manuscrito antiguo; perfil como bloque de atributos), salvo objeción legal. Alternativa: "Registro del gremio".

## Fuera de alcance v1

Chat entre usuarios, cobro de mesas dentro del sitio, calendario integrado, reseñas de jugadores y moderación con reportes. Todo eso queda para la etapa "producto real".

## Qué demuestra en el portafolio

- **Full-stack:** base de datos, autenticación con proveedores externos y control de acceso a datos sensibles.
- **Algoritmo de matching:** explicable, no una caja negra.
- **Formulario multi-paso complejo:** sliders accesibles y checklist de tres estados.
- **Diseño de producto:** pensado para la seguridad y el bienestar de los usuarios.
