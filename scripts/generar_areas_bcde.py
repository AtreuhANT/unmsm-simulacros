"""Genera cuatro bancos originales de práctica y sus vistas sin claves públicas.

La distribución es editorial para estos simulacros, no una cuota oficial UNMSM.
No sustituye bancos activos: los intentos actuales no guardan versión de examen.
"""

import json
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
NOMBRES = {
    'B': 'Ciencias Básicas', 'C': 'Ingenierías',
    'D': 'Ciencias Económicas y de la Gestión',
    'E': 'Humanidades y Ciencias Jurídicas y Sociales',
}

# Enunciado, solución, cuatro distractores y explicación. Compartir contenidos
# generales entre áreas es intencional; las lecturas y los problemas numéricos varían.
HUMANIDADES = [
    ('Lenguaje', '¿Qué palabra contiene un hiato?', 'país', ['tierra', 'causa', 'puerta', 'ciudad'], 'En país, la vocal cerrada tónica í se separa de la vocal abierta: pa-ís.'),
    ('Lenguaje', '¿Qué oración utiliza correctamente la tilde diacrítica?', 'Él trajo el libro.', ['El trajo él libro.', 'Él trajo él libro.', 'El trajo el libro.', 'El trájo el libro.'], 'Él, pronombre personal, lleva tilde; el, artículo, no la lleva.'),
    ('Lenguaje', 'En «Las investigadoras analizaron las muestras», ¿cuál es el núcleo del sujeto?', 'investigadoras', ['Las', 'analizaron', 'muestras', 'las muestras'], 'El sujeto es Las investigadoras y su núcleo nominal es investigadoras.'),
    ('Lenguaje', 'En «Entregué el informe a Lucía», ¿qué función cumple «el informe»?', 'Objeto directo', ['Sujeto', 'Objeto indirecto', 'Vocativo', 'Complemento de lugar'], 'Es lo entregado y puede sustituirse por lo: Lo entregué a Lucía.'),
    ('Lenguaje', '¿Qué conector expresa oposición?', 'Sin embargo', ['Por tanto', 'Además', 'En consecuencia', 'Por eso'], 'Sin embargo introduce una idea que contrasta con la anterior.'),
    ('Literatura', '¿Qué recurso aparece en «Tus ojos son dos luceros»?', 'Metáfora', ['Hipérbole', 'Anáfora', 'Onomatopeya', 'Enumeración'], 'Se identifica figuradamente los ojos con luceros sin usar un nexo comparativo.'),
    ('Literatura', '¿Qué recurso aparece en «Te esperé mil años», cuando se quiere enfatizar una espera larga?', 'Hipérbole', ['Símil', 'Epíteto', 'Anáfora', 'Aliteración'], 'La duración se exagera deliberadamente para intensificar la expresión.'),
    ('Literatura', '¿Qué tipo de narrador cuenta su propia historia usando «yo»?', 'Narrador protagonista', ['Narrador omnisciente externo', 'Narrador objetivo externo', 'Narrador en segunda persona', 'Narrador colectivo en tercera persona'], 'El narrador protagonista participa como personaje principal y relata su experiencia.'),
    ('Literatura', '¿Quién escribió Los ríos profundos?', 'José María Arguedas', ['César Vallejo', 'Ricardo Palma', 'José Santos Chocano', 'Manuel González Prada'], 'Los ríos profundos es una novela de José María Arguedas.'),
    ('Literatura', '¿A qué género pertenece principalmente una obra escrita para ser representada por actores?', 'Dramático', ['Lírico', 'Épico exclusivamente', 'Ensayístico', 'Periodístico informativo'], 'El género dramático organiza acciones y diálogos para su representación.'),
    ('Psicología', 'Una estudiante asocia un sonido con la llegada de alimento después de observarlos juntos varias veces. ¿Qué aprendizaje ejemplifica?', 'Condicionamiento clásico', ['Aprendizaje por insight exclusivamente', 'Habituación sin asociación', 'Maduración biológica', 'Memoria semántica sin asociación'], 'El condicionamiento clásico se basa en la asociación de estímulos.'),
    ('Psicología', 'Un alumno aprende una técnica al observar a su compañera y luego imitarla. ¿Qué proceso destaca?', 'Aprendizaje por observación', ['Reflejo innato', 'Pérdida de memoria', 'Adaptación sensorial', 'Sueño profundo'], 'Se adquiere una conducta mediante la observación de un modelo.'),
    ('Psicología', '¿Qué tipo de memoria permite mantener brevemente un número mientras se realiza una operación con él?', 'Memoria de trabajo', ['Memoria episódica remota', 'Memoria procedimental exclusivamente', 'Memoria autobiográfica exclusivamente', 'Memoria inmunológica'], 'La memoria de trabajo mantiene y manipula información durante una tarea.'),
    ('Psicología', 'Una persona reconoce que está irritada y decide hacer una pausa antes de responder. ¿Qué capacidad ejercita?', 'Autorregulación emocional', ['Supresión de toda percepción', 'Reflejo rotuliano', 'Amnesia', 'Discriminación cromática'], 'Reconoce la emoción y regula su respuesta en lugar de actuar impulsivamente.'),
    ('Psicología', 'En un estudio, se modifica el tiempo de práctica y se mide el número de aciertos. ¿Cuál es la variable dependiente?', 'El número de aciertos', ['El tiempo de práctica', 'El nombre del investigador', 'La hipótesis escrita', 'La fecha de publicación'], 'La variable dependiente es el resultado medido para observar el efecto de la intervención.'),
    ('Filosofía', '¿Qué disciplina estudia criterios para distinguir argumentos válidos de inválidos?', 'Lógica', ['Estética', 'Geología', 'Botánica', 'Fonética'], 'La lógica estudia formas de inferencia y criterios de validez.'),
    ('Filosofía', 'De «Todos los mamíferos son vertebrados» y «Todos los delfines son mamíferos», ¿qué se sigue necesariamente?', 'Todos los delfines son vertebrados.', ['Todos los vertebrados son delfines.', 'Ningún delfín es vertebrado.', 'Todos los mamíferos son delfines.', 'Algunos delfines no son mamíferos.'], 'La inclusión de delfines en mamíferos y de mamíferos en vertebrados permite esa conclusión.'),
    ('Filosofía', 'Una persona rechaza un argumento atacando la apariencia de quien lo presenta. ¿Qué falacia comete?', 'Ad hominem', ['Modus ponens', 'Doble negación', 'Silogismo válido', 'Definición por género'], 'El ataque personal sustituye el examen de las razones del argumento.'),
    ('Filosofía', '¿Qué rama estudia problemas sobre el conocimiento y su justificación?', 'Epistemología', ['Morfología', 'Cartografía', 'Mecánica', 'Demografía'], 'La epistemología examina el conocimiento, sus fundamentos y límites.'),
    ('Filosofía', '¿Qué pregunta pertenece principalmente a la ética?', '¿Qué razones justifican actuar con honestidad?', ['¿Cuál es la masa del objeto?', '¿Cuánto mide el río?', '¿Qué vocal es abierta?', '¿Cuántos protones tiene el carbono?'], 'La ética examina la acción humana y su justificación moral.'),
    ('Lenguaje', '¿Qué palabra es esdrújula?', 'música', ['reloj', 'papel', 'camino', 'pared'], 'Música tiene la sílaba tónica en la antepenúltima sílaba.'),
    ('Literatura', '¿Qué recurso aparece en «El viento susurraba entre las ventanas»?', 'Personificación', ['Enumeración', 'Hipérbaton obligatorio', 'Metonimia numérica', 'Anáfora'], 'Se atribuye al viento una acción humana: susurrar.'),
    ('Psicología', 'Un premio aumenta la frecuencia de una conducta en ocasiones posteriores. ¿Cómo se describe su función?', 'Reforzamiento positivo', ['Castigo negativo', 'Extinción', 'Reflejo incondicionado', 'Olvido por interferencia'], 'Se añade una consecuencia que incrementa la frecuencia de la conducta.'),
    ('Filosofía', 'Si es verdadero que «Si P, entonces Q» y también es verdadero P, ¿qué conclusión permite el modus ponens?', 'Q', ['No Q', 'No P', 'P y no P', 'Ninguna conclusión'], 'El modus ponens afirma el consecuente cuando se cumplen la condicional y su antecedente.'),
    ('Lenguaje', 'En «Ana compró pan y Luis preparó café», la conjunción «y» establece una relación', 'copulativa', ['adversativa', 'disyuntiva', 'condicional', 'concesiva'], 'La conjunción y une o suma proposiciones: coordinación copulativa.'),
]

