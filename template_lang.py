# -*- coding: utf-8 -*-
"""Строки шаблона исходных данных на трёх языках.

Ключ - русская строка, значение - перевод. Отсутствующий перевод
означает, что строка выводится по-русски: расчёт от этого не
страдает. Чтобы добавить язык, впишите его код в LANG_SUFFIX и
добавьте ключ в каждую запись.
"""

_LANG = "ru"
LANG_SUFFIX = {"ru": "_RU", "en": "_EN", "fr": "_FR"}


def set_lang(code):
    global _LANG
    _LANG = code if code in LANG_SUFFIX else "ru"


def T(s):
    """Строка шаблона на текущем языке."""
    if not isinstance(s, str) or _LANG == "ru":
        return s
    row = STR.get(" ".join(s.split()))
    if not row:
        return s
    return row.get(_LANG, s)


STR = {
    "00 Инструкция":
        {"en": "00 Instructions",
         "fr": "00 Instructions"},
    'Направление':
        {"en": 'Conductor pipe',
         "fr": 'Tube guide'},
    'Кондуктор 1':
        {"en": 'Surface casing 1',
         "fr": 'Tubage de surface 1'},
    'Кондуктор 2':
        {"en": 'Surface casing 2',
         "fr": 'Tubage de surface 2'},
    'Экс.колонна 1':
        {"en": 'Production casing 1',
         "fr": 'Tubage de production 1'},
    'Экс.колонна 2':
        {"en": 'Production casing 2',
         "fr": 'Tubage de production 2'},
    'Экс.колонна 3':
        {"en": 'Production casing 3',
         "fr": 'Tubage de production 3'},
    'Хвостовик':
        {"en": 'Liner',
         "fr": 'Liner'},
    'Исходные данные для гидравлического расчёта промывки скважины':
        {"en": 'Input data for drilling hydraulics calculation',
         "fr": "Donnees d'entree pour le calcul hydraulique de forage"},
    'by AR · НьюТек Сервисез':
        {"en": 'by AR',
         "fr": 'by AR'},
    'КАК ЗАПОЛНЯТЬ':
        {"en": 'HOW TO FILL IN',
         "fr": 'COMMENT REMPLIR'},
    'Листы пронумерованы в том порядке, в котором их удобно заполнять. Идите сверху вниз.':
        {"en": 'Sheets are numbered in the order they are best filled in. Work from top to bottom.',
         "fr": "Les feuilles sont numerotees dans l'ordre de remplissage. Procedez de haut en bas."},
    'Заполняются только ячейки со светло-жёлтой заливкой. Серые шапки и первый столбец не трогайте.':
        {"en": 'Fill in the light yellow cells only. Do not change the grey headers or the first column.',
         "fr": 'Ne remplissez que les cellules jaune clair. Ne modifiez ni les en-tetes gris ni la premiere colonne.'},
    'Если данных нет - напишите н/д . Программа возьмёт значение из своей конфигурации и отметит это в расчёте. Пустая ячейка равнозначна «н/д».':
        {"en": 'If a value is not available, write n/a . The program will take it from its own configuration and mark the value as assumed in the calculation. An empty cell means the same.',
         "fr": 'Si une valeur est inconnue, ecrivez n/a . Le programme prendra la valeur de sa configuration et la signalera comme supposee. Une cellule vide a le meme effet.'},
    'Строка «ПРИМЕР →» внизу каждой таблицы показывает формат. Её можно удалить или оставить - программа её игнорирует.':
        {"en": 'The EXAMPLE row at the bottom of each table shows the format. You may delete it or leave it - the program ignores it.',
         "fr": "La ligne EXEMPLE au bas de chaque tableau montre le format. Vous pouvez la supprimer ou la laisser: le programme l'ignore."},
    'Названия интервалов в первом столбце менять НЕЛЬЗЯ: по ним связываются данные всех листов. Если интервалов больше или меньше - правьте лист «05 Интервалы бурения», остальные листы подстроятся.':
        {"en": 'Interval names in the first column MUST NOT be changed: they link the data across all sheets. If the number of intervals differs, edit the sheet "05 Intervals" and the others will follow.',
         "fr": 'Les noms d\'intervalles de la premiere colonne NE DOIVENT PAS etre modifies: ils relient les donnees de toutes les feuilles. Si le nombre d\'intervalles change, modifiez la feuille "05 Intervalles".'},
    'Каждая величина вводится ровно один раз. Если кажется, что данные повторяются на разных листах - перепроверьте, скорее всего это разные величины.':
        {"en": 'Each value is entered exactly once. If data seem to repeat across sheets, check again - these are most likely different quantities.',
         "fr": "Chaque valeur n'est saisie qu'une fois. Si des donnees semblent se repeter, verifiez: il s'agit sans doute de grandeurs differentes."},
    'Числа пишите с точкой или запятой - оба варианта понимаются. Диапазон вида 50-55 тоже допустим, программа возьмёт нужный край.':
        {"en": 'Numbers may use a dot or a comma. A range such as 50-55 is also accepted; which end is used is set in the configuration.',
         "fr": 'Les nombres acceptent le point ou la virgule. Une plage comme 50-55 est admise; le choix de la borne est defini dans la configuration.'},
    'На листах «08 ВЗД» и «09 Телесистема» слово нет означает «оборудование не применяется, перепад давления равен нулю».':
        {"en": 'On the sheets "08 Mud motor" and "09 MWD" the word no means "equipment not used, pressure drop is zero".',
         "fr": 'Sur les feuilles "08 Moteur de fond" et "09 MWD", le mot non signifie "equipement non utilise, perte de charge nulle".'},
    'Слово н/д на тех же листах означает «данных пока нет» - будет взято значение из конфигурации. Это разные вещи.':
        {"en": 'The entry n/a on the same sheets means "data not yet available" - the configuration value will be used. These are different things.',
         "fr": 'La mention n/a sur ces memes feuilles signifie "donnee non encore disponible" - la valeur de configuration sera utilisee. Ce sont deux choses differentes.'},
    'Лист':
        {"en": 'Sheet',
         "fr": 'Feuille'},
    'Что содержит':
        {"en": 'Contents',
         "fr": 'Contenu'},
    'Приоритет':
        {"en": 'Priority',
         "fr": 'Priorite'},
    '01 Общие сведения':
        {"en": '01 General',
         "fr": '01 Informations generales'},
    'заказчик, месторождение, куст, скважина, подрядчик, исполнитель':
        {"en": 'client, field, pad, well, contractor, author',
         "fr": 'client, gisement, plateforme, puits, entreprise, auteur'},
    'обязательно':
        {"en": 'required',
         "fr": 'obligatoire'},
    '02 Конструкция':
        {"en": '02 Casing',
         "fr": '02 Tubages'},
    'обсадные колонны: диаметр, стенка, глубина спуска':
        {"en": 'casing strings: diameter, wall thickness, setting depth',
         "fr": 'colonnes de tubage: diametre, epaisseur, profondeur de descente'},
    '03 Инклинометрия':
        {"en": '03 Survey',
         "fr": '03 Deviation'},
    'MD / зенитный угол / азимут по стволу':
        {"en": 'MD / inclination / azimuth along the hole',
         "fr": 'MD / inclinaison / azimut le long du puits'},
    '04 Разрез и давления':
        {"en": '04 Geology and pressures',
         "fr": '04 Geologie et pressions'},
    'свиты, литология, плотность породы, поровое давление и давление ГРП':
        {"en": 'formations, lithology, rock density, pore and fracture pressure',
         "fr": 'formations, lithologie, densite de roche, pressions de pore et de fracturation'},
    'важно':
        {"en": 'important',
         "fr": 'important'},
    '05 Интервалы бурения':
        {"en": '05 Intervals',
         "fr": '05 Intervalles'},
    'разбивка на интервалы, диаметр долота, МСП, расход, кавернозность':
        {"en": 'interval split, bit size, ROP, flow rate, washout factor',
         "fr": "decoupage, diametre d'outil, VOP, debit, facteur de cavage"},
    '06 Буровой раствор':
        {"en": '06 Drilling fluid',
         "fr": '06 Boue de forage'},
    'плотность, показания Фанна, СНС, температура':
        {"en": 'density, Fann readings, gel strength, temperature',
         "fr": 'densite, lectures Fann, gel, temperature'},
    '07 Насадки долот':
        {"en": '07 Bit nozzles',
         "fr": '07 Duses'},
    'диаметры насадок или TFA':
        {"en": 'nozzle sizes or TFA',
         "fr": 'diametres de duses ou TFA'},
    '08 ВЗД':
        {"en": '08 Mud motor',
         "fr": '08 Moteur de fond'},
    'типоразмер, расход, перепады давления':
        {"en": 'size, flow rate, pressure drops',
         "fr": 'taille, debit, pertes de charge'},
    '09 Телесистема':
        {"en": '09 MWD',
         "fr": '09 MWD'},
    'тип, перепад давления':
        {"en": 'type, pressure drop',
         "fr": 'type, perte de charge'},
    '10 КНБК':
        {"en": '10 BHA',
         "fr": '10 Garniture de fond'},
    'все компоновки в одной таблице, снизу вверх от долота':
        {"en": 'all assemblies in one table, from the bit upwards',
         "fr": "toutes les garnitures dans un tableau, de l'outil vers le haut"},
    '11 Бурильная колонна':
        {"en": '11 Drill string',
         "fr": '11 Garniture de forage'},
    'трубы выше КНБК по интервалам':
        {"en": 'pipe above the BHA for each interval',
         "fr": 'tiges au-dessus de la garniture de fond, par intervalle'},
    '12 Буровые насосы':
        {"en": '12 Mud pumps',
         "fr": '12 Pompes a boue'},
    'тип, втулки, ход, предельное давление':
        {"en": 'type, liners, stroke, pressure limit',
         "fr": 'type, chemises, course, pression limite'},
    '13 Наземная обвязка':
        {"en": '13 Surface equipment',
         "fr": '13 Equipement de surface'},
    'стояк, рукав, вертлюг, ведущая труба':
        {"en": 'standpipe, hose, swivel, kelly',
         "fr": "colonne montante, flexible, tete d'injection, tige carree"},
    '14 Шлам':
        {"en": '14 Cuttings',
         "fr": '14 Deblais'},
    'размер частиц, критерии очистки ствола':
        {"en": 'particle size, hole cleaning criteria',
         "fr": 'taille des particules, criteres de nettoyage'},
    'желательно':
        {"en": 'optional',
         "fr": 'souhaitable'},
    '15 Температура':
        {"en": '15 Temperature',
         "fr": '15 Temperature'},
    'температурный режим по стволу':
        {"en": 'temperature profile along the hole',
         "fr": 'profil de temperature le long du puits'},
    'ОБЩИЕ СВЕДЕНИЯ':
        {"en": 'GENERAL INFORMATION',
         "fr": 'INFORMATIONS GENERALES'},
    'Выводятся на титульном листе отчёта, в колонтитулах каждой страницы и в свойствах PDF-файла.':
        {"en": 'Shown on the report cover page, in the footer of every page and in the PDF file properties.',
         "fr": 'Affichees sur la page de garde du rapport, dans le pied de page de chaque page et dans les proprietes du PDF.'},
    'Показатель':
        {"en": 'Item',
         "fr": 'Rubrique'},
    'Значение':
        {"en": 'Value',
         "fr": 'Valeur'},
    'Пояснение':
        {"en": 'Comment',
         "fr": 'Commentaire'},
    'Заказчик':
        {"en": 'Client',
         "fr": 'Client'},
    'Месторождение':
        {"en": 'Field',
         "fr": 'Gisement'},
    'Площадь':
        {"en": 'Licence area',
         "fr": 'Permis'},
    'Куст':
        {"en": 'Pad',
         "fr": 'Plateforme'},
    'Скважина':
        {"en": 'Well',
         "fr": 'Puits'},
    'Тип скважины':
        {"en": 'Well type',
         "fr": 'Type de puits'},
    'Проектный горизонт':
        {"en": 'Target formation',
         "fr": 'Horizon objectif'},
    'Проектная глубина, м MD':
        {"en": 'Total depth, m MD',
         "fr": 'Profondeur finale, m MD'},
    'Буровой подрядчик':
        {"en": 'Drilling contractor',
         "fr": 'Entreprise de forage'},
    'Буровая установка':
        {"en": 'Rig',
         "fr": 'Appareil de forage'},
    'Ответственный исполнитель':
        {"en": 'Prepared by',
         "fr": 'Etabli par'},
    'Дата расчёта':
        {"en": 'Date',
         "fr": 'Date'},
    'Номер документа':
        {"en": 'Document number',
         "fr": 'Numero du document'},
    'Примечание':
        {"en": 'Note',
         "fr": 'Remarque'},
    'КОНСТРУКЦИЯ СКВАЖИНЫ':
        {"en": 'CASING DESIGN',
         "fr": 'ARCHITECTURE DE TUBAGE'},
    'Обсадные колонны сверху вниз. Внутренний диаметр программа считает сама из наружного и толщины стенки. Если низ ствола остаётся необсаженным, добавьте строку «Открытый ствол»: укажите диаметр и глубину, толщину стенки оставьте пустой.':
        {"en": 'Casing strings from top to bottom. The program derives the inside diameter from the outside diameter and the wall thickness. If the lower hole section is left uncased, add a row "Open hole": give the diameter and depth and leave the wall thickness empty.',
         "fr": 'Colonnes de tubage de haut en bas. Le programme calcule le diametre interieur a partir du diametre exterieur et de l\'epaisseur. Si le bas du puits reste en trou ouvert, ajoutez une ligne "Trou ouvert": indiquez le diametre et la profondeur et laissez l\'epaisseur vide.'},
    'Колонна':
        {"en": 'Casing',
         "fr": 'Tubage'},
    'Ø наружный, мм':
        {"en": 'OD, mm',
         "fr": 'Ø exterieur, mm'},
    'Толщина стенки, мм':
        {"en": 'Wall thickness, mm',
         "fr": 'Epaisseur, mm'},
    'Глубина спуска, м MD':
        {"en": 'Setting depth, m MD',
         "fr": 'Profondeur, m MD'},
    'Глубина спуска, м TVD':
        {"en": 'Setting depth, m TVD',
         "fr": 'Profondeur, m TVD'},
    'Глубина подвески, м MD':
        {"en": 'Hanger depth, m MD',
         "fr": 'Suspension, m MD'},
    'Кондуктор':
        {"en": 'Surface casing',
         "fr": 'Tubage de surface'},
    'Промежуточная колонна':
        {"en": 'Intermediate casing',
         "fr": 'Tubage intermediaire'},
    'Эксплуатационная колонна':
        {"en": 'Production casing',
         "fr": 'Tubage de production'},
    'Открытый ствол':
        {"en": 'Open hole',
         "fr": 'Trou ouvert'},
    'Заполняется только для хвостовика. Для колонн от устья оставьте пусто.':
        {"en": 'For the liner only. Leave empty for strings run from surface.',
         "fr": 'Pour le liner uniquement. Laissez vide pour les colonnes depuis la surface.'},
    'спуск до кровли солей':
        {"en": 'set on top of the salt',
         "fr": 'descendu au toit des sels'},
    'ПРИМЕР →':
        {"en": 'EXAMPLE →',
         "fr": 'EXEMPLE →'},
    'ИНКЛИНОМЕТРИЯ':
        {"en": 'DIRECTIONAL SURVEY',
         "fr": 'RELEVE DE DEVIATION'},
    'Единственный источник данных о траектории. Шаг 10-30 м. TVD можно не заполнять - программа посчитает по зенитным углам. Строки добавляйте вниз без ограничений.':
        {"en": 'The only source of trajectory data. Station spacing 10-30 m. TVD may be left empty - the program computes it from the inclination. Add rows below without limit.',
         "fr": "Seule source des donnees de trajectoire. Pas de 10 a 30 m. Le TVD peut rester vide: le programme le calcule a partir de l'inclinaison. Ajoutez des lignes sans limite."},
    'MD, м':
        {"en": 'MD, m',
         "fr": 'MD, m'},
    'Зенитный угол, град':
        {"en": 'Inclination, deg',
         "fr": 'Inclinaison, deg'},
    'Азимут, град':
        {"en": 'Azimuth, deg',
         "fr": 'Azimut, deg'},
    'TVD, м (если известна)':
        {"en": 'TVD, m (if known)',
         "fr": 'TVD, m (si connu)'},
    'Угол отклонения от вертикали. 0° - вертикаль, 90° - горизонталь.':
        {"en": 'Angle from vertical. 0° is vertical, 90° is horizontal.',
         "fr": 'Angle par rapport a la verticale. 0° vertical, 90° horizontal.'},
    'ЛИТОЛОГИЧЕСКИЙ РАЗРЕЗ И ПЛАСТОВЫЕ ДАВЛЕНИЯ':
        {"en": 'LITHOLOGY AND FORMATION PRESSURES',
         "fr": 'LITHOLOGIE ET PRESSIONS DE FORMATION'},
    'Стратиграфия и давления в одной таблице - по каждой пачке. Давления задаются эквивалентной плотностью в г/см³. Без них программа не проверит, вписывается ли ЭЦП в «окно бурения».':
        {"en": 'Stratigraphy and pressures in one table, formation by formation. Pressures are given as equivalent density in g/cm³. Without them the program cannot check the ECD against the drilling window.',
         "fr": 'Stratigraphie et pressions dans un seul tableau, par formation. Les pressions sont exprimees en densite equivalente, g/cm³. Sans elles le programme ne peut verifier la DEC dans la fenetre de forage.'},
    'Свита / горизонт':
        {"en": 'Formation',
         "fr": 'Formation'},
    'От, м MD':
        {"en": 'From, m MD',
         "fr": 'De, m MD'},
    'До, м MD':
        {"en": 'To, m MD',
         "fr": 'A, m MD'},
    'Литология':
        {"en": 'Lithology',
         "fr": 'Lithologie'},
    'Плотность породы, г/см³':
        {"en": 'Rock density, g/cm³',
         "fr": 'Densite de roche, g/cm³'},
    'Поровое давление, г/см³':
        {"en": 'Pore pressure, g/cm³',
         "fr": 'Pression de pore, g/cm³'},
    'Давление ГРП, г/см³':
        {"en": 'Fracture pressure, g/cm³',
         "fr": 'Pression de fracturation, g/cm³'},
    'Начало поглощения, г/см³':
        {"en": 'Loss onset, g/cm³',
         "fr": 'Debut de pertes, g/cm³'},
    'Нужна для расчёта выноса шлама и вклада шлама в ЭЦП.':
        {"en": 'Needed for cuttings transport and the cuttings contribution to ECD.',
         "fr": 'Necessaire au transport des deblais et a leur contribution a la DEC.'},
    'Эквивалентная плотность давления гидроразрыва пласта.':
        {"en": 'Equivalent density of the formation fracture pressure.',
         "fr": 'Densite equivalente de la pression de fracturation.'},
    'долериты (траппы)':
        {"en": 'dolerite (traps)',
         "fr": 'dolerite (trapps)'},
    'зона поглощений':
        {"en": 'loss zone',
         "fr": 'zone de pertes'},
    'ИНТЕРВАЛЫ БУРЕНИЯ':
        {"en": 'DRILLING INTERVALS',
         "fr": 'INTERVALLES DE FORAGE'},
    'Главный лист: задаёт разбивку расчёта. Названия из первого столбца используются на всех остальных листах - если меняете их здесь, поменяйте и там. Один интервал = одна КНБК и один режим промывки.':
        {"en": 'The master sheet: it defines how the calculation is split. The names in the first column are used on every other sheet - if you change them here, change them there as well. One interval means one BHA and one circulation regime.',
         "fr": 'Feuille principale: elle definit le decoupage du calcul. Les noms de la premiere colonne sont utilises sur toutes les autres feuilles: si vous les modifiez ici, modifiez-les aussi ailleurs. Un intervalle correspond a une garniture et un regime.'},
    'Интервал':
        {"en": 'Interval',
         "fr": 'Intervalle'},
    'Ø долота, мм':
        {"en": 'Bit diameter, mm',
         "fr": "Diametre d'outil, mm"},
    'Тип долота':
        {"en": 'Bit type',
         "fr": "Type d'outil"},
    'Способ бурения':
        {"en": 'Drive',
         "fr": 'Entrainement'},
    'Расход, л/с':
        {"en": 'Flow rate, L/s',
         "fr": 'Debit, L/s'},
    'МСП, м/ч':
        {"en": 'ROP, m/h',
         "fr": 'VOP, m/h'},
    'Коэф. кавернозности':
        {"en": 'Washout factor',
         "fr": 'Facteur de cavage'},
    'Обороты колонны, об/мин':
        {"en": 'String rotation, rpm',
         "fr": 'Rotation garniture, tr/min'},
    'ротор / ротор+ВЗД / ВЗД / РУС':
        {"en": 'rotary / rotary+motor / motor / RSS',
         "fr": 'rotary / rotary+moteur / moteur / RSS'},
    'Можно диапазон: 50-55. Какой край брать - задаётся в конфигурации.':
        {"en": 'A range is allowed: 50-55. Which end is used is set in the configuration.',
         "fr": 'Une plage est admise: 50-55. Le choix de la borne est defini dans la configuration.'},
    'Увеличение ДИАМЕТРА открытого ствола. Типично 1,03…1,25. Влияет на скорость в затрубье и ЭЦП.':
        {"en": 'Increase of the open hole DIAMETER. Typically 1.03 to 1.25. Affects annular velocity and ECD.',
         "fr": 'Augmentation du DIAMETRE du trou ouvert. Typiquement 1,03 a 1,25. Influe sur la vitesse annulaire et la DEC.'},
    'Обороты ротора или верхнего привода. 0 или пусто - бурение скольжением на ВЗД без вращения колонны.':
        {"en": 'Rotary table or top drive speed. 0 or empty means sliding on the motor without string rotation.',
         "fr": 'Vitesse de la table ou du top drive. 0 ou vide signifie glissement sur moteur sans rotation.'},
    'ротор+ВЗД':
        {"en": 'rotary+motor',
         "fr": 'rotary+moteur'},
    'ПАРАМЕТРЫ БУРОВОГО РАСТВОРА':
        {"en": 'DRILLING FLUID PROPERTIES',
         "fr": 'PROPRIETES DE LA BOUE'},
    'Показания вискозиметра Фанна в фунт/100 фут². Если вискозиметра нет, заполните только плотность, ПВ и ДНС и выберите модель Бингама. Столбец «Модель реологии» можно оставить пустым: программа выберет модель по тому, какие данные заполнены.':
        {"en": 'Fann viscometer readings in lb/100 ft². If no viscometer data are available, fill in density, PV and YP only and choose the Bingham model. The "Rheology model" column may be left empty: the model is then chosen from the data provided.',
         "fr": 'Lectures du viscosimetre Fann en lb/100 pi². A defaut de viscosimetre, remplissez seulement la densite, VP et YP et choisissez le modele de Bingham. La colonne "Modele rheologique" peut rester vide: le modele est alors deduit des donnees.'},
    'Тип раствора':
        {"en": 'Fluid type',
         "fr": 'Type de boue'},
    'Плотность, г/см³':
        {"en": 'Density, g/cm³',
         "fr": 'Densite, g/cm³'},
    'СНС 10 с':
        {"en": 'Gel 10 s',
         "fr": 'Gel 10 s'},
    'СНС 10 мин':
        {"en": 'Gel 10 min',
         "fr": 'Gel 10 min'},
    'Температура замера, °C':
        {"en": 'Test temperature, °C',
         "fr": "Temperature d'essai, °C"},
    'Водоотдача, см³/30 мин':
        {"en": 'Fluid loss, cm³/30 min',
         "fr": 'Filtrat, cm³/30 min'},
    'ПВ, сПз':
        {"en": 'PV, cP',
         "fr": 'VP, cP'},
    'ДНС, фунт/100 фут²':
        {"en": 'YP, lb/100 ft²',
         "fr": 'YP, lb/100 pi²'},
    'Модель реологии':
        {"en": 'Rheology model',
         "fr": 'Modele rheologique'},
    'Показание при 600 об/мин, фунт/100 фут².':
        {"en": 'Reading at 600 rpm, lb/100 ft².',
         "fr": 'Lecture a 600 tr/min, lb/100 pi².'},
    'Показание при 3 об/мин. Определяет несущую способность в затрубье.':
        {"en": 'Reading at 3 rpm. Governs the carrying capacity in the annulus.',
         "fr": 'Lecture a 3 tr/min. Determine la capacite de transport en annulaire.'},
    'Пластическая вязкость. Заполняется, если показаний вискозиметра нет.':
        {"en": 'Plastic viscosity. Fill in if no viscometer readings are available.',
         "fr": "Viscosite plastique. A remplir en l'absence de lectures du viscosimetre."},
    'Гершеля-Балкли / степенная / Бингама. Пусто или «авто» - выбор по данным: есть θ6 и θ3 - Гершеля-Балкли, есть θ600 и θ300 - степенная, только ПВ и ДНС - Бингама.':
        {"en": 'Herschel-Bulkley / power law / Bingham. Empty or "auto" means the model is chosen from the data: theta6 and theta3 present - Herschel-Bulkley; only theta600 and theta300 - power law; only PV and YP - Bingham.',
         "fr": 'Herschel-Bulkley / loi de puissance / Bingham. Vide ou "auto": le modele est deduit des donnees - theta6 et theta3 presents: Herschel-Bulkley; seulement theta600 et theta300: loi de puissance; seulement VP et YP: Bingham.'},
    'полимерглинистый':
        {"en": 'polymer-bentonite',
         "fr": 'polymere-bentonite'},
    'Гершеля-Балкли':
        {"en": 'Herschel-Bulkley',
         "fr": 'Herschel-Bulkley'},
    'НАСАДКИ ДОЛОТ':
        {"en": 'BIT NOZZLES',
         "fr": "DUSES DE L'OUTIL"},
    'Диаметры насадок в 1/32 дюйма (Н1…Н8). Лишние ячейки оставьте пустыми. TFA считается формулой. Если известна только TFA - впишите её вручную в последний столбец вместо формулы.':
        {"en": 'Nozzle diameters in 1/32 inch (N1 to N8). Leave unused cells empty. TFA is calculated by a formula. If only the TFA is known, type it into the last column instead of the formula.',
         "fr": 'Diametres des duses en 1/32 de pouce (N1 a N8). Laissez vides les cellules inutilisees. La TFA est calculee par formule. Si seule la TFA est connue, saisissez-la dans la derniere colonne.'},
    'Н1':
        {"en": 'N1',
         "fr": 'N1'},
    'Н2':
        {"en": 'N2',
         "fr": 'N2'},
    'Н3':
        {"en": 'N3',
         "fr": 'N3'},
    'Н4':
        {"en": 'N4',
         "fr": 'N4'},
    'Н5':
        {"en": 'N5',
         "fr": 'N5'},
    'Н6':
        {"en": 'N6',
         "fr": 'N6'},
    'Н7':
        {"en": 'N7',
         "fr": 'N7'},
    'Н8':
        {"en": 'N8',
         "fr": 'N8'},
    'TFA, дюйм²':
        {"en": 'TFA, in²',
         "fr": 'TFA, po²'},
    'Диаметр в 1/32 дюйма. 16 = 16/32" = 12,7 мм.':
        {"en": 'Diameter in 1/32 inch. 16 = 16/32" = 12.7 mm.',
         "fr": 'Diametre en 1/32 de pouce. 16 = 16/32" = 12,7 mm.'},
    'Суммарная площадь промывочных отверстий.':
        {"en": 'Total flow area of the nozzles.',
         "fr": "Surface totale d'ecoulement des duses."},
    '6 насадок 16/32"':
        {"en": 'six 16/32" nozzles',
         "fr": 'six duses 16/32"'},
    'ЗАБОЙНЫЕ ДВИГАТЕЛИ':
        {"en": 'DOWNHOLE MOTORS',
         "fr": 'MOTEURS DE FOND'},
    'Если на интервале двигатель не применяется - напишите нет . Если паспорт пока не найден - напишите н/д .':
        {"en": 'If no motor is run on the interval, write no . If the data sheet is not available yet, write n/a .',
         "fr": "Si aucun moteur n'est utilise, ecrivez non . Si la fiche technique manque encore, ecrivez n/a ."},
    'Типоразмер':
        {"en": 'Size',
         "fr": 'Taille'},
    'Ø проходной, мм':
        {"en": 'Bore diameter, mm',
         "fr": 'Diametre de passage, mm'},
    'Расход min, л/с':
        {"en": 'Flow min, L/s',
         "fr": 'Debit min, L/s'},
    'Расход max, л/с':
        {"en": 'Flow max, L/s',
         "fr": 'Debit max, L/s'},
    'Перепад х.х., атм':
        {"en": 'Off-bottom ΔP, atm',
         "fr": 'ΔP hors fond, atm'},
    'Перепад под нагрузкой, атм':
        {"en": 'ΔP on load, atm',
         "fr": 'ΔP en charge, atm'},
    'Момент, кН·м':
        {"en": 'Torque, kN·m',
         "fr": 'Couple, kN·m'},
    'Обороты, об/мин':
        {"en": 'Speed, rpm',
         "fr": 'Vitesse, tr/min'},
    'Угол перекоса, град':
        {"en": 'Bend angle, deg',
         "fr": 'Angle de coude, deg'},
    'Перепад давления при циркуляции без нагрузки на долото, при расходе max.':
        {"en": 'Pressure drop when circulating off bottom, at the maximum flow rate.',
         "fr": 'Perte de charge en circulation hors fond, au debit max.'},
    'Дополнительный перепад при рабочем моменте.':
        {"en": 'Additional pressure drop at working torque.',
         "fr": 'Perte de charge supplementaire au couple de travail.'},
    'ТЕЛЕСИСТЕМА (MWD / LWD)':
        {"en": 'MWD / LWD',
         "fr": 'MWD / LWD'},
    'Перепад давления указывается при том расходе, который стоит в соседнем столбце. Если телесистема не применяется - напишите нет .':
        {"en": 'The pressure drop is given at the flow rate in the adjacent column. If no MWD is run, write no .',
         "fr": 'La perte de charge est donnee au debit indique dans la colonne voisine. Sans MWD, ecrivez non .'},
    'Тип / модель':
        {"en": 'Type / model',
         "fr": 'Type / modele'},
    'Ø внутренний, мм':
        {"en": 'ID, mm',
         "fr": 'Ø interieur, mm'},
    'Перепад давления, атм':
        {"en": 'Pressure drop, atm',
         "fr": 'Perte de charge, atm'},
    'Канал связи':
        {"en": 'Telemetry channel',
         "fr": 'Canal de telemesure'},
    'гидравлический':
        {"en": 'mud pulse',
         "fr": 'impulsion de boue'},
    'КОМПОНОВКИ НИЗА БУРИЛЬНОЙ КОЛОННЫ':
        {"en": 'BOTTOM HOLE ASSEMBLIES',
         "fr": 'GARNITURES DE FOND'},
    'Все компоновки в одной таблице. Для каждого интервала элементы перечисляются СНИЗУ ВВЕРХ: первая строка - долото, дальше вверх к устью. Название интервала пишется только в первой строке компоновки, ниже можно не повторять. Между компоновками оставьте пустую строку.':
        {"en": 'All assemblies in one table. For each interval the components are listed FROM THE BIT UPWARDS: the first row is the bit, then upwards towards surface. The interval name is written in the first row of the assembly only. Leave an empty row between assemblies.',
         "fr": "Toutes les garnitures dans un seul tableau. Pour chaque intervalle, les elements sont listes DE L'OUTIL VERS LE HAUT: la premiere ligne est l'outil. Le nom de l'intervalle n'est ecrit que sur la premiere ligne. Laissez une ligne vide entre les garnitures."},
    'Наименование элемента':
        {"en": 'Component',
         "fr": 'Element'},
    'Длина, м':
        {"en": 'Length, m',
         "fr": 'Longueur, m'},
    'Для долота и ВЗД можно не заполнять: они считаются по своим моделям.':
        {"en": 'May be left empty for the bit and the motor: they are handled by their own models.',
         "fr": "Peut rester vide pour l'outil et le moteur: ils ont leurs propres modeles."},
    'Длина без ниппеля.':
        {"en": 'Length excluding the pin.',
         "fr": 'Longueur hors filetage male.'},
    'Долото':
        {"en": 'Bit',
         "fr": 'Outil'},
    'Переводник':
        {"en": 'Crossover sub',
         "fr": 'Raccord'},
    'Калибратор':
        {"en": 'Stabiliser',
         "fr": 'Stabilisateur'},
    'УБТС':
        {"en": 'Drill collar',
         "fr": 'Masse-tige'},
    '↑ пример: так заполняется одна компоновка, дальше пустая строка и следующий интервал':
        {"en": 'example: this is how one assembly is filled in, then an empty row and the next interval',
         "fr": "exemple: voici comment saisir une garniture, puis une ligne vide et l'intervalle suivant"},
    'БУРИЛЬНАЯ КОЛОННА ВЫШЕ КНБК':
        {"en": 'DRILL STRING ABOVE THE BHA',
         "fr": 'GARNITURE AU-DESSUS DE LA GARNITURE DE FOND'},
    'Чем добирается колонна от верха КНБК до устья. Длину указывать не нужно - программа добьёт колонну до устья сама.':
        {"en": 'What makes up the string from the top of the BHA to surface. The length need not be given - the program fills the string to surface itself.',
         "fr": "Ce qui compose la garniture du haut de la garniture de fond jusqu'a la surface. La longueur est facultative: le programme complete jusqu'a la surface."},
    'Наименование':
        {"en": 'Description',
         "fr": 'Designation'},
    'Ø наружный трубы, мм':
        {"en": 'Pipe OD, mm',
         "fr": 'Ø exterieur tige, mm'},
    'Ø внутренний трубы, мм':
        {"en": 'Pipe ID, mm',
         "fr": 'Ø interieur tige, mm'},
    'Ø наружный замка, мм':
        {"en": 'Tool joint OD, mm',
         "fr": 'Ø exterieur raccord, mm'},
    'Ø внутренний замка, мм':
        {"en": 'Tool joint ID, mm',
         "fr": 'Ø interieur raccord, mm'},
    'СБТ 127х9,19 Е':
        {"en": 'DP 5" 19.5 lb/ft',
         "fr": 'Tige 5" 19,5 lb/pi'},
    'замок ЗП-162':
        {"en": 'NC50 tool joint',
         "fr": 'raccord NC50'},
    'БУРОВЫЕ НАСОСЫ':
        {"en": 'MUD PUMPS',
         "fr": 'POMPES A BOUE'},
    'Параметры насосной группы. Если по секциям ставятся разные втулки - укажите это в примечании.':
        {"en": 'Pump group parameters. If different liners are used on different sections, note this in the comment column.',
         "fr": 'Parametres du groupe de pompage. Si les chemises different selon les sections, indiquez-le en commentaire.'},
    'Параметр':
        {"en": 'Parameter',
         "fr": 'Parametre'},
    'Ед. изм.':
        {"en": 'Unit',
         "fr": 'Unite'},
    'Тип насоса':
        {"en": 'Pump type',
         "fr": 'Type de pompe'},
    'например УНБТ-950, НБТ-600, F-1600':
        {"en": 'e.g. F-1600, 12-P-160',
         "fr": 'p. ex. F-1600, 12-P-160'},
    'Количество насосов в работе':
        {"en": 'Pumps in operation',
         "fr": 'Pompes en service'},
    'шт.':
        {"en": 'pcs',
         "fr": 'unites'},
    'Число цилиндров':
        {"en": 'Number of cylinders',
         "fr": 'Nombre de cylindres'},
    'трёхпоршневой = 3':
        {"en": 'triplex = 3',
         "fr": 'triplex = 3'},
    'Диаметр втулки':
        {"en": 'Liner diameter',
         "fr": 'Diametre de chemise'},
    'мм':
        {"en": 'mm',
         "fr": 'mm'},
    'Длина хода поршня':
        {"en": 'Stroke length',
         "fr": 'Course du piston'},
    'Коэффициент наполнения':
        {"en": 'Volumetric efficiency',
         "fr": 'Rendement volumetrique'},
    'обычно 0,85…0,95':
        {"en": 'typically 0.85 to 0.95',
         "fr": 'typiquement 0,85 a 0,95'},
    'Максимальное число ходов':
        {"en": 'Maximum strokes',
         "fr": 'Courses maximales'},
    '1/мин':
        {"en": '1/min',
         "fr": '1/min'},
    'Максимальное давление насоса':
        {"en": 'Maximum pump pressure',
         "fr": 'Pression maximale de pompe'},
    'атм':
        {"en": 'atm',
         "fr": 'atm'},
    'по паспорту для данной втулки':
        {"en": 'per data sheet for this liner',
         "fr": 'selon la fiche technique pour cette chemise'},
    'Максимальное давление обвязки':
        {"en": 'Maximum surface line pressure',
         "fr": 'Pression maximale du manifold'},
    'ограничение манифольда':
        {"en": 'manifold limit',
         "fr": 'limite du manifold'},
    'Мощность одного насоса':
        {"en": 'Power per pump',
         "fr": 'Puissance par pompe'},
    'кВт':
        {"en": 'kW',
         "fr": 'kW'},
    'КПД насоса':
        {"en": 'Pump efficiency',
         "fr": 'Rendement de la pompe'},
    'обычно 0,80…0,90':
        {"en": 'typically 0.80 to 0.90',
         "fr": 'typiquement 0,80 a 0,90'},
    'Давление срабатывания предохранительного клапана':
        {"en": 'Relief valve setting',
         "fr": 'Tarage de la soupape de securite'},
    'НАЗЕМНАЯ ОБВЯЗКА':
        {"en": 'SURFACE EQUIPMENT',
         "fr": 'EQUIPEMENT DE SURFACE'},
    'Путь раствора от насоса до бурильной колонны. Потери считаются поэлементно.':
        {"en": 'The path of the mud from the pump to the drill string. Losses are computed component by component.',
         "fr": 'Trajet de la boue de la pompe a la garniture. Les pertes sont calculees element par element.'},
    'Элемент':
        {"en": 'Component',
         "fr": 'Element'},
    'Стояк (манифольд высокого давления)':
        {"en": 'Standpipe (high pressure manifold)',
         "fr": 'Colonne montante (manifold haute pression)'},
    'Буровой рукав':
        {"en": 'Rotary hose',
         "fr": "Flexible d'injection"},
    'Вертлюг':
        {"en": 'Swivel',
         "fr": "Tete d'injection"},
    'Ведущая труба / верхний привод':
        {"en": 'Kelly / top drive',
         "fr": 'Tige carree / top drive'},
    'Прочее':
        {"en": 'Other',
         "fr": 'Autre'},
    'типовое значение':
        {"en": 'typical value',
         "fr": 'valeur typique'},
    'ШЛАМ И ТРЕБОВАНИЯ ПО ОЧИСТКЕ СТВОЛА':
        {"en": 'CUTTINGS AND HOLE CLEANING CRITERIA',
         "fr": 'DEBLAIS ET CRITERES DE NETTOYAGE'},
    'Плотность породы брать не нужно - она уже есть на листе «04 Разрез и давления». Здесь только характеристики частиц и критерии из РД предприятия.':
        {"en": 'The rock density is not needed here - it is already on the sheet "04 Geology and pressures". This sheet holds only the particle characteristics and the criteria from your own standards.',
         "fr": 'La densite de roche n\'est pas requise ici: elle figure deja sur la feuille "04 Geologie et pressions". Cette feuille ne contient que les caracteristiques des particules et vos criteres.'},
    'Характерный размер частиц, мм':
        {"en": 'Typical particle size, mm',
         "fr": 'Taille typique des particules, mm'},
    'Допустимая концентрация шлама, %':
        {"en": 'Allowable cuttings concentration, %',
         "fr": 'Concentration admissible de deblais, %'},
    'Мин. скорость в затрубье по РД, м/с':
        {"en": 'Min annular velocity per standard, m/s',
         "fr": 'Vitesse annulaire min selon norme, m/s'},
    'по РД предприятия':
        {"en": 'per company standard',
         "fr": 'selon norme interne'},
    'ТЕМПЕРАТУРНЫЙ РЕЖИМ ПО СТВОЛУ':
        {"en": 'TEMPERATURE PROFILE ALONG THE HOLE',
         "fr": 'PROFIL DE TEMPERATURE DU PUITS'},
    'Влияет на реологию и плотность раствора на забое. Достаточно 5-10 точек либо температуры на устье и геотермического градиента.':
        {"en": 'Affects rheology and mud density at the bottom. Five to ten points are enough, or the surface temperature together with the geothermal gradient.',
         "fr": 'Influe sur la rheologie et la densite au fond. Cinq a dix points suffisent, ou la temperature en surface et le gradient geothermique.'},
    'Глубина, м TVD':
        {"en": 'Depth, m TVD',
         "fr": 'Profondeur, m TVD'},
    'Температура пласта, °C':
        {"en": 'Formation temperature, °C',
         "fr": 'Temperature de formation, °C'},
    'Температура раствора на входе, °C':
        {"en": 'Inlet mud temperature, °C',
         "fr": "Temperature de boue a l'entree, °C"},
    'градиент 2,2 °C/100 м':
        {"en": 'gradient 2.2 °C/100 m',
         "fr": 'gradient 2,2 °C/100 m'},
}
