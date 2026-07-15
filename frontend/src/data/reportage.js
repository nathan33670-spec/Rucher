// Contenu du site vitrine « reportage » sur l'abeille et le miel.
// Chaque chapitre = une page/URL distincte. Ordre = ordre de lecture + navigation.
//
// Schéma d'une section : { h, p:[], li:[], note:{title,text}, stats:[{v,l}], quote }

export const chapters = [
  {
    slug: 'l-abeille',
    nav: "L'abeille",
    icon: 'mdi-bee',
    eyebrow: 'Portrait',
    title: "L'abeille domestique",
    lead: "Apis mellifera, l'abeille à miel : un insecte social vieux de plus de 30 millions d'années, taillé pour butiner, communiquer et vivre en colonie.",
    hero: ['#f6b73c', '#e08a1e'],
    sections: [
      {
        h: 'Un insecte parfaitement équipé',
        p: [
          "L'abeille mellifère mesure à peine plus d'un centimètre, mais chaque partie de son corps est un outil. Sa tête porte deux grands yeux composés de milliers de facettes, trois petits yeux simples (ocelles) sensibles à la lumière, deux antennes qui sentent et touchent, et une longue langue (proboscis) qui aspire le nectar au fond des fleurs.",
        ],
        li: [
          "Trois parties : tête, thorax, abdomen.",
          "Deux paires d'ailes qui se couplent en vol et battent plus de 200 fois par seconde.",
          "Des « corbeilles à pollen » sur les pattes arrière pour transporter la récolte.",
          "Un aiguillon (chez les ouvrières et la reine) — barbelé chez l'ouvrière, qui meurt après avoir piqué un mammifère.",
        ],
      },
      {
        h: 'Des sens hors du commun',
        p: [
          "L'abeille voit l'ultraviolet : de nombreuses fleurs affichent, invisibles à nos yeux, de véritables « pistes d'atterrissage » qui la guident vers le nectar. Son odorat, logé dans les antennes, distingue des milliers de composés et reconnaît l'odeur de la colonie comme celle des fleurs.",
        ],
        note: {
          title: 'Le saviez-vous ?',
          text: "Une abeille perçoit le champ magnétique terrestre et la lumière polarisée du ciel, ce qui l'aide à s'orienter même quand le soleil est caché.",
        },
      },
    ],
  },

  {
    slug: 'abeilles-sauvages',
    nav: 'Les abeilles sauvages',
    icon: 'mdi-bee-flower',
    eyebrow: 'Diversité',
    title: 'Les abeilles sauvages, cousines discrètes',
    lead: "Quand on dit « abeille », on pense à la ruche. Mais l'abeille à miel n'est qu'une espèce parmi des milliers — la plupart vivent seules et ne font pas de miel.",
    hero: ['#c9a227', '#8a6d1b'],
    sections: [
      {
        h: 'Un peuple aux mille visages',
        p: [
          "On compte près de 1 000 espèces d'abeilles sauvages en France, et près de 20 000 dans le monde. La grande majorité sont solitaires : chaque femelle construit et approvisionne seule son nid, dans le sol, le bois mort ou des tiges creuses. Bourdons, osmies, andrènes, abeilles charpentières… une variété insoupçonnée.",
        ],
        li: [
          "La plupart ne piquent pas ou très peu et n'ont pas de colonie.",
          "Elles ne produisent pas de miel : elles butinent pour nourrir leur seule descendance.",
          "Le bourdon, tout rond et velu, en est le représentant le plus connu.",
        ],
      },
      {
        h: 'Des pollinisatrices irremplaçables',
        p: [
          "Les abeilles sauvages sont souvent des pollinisatrices redoutablement efficaces, parfois plus que l'abeille domestique pour certaines plantes. Elles butinent tôt, par temps frais, et visitent des fleurs que d'autres délaissent. Mais elles subissent les mêmes menaces — pesticides, disparition des fleurs — et déclinent partout.",
        ],
        note: {
          title: 'Un geste pour elles',
          text: "Un « hôtel à insectes », des tiges creuses ou un carré de sol nu et ensoleillé offrent un abri précieux aux abeilles solitaires.",
        },
      },
    ],
  },

  {
    slug: 'cycle-de-vie',
    nav: 'Le cycle de vie',
    icon: 'mdi-egg-outline',
    eyebrow: 'Métamorphose',
    title: "De l'œuf à la butineuse",
    lead: "En trois semaines, un œuf minuscule devient une ouvrière accomplie. Une métamorphose complète, réglée au jour près.",
    hero: ['#f4a259', '#d9772b'],
    sections: [
      {
        h: 'Quatre étapes, une transformation totale',
        p: [
          "L'abeille connaît une métamorphose complète : œuf, larve, nymphe, adulte. La reine pond un œuf par alvéole. Après trois jours, l'œuf éclot en larve, nourrie sans relâche par les ouvrières. La cellule est ensuite operculée (fermée de cire) : la larve tisse son cocon et se transforme en nymphe, avant d'émerger adulte.",
        ],
        stats: [
          { v: '16 j', l: 'Reine' },
          { v: '21 j', l: 'Ouvrière' },
          { v: '24 j', l: 'Faux-bourdon' },
        ],
      },
      {
        h: 'Toute une vie de métiers',
        p: [
          "L'ouvrière change de métier avec l'âge. Jeune, elle nettoie les alvéoles, puis nourrit les larves (nourrice), bâtit les rayons de cire, stocke le nectar, ventile et garde l'entrée. Ce n'est qu'après une vingtaine de jours qu'elle sort butiner — le métier le plus usant.",
        ],
        li: [
          "Ouvrière d'été : environ 5 à 6 semaines de vie, dont la moitié à butiner.",
          "Ouvrière d'hiver : plusieurs mois, pour passer la mauvaise saison.",
          "Reine : 2 à 5 ans, unique pondeuse de la colonie.",
        ],
      },
    ],
  },

  {
    slug: 'essaimage',
    nav: "L'essaimage",
    icon: 'mdi-transit-connection-variant',
    eyebrow: 'Reproduction',
    title: "L'essaimage, la ruche qui se divise",
    lead: "Une colonie ne se reproduit pas comme un individu : c'est la ruche entière qui se scinde en deux. Un moment décisif dans la vie des abeilles.",
    hero: ['#e0a030', '#a9701a'],
    sections: [
      {
        h: 'Partir pour se multiplier',
        p: [
          "Au printemps, quand la colonie est populeuse, l'ancienne reine quitte la ruche avec la moitié des ouvrières : c'est l'essaim. Il se pose en grappe sur une branche, le temps que des éclaireuses trouvent un nouveau logis. Dans la ruche d'origine, une jeune reine naît et prend la relève. D'une colonie, il y en a désormais deux.",
        ],
      },
      {
        h: 'Impressionnant mais paisible',
        p: [
          "Le nuage d'abeilles qui tourbillonne impressionne, mais un essaim est généralement très doux : gorgées de miel pour le voyage et sans couvain à défendre, les abeilles n'ont aucune raison d'être agressives. L'apiculteur peut alors recueillir l'essaim pour lui offrir une nouvelle ruche.",
        ],
        note: {
          title: 'Bon à savoir',
          text: "Un essaim dans votre jardin ? Ne le détruisez pas : contactez un apiculteur local, qui viendra le récupérer gratuitement.",
        },
      },
    ],
  },

  {
    slug: 'la-colonie',
    nav: 'La colonie',
    icon: 'mdi-account-group',
    eyebrow: 'Société',
    title: 'Une colonie, un superorganisme',
    lead: "Des dizaines de milliers d'individus qui, ensemble, se comportent comme un seul être vivant. Chacun son rôle, aucun chef.",
    hero: ['#e8a33d', '#c46f1b'],
    sections: [
      {
        h: 'Trois castes complémentaires',
        p: [
          "La colonie repose sur trois castes. La reine, seule femelle fertile, pond jusqu'à 2 000 œufs par jour et diffuse des phéromones qui soudent la ruche. Les ouvrières, femelles stériles, accomplissent tous les travaux. Les faux-bourdons, les mâles, n'ont qu'une mission : féconder une reine lors du vol nuptial.",
        ],
        li: [
          "1 reine — la mère de toute la colonie.",
          "40 000 à 60 000 ouvrières en pleine saison.",
          "Quelques centaines de faux-bourdons au printemps, chassés avant l'hiver.",
        ],
      },
      {
        h: 'Une intelligence collective',
        p: [
          "Aucune abeille ne dirige : les décisions émergent de milliers d'interactions. Le choix d'un nouveau nid lors de l'essaimage, la régulation de la température ou le partage du travail se font sans chef, par communication et rétroaction. On parle de « superorganisme ».",
        ],
        quote: "Une ruche pense sans cerveau : c'est la foule des abeilles qui décide.",
      },
    ],
  },

  {
    slug: 'la-ruche',
    nav: 'La ruche',
    icon: 'mdi-hexagon-multiple',
    eyebrow: 'Architecture',
    title: "La ruche, chef-d'œuvre d'ingénierie",
    lead: "L'hexagone de cire : la forme qui stocke le plus de miel avec le moins de matière. Une architecture optimale, bâtie dans le noir.",
    hero: ['#f2c14e', '#e0932f'],
    sections: [
      {
        h: 'La géométrie parfaite de la cire',
        p: [
          "Les rayons sont faits d'alvéoles hexagonales de cire, sécrétée par les glandes des jeunes ouvrières. L'hexagone n'est pas un hasard : c'est la forme qui pave un plan sans laisser de vide, en utilisant le minimum de cire pour le maximum de volume. Un modèle d'optimisation que les mathématiciens ont mis des siècles à démontrer.",
        ],
        note: {
          title: 'Précision',
          text: "Les alvéoles sont légèrement inclinées vers le haut pour empêcher le miel de couler, et bâties à une épaisseur de paroi d'un dixième de millimètre.",
        },
      },
      {
        h: 'Une ville climatisée',
        p: [
          "Le couvain doit rester autour de 35 °C. En été, les ouvrières ventilent avec leurs ailes et apportent de l'eau pour rafraîchir par évaporation. En hiver, elles se regroupent en grappe serrée et font vibrer leurs muscles pour produire de la chaleur, se relayant de l'extérieur vers le cœur du groupe.",
        ],
        stats: [
          { v: '35 °C', l: 'au couvain' },
          { v: '~50 kg', l: 'de miel / an* ' },
          { v: '0,1 mm', l: 'de paroi' },
        ],
      },
    ],
  },

  {
    slug: 'communication',
    nav: 'La communication',
    icon: 'mdi-message-processing',
    eyebrow: 'Langage',
    title: 'La danse des abeilles',
    lead: "Comment dire à ses sœurs où trouver un champ fleuri à trois kilomètres ? En dansant. Une découverte qui a valu un prix Nobel.",
    hero: ['#efb236', '#cc7a1a'],
    sections: [
      {
        h: 'La danse frétillante',
        p: [
          "De retour d'une bonne source, la butineuse exécute sur les rayons une « danse frétillante » en forme de huit. L'angle de la danse par rapport à la verticale indique la direction de la fleur par rapport au soleil ; la durée du frétillement indique la distance. Les abeilles voisines la suivent, la touchent, puis s'envolent dans la bonne direction.",
        ],
        note: {
          title: 'Prix Nobel',
          text: "Karl von Frisch a décodé ce langage dansé et reçu le prix Nobel de médecine en 1973.",
        },
      },
      {
        h: 'Un parfum pour tout dire',
        p: [
          "Au-delà de la danse, les abeilles se parlent par phéromones — des messages chimiques. La reine diffuse une phéromone qui apaise et unit la colonie ; une abeille qui pique libère une phéromone d'alarme qui mobilise les gardiennes ; une autre, à l'entrée, bat des ailes pour diffuser un parfum de ralliement.",
        ],
      },
    ],
  },

  {
    slug: 'pollinisation',
    nav: 'La pollinisation',
    icon: 'mdi-flower-pollen',
    eyebrow: 'Écologie',
    title: 'Les gardiennes de nos assiettes',
    lead: "En butinant, l'abeille transporte le pollen de fleur en fleur et féconde les plantes. Sans elle, nos vergers et nos champs seraient bien vides.",
    hero: ['#f0a93a', '#cf7420'],
    sections: [
      {
        h: 'Un service rendu à la nature',
        p: [
          "Pour se nourrir, l'abeille récolte nectar et pollen. En passant d'une fleur à l'autre, elle dépose au passage des grains de pollen : c'est la pollinisation, l'étape qui permet aux plantes de produire fruits et graines. Un seul aller-retour peut féconder des dizaines de fleurs.",
        ],
        stats: [
          { v: '~75 %', l: 'des cultures alimentaires aidées' },
          { v: '1/3', l: 'de notre alimentation' },
          { v: '3 km', l: 'de rayon de butinage' },
        ],
      },
      {
        h: 'Pommes, amandes, courges… et bien plus',
        p: [
          "Pommiers, cerisiers, amandiers, colza, tournesol, courges, fraises, melons : d'innombrables cultures dépendent des pollinisateurs pour donner des récoltes abondantes et de qualité. Les abeilles, sauvages comme domestiques, sont au cœur de cet équilibre — un service écologique gratuit et irremplaçable.",
        ],
      },
    ],
  },

  {
    slug: 'biodiversite',
    nav: 'Abeilles & nature',
    icon: 'mdi-sprout',
    eyebrow: 'Environnement',
    title: 'Une sentinelle de la biodiversité',
    lead: "L'abeille ne fait pas que du miel : elle tisse des liens entre les plantes, les animaux et les paysages. Sa santé raconte celle de notre environnement.",
    hero: ['#a7c957', '#6a994e'],
    sections: [
      {
        h: 'Un maillon qui en soutient beaucoup d\'autres',
        p: [
          "En pollinisant les plantes sauvages, les abeilles entretiennent les prairies, les haies et les forêts qui nourrissent et abritent oiseaux, mammifères et autres insectes. Là où les fleurs prospèrent, toute une chaîne de vie prospère avec elles.",
        ],
        quote: "Là où l'abeille disparaît, c'est tout un tissu vivant qui se défait.",
      },
      {
        h: 'Un indicateur de la santé des milieux',
        p: [
          "Sensibles aux pesticides, à la pollution et au manque de fleurs, les abeilles réagissent vite à la dégradation de leur environnement. Suivre leurs colonies, c'est prendre le pouls de la nature qui nous entoure — et c'est justement ce que fait, au quotidien, notre association.",
        ],
      },
    ],
  },

  {
    slug: 'du-nectar-au-miel',
    nav: 'Du nectar au miel',
    icon: 'mdi-beehive-outline',
    eyebrow: 'Fabrication',
    title: 'Du nectar au pot de miel',
    lead: "Le miel n'est pas récolté tout fait : c'est le fruit d'un long travail de transformation, de bouche en bouche et d'aile en aile.",
    hero: ['#f6ad3c', '#d98324'],
    sections: [
      {
        h: 'Une transformation collective',
        p: [
          "La butineuse aspire le nectar, riche en eau et en saccharose, et le stocke dans son jabot. De retour à la ruche, elle le transmet aux ouvrières « receveuses » qui le passent de bouche en bouche. À chaque échange, des enzymes découpent le saccharose en sucres simples. Le nectar est ensuite déposé en fine couche dans les alvéoles.",
        ],
        li: [
          "Le nectar contient 70 à 80 % d'eau au départ.",
          "Les abeilles ventilent pour évaporer l'excès d'eau, jusqu'à moins de 18 %.",
          "Quand le miel est mûr, l'alvéole est fermée d'un opercule de cire.",
        ],
      },
      {
        h: 'La récolte de l\'apiculteur',
        p: [
          "L'apiculteur ne récolte que le surplus des hausses, en laissant à la colonie de quoi passer l'hiver. Les cadres operculés sont désoperculés, puis extraits par centrifugation. Le miel est filtré, laissé à décanter, puis mis en pot — sans cuisson ni ajout.",
        ],
        note: {
          title: 'Un trésor d\'énergie',
          text: "Pour produire un seul kilo de miel, les butineuses visitent plusieurs millions de fleurs et parcourent l'équivalent de plusieurs fois le tour de la Terre.",
        },
      },
    ],
  },

  {
    slug: 'chimie-du-miel',
    nav: 'La chimie du miel',
    icon: 'mdi-flask',
    eyebrow: 'Science',
    title: 'La chimie du miel',
    lead: "Sucré, acide, antibactérien, éternel : le miel est un concentré de chimie naturelle. Décryptage de sa composition et de ses pouvoirs.",
    hero: ['#e9b44c', '#c98a1f'],
    sections: [
      {
        h: 'Que contient un pot de miel ?',
        p: [
          "Le miel est avant tout une solution ultra-concentrée de sucres. Les deux principaux, le fructose et le glucose, proviennent de la découpe du saccharose du nectar par une enzyme, l'invertase. Le reste, c'est un peu d'eau et une multitude de composés en traces qui font l'arôme et la couleur.",
        ],
        li: [
          "≈ 80 % de sucres (surtout fructose ~38 % et glucose ~31 %).",
          "≈ 17 % d'eau seulement.",
          "Enzymes, acides organiques, minéraux, vitamines, arômes et pollens en traces.",
        ],
      },
      {
        h: 'Pourquoi le miel ne se périme (presque) jamais',
        p: [
          "Trois barrières protègent le miel des micro-organismes. Sa très faible teneur en eau et sa forte concentration en sucres « assèchent » les bactéries par osmose. Son acidité (pH voisin de 3,9), due à l'acide gluconique, freine leur croissance. Enfin, une enzyme apportée par l'abeille, la glucose-oxydase, libère lentement de l'eau oxygénée, un antiseptique naturel.",
        ],
        note: {
          title: 'Antibactérien naturel',
          text: "C'est cette combinaison — sucre, acidité et peroxyde d'hydrogène — qui explique l'usage ancestral du miel sur les plaies. Retrouvé intact dans des tombes égyptiennes, il était encore comestible après des millénaires.",
        },
      },
      {
        h: 'Cristallisation et fraîcheur',
        p: [
          "Un miel qui cristallise n'est pas un miel gâté : c'est le glucose qui se solidifie naturellement. Les miels riches en glucose (colza, tournesol) figent vite ; ceux riches en fructose (acacia, châtaignier) restent liquides longtemps. Un doux bain-marie tiède le rend à nouveau liquide.",
          "La qualité, elle, se lit à un marqueur : le HMF (hydroxyméthylfurfural). Il augmente avec la chaleur et le vieillissement. Un miel frais, extrait à froid et bien conservé, en contient très peu — c'est la signature d'un miel respecté.",
        ],
      },
    ],
  },

  {
    slug: 'varietes-de-miel',
    nav: 'Les variétés de miel',
    icon: 'mdi-palette',
    eyebrow: 'Dégustation',
    title: 'Mille fleurs, mille miels',
    lead: "Du miel d'acacia limpide au châtaignier corsé, chaque miel raconte un paysage et une saison. La fleur d'origine fait tout.",
    hero: ['#d98f2b', '#a5641a'],
    sections: [
      {
        h: 'Monofloral ou toutes fleurs',
        p: [
          "Quand les abeilles butinent surtout une espèce, on obtient un miel « monofloral » au caractère marqué ; sinon, un miel « toutes fleurs » (polyfloral), reflet de la flore locale. L'apiculteur oriente la récolte selon les floraisons, mais ce sont les abeilles qui choisissent leurs fleurs.",
        ],
        li: [
          "<b>Acacia</b> : très clair, liquide longtemps, doux et délicat.",
          "<b>Châtaignier</b> : foncé, corsé, légèrement amer.",
          "<b>Lavande, tilleul</b> : parfumés, typés de leur région.",
          "<b>Colza</b> : clair, doux, cristallise très vite.",
          "<b>Miellat de forêt</b> : sombre, boisé, issu non des fleurs mais du miellat des arbres.",
        ],
      },
      {
        h: 'Couleur, arôme, texture',
        p: [
          "La couleur va du presque blanc au brun foncé selon l'origine florale ; l'arôme, de la douceur florale aux notes boisées. La texture dépend de l'équilibre des sucres : riches en glucose, certains miels figent en une crème onctueuse ; riches en fructose, d'autres restent liquides des mois. Aucun n'est meilleur dans l'absolu — tout est affaire de goût.",
        ],
      },
    ],
  },

  {
    slug: 'produits-de-la-ruche',
    nav: 'Produits de la ruche',
    icon: 'mdi-jar',
    eyebrow: 'Trésors',
    title: 'Les autres trésors de la ruche',
    lead: "Le miel n'est que le plus connu. La ruche produit une pharmacie entière : cire, propolis, pollen, gelée royale.",
    hero: ['#f0a63b', '#cd7a1f'],
    sections: [
      {
        h: 'Cire, propolis, pollen, gelée royale',
        li: [
          "<b>La cire</b> : sécrétée par les jeunes ouvrières, elle bâtit les rayons. On en fait bougies et cosmétiques.",
          "<b>La propolis</b> : une résine récoltée sur les bourgeons, utilisée pour colmater et désinfecter la ruche. Antimicrobienne reconnue.",
          "<b>Le pollen</b> : la source de protéines de la colonie, riche en acides aminés et vitamines.",
          "<b>La gelée royale</b> : sécrétée par les nourrices, elle nourrit toutes les larves les premiers jours et, seule, la future reine toute sa vie.",
        ],
      },
      {
        h: 'La reine, fille de la gelée royale',
        p: [
          "Une larve d'ouvrière et une larve de reine sont génétiquement identiques. Ce qui les sépare ? La nourriture. La future reine est baignée de gelée royale en continu : c'est elle qui déclenche son développement en femelle fertile. Un exemple spectaculaire du pouvoir de l'alimentation sur le vivant.",
        ],
      },
    ],
  },

  {
    slug: 'les-menaces',
    nav: 'Les menaces',
    icon: 'mdi-alert',
    eyebrow: 'Alerte',
    title: 'Les abeilles en danger',
    lead: "Partout, les colonies s'affaiblissent. Parasites, pesticides, prédateurs et perte de fleurs : un faisceau de menaces qui se cumulent.",
    hero: ['#e07a5f', '#b5462e'],
    sections: [
      {
        h: 'Un cocktail de pressions',
        li: [
          "<b>Le varroa</b> : un acarien parasite qui affaiblit les abeilles et transmet des virus. La menace n°1 des ruchers.",
          "<b>Les pesticides</b> : certains insecticides désorientent les butineuses et déciment les colonies.",
          "<b>Le frelon asiatique</b> : un prédateur redoutable qui chasse les abeilles devant la ruche.",
          "<b>La perte de fleurs</b> : monocultures et bétonisation réduisent les ressources disponibles.",
          "<b>Le climat</b> : sécheresses et saisons déréglées perturbent floraisons et butinage.",
        ],
      },
      {
        h: 'Des colonies qui s\'effondrent',
        p: [
          "Quand ces facteurs se cumulent, des ruches entières peuvent s'effondrer en quelques semaines. Face à cela, les apiculteurs surveillent, comptent les parasites, traitent au bon moment et nourrissent si besoin. C'est un combat de tous les jours — celui que notre association mène pour ses colonies.",
        ],
      },
    ],
  },

  {
    slug: 'agir',
    nav: 'Agir',
    icon: 'mdi-hand-heart',
    eyebrow: 'Passer à l\'action',
    title: 'Comment aider les abeilles',
    lead: "Pas besoin d'être apiculteur pour agir. Quelques gestes simples, à la portée de tous, font une vraie différence.",
    hero: ['#8ac926', '#5a923e'],
    sections: [
      {
        h: 'Au jardin, sur le balcon',
        li: [
          "Semer des fleurs mellifères et variées, qui fleurissent du printemps à l'automne.",
          "Laisser un coin de nature libre : herbes hautes, ronces, fleurs sauvages.",
          "Proscrire les pesticides et désherbants chimiques.",
          "Offrir un point d'eau peu profond avec des cailloux pour que les abeilles s'y posent.",
        ],
      },
      {
        h: 'Au quotidien',
        li: [
          "Acheter le miel de producteurs locaux, qui soutiennent des ruchers de proximité.",
          "Préserver les haies et les arbres à floraison (tilleul, saule, châtaignier…).",
          "Faire connaître le rôle des pollinisateurs autour de soi.",
          "Soutenir les associations apicoles — comme la nôtre.",
        ],
        note: {
          title: 'Un geste utile',
          text: "Un simple carré de fleurs sauvages non traité peut nourrir des centaines de butineuses tout l'été.",
        },
      },
    ],
  },

  {
    slug: 'apiculture',
    nav: "L'apiculture",
    icon: 'mdi-account-hard-hat',
    eyebrow: 'Savoir-faire',
    title: "L'apiculture au fil des saisons",
    lead: "Accompagner une colonie, ce n'est pas la commander : c'est l'observer, la protéger et récolter avec mesure. Le rythme est donné par les fleurs.",
    hero: ['#e9a13c', '#c1741d'],
    sections: [
      {
        h: 'Une année au rucher',
        li: [
          "<b>Printemps</b> : la colonie explose, l'apiculteur pose les hausses et surveille l'essaimage.",
          "<b>Été</b> : c'est la miellée et la récolte du surplus.",
          "<b>Automne</b> : traitement contre le varroa et préparation de l'hivernage.",
          "<b>Hiver</b> : la colonie se met en grappe ; on la laisse au repos, on veille de loin.",
        ],
      },
      {
        h: 'Notre rucher au bord du canal',
        p: [
          "Notre association veille sur ses ruches le long du canal de la Croix Bonnet, à Bois-d'Arcy — un site calme et fleuri, idéal pour la santé des colonies. Visites, suivi sanitaire, récoltes et registres : tout est consigné dans notre application, pour prendre soin des abeilles avec méthode et transparence.",
        ],
        note: {
          title: 'Cadre réglementaire',
          text: "En France, toute personne possédant des ruches doit les déclarer chaque année et tenir un registre d'élevage. Une exigence que nous respectons scrupuleusement.",
        },
      },
    ],
  },

  {
    slug: 'histoire-apiculture',
    nav: "Histoire de l'apiculture",
    icon: 'mdi-history',
    eyebrow: 'Patrimoine',
    title: "Une histoire vieille de 9 000 ans",
    lead: "Bien avant d'élever les abeilles, l'humanité a chassé leur miel. Des peintures rupestres aux ruches modernes, une longue aventure commune.",
    hero: ['#b98a3e', '#7c5a22'],
    sections: [
      {
        h: 'Des chasseurs de miel aux premières ruches',
        p: [
          "Il y a près de 9 000 ans, des peintures rupestres montrent déjà des hommes récoltant le miel d'essaims sauvages. Les Égyptiens de l'Antiquité élevaient les abeilles dans des ruches de terre cuite et transportaient leurs colonies le long du Nil. Au Moyen Âge, on utilisait des paniers de paille tressée, les « ruches-paniers ».",
        ],
      },
      {
        h: 'La révolution de la ruche moderne',
        p: [
          "En 1851, l'Américain Lorenzo Langstroth comprend qu'en laissant un espace précis entre les cadres — l'« espace abeille » —, celles-ci ne les collent plus. Il invente la ruche à cadres mobiles : on peut désormais visiter la colonie et récolter le miel sans détruire les rayons. C'est la naissance de l'apiculture moderne, dont nos ruches Dadant sont les héritières.",
        ],
        note: {
          title: 'Un héritage vivant',
          text: "Les ruches à cadres mobiles que nous utilisons aujourd'hui découlent directement de cette découverte du XIXᵉ siècle.",
        },
      },
    ],
  },

  {
    slug: 'en-chiffres',
    nav: 'En chiffres',
    icon: 'mdi-counter',
    eyebrow: 'Vertige',
    title: 'Les abeilles en chiffres',
    lead: "Quelques nombres pour mesurer le prodige : une colonie est une véritable usine vivante.",
    hero: ['#f2b134', '#d38a1c'],
    sections: [
      {
        h: 'Le prodige en un coup d\'œil',
        stats: [
          { v: '60 000', l: 'abeilles dans une ruche en été' },
          { v: '2 000', l: "œufs pondus par la reine chaque jour" },
          { v: '4 M', l: 'de fleurs pour 1 kg de miel' },
          { v: '200/s', l: "battements d'ailes par seconde" },
          { v: '~7 km/h', l: 'vitesse de vol en charge' },
          { v: '1/12', l: "de cuillère de miel produite par une abeille dans sa vie" },
        ],
      },
      {
        h: 'Petite mais vertigineuse',
        p: [
          "Pour remplir un seul pot de miel, la colonie mobilise des centaines de butineuses qui, ensemble, parcourent des distances astronomiques et visitent des millions de fleurs. Derrière chaque cuillère se cache le travail patient de tout un peuple.",
        ],
      },
    ],
  },
]

export const chaptersBySlug = Object.fromEntries(chapters.map((c) => [c.slug, c]))