CIENCIAS = [
    ('Física', 'Un objeto recorre 120 m en 20 s con rapidez constante. ¿Cuál es su rapidez?', '6 m/s', ['2 m/s', '4 m/s', '12 m/s', '24 m/s'], 'La rapidez es distancia entre tiempo: 120/20 = 6 m/s.'),
    ('Física', 'Una fuerza neta de 18 N actúa sobre una masa de 3 kg. ¿Qué aceleración produce?', '6 m/s²', ['3 m/s²', '9 m/s²', '15 m/s²', '54 m/s²'], 'Por la segunda ley de Newton, a = F/m = 18/3 = 6 m/s².'),
    ('Física', 'Una resistencia de 4 Ω se conecta a 12 V. ¿Qué corriente circula?', '3 A', ['0,3 A', '4 A', '8 A', '48 A'], 'La ley de Ohm da I = V/R = 12/4 = 3 A.'),
    ('Física', '¿Qué magnitud se conserva en una colisión de un sistema aislado, aunque la colisión no sea elástica?', 'Cantidad de movimiento total', ['Energía cinética total en todos los casos', 'Rapidez de cada cuerpo', 'Temperatura de cada cuerpo', 'Volumen de cada cuerpo'], 'Sin impulso externo neto se conserva la cantidad de movimiento del sistema.'),
    ('Física', '¿Cuál es la energía cinética de una masa de 2 kg que se mueve a 3 m/s?', '9 J', ['3 J', '6 J', '12 J', '18 J'], 'Ec = mv²/2 = 2 × 9/2 = 9 J.'),
    ('Física', 'Una onda tiene frecuencia de 5 Hz y longitud de onda de 2 m. ¿Cuál es su rapidez de propagación?', '10 m/s', ['2,5 m/s', '3 m/s', '5 m/s', '20 m/s'], 'La rapidez es v = fλ = 5 × 2 = 10 m/s.'),
    ('Física', 'Un objeto de 200 g ocupa 50 cm³. ¿Cuál es su densidad?', '4 g/cm³', ['0,25 g/cm³', '2 g/cm³', '10 g/cm³', '250 g/cm³'], 'La densidad es masa entre volumen: 200/50 = 4 g/cm³.'),
    ('Física', 'Dos resistencias de 2 Ω y 3 Ω se conectan en serie. ¿Cuál es la resistencia equivalente?', '5 Ω', ['1 Ω', '1,2 Ω', '2,5 Ω', '6 Ω'], 'En serie se suman las resistencias: 2 + 3 = 5 Ω.'),
    ('Física', 'Una máquina realiza 600 J de trabajo en 3 s. ¿Qué potencia media desarrolla?', '200 W', ['50 W', '100 W', '300 W', '1800 W'], 'La potencia media es trabajo entre tiempo: 600/3 = 200 W.'),
    ('Química', 'Un átomo neutro tiene 8 protones. ¿Cuántos electrones posee?', '8', ['4', '6', '10', '16'], 'En un átomo neutro el número de electrones es igual al de protones.'),
    ('Química', 'Dos átomos del mismo elemento tienen diferente número de neutrones. Son', 'isótopos', ['iones de signo opuesto necesariamente', 'elementos de distinto número atómico', 'moléculas idénticas', 'cationes necesariamente'], 'Los isótopos comparten número de protones y difieren en neutrones.'),
    ('Química', 'Un átomo pierde dos electrones. ¿Qué carga adquiere respecto del átomo neutro?', '+2', ['−2', '−1', '0', '+4'], 'Perder dos cargas negativas deja una carga neta de +2.'),
    ('Química', '¿Qué enlace se caracteriza por compartir pares de electrones entre átomos?', 'Covalente', ['Iónico por transferencia exclusivamente', 'Gravitacional', 'Nuclear fuerte', 'Magnético macroscópico'], 'El enlace covalente consiste en compartir pares electrónicos.'),
    ('Química', 'Si la masa molar del agua es 18 g/mol, ¿cuántos moles hay en 36 g de agua?', '2 mol', ['0,5 mol', '1 mol', '3 mol', '18 mol'], 'n = m/M = 36/18 = 2 mol.'),
    ('Química', 'Para la ecuación balanceada 2 H₂ + O₂ → 2 H₂O, ¿cuántos moles de O₂ se requieren para reaccionar completamente con 4 mol de H₂?', '2 mol', ['1 mol', '3 mol', '4 mol', '8 mol'], 'La proporción H₂:O₂ es 2:1; para 4 mol de H₂ hacen falta 2 mol de O₂.'),
    ('Química', 'A 25 °C, una disolución acuosa con pH 3 se clasifica como', 'ácida', ['neutra', 'básica', 'sin iones', 'necesariamente saturada'], 'A 25 °C, un pH inferior a 7 indica acidez.'),
    ('Química', '¿Cuál es el número atómico de un átomo que contiene 11 protones y 12 neutrones?', '11', ['12', '23', '1', '22'], 'El número atómico es el número de protones: 11.'),
    ('Biología', '¿Qué estructura realiza la síntesis de proteínas a partir de la información del ARN mensajero?', 'Ribosoma', ['Lisosoma', 'Centriolo', 'Vacuola contráctil', 'Pared celular'], 'Los ribosomas llevan a cabo la traducción del ARN mensajero.'),
    ('Biología', '¿En qué orgánulo se realiza la fotosíntesis de las células vegetales?', 'Cloroplasto', ['Mitocondria', 'Lisosoma', 'Centriolo', 'Aparato de Golgi'], 'El cloroplasto contiene los sistemas que permiten realizar la fotosíntesis.'),
    ('Biología', '¿Qué proceso produce, normalmente, dos células hijas con el mismo número de cromosomas que la célula inicial?', 'Mitosis', ['Meiosis completa', 'Fecundación', 'Traducción', 'Transcripción'], 'La mitosis conserva el número cromosómico en las células hijas.'),
    ('Biología', 'En un cruce Aa × Aa con dominancia completa, ¿qué proporción de descendientes se espera con genotipo aa?', '1/4', ['1/2', '3/4', '1', '0'], 'Las combinaciones equiprobables son AA, Aa, Aa y aa: una de cuatro es aa.'),
    ('Biología', 'En una cadena trófica, un organismo que fabrica materia orgánica a partir de sustancias inorgánicas es un', 'productor', ['consumidor primario necesariamente', 'consumidor secundario necesariamente', 'depredador exclusivamente', 'parásito exclusivamente'], 'Los productores autótrofos sintetizan materia orgánica a partir de fuentes inorgánicas.'),
    ('Biología', '¿Qué base nitrogenada aparece en el ARN y normalmente no en el ADN?', 'Uracilo', ['Timina', 'Adenina', 'Guanina', 'Citosina'], 'El ARN utiliza uracilo; el ADN utiliza timina.'),
    ('Biología', 'El movimiento neto de agua a través de una membrana selectivamente permeable por una diferencia de concentración se denomina', 'ósmosis', ['exocitosis', 'endocitosis', 'traducción', 'replicación'], 'La ósmosis describe ese movimiento neto del agua.'),
    ('Biología', '¿Qué relación describe a dos especies que obtienen beneficios de su interacción?', 'Mutualismo', ['Parasitismo', 'Depredación', 'Amensalismo', 'Competencia por definición'], 'En el mutualismo ambas especies resultan beneficiadas.'),
]

