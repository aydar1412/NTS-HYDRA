# -*- coding: utf-8 -*-
"""Сборка словаря перевода шаблона: ключ - русская строка по номеру."""

import io

RU = [x for x in io.open("/home/claude/strings.txt", encoding="utf-8")
      .read().split("\n") if x.strip()]

TR = {
 0: ("Conductor pipe", "Tube guide"),

 1: ("Surface casing 1", "Tubage de surface 1"),
 2: ("Surface casing 2", "Tubage de surface 2"),
 3: ("Production casing 1", "Tubage de production 1"),
 4: ("Production casing 2", "Tubage de production 2"),
 5: ("Production casing 3", "Tubage de production 3"),
 6: ("Liner", "Liner"),
 8: ("Input data for drilling hydraulics calculation",
     "Donnees d'entree pour le calcul hydraulique de forage"),
 9: ("by AR", "by AR"),
 10: ("HOW TO FILL IN", "COMMENT REMPLIR"),
 11: ("Sheets are numbered in the order they are best filled in. "
      "Work from top to bottom.",
      "Les feuilles sont numerotees dans l'ordre de remplissage. "
      "Procedez de haut en bas."),
 12: ("Fill in the light yellow cells only. Do not change the grey "
      "headers or the first column.",
      "Ne remplissez que les cellules jaune clair. Ne modifiez ni les "
      "en-tetes gris ni la premiere colonne."),
 13: ("If a value is not available, write n/a . The program will take it "
      "from its own configuration and mark the value as assumed in the "
      "calculation. An empty cell means the same.",
      "Si une valeur est inconnue, ecrivez n/a . Le programme prendra la "
      "valeur de sa configuration et la signalera comme supposee. Une "
      "cellule vide a le meme effet."),
 14: ("The EXAMPLE row at the bottom of each table shows the format. "
      "You may delete it or leave it - the program ignores it.",
      "La ligne EXEMPLE au bas de chaque tableau montre le format. Vous "
      "pouvez la supprimer ou la laisser: le programme l'ignore."),
 15: ("Interval names in the first column MUST NOT be changed: they link "
      "the data across all sheets. If the number of intervals differs, "
      "edit the sheet \"05 Intervals\" and the others will follow.",
      "Les noms d'intervalles de la premiere colonne NE DOIVENT PAS etre "
      "modifies: ils relient les donnees de toutes les feuilles. Si le "
      "nombre d'intervalles change, modifiez la feuille \"05 "
      "Intervalles\"."),
 16: ("Each value is entered exactly once. If data seem to repeat across "
      "sheets, check again - these are most likely different quantities.",
      "Chaque valeur n'est saisie qu'une fois. Si des donnees semblent se "
      "repeter, verifiez: il s'agit sans doute de grandeurs differentes."),
 17: ("Numbers may use a dot or a comma. A range such as 50-55 is also "
      "accepted; which end is used is set in the configuration.",
      "Les nombres acceptent le point ou la virgule. Une plage comme "
      "50-55 est admise; le choix de la borne est defini dans la "
      "configuration."),
 18: ("On the sheets \"08 Mud motor\" and \"09 MWD\" the word no means "
      "\"equipment not used, pressure drop is zero\".",
      "Sur les feuilles \"08 Moteur de fond\" et \"09 MWD\", le mot non "
      "signifie \"equipement non utilise, perte de charge nulle\"."),
 19: ("The entry n/a on the same sheets means \"data not yet available\" - "
      "the configuration value will be used. These are different things.",
      "La mention n/a sur ces memes feuilles signifie \"donnee non encore "
      "disponible\" - la valeur de configuration sera utilisee. Ce sont "
      "deux choses differentes."),
 20: ("Sheet", "Feuille"),
 21: ("Contents", "Contenu"),
 22: ("Priority", "Priorite"),
 23: ("01 General", "01 Informations generales"),
 24: ("client, field, pad, well, contractor, author",
     "client, gisement, plateforme, puits, entreprise, auteur"),
 25: ("required", "obligatoire"),
 26: ("02 Casing", "02 Tubages"),
 27: ("casing strings: diameter, wall thickness, setting depth",
     "colonnes de tubage: diametre, epaisseur, profondeur de descente"),
 28: ("03 Survey", "03 Deviation"),
 29: ("MD / inclination / azimuth along the hole",
     "MD / inclinaison / azimut le long du puits"),
 30: ("04 Geology and pressures", "04 Geologie et pressions"),
 31: ("formations, lithology, rock density, pore and fracture pressure",
     "formations, lithologie, densite de roche, pressions de pore et de "
     "fracturation"),
 32: ("important", "important"),
 33: ("05 Intervals", "05 Intervalles"),
 34: ("interval split, bit size, ROP, flow rate, washout factor",
     "decoupage, diametre d'outil, VOP, debit, facteur de cavage"),
 35: ("06 Drilling fluid", "06 Boue de forage"),
 36: ("density, Fann readings, gel strength, temperature",
     "densite, lectures Fann, gel, temperature"),
 37: ("07 Bit nozzles", "07 Duses"),
 38: ("nozzle sizes or TFA", "diametres de duses ou TFA"),
 39: ("08 Mud motor", "08 Moteur de fond"),
 40: ("size, flow rate, pressure drops", "taille, debit, pertes de charge"),
 41: ("09 MWD", "09 MWD"),
 42: ("type, pressure drop", "type, perte de charge"),
 43: ("10 BHA", "10 Garniture de fond"),
 44: ("all assemblies in one table, from the bit upwards",
     "toutes les garnitures dans un tableau, de l'outil vers le haut"),
 45: ("11 Drill string", "11 Garniture de forage"),
 46: ("pipe above the BHA for each interval",
     "tiges au-dessus de la garniture de fond, par intervalle"),
 47: ("12 Mud pumps", "12 Pompes a boue"),
 48: ("type, liners, stroke, pressure limit",
     "type, chemises, course, pression limite"),
 49: ("13 Surface equipment", "13 Equipement de surface"),
 50: ("standpipe, hose, swivel, kelly",
     "colonne montante, flexible, tete d'injection, tige carree"),
 51: ("14 Cuttings", "14 Deblais"),
 52: ("particle size, hole cleaning criteria",
     "taille des particules, criteres de nettoyage"),
 53: ("optional", "souhaitable"),
 54: ("15 Temperature", "15 Temperature"),
 55: ("temperature profile along the hole",
     "profil de temperature le long du puits"),
 56: ("GENERAL INFORMATION", "INFORMATIONS GENERALES"),
 57: ("Shown on the report cover page, in the footer of every page and in "
      "the PDF file properties.",
      "Affichees sur la page de garde du rapport, dans le pied de page de "
      "chaque page et dans les proprietes du PDF."),
 58: ("Item", "Rubrique"),
 59: ("Value", "Valeur"),
 60: ("Comment", "Commentaire"),
 61: ("Client", "Client"),
 62: ("Field", "Gisement"),
 63: ("Licence area", "Permis"),
 64: ("Pad", "Plateforme"),
 65: ("Well", "Puits"),
 66: ("Well type", "Type de puits"),
 67: ("Target formation", "Horizon objectif"),
 68: ("Total depth, m MD", "Profondeur finale, m MD"),
 69: ("Drilling contractor", "Entreprise de forage"),
 70: ("Rig", "Appareil de forage"),
 71: ("Prepared by", "Etabli par"),
 72: ("Date", "Date"),
 73: ("Document number", "Numero du document"),
 74: ("Note", "Remarque"),
 75: ("CASING DESIGN", "ARCHITECTURE DE TUBAGE"),
 76: ("Casing strings from top to bottom. The program derives the inside "
      "diameter from the outside diameter and the wall thickness. If the "
      "lower hole section is left uncased, add a row \"Open hole\": give "
      "the diameter and depth and leave the wall thickness empty.",
      "Colonnes de tubage de haut en bas. Le programme calcule le "
      "diametre interieur a partir du diametre exterieur et de "
      "l'epaisseur. Si le bas du puits reste en trou ouvert, ajoutez une "
      "ligne \"Trou ouvert\": indiquez le diametre et la profondeur et "
      "laissez l'epaisseur vide."),
 77: ("Casing", "Tubage"),
 78: ("OD, mm", "Ø exterieur, mm"),
 79: ("Wall thickness, mm", "Epaisseur, mm"),
 80: ("Setting depth, m MD", "Profondeur, m MD"),
 81: ("Setting depth, m TVD", "Profondeur, m TVD"),
 82: ("Hanger depth, m MD", "Suspension, m MD"),
 83: ("Surface casing", "Tubage de surface"),
 84: ("Intermediate casing", "Tubage intermediaire"),
 85: ("Production casing", "Tubage de production"),
 86: ("Open hole", "Trou ouvert"),
 87: ("For the liner only. Leave empty for strings run from surface.",
     "Pour le liner uniquement. Laissez vide pour les colonnes depuis la "
     "surface."),
 88: ("set on top of the salt", "descendu au toit des sels"),
 89: ("EXAMPLE →", "EXEMPLE →"),
 90: ("DIRECTIONAL SURVEY", "RELEVE DE DEVIATION"),
 91: ("The only source of trajectory data. Station spacing 10-30 m. TVD "
      "may be left empty - the program computes it from the inclination. "
      "Add rows below without limit.",
      "Seule source des donnees de trajectoire. Pas de 10 a 30 m. Le TVD "
      "peut rester vide: le programme le calcule a partir de "
      "l'inclinaison. Ajoutez des lignes sans limite."),
 92: ("MD, m", "MD, m"),
 93: ("Inclination, deg", "Inclinaison, deg"),
 94: ("Azimuth, deg", "Azimut, deg"),
 95: ("TVD, m (if known)", "TVD, m (si connu)"),
 96: ("Angle from vertical. 0° is vertical, 90° is horizontal.",
     "Angle par rapport a la verticale. 0° vertical, 90° horizontal."),
 97: ("LITHOLOGY AND FORMATION PRESSURES",
     "LITHOLOGIE ET PRESSIONS DE FORMATION"),
 98: ("Stratigraphy and pressures in one table, formation by formation. "
      "Pressures are given as equivalent density in g/cm³. Without them "
      "the program cannot check the ECD against the drilling window.",
      "Stratigraphie et pressions dans un seul tableau, par formation. "
      "Les pressions sont exprimees en densite equivalente, g/cm³. Sans "
      "elles le programme ne peut verifier la DEC dans la fenetre de "
      "forage."),
 99: ("Formation", "Formation"),
 100: ("From, m MD", "De, m MD"),
 101: ("To, m MD", "A, m MD"),
 102: ("Lithology", "Lithologie"),
 103: ("Rock density, g/cm³", "Densite de roche, g/cm³"),
 104: ("Pore pressure, g/cm³", "Pression de pore, g/cm³"),
 105: ("Fracture pressure, g/cm³", "Pression de fracturation, g/cm³"),
 106: ("Loss onset, g/cm³", "Debut de pertes, g/cm³"),
 107: ("Needed for cuttings transport and the cuttings contribution to "
       "ECD.",
       "Necessaire au transport des deblais et a leur contribution a la "
       "DEC."),
 108: ("Equivalent density of the formation fracture pressure.",
      "Densite equivalente de la pression de fracturation."),
 109: ("dolerite (traps)", "dolerite (trapps)"),
 110: ("loss zone", "zone de pertes"),
 111: ("DRILLING INTERVALS", "INTERVALLES DE FORAGE"),
 112: ("The master sheet: it defines how the calculation is split. The "
       "names in the first column are used on every other sheet - if you "
       "change them here, change them there as well. One interval means "
       "one BHA and one circulation regime.",
       "Feuille principale: elle definit le decoupage du calcul. Les noms "
       "de la premiere colonne sont utilises sur toutes les autres "
       "feuilles: si vous les modifiez ici, modifiez-les aussi ailleurs. "
       "Un intervalle correspond a une garniture et un regime."),
 113: ("Interval", "Intervalle"),
 114: ("Bit diameter, mm", "Diametre d'outil, mm"),
 115: ("Bit type", "Type d'outil"),
 116: ("Drive", "Entrainement"),
 117: ("Flow rate, L/s", "Debit, L/s"),
 118: ("ROP, m/h", "VOP, m/h"),
 119: ("Washout factor", "Facteur de cavage"),
 120: ("String rotation, rpm", "Rotation garniture, tr/min"),
 121: ("rotary / rotary+motor / motor / RSS",
      "rotary / rotary+moteur / moteur / RSS"),
 122: ("A range is allowed: 50-55. Which end is used is set in the "
       "configuration.",
       "Une plage est admise: 50-55. Le choix de la borne est defini dans "
       "la configuration."),
 123: ("Increase of the open hole DIAMETER. Typically 1.03 to 1.25. "
       "Affects annular velocity and ECD.",
       "Augmentation du DIAMETRE du trou ouvert. Typiquement 1,03 a 1,25. "
       "Influe sur la vitesse annulaire et la DEC."),
 124: ("Rotary table or top drive speed. 0 or empty means sliding on the "
       "motor without string rotation.",
       "Vitesse de la table ou du top drive. 0 ou vide signifie glissement "
       "sur moteur sans rotation."),
 126: ("rotary+motor", "rotary+moteur"),
 127: ("DRILLING FLUID PROPERTIES", "PROPRIETES DE LA BOUE"),
 128: ("Fann viscometer readings in lb/100 ft². If no viscometer data are "
       "available, fill in density, PV and YP only and choose the Bingham "
       "model. The \"Rheology model\" column may be left empty: the model "
       "is then chosen from the data provided.",
       "Lectures du viscosimetre Fann en lb/100 pi². A defaut de "
       "viscosimetre, remplissez seulement la densite, VP et YP et "
       "choisissez le modele de Bingham. La colonne \"Modele rheologique\" "
       "peut rester vide: le modele est alors deduit des donnees."),
 129: ("Fluid type", "Type de boue"),
 130: ("Density, g/cm³", "Densite, g/cm³"),
 137: ("Gel 10 s", "Gel 10 s"),
 138: ("Gel 10 min", "Gel 10 min"),
 139: ("Test temperature, °C", "Temperature d'essai, °C"),
 140: ("Fluid loss, cm³/30 min", "Filtrat, cm³/30 min"),
 141: ("PV, cP", "VP, cP"),
 142: ("YP, lb/100 ft²", "YP, lb/100 pi²"),
 143: ("Rheology model", "Modele rheologique"),
 144: ("Reading at 600 rpm, lb/100 ft².",
      "Lecture a 600 tr/min, lb/100 pi²."),
 145: ("Reading at 3 rpm. Governs the carrying capacity in the annulus.",
      "Lecture a 3 tr/min. Determine la capacite de transport en "
      "annulaire."),
 146: ("Plastic viscosity. Fill in if no viscometer readings are "
       "available.",
       "Viscosite plastique. A remplir en l'absence de lectures du "
       "viscosimetre."),
 147: ("Herschel-Bulkley / power law / Bingham. Empty or \"auto\" means "
       "the model is chosen from the data: theta6 and theta3 present - "
       "Herschel-Bulkley; only theta600 and theta300 - power law; only PV "
       "and YP - Bingham.",
       "Herschel-Bulkley / loi de puissance / Bingham. Vide ou \"auto\": "
       "le modele est deduit des donnees - theta6 et theta3 presents: "
       "Herschel-Bulkley; seulement theta600 et theta300: loi de "
       "puissance; seulement VP et YP: Bingham."),
 148: ("polymer-bentonite", "polymere-bentonite"),
 149: ("Herschel-Bulkley", "Herschel-Bulkley"),
 150: ("BIT NOZZLES", "DUSES DE L'OUTIL"),
 151: ("Nozzle diameters in 1/32 inch (N1 to N8). Leave unused cells "
       "empty. TFA is calculated by a formula. If only the TFA is known, "
       "type it into the last column instead of the formula.",
       "Diametres des duses en 1/32 de pouce (N1 a N8). Laissez vides les "
       "cellules inutilisees. La TFA est calculee par formule. Si seule "
       "la TFA est connue, saisissez-la dans la derniere colonne."),
 152: ("N1", "N1"), 153: ("N2", "N2"), 154: ("N3", "N3"),
 155: ("N4", "N4"), 156: ("N5", "N5"), 157: ("N6", "N6"),
 158: ("N7", "N7"), 159: ("N8", "N8"),
 160: ("TFA, in²", "TFA, po²"),
 161: ("Diameter in 1/32 inch. 16 = 16/32\" = 12.7 mm.",
      "Diametre en 1/32 de pouce. 16 = 16/32\" = 12,7 mm."),
 162: ("Total flow area of the nozzles.",
      "Surface totale d'ecoulement des duses."),
 163: ("six 16/32\" nozzles", "six duses 16/32\""),
 164: ("DOWNHOLE MOTORS", "MOTEURS DE FOND"),
 165: ("If no motor is run on the interval, write no . If the data sheet "
       "is not available yet, write n/a .",
       "Si aucun moteur n'est utilise, ecrivez non . Si la fiche "
       "technique manque encore, ecrivez n/a ."),
 166: ("Size", "Taille"),
 167: ("Bore diameter, mm", "Diametre de passage, mm"),
 168: ("Flow min, L/s", "Debit min, L/s"),
 169: ("Flow max, L/s", "Debit max, L/s"),
 170: ("Off-bottom ΔP, atm", "ΔP hors fond, atm"),
 171: ("ΔP on load, atm", "ΔP en charge, atm"),
 172: ("Torque, kN·m", "Couple, kN·m"),
 173: ("Speed, rpm", "Vitesse, tr/min"),
 174: ("Bend angle, deg", "Angle de coude, deg"),
 175: ("Pressure drop when circulating off bottom, at the maximum flow "
       "rate.", "Perte de charge en circulation hors fond, au debit max."),
 176: ("Additional pressure drop at working torque.",
      "Perte de charge supplementaire au couple de travail."),
 178: ("MWD / LWD", "MWD / LWD"),
 179: ("The pressure drop is given at the flow rate in the adjacent "
       "column. If no MWD is run, write no .",
       "La perte de charge est donnee au debit indique dans la colonne "
       "voisine. Sans MWD, ecrivez non ."),
 180: ("Type / model", "Type / modele"),
 181: ("ID, mm", "Ø interieur, mm"),
 182: ("Pressure drop, atm", "Perte de charge, atm"),
 183: ("Telemetry channel", "Canal de telemesure"),
 185: ("mud pulse", "impulsion de boue"),
 186: ("BOTTOM HOLE ASSEMBLIES", "GARNITURES DE FOND"),
 187: ("All assemblies in one table. For each interval the components are "
       "listed FROM THE BIT UPWARDS: the first row is the bit, then "
       "upwards towards surface. The interval name is written in the "
       "first row of the assembly only. Leave an empty row between "
       "assemblies.",
       "Toutes les garnitures dans un seul tableau. Pour chaque "
       "intervalle, les elements sont listes DE L'OUTIL VERS LE HAUT: la "
       "premiere ligne est l'outil. Le nom de l'intervalle n'est ecrit "
       "que sur la premiere ligne. Laissez une ligne vide entre les "
       "garnitures."),
 188: ("Component", "Element"),
 189: ("Length, m", "Longueur, m"),
 190: ("May be left empty for the bit and the motor: they are handled by "
       "their own models.",
       "Peut rester vide pour l'outil et le moteur: ils ont leurs propres "
       "modeles."),
 191: ("Length excluding the pin.", "Longueur hors filetage male."),
 192: ("Bit", "Outil"),
 193: ("Crossover sub", "Raccord"),
 194: ("Stabiliser", "Stabilisateur"),
 195: ("Drill collar", "Masse-tige"),
 196: ("example: this is how one assembly is filled in, then an empty row "
       "and the next interval",
       "exemple: voici comment saisir une garniture, puis une ligne vide "
       "et l'intervalle suivant"),
 197: ("DRILL STRING ABOVE THE BHA",
      "GARNITURE AU-DESSUS DE LA GARNITURE DE FOND"),
 198: ("What makes up the string from the top of the BHA to surface. The "
       "length need not be given - the program fills the string to "
       "surface itself.",
       "Ce qui compose la garniture du haut de la garniture de fond "
       "jusqu'a la surface. La longueur est facultative: le programme "
       "complete jusqu'a la surface."),
 199: ("Description", "Designation"),
 200: ("Pipe OD, mm", "Ø exterieur tige, mm"),
 201: ("Pipe ID, mm", "Ø interieur tige, mm"),
 202: ("Tool joint OD, mm", "Ø exterieur raccord, mm"),
 203: ("Tool joint ID, mm", "Ø interieur raccord, mm"),
 204: ("DP 5\" 19.5 lb/ft", "Tige 5\" 19,5 lb/pi"),
 205: ("NC50 tool joint", "raccord NC50"),
 206: ("MUD PUMPS", "POMPES A BOUE"),
 207: ("Pump group parameters. If different liners are used on different "
       "sections, note this in the comment column.",
       "Parametres du groupe de pompage. Si les chemises different selon "
       "les sections, indiquez-le en commentaire."),
 208: ("Parameter", "Parametre"),
 209: ("Unit", "Unite"),
 210: ("Pump type", "Type de pompe"),
 211: ("e.g. F-1600, 12-P-160", "p. ex. F-1600, 12-P-160"),
 212: ("Pumps in operation", "Pompes en service"),
 213: ("pcs", "unites"),
 214: ("Number of cylinders", "Nombre de cylindres"),
 215: ("triplex = 3", "triplex = 3"),
 216: ("Liner diameter", "Diametre de chemise"),
 217: ("mm", "mm"),
 218: ("Stroke length", "Course du piston"),
 219: ("Volumetric efficiency", "Rendement volumetrique"),
 220: ("typically 0.85 to 0.95", "typiquement 0,85 a 0,95"),
 221: ("Maximum strokes", "Courses maximales"),
 222: ("1/min", "1/min"),
 223: ("Maximum pump pressure", "Pression maximale de pompe"),
 224: ("atm", "atm"),
 225: ("per data sheet for this liner",
      "selon la fiche technique pour cette chemise"),
 226: ("Maximum surface line pressure", "Pression maximale du manifold"),
 227: ("manifold limit", "limite du manifold"),
 228: ("Power per pump", "Puissance par pompe"),
 229: ("kW", "kW"),
 230: ("Pump efficiency", "Rendement de la pompe"),
 231: ("typically 0.80 to 0.90", "typiquement 0,80 a 0,90"),
 232: ("Relief valve setting", "Tarage de la soupape de securite"),
 233: ("SURFACE EQUIPMENT", "EQUIPEMENT DE SURFACE"),
 234: ("The path of the mud from the pump to the drill string. Losses are "
       "computed component by component.",
       "Trajet de la boue de la pompe a la garniture. Les pertes sont "
       "calculees element par element."),
 235: ("Component", "Element"),
 236: ("Standpipe (high pressure manifold)",
      "Colonne montante (manifold haute pression)"),
 237: ("Rotary hose", "Flexible d'injection"),
 238: ("Swivel", "Tete d'injection"),
 239: ("Kelly / top drive", "Tige carree / top drive"),
 240: ("Other", "Autre"),
 241: ("typical value", "valeur typique"),
 242: ("CUTTINGS AND HOLE CLEANING CRITERIA",
      "DEBLAIS ET CRITERES DE NETTOYAGE"),
 243: ("The rock density is not needed here - it is already on the sheet "
       "\"04 Geology and pressures\". This sheet holds only the particle "
       "characteristics and the criteria from your own standards.",
       "La densite de roche n'est pas requise ici: elle figure deja sur "
       "la feuille \"04 Geologie et pressions\". Cette feuille ne contient "
       "que les caracteristiques des particules et vos criteres."),
 244: ("Typical particle size, mm", "Taille typique des particules, mm"),
 245: ("Allowable cuttings concentration, %",
      "Concentration admissible de deblais, %"),
 246: ("Min annular velocity per standard, m/s",
      "Vitesse annulaire min selon norme, m/s"),
 247: ("per company standard", "selon norme interne"),
 248: ("TEMPERATURE PROFILE ALONG THE HOLE",
      "PROFIL DE TEMPERATURE DU PUITS"),
 249: ("Affects rheology and mud density at the bottom. Five to ten "
       "points are enough, or the surface temperature together with the "
       "geothermal gradient.",
       "Influe sur la rheologie et la densite au fond. Cinq a dix points "
       "suffisent, ou la temperature en surface et le gradient "
       "geothermique."),
 250: ("Depth, m TVD", "Profondeur, m TVD"),
 251: ("Formation temperature, °C", "Temperature de formation, °C"),
 252: ("Inlet mud temperature, °C", "Temperature de boue a l'entree, °C"),
 253: ("gradient 2.2 °C/100 m", "gradient 2,2 °C/100 m"),
}

