// Questions du quiz « Connaissez-vous les abeilles ? »
// answer = index de la bonne réponse dans options.

export const quizQuestions = [
  {
    q: "Combien de temps met une ouvrière pour passer de l'œuf à l'adulte ?",
    options: ['16 jours', '21 jours', '24 jours', '30 jours'],
    answer: 1,
    explain: "Une ouvrière se développe en 21 jours. La reine met 16 jours, le faux-bourdon 24.",
  },
  {
    q: 'Quelle est la forme des alvéoles de cire ?',
    options: ['Le carré', 'Le triangle', "L'hexagone", 'Le cercle'],
    answer: 2,
    explain: "L'hexagone pave l'espace sans vide en utilisant le minimum de cire : la forme la plus économe.",
  },
  {
    q: 'Que communique la « danse frétillante » d\'une butineuse ?',
    options: ["L'âge de la reine", 'La direction et la distance d\'une source', 'La météo', 'Le niveau de miel'],
    answer: 1,
    explain: "L'angle indique la direction par rapport au soleil, la durée du frétillement la distance. Von Frisch a reçu le Nobel pour cette découverte.",
  },
  {
    q: 'Quel parasite menace le plus les colonies ?',
    options: ['Le frelon européen', 'La fourmi', 'Le varroa', 'La guêpe'],
    answer: 2,
    explain: "Le varroa, un acarien, affaiblit les abeilles et transmet des virus. C'est la menace n°1 des ruchers.",
  },
  {
    q: 'De quoi le miel est-il majoritairement composé ?',
    options: ['De protéines', 'De sucres (fructose et glucose)', 'De cire', 'De pollen'],
    answer: 1,
    explain: "Le miel est à ~80 % des sucres — surtout fructose et glucose — et ne contient que ~17 % d'eau.",
  },
  {
    q: 'Combien d\'œufs une reine peut-elle pondre par jour ?',
    options: ["Une dizaine", 'Environ 200', "Jusqu'à 2 000", '10 000'],
    answer: 2,
    explain: "En pleine saison, la reine pond jusqu'à 2 000 œufs par jour — plus que son propre poids.",
  },
  {
    q: 'Pourquoi le miel se conserve-t-il presque indéfiniment ?',
    options: ['Il est stérilisé', 'Peu d\'eau + acidité + peroxyde antibactérien', 'Il est congelé', 'Grâce au pollen'],
    answer: 1,
    explain: "Sa faible teneur en eau, son acidité et l'eau oxygénée libérée par une enzyme empêchent les micro-organismes de se développer.",
  },
  {
    q: 'Comment appelle-t-on le mâle de l\'abeille ?',
    options: ['Le bourdon', 'Le faux-bourdon', 'Le frelon', 'L\'ouvrier'],
    answer: 1,
    explain: "Le faux-bourdon est le mâle. Sa seule mission : féconder une reine lors du vol nuptial.",
  },
  {
    q: 'Qu\'est-ce qui transforme une larve ordinaire en future reine ?',
    options: ['Sa génétique', 'La gelée royale', 'La taille de l\'alvéole seule', 'La température'],
    answer: 1,
    explain: "Larve d'ouvrière et de reine sont identiques : c'est l'alimentation en gelée royale en continu qui fait la reine.",
  },
  {
    q: 'Combien d\'abeilles compte environ une ruche en été ?',
    options: ['Quelques centaines', '2 000 à 5 000', '40 000 à 60 000', 'Plus d\'un million'],
    answer: 2,
    explain: "Une colonie forte atteint 40 000 à 60 000 individus au plus fort de la saison.",
  },
  {
    q: 'Quel service écologique majeur rendent les abeilles ?',
    options: ['La décomposition', 'La pollinisation', 'La filtration de l\'eau', 'La dispersion des graines par le vent'],
    answer: 1,
    explain: "En transportant le pollen de fleur en fleur, elles fécondent les plantes. Près d'une culture sur trois en dépend.",
  },
  {
    q: 'À quelle température les abeilles maintiennent-elles le couvain ?',
    options: ['Environ 20 °C', 'Environ 28 °C', 'Environ 35 °C', 'Environ 42 °C'],
    answer: 2,
    explain: "Le couvain est régulé autour de 35 °C, été comme hiver, par ventilation ou mise en grappe.",
  },
]