SOCIALES = [
    ('Historia del Perú', '¿Qué civilización tuvo como capital la ciudad del Cusco?', 'Inca', ['Moche', 'Nazca', 'Chimú', 'Paracas'], 'El Cusco fue la capital del Estado inca.'),
    ('Historia del Perú', '¿Qué sistema de cuerdas anudadas se utilizó en el mundo andino para registrar información?', 'Quipu', ['Papiro', 'Códice alfabético latino', 'Pergamino', 'Imprenta de tipos móviles'], 'Los quipus registraban información mediante cuerdas y nudos.'),
    ('Historia del Perú', '¿Qué cultura es conocida por los grandes geoglifos trazados en la costa sur peruana?', 'Nazca', ['Chavín', 'Chimú', 'Caral', 'Wari'], 'Las líneas y figuras de Nazca son geoglifos de la costa sur.'),
    ('Historia del Perú', '¿Quién proclamó la independencia del Perú en Lima en 1821?', 'José de San Martín', ['Simón Bolívar', 'Miguel Grau', 'Ramón Castilla', 'Francisco Bolognesi'], 'San Martín proclamó la independencia en Lima el 28 de julio de 1821.'),
    ('Historia del Perú', '¿En qué batalla de 1824 se produjo la victoria patriota decisiva que consolidó la independencia del Perú?', 'Ayacucho', ['Arica', 'Angamos', 'Tarapacá', 'San Juan'], 'La batalla de Ayacucho, en diciembre de 1824, fue decisiva para la independencia.'),
    ('Historia del Perú', 'En el sistema de reciprocidad andino, el intercambio de trabajo entre familias se conoce como', 'ayni', ['tributo monetario', 'latifundio', 'mercantilismo', 'monopolio'], 'El ayni se basa en la ayuda recíproca entre familias o integrantes de la comunidad.'),
    ('Historia Universal', '¿Qué proceso histórico se caracterizó por la mecanización de la producción y la expansión del sistema fabril?', 'Revolución Industrial', ['Neolítico exclusivamente', 'Reforma gregoriana', 'Guerra del Peloponeso', 'Caída del Imperio romano de Occidente'], 'La Revolución Industrial transformó la producción mediante máquinas y fábricas.'),
    ('Historia Universal', '¿Qué acontecimiento se asocia con el inicio de la Revolución francesa en 1789?', 'Toma de la Bastilla', ['Caída de Constantinopla', 'Congreso de Viena', 'Batalla de Waterloo', 'Inicio de la Primera Guerra Mundial'], 'La toma de la Bastilla ocurrió el 14 de julio de 1789.'),
    ('Historia Universal', '¿Qué invento de Gutenberg favoreció la difusión de libros en Europa en el siglo XV?', 'Imprenta de tipos móviles metálicos', ['Telégrafo eléctrico', 'Máquina de vapor', 'Radio', 'Motor de combustión interna'], 'La imprenta de Gutenberg permitió reproducir libros mediante tipos móviles metálicos.'),
    ('Historia Universal', '¿Qué transformación define principalmente la transición neolítica?', 'Expansión de la agricultura y la domesticación', ['Invención del ferrocarril', 'Uso masivo de electricidad', 'Nacimiento de internet', 'Industrialización fabril'], 'El Neolítico se relaciona con la agricultura, la domesticación y cambios hacia formas de vida sedentarias.'),
    ('Historia Universal', 'La expresión «Guerra Fría» alude principalmente a', 'la rivalidad entre bloques liderados por Estados Unidos y la Unión Soviética', ['una guerra exclusiva por territorios polares', 'las campañas de Alejandro Magno', 'la conquista romana de la Galia', 'las guerras médicas'], 'Fue una rivalidad política, económica y estratégica entre ambos bloques durante el siglo XX.'),
    ('Historia Universal', '¿Qué movimiento cultural europeo promovió el humanismo y retomó referentes clásicos durante los siglos XV y XVI?', 'Renacimiento', ['Romanticismo del siglo XIX', 'Positivismo del siglo XIX', 'Realismo literario del siglo XIX', 'Vanguardismo del siglo XX'], 'El Renacimiento revalorizó la cultura clásica y desarrolló el humanismo.'),
    ('Geografía', '¿Qué coordenada expresa la distancia angular de un lugar al ecuador?', 'Latitud', ['Longitud', 'Altitud', 'Pendiente', 'Profundidad'], 'La latitud se mide al norte o al sur del ecuador.'),
    ('Geografía', 'En un mapa de escala 1:50 000, ¿qué distancia real representan 2 cm?', '1 km', ['100 m', '500 m', '5 km', '10 km'], '2 × 50 000 cm = 100 000 cm = 1 km.'),
    ('Geografía', '¿Cómo se llama el conjunto de tierras cuyas aguas drenan hacia un mismo río o salida?', 'Cuenca hidrográfica', ['Meseta necesariamente', 'Istmo', 'Archipiélago', 'Duna'], 'Una cuenca reúne el territorio que aporta agua a una red de drenaje común.'),
    ('Geografía', '¿Qué proceso transforma agua líquida en vapor?', 'Evaporación', ['Condensación', 'Solidificación', 'Fusión', 'Precipitación'], 'La evaporación es el paso del estado líquido al gaseoso desde la superficie.'),
    ('Geografía', '¿Qué fenómeno natural contribuye a mantener la temperatura terrestre al absorber y reemitir radiación infrarroja?', 'Efecto invernadero', ['Rotación lunar', 'Erosión fluvial', 'Marea exclusivamente', 'Deriva continental exclusivamente'], 'Los gases de efecto invernadero absorben y reemiten parte de la radiación infrarroja.'),
    ('Geografía', '¿Qué diferencia principal existe entre tiempo atmosférico y clima?', 'El tiempo describe condiciones de corto plazo y el clima patrones de largo plazo.', ['Son siempre sinónimos exactos.', 'El clima cambia cada minuto por definición.', 'El tiempo solo describe la temperatura del océano.', 'El clima no considera precipitaciones.'], 'La distinción se basa en la escala temporal de las condiciones atmosféricas.'),
    ('Economía', '¿Qué expresa el costo de oportunidad de una decisión?', 'El valor de la mejor alternativa sacrificada', ['La suma de todos los precios históricos', 'Un gasto que siempre es cero', 'Solo el dinero ya gastado e irrecuperable', 'La cantidad total de billetes existentes'], 'Elegir implica renunciar a la mejor alternativa disponible.'),
    ('Economía', 'Si el precio de un bien aumenta y lo demás permanece constante, la ley de la demanda predice una', 'disminución de la cantidad demandada', ['expansión obligatoria de la oferta monetaria', 'subida de la cantidad demandada', 'desaparición de la escasez', 'igualdad automática entre todos los ingresos'], 'Con los demás factores constantes, precio y cantidad demandada se relacionan inversamente.'),
    ('Economía', 'Un taller vende 20 unidades a S/ 15 cada una. ¿Cuál es su ingreso total?', 'S/ 300', ['S/ 35', 'S/ 150', 'S/ 200', 'S/ 600'], 'Ingreso total = precio × cantidad = 15 × 20 = 300.'),
    ('Economía', 'Una empresa obtiene ingresos de S/ 900 y costos totales de S/ 650. ¿Cuál es su beneficio contable?', 'S/ 250', ['S/ 1550', 'S/ 650', 'S/ 900', 'S/ 150'], 'Beneficio contable = ingresos menos costos = 900 − 650 = 250.'),
    ('Economía', '¿Qué caracteriza a un costo fijo dentro de un periodo y rango de producción determinados?', 'No cambia con la cantidad producida dentro de ese rango.', ['Siempre vale cero.', 'Es idéntico al ingreso total.', 'Aumenta obligatoriamente por cada unidad.', 'Solo existe cuando se vende todo.'], 'El costo fijo permanece constante respecto de la producción en el rango considerado.'),
    ('Economía', '¿Qué concepto describe un aumento sostenido y generalizado del nivel de precios?', 'Inflación', ['Trueque', 'Deflación', 'Ahorro', 'Productividad'], 'La inflación es el aumento sostenido del nivel general de precios.'),
    ('Educación Cívica', 'En una decisión colectiva, escuchar las razones de quienes discrepan contribuye a', 'la deliberación', ['la censura previa', 'la exclusión por opinión', 'la arbitrariedad', 'la imposición sin diálogo'], 'Deliberar supone intercambiar y evaluar razones antes de decidir.'),
    ('Educación Cívica', 'Una regla se aplica con criterios públicos y las decisiones pueden justificarse. ¿Qué principio se favorece?', 'Transparencia', ['Secreto absoluto', 'Favoritismo', 'Discriminación arbitraria', 'Ausencia de rendición de cuentas'], 'Los criterios accesibles y las razones explícitas favorecen la transparencia.'),
    ('Educación Cívica', '¿Qué práctica permite resolver pacíficamente una discrepancia sin imponer amenazas?', 'Diálogo sustentado en razones', ['Intimidación', 'Difusión de rumores', 'Agresión', 'Silenciamiento forzado'], 'El diálogo permite examinar posiciones y buscar acuerdos sin violencia.'),
    ('Educación Cívica', 'Respetar la dignidad de una persona implica', 'reconocer su valor sin condicionarlo a su origen', ['atribuirle menos derechos por su idioma', 'reducirla a su ingreso económico', 'negarle voz por su apariencia', 'tratarla únicamente como instrumento'], 'La dignidad reconoce el valor de la persona sin discriminación por origen u otras condiciones.'),
    ('Educación Cívica', '¿Qué acción ejemplifica rendición de cuentas en una asociación?', 'Presentar y explicar el uso de los fondos a sus integrantes', ['Ocultar todos los comprobantes', 'Impedir preguntas sobre los gastos', 'Cambiar cifras para evitar críticas', 'Usar el fondo sin registro'], 'Rendir cuentas implica informar y justificar la gestión de los recursos.'),
    ('Educación Cívica', 'Al evaluar dos propuestas, ¿qué criterio favorece una decisión imparcial?', 'Aplicar los mismos criterios pertinentes a ambas', ['Preferir a una amistad sin revisar su propuesta', 'Cambiar los criterios según la persona', 'Ignorar la evidencia de una propuesta', 'Decidir solo por rumores'], 'La imparcialidad exige criterios consistentes y relevantes para las propuestas evaluadas.'),
]