out = ['# -*- coding: utf-8 -*-',
       '"""Строки шаблона исходных данных на трёх языках.',
       '',
       'Ключ - русская строка, значение - перевод. Отсутствующий перевод',
       'означает, что строка выводится по-русски: расчёт от этого не',
       'страдает. Чтобы добавить язык, впишите его код в LANG_SUFFIX и',
       'добавьте ключ в каждую запись.',
       '"""',
       '',
       '_LANG = "ru"',
       'LANG_SUFFIX = {"ru": "_RU", "en": "_EN", "fr": "_FR"}',
       '',
       '',
       'def set_lang(code):',
       '    global _LANG',
       '    _LANG = code if code in LANG_SUFFIX else "ru"',
       '',
       '',
       'def T(s):',
       '    """Строка шаблона на текущем языке."""',
       '    if not isinstance(s, str) or _LANG == "ru":',
       '        return s',
       '    row = STR.get(" ".join(s.split()))',
       '    if not row:',
       '        return s',
       '    return row.get(_LANG, s)',
       '',
       '',
       'STR = {',
       '    "00 \u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446'
       '\u0438\u044f":',
       '        {"en": "00 Instructions",',
       '         "fr": "00 Instructions"},']
for i, (en, fr) in sorted(TR.items()):
    ru = " ".join(RU[i].split())
    out.append('    %r:' % ru)
    out.append('        {"en": %r,' % en)
    out.append('         "fr": %r},' % fr)
out.append('}')
io.open("/home/claude/repo/template_lang.py", "w",
        encoding="utf-8").write("\n".join(out) + "\n")
print("переведено", len(TR), "из", len(RU))