def pregunta(curso, enunciado, respuesta, distractores, explicacion, semilla):
    """Distribuye las claves sin aleatoriedad y comprueba cinco opciones únicas."""
    opciones = list(distractores)
    posicion = semilla % 5
    opciones.insert(posicion, respuesta)
    if len(opciones) != 5 or len(set(opciones)) != 5:
        raise ValueError(f'Alternativas duplicadas: {enunciado}')
    return dict(curso=curso, seccion=curso, enunciado=enunciado,
                opciones=dict(zip('ABCDE', opciones)), correcta='ABCDE'[posicion],
                explicacion=explicacion, formato='texto', origen='Creación original para práctica')


def matematicas(area):
    """Problemas de seis cursos; cada área cambia datos, soluciones y distractores."""
    k = 'BCDE'.index(area) + 1
    banco = []

    def agregar(curso, texto, valor, explicacion, unidad=''):
        opciones = [str(valor + d) + unidad for d in (-3, -1, 1, 3)]
        banco.append(pregunta(curso, texto, str(valor) + unidad, opciones,
                              explicacion, len(banco) + k))

    for i in range(1, 11):
        n = 2 * i + k
        if i <= 3:
            agregar('H.L.M.', f'Una sucesión aumenta siempre en {n} unidades: {n}, {2*n}, {3*n}, {4*n}, ... ¿Cuál es el sexto término?', 6*n,
                    f'Es una sucesión aritmética de término general a(j) = {n}j; a(6) = {6*n}.')
        elif i <= 6:
            a, b = n, n+4
            agregar('H.L.M.', f'En una fila, Julia ocupa el lugar {a} desde el inicio y el lugar {b} desde el final. ¿Cuántas personas hay en la fila?', a+b-1,
                    f'Se suman ambas posiciones y se resta a Julia, contada dos veces: {a} + {b} − 1 = {a+b-1}.')
        elif i <= 8:
            agregar('H.L.M.', f'En una reunión de {n} personas, cada una saluda con un apretón de manos a todas las demás una sola vez. ¿Cuántos apretones se realizan?', n*(n-1)//2,
                    f'Cada pareja se cuenta una vez: {n} × {n-1}/2 = {n*(n-1)//2}.')
        else:
            agregar('H.L.M.', f'Un código consta de dos letras distintas elegidas de un alfabeto de {n} letras. Si importa el orden, ¿cuántos códigos pueden formarse?', n*(n-1),
                    f'Hay {n} posibilidades para la primera letra y {n-1} para la segunda: {n*(n-1)}.')
    for i in range(1, 9):
        n = 10 + 2*i + k
        if i % 2:
            agregar('Aritmética', f'Un artículo cuesta S/ {10*n} y recibe un descuento del 20 %. ¿Cuál es el precio final en soles?', 8*n,
                    f'Se paga el 80 % del precio: 0,8 × {10*n} = {8*n}.')
        else:
            agregar('Aritmética', f'El promedio aritmético de {n-4}, {n}, {n+4} y x es {n+2}. Halle x.', n+8,
                    f'La suma requerida es 4 × {n+2} = {4*(n+2)}; restando {3*n}, resulta x = {n+8}.')
    for i in range(1, 9):
        n = 3*i+k
        if i % 2:
            agregar('Álgebra', f'Resuelva en los reales: 3x + {n} = {4*n}.', n,
                    f'3x = {4*n} − {n} = {3*n}; por tanto x = {n}.')
        else:
            agregar('Álgebra', f'Las raíces de x² − {2*n+1}x + {n*(n+1)} = 0 son r y s. Halle r² + s².', n*n+(n+1)**2,
                    f'r + s = {2*n+1}, rs = {n*(n+1)}. Entonces r²+s² = (r+s)² − 2rs = {n*n+(n+1)**2}.')
    for i in range(1, 9):
        n = i+k+2
        if i % 2:
            agregar('Geometría', f'Un triángulo rectángulo tiene catetos de {3*n} cm y {4*n} cm. ¿Cuánto mide la hipotenusa en centímetros?', 5*n,
                    f'Por Pitágoras, c = √(({3*n})² + ({4*n})²) = {5*n} cm.')
        else:
            agregar('Geometría', f'Un rectángulo tiene base de {n+3} cm y altura de {n} cm. ¿Cuál es su área en centímetros cuadrados?', n*(n+3),
                    f'Área = base × altura = {n+3} × {n} = {n*(n+3)} cm².')
    for i in range(1, 7):
        n = i+k+2
        funcion, factor, razon, resultado = [
            ('sen', 10*n, '3/5', 6*n), ('cos', 10*n, '4/5', 8*n),
            ('tan', 4*n, '3/4', 3*n), ('cot', 3*n, '4/3', 4*n),
            ('sec', 4*n, '5/4', 5*n), ('csc', 3*n, '5/3', 5*n),
        ][i-1]
        agregar('Trigonometría', f'En un triángulo rectángulo, el cateto opuesto a θ mide {3*n} cm y el adyacente mide {4*n} cm. Si x = {factor} {funcion}(θ), halle x.', resultado,
                f'La hipotenusa mide {5*n} cm. Así, {funcion}(θ) = {razon} y x = {resultado}.')
    return banco


SITUACIONES = [
    ('Honestidad', 'Descubres un error de cálculo que favorece la nota de tu equipo.', 'Comunicar el error y pedir que se revise el cálculo.', ['Ocultarlo para conservar la nota.', 'Culpar sin pruebas a otro equipo.', 'Borrar el registro original.', 'Presionar a quien detectó el error para que calle.'], 'Reconocer el error permite una evaluación honesta y verificable.'),
    ('Empatía', 'Una compañera explica que no comprendió una indicación y teme preguntar.', 'Escucharla y ayudarla a formular su consulta con respeto.', ['Burlarse de su dificultad.', 'Excluirla del equipo.', 'Responder por ella sin escucharla.', 'Difundir su temor para entretener a otros.'], 'Escuchar y facilitar una consulta respetuosa apoya su autonomía.'),
    ('Responsabilidad', 'No podrás entregar a tiempo la parte que asumiste en un trabajo grupal.', 'Avisar con anticipación y acordar una solución realista.', ['Esperar a que venza el plazo sin avisar.', 'Inventar que ya entregaste.', 'Eliminar los mensajes del equipo.', 'Culpar a alguien ajeno al retraso.'], 'La comunicación temprana permite reorganizar el trabajo y asumir la responsabilidad.'),
    ('Trabajo en equipo', 'Dos integrantes proponen soluciones distintas y la discusión se vuelve personal.', 'Volver a los criterios del problema y comparar las razones de ambas propuestas.', ['Elegir por amistad sin revisar razones.', 'Insultar a quien discrepa.', 'Interrumpir toda participación.', 'Decidir por rumores sobre los integrantes.'], 'Centrarse en razones y criterios evita ataques personales y facilita una decisión fundamentada.'),
    ('Respeto', 'Alguien se burla del acento de una persona durante una exposición.', 'Detener la burla con respeto y respaldar el derecho de la persona a participar.', ['Sumarse a la burla.', 'Grabarla para difundirla.', 'Pedir que no vuelva a exponer.', 'Evaluar su trabajo únicamente por su acento.'], 'El respeto exige evitar la discriminación y proteger la participación.'),
    ('Autocontrol', 'Recibes una crítica que te irrita durante una revisión de tu proyecto.', 'Hacer una pausa, escuchar el contenido y responder con argumentos.', ['Responder con un ataque personal.', 'Romper los materiales.', 'Difundir información privada de quien critica.', 'Cambiar resultados para aparentar éxito.'], 'Regular la reacción permite evaluar la crítica y responder de manera constructiva.'),
    ('Integridad', 'Te ofrecen una copia de las respuestas antes de una evaluación.', 'Rechazarla y continuar con tu preparación honesta.', ['Usarla y negar que la recibiste.', 'Venderla a otros estudiantes.', 'Ocultarla para usarla durante la prueba.', 'Pedir más respuestas a cambio de un favor.'], 'Rechazar una ventaja indebida protege la integridad de la evaluación.'),
    ('Liderazgo', 'Coordinas un equipo y una integrante todavía no ha podido dar su opinión.', 'Invitarla a participar y escuchar sus aportes antes de cerrar la decisión.', ['Dar por hecho que está de acuerdo.', 'Excluirla por hablar poco.', 'Asignarle toda la culpa de un problema.', 'Impedir preguntas para terminar antes.'], 'Un liderazgo participativo crea oportunidades de intervención para todos.'),
    ('Pensamiento crítico', 'Encuentras un mensaje alarmante sin fuente sobre un asunto relacionado con tu carrera.', 'Comprobar su origen y evidencia antes de compartirlo.', ['Difundirlo porque causa impresión.', 'Cambiarle el autor para que parezca fiable.', 'Presentarlo como un hecho sin comprobarlo.', 'Inventar datos que lo respalden.'], 'La verificación evita tratar una afirmación no sustentada como un hecho.'),
    ('Vocación de servicio', 'Una persona necesita orientación sobre un procedimiento que tú no conoces bien.', 'Reconocer el límite de tu conocimiento y ayudarla a encontrar una fuente adecuada.', ['Inventar una respuesta con seguridad.', 'Culparla por no saber.', 'Dar información falsa para terminar rápido.', 'Prometer un resultado que no puedes garantizar.'], 'Ayudar responsablemente requiere reconocer límites y orientar hacia información pertinente.'),
]


def generar():
    lecturas_fuente = json.loads((RAIZ / 'data/examenes/lecturas_originales_bcde.json').read_text(encoding='utf-8'))
    salida = RAIZ / 'static/practica'
    salida.mkdir(exist_ok=True)
    # Se conservan los 19 cursos de la referencia A. Las cuotas son editoriales.
    distribuciones = {
        'B': [10,5,4,5,4, 7,3,4,4,3,3,4,4,3,5,5,7],
        'C': [10,5,5,5,5, 5,3,4,4,3,3,4,4,3,7,5,5],
        'D': [10,5,3,4,2, 7,4,5,4,3,3,4,6,4,5,5,6],
        'E': [10,3,3,3,2, 7,6,5,6,5,5,5,4,5,3,3,5],
    }
    for area, nombre in NOMBRES.items():
        preguntas, lecturas = [], []
        for competencia, situacion, respuesta, distractores, explicacion in SITUACIONES:
            q = pregunta('Actitudinales', f'En una actividad de formación del área de {nombre}, ocurre lo siguiente: {situacion} ¿Cuál es la actuación más adecuada?', respuesta, distractores, explicacion, len(preguntas))
            q['competencia'] = competencia
            preguntas.append(q)
        for i, fuente in enumerate(lecturas_fuente['areas'][area], 1):
            lectura_id = f'{area.lower()}-hv-{i}'
            ids = []
            for enunciado, opciones, correcta, explicacion in fuente['preguntas']:
                q = dict(curso='HV', seccion='Habilidad Verbal', enunciado=enunciado,
                         opciones=dict(zip('ABCDE', opciones)), correcta=correcta,
                         explicacion=explicacion, lectura_id=lectura_id,
                         formato='texto', origen=lecturas_fuente['origen'])
                preguntas.append(q)
                ids.append(len(preguntas))
            lecturas.append(dict(id=lectura_id, titulo=fuente['titulo'], preguntas=ids,
                                  idioma='es', figuras=[], bloques=[dict(parrafos=fuente['parrafos'])]))
        academicas = matematicas(area)
        for fila in CIENCIAS + HUMANIDADES + SOCIALES:
            academicas.append(pregunta(*fila, semilla=len(academicas) + ord(area)))
        for curso, cantidad in zip(ORDEN, distribuciones[area]):
            disponibles = [q for q in academicas if q['curso'] == curso]
            if len(disponibles) < cantidad:
                raise ValueError(f'Área {area}, {curso}: faltan preguntas')
            preguntas.extend(disponibles[:cantidad])
        # Agrupar materias conservando el bloque 1–10 / 11–20.
        preguntas = preguntas[:20] + sorted(preguntas[20:], key=lambda q: ORDEN.index(q['curso']))
        grupos = []
        for numero, q in enumerate(preguntas, 1):
            q['id'] = numero
            grupo = next((g for g in grupos if g['nombre'] == q['curso']), None)
            if grupo is None:
                grupo = dict(nombre=q['curso'], preguntas=[])
                if q['curso'] == 'HV':
                    grupo.update(nombre_completo='Habilidad Verbal', lecturas=[l['id'] for l in lecturas])
                grupos.append(grupo)
            grupo['preguntas'].append(numero)
        # Dos apoyos geométricos, construidos a partir de los mismos datos.
        for q in preguntas:
            if q['curso'] == 'Geometría':
                q['figura'] = 'rectangulo' if 'rectángulo tiene' in q['enunciado'] else 'triangulo'
        if len(preguntas) != 100:
            raise ValueError(f'Área {area}: {len(preguntas)} preguntas')
        privado = dict(area=area, titulo=nombre, version='practica-original-1',
                       origen='Material original de práctica, sin atribución oficial ni validación psicométrica.',
                       distribucion='Distribución editorial de práctica; no representa cuotas oficiales de admisión.',
                       preguntas=preguntas, lecturas=lecturas, grupos=grupos)
        ruta = RAIZ / f'data/examenes/area_{area.lower()}_practica.json'
        ruta.write_text(json.dumps(privado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        publico = dict(privado, preguntas=[{k:v for k,v in q.items() if k not in ('correcta', 'explicacion')} for q in preguntas])
        (salida / f'area_{area.lower()}.json').write_text(json.dumps(publico, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Área {area}: 100 preguntas, 3 lecturas, {sum(bool(q.get("figura")) for q in preguntas)} figuras de geometría; claves privadas.')


ORDEN = ['H.L.M.', 'Aritmética', 'Geometría', 'Álgebra', 'Trigonometría',
         'Lenguaje', 'Literatura', 'Psicología', 'Educación Cívica',
         'Historia del Perú', 'Historia Universal', 'Geografía', 'Economía',
         'Filosofía', 'Física', 'Química', 'Biología']


if __name__ == '__main__':
    generar()
