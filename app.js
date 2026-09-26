// The Voice of ADA Holders: one script for the whole site.
// Every page has the same chrome (top bar + nav); only <main> differs.
// Two languages, English and Spanish: every visible text lives in TEXT below,
// so both languages always carry the same content.
// Data comes from data.json, written by the generator from db-sync.

const TEXT = {
  en: {
    locale: 'en-US',
    sub: 'on-chain',
    nav: ['Governance actions', 'How it works', 'Recount it yourself', 'Contact', 'Disclaimer'],
    tally: (b, e) => `Tally at block ${b} · epoch ${e}`,
    footer: 'This site is a window, not the source. Every figure can be recounted from the Cardano chain. Not affiliated with or endorsed by the Cardano Foundation, IOG or Intersect.',
    mock: '<b>Mock-up.</b> The actions and figures on this page are example data, not a real tally.',
    holders: 'Wallets', ada: 'ADA',
    yes: 'Yes', no: 'No', none: 'No opinion',
    openUntil: (e, when) => `Open through epoch ${e} at the latest${when ? ' · closes by ' + when : ''}`,
    closesEarly: 'Answering stays open exactly as long as official voting does: until the start of the epoch in which the action is enacted, dropped or expires, whichever comes first.',
    outcome: { enacted: 'Enacted', ratified: 'Ratified', expired: 'Expired', dropped: 'Dropped' },
    outcomeAt: (o, e) => `${o} in epoch ${e}`,
    submitted: e => `Submitted in epoch ${e}`,
    types: { ParameterChange: 'Parameter change', HardForkInitiation: 'Hard fork', TreasuryWithdrawals: 'Treasury withdrawal', NoConfidence: 'No confidence', NewCommittee: 'Committee', NewConstitution: 'Constitution', InfoAction: 'Info action' },
    untitled: 'Untitled action',
    openTitle: 'Open now', closedTitle: 'Earlier actions',
    thTitle: 'Action', thType: 'Type', thSubmitted: 'Submitted', thOutcome: 'Outcome',
    noOpen: 'No governance action is open right now.',
    welcome: '<b>Welcome to The Voice of ADA Holders.</b> Here your voice is heard on every Cardano governance action. Answer yes, no or no opinion from your own wallet, and your answer goes on the chain, where everyone can see it and no one can remove it. One wallet, one voice.',
    noAnswers: 'No answers yet.',
    abstractTitle: 'What the proposer wrote', abstractNote: 'From the proposer\'s own document, in their words and language. Its bytes match the hash recorded on chain.',
    titleWhy: {
      unreachable: 'No title: the proposer\'s document could not be fetched.',
      rate_limited: 'No title yet: the document could not be fetched this time and will be tried again.',
      hash_mismatch: 'No title: the document at the link does not match the hash on chain, so it is not shown.',
      not_json: 'No title: the document is not in the standard format.',
      no_title: 'No title: the document does not contain one.',
      not_https: 'No title: the document link is not a secure address.',
      too_large: 'No title: the document is too large to read.',
      no_anchor: 'No title: the action carries no document.',
    },
    govId: 'Governance action ID',
    readFull: 'Read the full proposal (original language)', docHeading: 'The proposer\'s document',
    docNote: h => `The proposer's own document, in their words and original language; not translated. Its bytes match the hash recorded on chain (blake2b-256 ${h}).`,
    secAbstract: 'Abstract', secMotivation: 'Motivation', secRationale: 'Rationale', secReferences: 'References', secAuthors: 'Authors',
    close: 'Close', loading: 'Loading…', renderError: 'This page could not be drawn. Please reload; if it persists, the site is being fixed.', docMissing: 'The document could not be loaded.',
    machine: 'Machine translation from English', seeOriginal: 'Show original', original: 'Original in English', seeTranslation: 'Show translation',
    titlesMachine: 'Proposal titles are machine-translated from English.',
    groups: { 'Delegated to a DRep': 'Delegated to a DRep', 'Always abstain': 'Always abstain', 'Always no confidence': 'Always no confidence', 'No DRep chosen': 'No DRep chosen' },
    indexTitle: 'Governance actions',
    indexLead: 'Every governance action on Cardano appears here automatically. ADA holders answer yes, no or no opinion with a transaction from their own wallet. The result is counted in wallets: one wallet, one voice. The ADA behind the answers is shown underneath as a check; it does not count. This is not an official vote: an answer does not change the outcome. It shows DReps, stake pools and everyone else what ADA holders think, on the chain.',
    said: 'What the wallets answered', answered: n => `${n} wallets answered`,
    ofHolders: (n, t, p) => `${n} of ${t} wallets answered (${p})`,
    ofAda: (n, t, p) => `ADA behind them: ${n} of ${t} (${p})`,
    check: e => `ADA behind the answers${e === 'tip' ? ' (at the tally block)' : e ? ` (epoch ${e})` : ''}: a check, not counted`,
    statHolders: 'Wallets that can take part', statAda: 'Their ADA', epochShort: e => `epoch ${e}`, counting: 'counting from the chain…', statActions: 'Governance actions',
    statNote: 'Every registered stake credential counts as one wallet. One person can have more than one.',
    byDelegation: 'By delegation', byDelegationNote: 'Grouped by the DRep choice each wallet had when the action was submitted.',
    thWho: 'Delegation',
    signNote: 'This site builds one transaction and your wallet signs it; your keys never leave the wallet. Cost: the network fee, about 0.18 ADA. A later answer replaces an earlier one.',
    walletShows: 'Your wallet should show only the fee leaving it; everything else comes back to your own address. If it shows any other amount leaving, do not sign.',
    publicNote: 'Your answer is public and permanent: it stays on the chain, linked to your stake address.',
    speak: 'Let your voice be heard', sign: 'Sign with your wallet',
    alsoAnswer: 'Also answer another action',
    basketReady: n => n === 1 ? '1 answer ready' : `${n} answers ready`,
    newsLabel: 'On chain',
    news: {
      submitted: x => `New governance action: ${x.title}`,
      ratified: x => `Ratified: ${x.title}`,
      enacted: x => `Enacted: ${x.title}`,
      expired: x => `Expired: ${x.title}`,
      dropped: x => `Dropped: ${x.title}`,
      closing: x => `Answering closes ${x.when}: ${x.title}`,
      answers_day: x => x.count === 1 ? '1 answer on chain in the last 24 hours' : `${x.count} answers on chain in the last 24 hours`,
      epoch_began: x => `Epoch ${x.epoch} has begun`,
      epoch_ends: x => `Epoch ${x.epoch} ends ${x.when}`,
    },
    menu: 'Menu', connect: 'Connect wallet', connectHeading: 'Connect your wallet', disconnect: 'Disconnect',
    connectNote: 'Connecting only reads your stake key, to show your answers and whether you can answer. Nothing is signed and it costs nothing. If your wallet has several accounts, the one active when you connect is used.',
    connectFirst: 'Connect your wallet (top right) to answer.',
    notEligible: 'This wallet cannot answer on this action: its stake key was not registered before the action was submitted.',
    notEligibleShort: 'This wallet cannot answer on this action',
    eligUnknown: 'Whether this wallet may answer on this action could not be checked just now. Reload the page in a moment; until then, answering is off.',
    eligUnknownShort: 'Could not check this wallet just now',
    notLanded: (v, link) => `Sent: ${v} (${link}), but it did not reach the chain before its time ran out, so it does not count. Answer again if you want it to.`,
    noSuchAction: 'There is no governance action at this link. <a href="/">See all actions</a>.',
    noData: 'The tally could not be loaded. Please reload the page in a moment.',
    onChain: (v, link) => `Your voice is already on chain: ${v} (${link})`, onChainCounted: 'counted',
    changeMind: 'Changed your mind? Choose again and sign: your new answer replaces this one. Until then, this one counts.', onChainNot: r => `not counted: ${r}`,
    pending: (v, link) => `Sent: ${v} (${link}), counted from the next tally`,
    reasons: { 'no such action': 'no such action', 'before the action': 'sent before the action existed', 'after closing': 'sent after closing', 'not registered since before the action': 'the stake key was not registered since before the action' },
    cart: 'Your answers', added: 'Added to your answers.', changed: 'Changed in your answers.', viewAnswers: 'View your answers',
    basketEmpty: 'You have no answers yet. Choose yes, no or no opinion on an open action.',
    basketNotYet: 'Signing is switched off for the moment. Your answers are kept in this browser until it is on again.',
    signTestOn: 'Signing is switched on in this browser only (?sign=off switches it off).',
    chooseWallet: 'Sign with your wallet',
    noWallet: 'No Cardano wallet found in this browser. Install one, or open this page in your wallet\'s own browser.',
    signStep: { connect: 'Connecting to your wallet…', build: 'Building the transaction…', sign: 'Waiting for your signature in the wallet…', submit: 'Sending it to the chain…' },
    signDone: (n, link) => `Sent. ${n === 1 ? 'Your answer is' : `Your ${n} answers are`} in transaction ${link}. It counts in the first tally after it is in a block, usually within a quarter of an hour.`,
    signErr: {
      declined: w => `${w} did not sign.`,
      wrongNet: w => `${w} is not on Cardano mainnet.`,
      noStake: w => `${w} has no stake key for this account. Only a wallet with a stake key can answer.`,
      script: w => `The stake credential of this ${w} account is a script, such as a multisig. Those cannot answer.`,
      closing: () => 'Official voting on one of these actions closes too soon to send an answer.',
      epochEdge: () => 'A new epoch starts within five minutes. Please sign once it has started.',
      noFunds: w => `There is not enough ADA in this ${w} account for the fee.`,
      noStakeSig: w => `${w} signed without the stake key, so the chain would refuse this answer.`,
      missingSig: w => `${w} did not sign for all the funds the transaction uses.`,
      submitFailed: w => `${w} could not send the transaction.`,
      feeShort: w => `${w} signed a transaction larger than its fee covers, so the chain would refuse it.`,
      failed: w => `Something went wrong with ${w}.`,
      walletChanged: w => `${w} is now on another account than the one connected here. Connect again.`,
    },
    nothingSent: 'Nothing was sent, and your answers are still here.',
    remove: 'Remove', clearAll: 'Clear all', allAnswered: 'You have an answer ready for every open action.',
    signFromBasket: 'Your choice goes into your answers, under “Your answers” at the top of the page. All of them are signed there together, with one signature.',
    yourAnswer: v => `Your answer: ${v}`, changeHint: 'To change it, remove it under “Your answers” at the top.',
    basketPruned: t => `Removed from your answers: “${t}”. Official voting on it has closed.`,
    whoCounts: 'Who counts',
    rulesShort: [
      ['Every stake credential', 'registered before this action was submitted, and still registered when it closes. No minimum amount, no DRep choice needed.'],
      ['Your own keys', 'ADA held on an exchange cannot send a transaction. Move it to your own wallet to take part.'],
      ['One wallet, one voice', 'The result is counted in wallets. The ADA behind the answers is shown as a check; it does not count.'],
    ],
    how: {
      title: 'How it works',
      stepsTitle: 'Step by step',
      steps: [
        ['Connect your wallet', 'Click <b>Connect wallet</b> at the top of the page. A window lists the wallets in your browser; click yours and approve in the wallet. The button then shows your wallet\'s name.'],
        ['Choose an action', 'Click <b>Governance actions</b> in the menu (on a phone: the button with three lines, top right). Under <b>Open now</b>, click the title of an action.'],
        ['Read, then answer', 'On the action page you find the result, the proposer\'s text and <b>Read the full proposal</b>. Under <b>Let your voice be heard</b>, click <b>Yes</b>, <b>No</b> or <b>No opinion</b>. A message appears: <b>Added to your answers</b>.'],
        ['Answer more, or not', 'Click <b>Also answer another action</b> to go back to the list and repeat step 3. Actions already in your answers are greyed out in the list.'],
        ['Check your answers', 'Click <b>Your answers</b> at the top of the page; the number shows how many there are. Click <b>Remove</b> next to any answer you want to take back.'],
        ['Sign', 'In the same window, click <b>Sign with your wallet</b>. Your wallet opens and shows the transaction. Check that only the fee, about 0.18 ADA, leaves your wallet; then enter your password and confirm. The site says <b>Sent</b>, with a link to the transaction.'],
        ['See it counted', 'Within about a quarter of an hour, the action shows <b>Your voice is already on chain: Yes (tx …) · counted</b>. To change your answer, go back to step 3; the latest answer counts.'],
      ],
      lead: 'DReps and stake pools have a vote in Cardano governance. The holders who lend them that power have no place to say what they think. This site gives them one, on the chain itself.',
      txTitle: 'One answer is one transaction',
      tx: 'You pick yes, no or no opinion. This site builds a transaction back to yourself that carries your answers under metadata label 1695; your wallet shows it, you sign it, and it goes on the chain. There is no account, no login and no database: the chain carries who answered, and when.',
      txFine: 'You pay only the network fee, about 0.18 ADA. Nothing is sent to anyone else.',
      who: 'Who counts',
      whoRules: [
        ['Every stake credential', 'that was registered before the governance action was submitted and stays registered until it closes, with or without a stake pool. That cannot be arranged afterwards.'],
        ['No minimum amount', 'A wallet with a single ADA counts as one voice. We exclude as few holders as possible. To send an answer you need about 1.2 ADA in the wallet: only the network fee, about 0.18 ADA, is spent; the rest comes back to you.'],
        ['No DRep choice needed', 'Wallets without a DRep are shown as their own group.'],
        ['Your own keys', 'ADA on an exchange cannot sign a transaction. That is the holder\'s choice, and it can be undone by moving it to a wallet of your own.'],
        ['A key, not a script', 'A stake credential that is a script, such as a multisig, cannot answer.'],
      ],
      shown: 'How it is shown',
      shownRules: [
        ['The chain sets the agenda', 'Every governance action appears automatically. Nobody chooses the questions.'],
        ['One wallet, one voice', 'The result is counted in wallets. In ADA an exchange is billions, in wallets it is one. The ADA is shown underneath as a check against fake wallets: many wallets with almost nothing behind them stand out.'],
        ['Multiple choice only', 'No free text, so there is nothing to moderate and nothing to remove.'],
        ['No verdicts', 'The site shows what holders said. It does not judge DReps.'],
        ['Not an official vote', 'An answer does not change the outcome of any governance action; only DReps, stake pools and the Constitutional Committee vote. It makes visible what ADA holders think. Every answer is linked to a stake key, so anyone can set it next to that wallet\'s DRep and how that DRep voted.'],
      ],
      wallets: 'Supported wallets',
      walletsText: 'Your wallet must be able to sign with your stake key. Tested with a real transaction: Eternl, Gero, Lace, Typhon and VESPR. If a wallet cannot sign with the stake key, the site says so and nothing is sent.',
      safe: 'Before you sign',
      safeRules: [
        ['Only the fee leaves', 'Your wallet should show about 0.18 ADA leaving as the fee, and everything else coming back to your own address. If it shows any other amount leaving, do not sign.'],
        ['No seed phrase, ever', 'This site never asks for your seed phrase or recovery words. Only your wallet asks for its password, in its own window.'],
        ['Check the address', 'This site is at https://voiceofadaholders.com. A copy elsewhere could build a different transaction.'],
        ['Public and permanent', 'An answer stays on the chain for good, linked to your stake address. Anyone can see how that wallet answered, together with its balance and its DRep choice.'],
      ],
    },
    disclaimer: {
      title: 'Disclaimer',
      items: [
        ['Not an official vote', 'The Voice of ADA Holders shows what ADA holders answer. An answer has no effect on the outcome of any governance action, and nothing on this site is legal, financial or investment advice.'],
        ['Figures as they are', 'Every figure is read from the Cardano chain and can be recounted by anyone. We take care to count correctly, but we give no guarantee that the figures, titles, summaries or translations are complete, correct or current. Proposal documents are written by their proposers, not by us; machine translations can contain mistakes.'],
        ['Your wallet, your transaction', 'This site never holds your keys, never asks for your seed phrase, and never signs for you. You sign every transaction yourself, in your own wallet, and you pay its fee. A transaction on the chain is public and permanent; it cannot be withdrawn. Check what your wallet shows before you sign.'],
        ['Privacy', 'This site sets no cookies, uses no analytics and loads nothing from third parties. It keeps no user data: your language, your connected wallet and your unsigned answers are stored in your own browser only, and never sent to us. The server keeps a standard access log (time, page, browser type; no IP addresses), deleted after about two weeks. Your answers themselves are public on the chain.'],
        ['Availability', 'The site may be changed, interrupted or taken offline at any time, without notice.'],
        ['Open source', u => `The source code of this site and of the program that counts the answers is published on GitHub (${u}), so that anyone can check how every figure is made.`],
        ['Liability', 'You use this site at your own risk. To the extent the law allows, we accept no liability for any loss or damage arising from its use, from the figures it shows, or from a transaction you sign.'],
        ['Not affiliated', 'Not affiliated with or endorsed by the Cardano Foundation, IOG or Intersect. Spanish law applies.'],
      ],
    },
    contact: {
      title: 'Contact',
      text: m => `In case you have any questions or comments feel free to contact us on ${m}`,
    },
    recount: {
      title: 'Recount it yourself',
      lead: 'This site is a window, not the source. Every figure on it can be rebuilt from the Cardano chain by anyone, without asking us.',
      reads: 'What a tally reads', thFrom: 'From the chain', thFor: 'Used for',
      rows: [
        ['Governance actions and their submission slot', 'The agenda, and the moment that decides who counts'],
        ['Transactions under metadata label 1695', 'The answers; the latest per action and stake credential wins'],
        ['Stake credential registration', 'Who counts: every credential registered before the action and until it closes'],
        ['Address balances and withdrawable rewards per credential', 'The ADA shown as a check'],
        ['DRep delegation per credential, when the action was submitted', 'The groups by delegation'],
      ],
      block: 'Every tally states the block height it was taken at, so two recounts at the same block must agree.',
      tool: 'The counting tool',
      toolText: 'The generator that produces this site\'s figures can run against your own db-sync. A competing window on the same label is welcome: it is what keeps this one honest.',
      tba: 'The code is not public yet.',
      published: u => `The code is public: ${u}`,
      formatTitle: 'The record',
      format: 'Every answer is a transaction with this under metadata label 1695: <code>{ 0: 1, 1: [0, stake key hash], 2: [ [[action tx hash, index], choice], … ] }</code>, where the choice is 0 for no, 1 for yes and 2 for no opinion, as in the ledger. The stake key hash must be in the transaction\'s required signers, so the chain itself checks that the wallet signed. An answer counts if the action was submitted before it, if it is in a block before the action closes, and if the stake key was registered from before the action until it closes. Per action and stake key, only the latest answer counts.',
      filesTitle: 'Published with every tally',
      files: [
        ['data.json', 'The tally: every action, its closing time and the counts'],
        ['answers.json', 'Every answer per stake key hash, whether it counts, and if not, why'],
        ['elig/&lt;first 3 hex&gt;.json', 'For every registered stake key, db-sync\'s number for the transaction of its current registration; a key may answer on an action whose <code>pos</code> in data.json is higher'],
      ],
    },
  },

  es: {
    locale: 'es-ES',
    sub: 'en la cadena',
    nav: ['Acciones de gobernanza', 'Cómo funciona', 'Recuéntalo tú mismo', 'Contacto', 'Aviso legal'],
    tally: (b, e) => `Recuento en el bloque ${b} · época ${e}`,
    footer: 'Este sitio es una ventana, no la fuente. Cada cifra puede recontarse desde la cadena de Cardano. Sin afiliación ni respaldo de la Cardano Foundation, IOG o Intersect.',
    mock: '<b>Maqueta.</b> Las acciones y cifras de esta página son datos de ejemplo, no un recuento real.',
    holders: 'Billeteras', ada: 'ADA',
    yes: 'Sí', no: 'No', none: 'Sin opinión',
    openUntil: (e, when) => `Abierta como muy tarde hasta el final de la época ${e}${when ? ' · cierra a más tardar el ' + when : ''}`,
    closesEarly: 'Se puede responder exactamente mientras se puede votar oficialmente: hasta el inicio de la época en que la acción se promulga, se descarta o expira, lo que ocurra primero.',
    outcome: { enacted: 'Promulgada', ratified: 'Ratificada', expired: 'Expirada', dropped: 'Descartada' },
    outcomeAt: (o, e) => `${o} en la época ${e}`,
    submitted: e => `Presentada en la época ${e}`,
    types: { ParameterChange: 'Cambio de parámetros', HardForkInitiation: 'Hard fork', TreasuryWithdrawals: 'Retiro de la tesorería', NoConfidence: 'Moción de censura', NewCommittee: 'Comité', NewConstitution: 'Constitución', InfoAction: 'Acción informativa' },
    untitled: 'Acción sin título',
    openTitle: 'Abiertas ahora', closedTitle: 'Acciones anteriores',
    thTitle: 'Acción', thType: 'Tipo', thSubmitted: 'Presentada', thOutcome: 'Resultado',
    noOpen: 'No hay ninguna acción de gobernanza abierta en este momento.',
    welcome: '<b>Te damos la bienvenida a The Voice of ADA Holders.</b> Aquí se escucha tu voz en cada acción de gobernanza de Cardano. Responde sí, no o sin opinión desde tu propia billetera, y tu respuesta queda en la cadena, donde todos pueden verla y nadie puede borrarla. Una billetera, una voz.',
    noAnswers: 'Todavía no hay respuestas.',
    abstractTitle: 'Lo que escribió el proponente', abstractNote: 'Del propio documento del proponente, con sus palabras y en su idioma. Sus bytes coinciden con el hash registrado en la cadena.',
    titleWhy: {
      unreachable: 'Sin título: no se pudo obtener el documento del proponente.',
      rate_limited: 'Aún sin título: esta vez no se pudo obtener el documento; se volverá a intentar.',
      hash_mismatch: 'Sin título: el documento del enlace no coincide con el hash de la cadena, por eso no se muestra.',
      not_json: 'Sin título: el documento no tiene el formato estándar.',
      no_title: 'Sin título: el documento no contiene uno.',
      not_https: 'Sin título: el enlace del documento no es una dirección segura.',
      too_large: 'Sin título: el documento es demasiado grande para leerlo.',
      no_anchor: 'Sin título: la acción no lleva ningún documento.',
    },
    govId: 'ID de la acción de gobernanza',
    readFull: 'Leer la propuesta completa (idioma original)', docHeading: 'El documento del proponente',
    docNote: h => `El propio documento del proponente, con sus palabras y en su idioma original; no se traduce. Sus bytes coinciden con el hash registrado en la cadena (blake2b-256 ${h}).`,
    secAbstract: 'Resumen', secMotivation: 'Motivación', secRationale: 'Justificación', secReferences: 'Referencias', secAuthors: 'Autores',
    close: 'Cerrar', loading: 'Cargando…', renderError: 'Esta página no se pudo mostrar. Vuelve a cargarla; si persiste, se está corrigiendo el sitio.', docMissing: 'No se pudo cargar el documento.',
    machine: 'Traducción automática del inglés', seeOriginal: 'Ver original', original: 'Original en inglés', seeTranslation: 'Ver traducción',
    titlesMachine: 'Los títulos de las propuestas están traducidos automáticamente del inglés.',
    groups: { 'Delegated to a DRep': 'Delegada en un DRep', 'Always abstain': 'Abstención permanente', 'Always no confidence': 'Siempre sin confianza', 'No DRep chosen': 'Sin DRep elegido' },
    indexTitle: 'Acciones de gobernanza',
    indexLead: 'Cada acción de gobernanza de Cardano aparece aquí automáticamente. Los poseedores de ADA responden sí, no o sin opinión con una transacción desde su propia billetera. El resultado se cuenta en billeteras: una billetera, una voz. El ADA detrás de las respuestas se muestra debajo como control; no cuenta. Esto no es una votación oficial: una respuesta no cambia el resultado. Muestra a los DReps, a los pools de stake y a todos lo que piensan los poseedores de ADA, en la cadena.',
    said: 'Lo que respondieron las billeteras', answered: n => `${n} billeteras respondieron`,
    ofHolders: (n, t, p) => `${n} de ${t} billeteras respondieron (${p})`,
    ofAda: (n, t, p) => `ADA detrás: ${n} de ${t} (${p})`,
    check: e => `ADA detrás de las respuestas${e === 'tip' ? ' (en el bloque del recuento)' : e ? ` (época ${e})` : ''}: un control, no cuenta`,
    statHolders: 'Billeteras que pueden participar', statAda: 'ADA en estas billeteras', epochShort: e => `época ${e}`, counting: 'contando desde la cadena…', statActions: 'Acciones de gobernanza',
    statNote: 'Cada credencial de stake registrada cuenta como una billetera. Una persona puede tener más de una.',
    byDelegation: 'Por delegación', byDelegationNote: 'Agrupadas según la delegación que tenía cada billetera cuando se presentó la acción.',
    thWho: 'Delegación',
    signNote: 'Este sitio construye una sola transacción y tu billetera la firma; tus claves nunca salen de la billetera. Solo cuesta la comisión de la red, unos 0,18 ADA. Una respuesta posterior reemplaza a la anterior.',
    walletShows: 'Tu billetera debe mostrar que solo sale la comisión; todo lo demás vuelve a tu propia dirección. Si muestra que sale cualquier otra cantidad, no firmes.',
    publicNote: 'Tu respuesta es pública y permanente: queda en la cadena, vinculada a tu dirección de stake.',
    speak: 'Haz oír tu voz', sign: 'Firmar con tu billetera',
    alsoAnswer: 'Responder también a otra acción',
    basketReady: n => n === 1 ? '1 respuesta lista' : `${n} respuestas listas`,
    newsLabel: 'En la cadena',
    news: {
      submitted: x => `Nueva acción de gobernanza: ${x.title}`,
      ratified: x => `Ratificada: ${x.title}`,
      enacted: x => `Promulgada: ${x.title}`,
      expired: x => `Expirada: ${x.title}`,
      dropped: x => `Descartada: ${x.title}`,
      closing: x => `Se puede responder hasta el ${x.when}: ${x.title}`,
      answers_day: x => x.count === 1 ? '1 respuesta en la cadena en las últimas 24 horas' : `${x.count} respuestas en la cadena en las últimas 24 horas`,
      epoch_began: x => `Ha empezado la época ${x.epoch}`,
      epoch_ends: x => `La época ${x.epoch} termina el ${x.when}`,
    },
    menu: 'Menú', connect: 'Conectar billetera', connectHeading: 'Conecta tu billetera', disconnect: 'Desconectar',
    connectNote: 'Conectar solo lee tu clave de stake, para mostrar tus respuestas y si puedes responder. No se firma nada y no cuesta nada. Si tu billetera tiene varias cuentas, se usa la que está activa al conectar.',
    connectFirst: 'Conecta tu billetera (arriba a la derecha) para responder.',
    notEligible: 'Esta billetera no puede responder a esta acción: su clave de stake no estaba registrada antes de presentarse la acción.',
    notEligibleShort: 'Esta billetera no puede responder a esta acción',
    eligUnknown: 'No se pudo comprobar ahora si esta billetera puede responder a esta acción. Vuelve a cargar la página en un momento; mientras tanto, responder está desactivado.',
    eligUnknownShort: 'No se pudo comprobar esta billetera ahora',
    notLanded: (v, link) => `Enviada: ${v} (${link}), pero no llegó a la cadena antes de que venciera su plazo, así que no cuenta. Responde de nuevo si quieres que cuente.`,
    noSuchAction: 'No hay ninguna acción de gobernanza en este enlace. <a href="/">Ver todas las acciones</a>.',
    noData: 'No se pudo cargar el recuento. Vuelve a cargar la página en un momento.',
    onChain: (v, link) => `Tu voz ya está en la cadena: ${v} (${link})`, onChainCounted: 'contada',
    changeMind: '¿Cambiaste de opinión? Elige de nuevo y firma: tu nueva respuesta reemplaza a esta. Hasta entonces, cuenta esta.', onChainNot: r => `no contada: ${r}`,
    pending: (v, link) => `Enviada: ${v} (${link}), cuenta desde el próximo recuento`,
    reasons: { 'no such action': 'no existe esa acción', 'before the action': 'enviada antes de existir la acción', 'after closing': 'enviada después del cierre', 'not registered since before the action': 'la clave de stake no estaba registrada desde antes de la acción' },
    cart: 'Tus respuestas', added: 'Añadida a tus respuestas.', changed: 'Cambiada en tus respuestas.', viewAnswers: 'Ver tus respuestas',
    basketEmpty: 'Aún no tienes respuestas. Elige sí, no o sin opinión en una acción abierta.',
    basketNotYet: 'Firmar está desactivado por el momento. Tus respuestas se guardan en este navegador hasta que vuelva a estar activo.',
    signTestOn: 'La firma está activada solo en este navegador (?sign=off la desactiva).',
    chooseWallet: 'Firmar con tu billetera',
    noWallet: 'No se encontró ninguna billetera de Cardano en este navegador. Instala una, o abre esta página en el navegador de tu billetera.',
    signStep: { connect: 'Conectando con tu billetera…', build: 'Construyendo la transacción…', sign: 'Esperando tu firma en la billetera…', submit: 'Enviándola a la cadena…' },
    signDone: (n, link) => `Enviado. ${n === 1 ? 'Tu respuesta está' : `Tus ${n} respuestas están`} en la transacción ${link}. Cuenta en el primer recuento después de entrar en un bloque, normalmente en un cuarto de hora.`,
    signErr: {
      declined: w => `${w} no firmó.`,
      wrongNet: w => `${w} no está en la red principal de Cardano.`,
      noStake: w => `${w} no tiene clave de stake para esta cuenta. Solo una billetera con clave de stake puede responder.`,
      script: w => `La credencial de stake de esta cuenta de ${w} es un script, como una multifirma. Esas no pueden responder.`,
      closing: () => 'La votación oficial de una de estas acciones cierra demasiado pronto para enviar una respuesta.',
      epochEdge: () => 'Una nueva época empieza en menos de cinco minutos. Firma cuando haya empezado.',
      noFunds: w => `No hay suficiente ADA en esta cuenta de ${w} para la comisión.`,
      noStakeSig: w => `${w} firmó sin la clave de stake, así que la cadena rechazaría esta respuesta.`,
      missingSig: w => `${w} no aportó la firma de todos los fondos que usa la transacción.`,
      submitFailed: w => `${w} no pudo enviar la transacción.`,
      feeShort: w => `${w} firmó una transacción más grande de lo que cubre su comisión, así que la cadena la rechazaría.`,
      failed: w => `Algo salió mal con ${w}.`,
      walletChanged: w => `${w} está ahora en una cuenta distinta de la conectada aquí. Conéctala de nuevo.`,
    },
    nothingSent: 'No se envió nada, y tus respuestas siguen aquí.',
    remove: 'Quitar', clearAll: 'Quitar todas', allAnswered: 'Tienes una respuesta lista para cada acción abierta.',
    signFromBasket: 'Tu elección pasa a tus respuestas, en “Tus respuestas” arriba en la página. Allí se firman todas juntas, con una sola firma.',
    yourAnswer: v => `Tu respuesta: ${v}`, changeHint: 'Para cambiarla, quítala en “Tus respuestas” arriba.',
    basketPruned: t => `Quitada de tus respuestas: “${t}”. La votación oficial ya cerró.`,
    whoCounts: 'Quién cuenta',
    rulesShort: [
      ['Toda credencial de stake', 'registrada antes de que se presentara esta acción, y aún registrada cuando cierra. Sin cantidad mínima y sin necesidad de haber elegido un DRep.'],
      ['Tus propias claves', 'El ADA guardado en un exchange no puede enviar una transacción. Pásalo a tu propia billetera para participar.'],
      ['Una billetera, una voz', 'El resultado se cuenta en billeteras. El ADA detrás de las respuestas se muestra como control; no cuenta.'],
    ],
    how: {
      title: 'Cómo funciona',
      stepsTitle: 'Paso a paso',
      steps: [
        ['Conecta tu billetera', 'Haz clic en <b>Conectar billetera</b>, arriba en la página. Una ventana muestra las billeteras de tu navegador; haz clic en la tuya y aprueba la conexión en la billetera. El botón muestra entonces el nombre de tu billetera.'],
        ['Elige una acción', 'Haz clic en <b>Acciones de gobernanza</b> en el menú (en un teléfono: el botón con tres líneas, arriba a la derecha). En <b>Abiertas ahora</b>, haz clic en el título de una acción.'],
        ['Lee y responde', 'En la página de la acción encontrarás el resultado, el texto del proponente y <b>Leer la propuesta completa</b>. En <b>Haz oír tu voz</b>, haz clic en <b>Sí</b>, <b>No</b> o <b>Sin opinión</b>. Aparece un mensaje: <b>Añadida a tus respuestas</b>.'],
        ['Responde más, o no', 'Haz clic en <b>Responder también a otra acción</b> para volver a la lista y repetir el paso 3. Las acciones que ya están en tus respuestas aparecen en gris en la lista.'],
        ['Revisa tus respuestas', 'Haz clic en <b>Tus respuestas</b>, arriba en la página; el número indica cuántas hay. Haz clic en <b>Quitar</b> junto a cualquier respuesta que quieras retirar.'],
        ['Firma', 'En la misma ventana, haz clic en <b>Firmar con tu billetera</b>. Tu billetera se abre y muestra la transacción. Comprueba que solo sale la comisión, unos 0,18 ADA; luego escribe tu contraseña y confirma. El sitio dice <b>Enviado</b>, con un enlace a la transacción.'],
        ['Mira cómo se cuenta', 'En un cuarto de hora aproximadamente, la acción muestra <b>Tu voz ya está en la cadena: Sí (tx …) · contada</b>. Para cambiar tu respuesta, vuelve al paso 3; cuenta la respuesta más reciente.'],
      ],
      lead: 'Los DReps y los pools de stake tienen voto en la gobernanza de Cardano. Los poseedores que les prestan ese poder no tienen dónde decir lo que piensan. Este sitio les da ese lugar, en la propia cadena.',
      txTitle: 'Una respuesta es una transacción',
      tx: 'Eliges sí, no o sin opinión. Este sitio construye una transacción hacia tu propia billetera que lleva tus respuestas bajo la etiqueta de metadatos 1695; tu billetera la muestra, tú la firmas y queda en la cadena. No hay cuenta, ni inicio de sesión, ni base de datos: la cadena registra quién respondió y cuándo.',
      txFine: 'Solo pagas la comisión de la red, unos 0,18 ADA. No se envía nada a nadie más.',
      who: 'Quién cuenta',
      whoRules: [
        ['Toda credencial de stake', 'registrada antes de que se presentara la acción de gobernanza y que sigue registrada hasta que cierra, con o sin pool de stake. Eso no se puede hacer con efecto retroactivo.'],
        ['Sin cantidad mínima', 'Una billetera con un solo ADA cuenta como una voz. Excluimos a la menor cantidad posible de poseedores. Para enviar una respuesta necesitas unos 1,2 ADA en la billetera: solo se gasta la comisión de la red, unos 0,18 ADA; el resto vuelve a ti.'],
        ['Sin necesidad de elegir un DRep', 'Las billeteras sin DRep se muestran como un grupo propio.'],
        ['Tus propias claves', 'El ADA en un exchange no puede firmar una transacción. Es decisión del poseedor, y se revierte pasándolo a una billetera propia.'],
        ['Una clave, no un script', 'Una credencial de stake que es un script, como una multifirma, no puede responder.'],
      ],
      shown: 'Cómo se muestra',
      shownRules: [
        ['La cadena fija la agenda', 'Cada acción de gobernanza aparece automáticamente. Nadie elige las preguntas.'],
        ['Una billetera, una voz', 'El resultado se cuenta en billeteras. En ADA, un exchange suma miles de millones; en billeteras, es solo una. El ADA se muestra debajo como control contra billeteras falsas: muchas billeteras con casi nada detrás llaman la atención.'],
        ['Solo opción múltiple', 'Sin texto libre, así que no hay nada que moderar ni nada que borrar.'],
        ['Sin veredictos', 'El sitio muestra lo que dijeron los poseedores. No juzga a los DReps.'],
        ['No es una votación oficial', 'Una respuesta no cambia el resultado de ninguna acción de gobernanza; solo votan los DReps, los pools de stake y el Comité Constitucional. Hace visible lo que piensan los poseedores de ADA. Cada respuesta está vinculada a una clave de stake, así que cualquiera puede compararla con el DRep de esa billetera y con cómo votó ese DRep.'],
      ],
      wallets: 'Billeteras compatibles',
      walletsText: 'Tu billetera debe poder firmar con tu clave de stake. Probadas con una transacción real: Eternl, Gero, Lace, Typhon y VESPR. Si una billetera no puede firmar con la clave de stake, el sitio lo dice y no se envía nada.',
      safe: 'Antes de firmar',
      safeRules: [
        ['Solo sale la comisión', 'Tu billetera debe mostrar que salen unos 0,18 ADA como comisión y que todo lo demás vuelve a tu propia dirección. Si muestra que sale cualquier otra cantidad, no firmes.'],
        ['Nunca tu frase semilla', 'Este sitio nunca te pide tu frase semilla ni tus palabras de recuperación. Solo tu billetera te pide su contraseña, en su propia ventana.'],
        ['Comprueba la dirección', 'Este sitio está en https://voiceofadaholders.com. Una copia en otro lugar podría construir otra transacción.'],
        ['Pública y permanente', 'Una respuesta queda en la cadena para siempre, vinculada a tu dirección de stake. Cualquiera puede ver cómo respondió esa billetera, junto con su saldo y su elección de DRep.'],
      ],
    },
    disclaimer: {
      title: 'Aviso legal',
      items: [
        ['No es una votación oficial', 'The Voice of ADA Holders muestra lo que responden los poseedores de ADA. Una respuesta no tiene ningún efecto en el resultado de ninguna acción de gobernanza, y nada en este sitio es asesoramiento legal, financiero ni de inversión.'],
        ['Las cifras, tal como son', 'Cada cifra se lee de la cadena de Cardano y cualquiera puede recontarla. Ponemos cuidado en contar bien, pero no garantizamos que las cifras, los títulos, los resúmenes o las traducciones sean completos, correctos o actuales. Los documentos de las propuestas los escriben sus autores, no nosotros; las traducciones automáticas pueden contener errores.'],
        ['Tu billetera, tu transacción', 'Este sitio nunca guarda tus claves, nunca te pide tu frase semilla y nunca firma por ti. Tú firmas cada transacción en tu propia billetera y pagas su comisión. Una transacción en la cadena es pública y permanente; no se puede retirar. Comprueba lo que muestra tu billetera antes de firmar.'],
        ['Privacidad', 'Este sitio no usa cookies ni analítica, y no carga nada de terceros. No guarda datos de usuarios: tu idioma, tu billetera conectada y tus respuestas sin firmar se guardan solo en tu propio navegador y nunca se nos envían. El servidor guarda un registro de accesos normal (hora, página, tipo de navegador; sin direcciones IP), que se borra al cabo de unas dos semanas. Tus respuestas en sí son públicas en la cadena.'],
        ['Disponibilidad', 'El sitio puede cambiar, interrumpirse o dejar de estar disponible en cualquier momento, sin previo aviso.'],
        ['Código abierto', u => `El código fuente de este sitio y del programa que cuenta las respuestas está publicado en GitHub (${u}), para que cualquiera pueda comprobar cómo se obtiene cada cifra.`],
        ['Responsabilidad', 'Usas este sitio bajo tu propio riesgo. En la medida en que la ley lo permita, no aceptamos ninguna responsabilidad por pérdidas o daños derivados de su uso, de las cifras que muestra o de una transacción que firmes.'],
        ['Sin afiliación', 'Sin afiliación ni respaldo de la Cardano Foundation, IOG o Intersect. Se aplica la legislación española.'],
      ],
    },
    contact: {
      title: 'Contacto',
      text: m => `Si tienes preguntas o comentarios, no dudes en escribirnos a ${m}`,
    },
    recount: {
      title: 'Recuéntalo tú mismo',
      lead: 'Este sitio es una ventana, no la fuente. Cualquiera puede reconstruir cada cifra desde la cadena de Cardano, sin pedirnos permiso.',
      reads: 'Qué lee un recuento', thFrom: 'De la cadena', thFor: 'Se usa para',
      rows: [
        ['Las acciones de gobernanza y su slot de presentación', 'La agenda, y el momento que decide quién cuenta'],
        ['Las transacciones bajo la etiqueta de metadatos 1695', 'Las respuestas; vale la más reciente por acción y credencial de stake'],
        ['El registro de la credencial de stake', 'Quién cuenta: toda credencial registrada desde antes de la acción hasta que cierra'],
        ['Los saldos de las direcciones y las recompensas retirables de cada credencial', 'El ADA que se muestra como control'],
        ['La delegación en un DRep de cada credencial, cuando se presentó la acción', 'Los grupos por delegación'],
      ],
      block: 'Cada recuento indica la altura de bloque en que se hizo, así que dos recuentos en el mismo bloque deben coincidir.',
      tool: 'La herramienta de recuento',
      toolText: 'El generador que produce las cifras de este sitio puede ejecutarse contra tu propio db-sync. Una ventana competidora sobre la misma etiqueta es bienvenida: es lo que mantiene honesta a esta.',
      tba: 'El código aún no es público.',
      published: u => `El código es público: ${u}`,
      formatTitle: 'El registro',
      format: 'Cada respuesta es una transacción con esto bajo la etiqueta de metadatos 1695: <code>{ 0: 1, 1: [0, hash de la clave de stake], 2: [ [[hash de la tx de la acción, índice], elección], … ] }</code>, donde la elección es 0 para no, 1 para sí y 2 para sin opinión, como en el ledger. El hash de la clave de stake debe estar entre los firmantes requeridos de la transacción, así que la propia cadena comprueba que la billetera firmó. Una respuesta cuenta si la acción se presentó antes, si está en un bloque anterior al cierre de la acción, y si la clave de stake estuvo registrada desde antes de la acción hasta su cierre. Por acción y clave de stake, solo cuenta la respuesta más reciente.',
      filesTitle: 'Publicado con cada recuento',
      files: [
        ['data.json', 'El recuento: cada acción, su hora de cierre y las cifras'],
        ['answers.json', 'Cada respuesta por hash de clave de stake, si cuenta y, si no, por qué'],
        ['elig/&lt;3 primeros hex&gt;.json', 'Para cada clave de stake registrada, el número de db-sync de la transacción de su registro actual; una clave puede responder a una acción cuyo <code>pos</code> en data.json es mayor'],
      ],
    },
  },
};

// Addresses without .html (the server maps /how to how.html and redirects the old ones).
const PAGES = ['/', '/how', '/recount', '/contact', '/disclaimer'];
// The page's own address as in PAGES, whether it was opened as /how or /how.html.
const pagePath = () => location.pathname.replace(/\.html$/, '').replace(/^\/index$/, '/') || '/';
const onIndex = () => pagePath() === '/';
const CONTACT = 'developmentbkind@gmail.com';
// Where the source code is published. Empty until it is: then the disclaimer
// leaves out its open-source line and the recount page says it is not public.
// Filling this in makes both true at once.
const SOURCE_URL = 'https://github.com/GS1973/voice-of-ada-holders';

function currentLang() {
  let saved = null;
  try { saved = localStorage.getItem('lang'); } catch (e) { /* storage blocked */ }
  if (saved === 'en' || saved === 'es') return saved;
  return (navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
}
function setLang(l) {
  try { localStorage.setItem('lang', l); } catch (e) { /* storage blocked */ }
  location.reload();
}

const LANG = currentLang();
const T = TEXT[LANG];
document.documentElement.lang = LANG;

const fmt = n => n.toLocaleString(T.locale);
const ada = v => {
  if (v === null || v === undefined) return '-';   // no ADA snapshot yet
  const n = (x, d) => x.toLocaleString(T.locale, { minimumFractionDigits: d, maximumFractionDigits: d });
  // Spanish has no short word for a billion ("mil millones"), so it stays in millions.
  if (v >= 1e9 && LANG === 'en') return n(v / 1e9, 2) + 'B ADA';
  if (v >= 1e6) return n(v / 1e6, 1) + 'M ADA';
  if (v >= 1e3) return n(v / 1e3, 0) + 'k ADA';
  return fmt(v) + ' ADA';
};
const pct = (part, whole) => whole ? Math.round(100 * part / whole) : 0;
// Participation is often far below one percent, so it keeps two decimals there.
const share = (part, whole) => {
  const v = whole ? 100 * part / whole : 0;
  return v.toLocaleString(T.locale, { maximumFractionDigits: v < 1 ? 2 : 1 }) + '%';
};
const sum3 = t => t.yes + t.no + t.none;
const turnout = a => `${T.ofHolders(fmt(sum3(a.heads)), fmt(a.eligible.heads), share(sum3(a.heads), a.eligible.heads))}
  ${a.eligible.ada == null ? '' : `<br><span class="faint">${T.ofAda(ada(sum3(a.ada)), ada(a.eligible.ada), share(sum3(a.ada), a.eligible.ada))}</span>`}`;
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const rules = list => `<dl class="rules">${list.map(([t, d]) => `<dt>${t}</dt><dd>${d}</dd>`).join('')}</dl>`;

function chrome(data) {
  const here = pagePath();
  const stamp = data ? T.tally(fmt(data.tally.block), data.tally.epoch) : '';
  document.body.insertAdjacentHTML('afterbegin', `
    <header class="topbar">
      <a class="brand" href="/">
        <span class="brand-mark"></span>
        <span class="brand-name">The Voice of ADA Holders</span>
        <span class="brand-sub">${T.sub}</span>
      </a>
      <button class="menu-btn" data-act="menu" aria-controls="nav" aria-expanded="false" aria-label="${T.menu}" title="${T.menu}"><span></span><span></span><span></span></button>
      <span class="row-break"></span>
      <span class="spacer"></span>
      <span class="tally-stamp num">${stamp}</span>
      <span class="lang" role="group" aria-label="Language / Idioma">
        <button class="${LANG === 'en' ? 'on' : ''}" data-act="lang" data-arg="en">EN</button>
        <button class="${LANG === 'es' ? 'on' : ''}" data-act="lang" data-arg="es">ES</button>
      </span>
      <button class="btn cart" id="cart" data-act="basket" hidden></button>
      ${wallet() ? `<button class="btn ghost wallet-on" data-act="disconnect" title="${T.disconnect}">${esc(wallet().name)}<span class="wallet-stake"> · ${esc(shortStake(wallet().stake))}</span></button>`
        : `<button class="btn" data-act="connect">${T.connect}</button>`}
      <nav class="nav" id="nav">
        ${PAGES.map((p, i) => `<a href="${p}" class="${here === p || (here === '/action' && i === 0) ? 'active' : ''}">${T.nav[i]}</a>`).join('')}
      </nav>
    </header>`);
  footer();
}

// The result: wallets, one voice each. Large, and the only thing that decides.
function resultMain(t) {
  const total = sum3(t);
  const part = (cls, label, n) => `<span class="fig"><i class="${cls}"></i>${label} <b class="num">${fmt(n)}</b> <span class="num">${share(n, total)}</span></span>`;
  return `
    <div class="bar main" role="img" aria-label="${T.holders}: ${T.yes} ${pct(t.yes, total)}%, ${T.no} ${pct(t.no, total)}%, ${T.none} ${pct(t.none, total)}%">
      <span class="yes" data-w="${pct(t.yes, total)}"></span>
      <span class="no" data-w="${pct(t.no, total)}"></span>
      <span class="none" data-w="${pct(t.none, total)}"></span>
    </div>
    <div class="figs">${part('yes', T.yes, t.yes)}${part('no', T.no, t.no)}${part('none', T.none, t.none)}</div>`;
}

// The check: the ADA behind the same answers. Small, and it does not count.
// The epoch of the ADA snapshot an action's figures come from ('tip' when the
// answers' ADA was read at the tally block); a closed action keeps its own.
const adaEpochOf = a => a && 'ada_epoch' in a ? (a.ada_epoch ?? 'tip')
  : DATA && DATA.answers && DATA.answers.ada_from === 'tip' ? 'tip' : DATA && DATA.tally && DATA.tally.ada_epoch;
function resultCheck(t, a) {
  const total = sum3(t);
  return `
    <div class="check">
      <div class="check-label">${T.check(adaEpochOf(a))}</div>
      <div class="bar thin" role="img" aria-label="${T.ada}: ${T.yes} ${pct(t.yes, total)}%, ${T.no} ${pct(t.no, total)}%, ${T.none} ${pct(t.none, total)}%">
        <span class="yes" data-w="${pct(t.yes, total)}"></span>
        <span class="no" data-w="${pct(t.no, total)}"></span>
        <span class="none" data-w="${pct(t.none, total)}"></span>
      </div>
      <div class="check-figs num">${ada(t.yes)} / ${ada(t.no)} / ${ada(t.none)}</div>
    </div>`;
}

const exampleNotice = data => !data ? '' : data.example ? `<div class="notice">${T.mock}</div>`
  : `<div class="notice">${T.welcome}</div>`;
// An action is open through last_open_epoch and closes at the start of the
// next epoch; closes_at is that moment, shown in the reader's own time zone.
// dateStyle/timeStyle cannot be combined with timeZoneName (the browser throws), so the parts are named.
const closesAt = a => a.closes_at ? new Date(a.closes_at).toLocaleString(T.locale, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' }) : '';
// Open for answers until the closing time, whatever the outcome label says: a
// ratified action takes answers through its ratified epoch (answerable, from
// the generator; older data has only the status).
const isOpen = a => a.answerable ?? a.status === 'open';
const status = a => isOpen(a)
  ? (a.status === 'open' ? '' : T.outcomeAt(T.outcome[a.status] || a.status, a.status_epoch) + ' · ')
    + T.openUntil(a.last_open_epoch ?? (a.expires_epoch - 1), closesAt(a))
  : T.outcomeAt(T.outcome[a.status] || a.status, a.status_epoch);
const typeName = a => T.types[a.type] || a.type;
// Proposal texts are in the proposer's language. In another site language a
// machine translation is shown when there is one, marked as such, and the
// original is one click away (?orig=1).
const SHOW_ORIGINAL = new URLSearchParams(location.search).get('orig') === '1';
const tr = a => (!SHOW_ORIGINAL && a.i18n && a.i18n[LANG]) || null;
const titleOf = a => (tr(a) && tr(a).title) || a.title || `${T.untitled} · ${typeName(a)}`;
const abstractOf = a => (tr(a) && tr(a).abstract) || a.abstract;
const langAttr = a => tr(a) ? '' : ' lang="en"';
const anyTranslated = data => data.actions.some(a => tr(a));
// The result, or a plain line while nobody has answered.
const resultBlock = a => sum3(a.heads) === 0 ? `<p class="empty">${T.noAnswers}</p>` : resultMain(a.heads) + resultCheck(a.ada, a);
// Bar widths are set through the style object, not written into the markup:
// the Content-Security-Policy refuses style attributes.
function applyWidths() { document.querySelectorAll('[data-w]').forEach(el => { el.style.width = el.dataset.w + '%'; }); }

function renderIndex(data) {
  const open = data.actions.filter(isOpen);
  const closed = data.actions.filter(a => !isOpen(a));
  const b = basket();
  const cards = open.map(a => `
    <div class="card${b[a.id] ? ' answered' : ''}">
      ${b[a.id] ? `<p class="answered-tag">${T.yourAnswer(T[b[a.id]] || esc(b[a.id]))} · <span class="fine">${T.changeHint}</span></p>`
        : mineTag(a)}
      <div class="card-head">
        <h2${langAttr(a)}>${b[a.id] ? esc(titleOf(a)) : `<a href="/action?id=${encodeURIComponent(a.id)}">${esc(titleOf(a))}</a>`}</h2>
        <span class="tag">${esc(typeName(a))}</span>
        <span class="spacer"></span>
        <span class="meta num">${status(a)}</span>
      </div>
      ${resultBlock(a)}
      <p class="turnout num">${turnout(a)}</p>
    </div>`).join('');
  const rows = closed.map(a => `
    <tr><td${langAttr(a)}><a href="/action?id=${encodeURIComponent(a.id)}">${esc(titleOf(a))}</a></td>
      <td>${esc(typeName(a))}</td><td class="r num"><span class="wide-only">${a.submitted_epoch}</span><span class="narrow-only">${T.submitted(a.submitted_epoch)}</span></td>
      <td class="num">${status(a)}</td></tr>`).join('');
  document.querySelector('main').innerHTML = `
    ${exampleNotice(data)}
    <h1>${T.indexTitle}</h1>
    <p class="lead">${T.indexLead}</p>
    <div class="stats">
      <div class="stat"><div class="stat-label">${T.statHolders}</div><div class="stat-value num">${fmt(data.eligible.credentials)}</div></div>
      <div class="stat"><div class="stat-label">${T.statAda}${data.tally.ada_epoch ? ' · ' + T.epochShort(data.tally.ada_epoch) : ''}</div>${data.eligible.ada == null ? `<div class="stat-value pending">${T.counting}</div>` : `<div class="stat-value num">${ada(data.eligible.ada).replace(/ ADA$/, '')}</div>`}</div>
      <div class="stat"><div class="stat-label">${T.statActions}</div><div class="stat-value num">${fmt(data.actions.length)}</div></div>
    </div>
    <p class="fine">${T.statNote}${anyTranslated(data) ? ' ' + T.titlesMachine : ''}</p>
    <h2 class="section">${T.openTitle}</h2>
    ${cards || `<p class="empty">${T.noOpen}</p>`}
    ${closed.length ? `
    <h2 class="section">${T.closedTitle}</h2>
    <div class="card">
      <table class="stack">
        <thead><tr><th>${T.thTitle}</th><th>${T.thType}</th><th class="r">${T.thSubmitted}</th><th>${T.thOutcome}</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>` : ''}`;
  applyWidths();
}

function renderAction(data) {
  const id = new URLSearchParams(location.search).get('id');
  const a = data.actions.find(x => x.id === id);
  if (!a) {
    document.querySelector('main').innerHTML = `<div class="notice">${T.noSuchAction}</div>`;
    return;
  }
  const rows = a.groups.map(g => {
    const h = sum3(g.heads);
    return `<tr><td>${esc(T.groups[g.name] || g.name)}</td>
      <td class="r num" data-label="${T.holders}">${fmt(h)}</td><td class="r num" data-label="${T.yes}">${share(g.heads.yes, h)}</td><td class="r num" data-label="${T.no}">${share(g.heads.no, h)}</td>
      <td class="r num faint">${ada(sum3(g.ada))}</td></tr>`;
  }).join('');
  document.querySelector('main').innerHTML = `
    ${exampleNotice(data)}
    <p class="meta"><a href="/">${T.indexTitle}</a> / ${esc(titleOf(a))}</p>
    <h1${langAttr(a)}>${esc(titleOf(a))}</h1>
    ${a.i18n && a.i18n[LANG] ? `<p class="meta">${SHOW_ORIGINAL
      ? `${T.original} · <a href="/action?id=${encodeURIComponent(a.id)}">${T.seeTranslation}</a>`
      : `${T.machine} · <a href="/action?id=${encodeURIComponent(a.id)}&orig=1">${T.seeOriginal}</a>`}</p>` : ''}
    <p class="meta num"><span class="tag">${esc(typeName(a))}</span>&nbsp; ${T.submitted(a.submitted_epoch)} · ${status(a)}</p>
    ${a.gov_action_id ? `<p class="meta mono">${T.govId}: ${esc(a.gov_action_id)}</p>` : ''}
    ${!a.title && T.titleWhy[a.title_status] ? `<p class="meta">${T.titleWhy[a.title_status]}</p>` : ''}

    <div class="card">
      <div class="card-head"><h2>${T.said}</h2></div>
      ${resultBlock(a)}
      <p class="turnout num">${turnout(a)}</p>
    </div>

    ${a.groups.length ? `
    <div class="card">
      <div class="card-head"><h2>${T.byDelegation}</h2></div>
      <p class="fine">${T.byDelegationNote}</p>
      <div class="table-wrap"><table class="stack">
        <thead><tr><th>${T.thWho}</th><th class="r">${T.holders}</th><th class="r">${T.yes}</th><th class="r">${T.no}</th><th class="r faint">${T.ada}</th></tr></thead>
        <tbody>${rows}</tbody>
      </table></div>
    </div>` : ''}

    ${abstractOf(a) ? `
    <div class="card">
      <div class="card-head"><h2>${T.abstractTitle}</h2></div>
      <p class="proposer"${langAttr(a)}>${esc(abstractOf(a))}</p>
      <p class="fine">${T.abstractNote}</p>
      ${a.title_status === 'verified' ? `<button class="btn ghost" data-act="doc" data-arg="${esc(a.anchor_hash)}">${T.readFull}</button>` : ''}
    </div>` : ''}

    ${isOpen(a) ? `
    <div class="grid-2">
      <div class="card">
        <h2>${T.speak}</h2>
        ${mineBlock(a)}
        <div class="choices">
          ${['yes', 'no', 'none'].map(v => `<label class="choice"><input type="radio" name="c" data-act="choose" data-arg="${esc(a.id)}" value="${v}"${basket()[a.id] === v ? ' checked' : ''}${canAnswer(a) ? '' : ' disabled'}> ${T[v]}</label>`).join('')}
        </div>
        <div class="answer-actions">
          <button class="btn ghost" id="also" data-act="another"${basket()[a.id] ? '' : ' disabled'}>${T.alsoAnswer}</button>
        </div>
        <p class="fine gap">${T.signFromBasket}</p>
        <p class="fine gap">${T.signNote}</p>
        <p class="fine">${T.walletShows}</p>
        <p class="fine">${T.publicNote}</p>
        <p class="fine">${T.closesEarly}</p>
      </div>
      <div class="card">
        <h2>${T.whoCounts}</h2>
        ${rules(T.rulesShort)}
      </div>
    </div>` : ''}`;
  applyWidths();
  document.title = titleOf(a) + ' · The Voice of ADA Holders';
}

function renderHow() {
  const H = T.how;
  document.querySelector('main').innerHTML = `
    <h1>${H.title}</h1>
    <p class="lead">${H.lead}</p>
    <div class="card">
      <h2>${H.stepsTitle}</h2>
      <ol class="steps">${H.steps.map(([t, d]) => `<li><strong>${t}.</strong> ${d}</li>`).join('')}</ol>
    </div>
    <div class="card">
      <h2>${H.txTitle}</h2>
      <p>${H.tx}</p>
      <p class="fine">${H.txFine}</p>
    </div>
    <div class="grid-2">
      <div class="card"><h2>${H.who}</h2>${rules(H.whoRules)}</div>
      <div class="card"><h2>${H.shown}</h2>${rules(H.shownRules)}</div>
    </div>
    <div class="card"><h2>${H.safe}</h2>${rules(H.safeRules)}</div>
    <div class="card">
      <h2>${H.wallets}</h2>
      <p>${H.walletsText}</p>
    </div>`;
  document.title = H.title + ' · The Voice of ADA Holders';
}

function renderRecount() {
  const R = T.recount;
  document.querySelector('main').innerHTML = `
    <h1>${R.title}</h1>
    <p class="lead">${R.lead}</p>
    <div class="card">
      <h2>${R.reads}</h2>
      <table>
        <thead><tr><th>${R.thFrom}</th><th>${R.thFor}</th></tr></thead>
        <tbody>${R.rows.map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join('')}</tbody>
      </table>
      <p class="fine gap">${R.block}</p>
    </div>
    <div class="card">
      <h2>${R.formatTitle}</h2>
      <p>${R.format}</p>
    </div>
    <div class="card">
      <h2>${R.filesTitle}</h2>
      <table><tbody>${R.files.map(([f, d]) => `<tr><td><code>${f}</code></td><td>${d}</td></tr>`).join('')}</tbody></table>
    </div>
    <div class="card">
      <h2>${R.tool}</h2>
      <p>${R.toolText}</p>
      <p class="fine">${SOURCE_URL ? R.published(`<a href="${SOURCE_URL}" target="_blank" rel="noopener noreferrer">${SOURCE_URL}</a>`) : R.tba}</p>
    </div>`;
  document.title = R.title + ' · The Voice of ADA Holders';
}

function renderDisclaimer() {
  const D = T.disclaimer;
  const link = SOURCE_URL && `<a href="${SOURCE_URL}" target="_blank" rel="noopener noreferrer">${SOURCE_URL}</a>`;
  document.querySelector('main').innerHTML = `
    <h1>${D.title}</h1>
    <div class="card">${D.items.filter(([, t]) => typeof t === 'string' || link)
      .map(([h, t]) => `<p><strong>${h}.</strong> ${typeof t === 'string' ? t : t(link)}</p>`).join('')}</div>`;
  document.title = D.title + ' · The Voice of ADA Holders';
}

function renderContact() {
  const C = T.contact;
  document.querySelector('main').innerHTML = `
    <h1>${C.title}</h1>
    <div class="card"><p>${C.text(`<a href="mailto:${CONTACT}">${CONTACT}</a>`)}</p></div>`;
  document.title = C.title + ' · The Voice of ADA Holders';
}

// The proposer's document, shown whole in a dialog. It is served from this site
// (docs/<hash>.json) and was only published there after its bytes matched the
// hash on chain. The text is untrusted: every character is escaped first, and
// only a small set of Markdown is then turned into markup. Links open outside.
function mdInline(t) {
  return t
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[\s(])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>');
}

function md(text) {
  const lines = esc(text || '').replace(/\r/g, '').split('\n');
  const out = [];
  let para = [], list = null, code = null;
  const flushPara = () => { if (para.length) { out.push(`<p>${mdInline(para.join('<br>'))}</p>`); para = []; } };
  const flushList = () => { if (list) { out.push(`<${list.tag}>${list.items.map(x => `<li>${mdInline(x)}</li>`).join('')}</${list.tag}>`); list = null; } };
  for (const line of lines) {
    if (code !== null) {
      if (/^\s*```/.test(line)) { out.push(`<pre>${code.join('\n')}</pre>`); code = null; } else code.push(line);
      continue;
    }
    if (/^\s*```/.test(line)) { flushPara(); flushList(); code = []; continue; }
    let m;
    if ((m = line.match(/^\s*(#{1,6})\s+(.*)$/))) {
      flushPara(); flushList();
      const lvl = Math.min(m[1].length + 2, 6);
      out.push(`<h${lvl}>${mdInline(m[2])}</h${lvl}>`);
    } else if ((m = line.match(/^\s*([-*+]|\d+[.)])\s+(.*)$/))) {
      flushPara();
      const tag = /\d/.test(m[1]) ? 'ol' : 'ul';
      if (!list || list.tag !== tag) { flushList(); list = { tag, items: [] }; }
      list.items.push(m[2].replace(/^#{1,6}\s+/, ''));   // a heading written inside a list item
    } else if (/^\s*\|.*\|\s*$/.test(line)) {
      flushPara(); flushList();
      if (!/^\s*\|[\s:|-]+\|\s*$/.test(line)) out.push(`<div class="mdrow">${line.trim().replace(/^\||\|$/g, '').split('|').map(c => `<span>${mdInline(c.trim())}</span>`).join('')}</div>`);
    } else if ((m = line.match(/^\s*&gt;\s?(.*)$/))) {
      flushPara(); flushList();
      out.push(`<blockquote>${mdInline(m[1])}</blockquote>`);
    } else if (!line.trim()) {
      flushPara(); flushList();
    } else {
      flushList(); para.push(line);
    }
  }
  if (code !== null) out.push(`<pre>${code.join('\n')}</pre>`);
  flushPara(); flushList();
  return out.join('\n');
}

const cip = v => (v && typeof v === 'object' && '@value' in v) ? v['@value'] : v;

async function openDoc(hash) {
  const box = document.createElement('div');
  box.className = 'modal-overlay';
  box.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-label="${T.docHeading}">
      <div class="modal-head"><h2>${T.docHeading}</h2><button class="btn ghost" data-close>${T.close}</button></div>
      <div class="modal-body"><p class="fine">${T.loading}</p></div></div>`;
  const close = () => { box.remove(); document.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  const onKey = e => { if (e.key === 'Escape') close(); };
  box.addEventListener('click', e => { if (e.target === box || e.target.hasAttribute('data-close')) close(); });
  document.addEventListener('keydown', onKey);
  document.body.style.overflow = 'hidden';
  document.body.appendChild(box);
  const body = box.querySelector('.modal-body');
  let doc;
  try { doc = await (await fetch(`docs/${encodeURIComponent(hash)}.json`)).json(); }
  catch (e) { body.innerHTML = `<p class="fine">${T.docMissing}</p>`; return; }
  const b = (doc && typeof doc.body === 'object' && doc.body) || {};
  const section = (label, text) => cip(text) ? `<h3>${label}</h3><div class="md" lang="en">${md(String(cip(text)))}</div>` : '';
  const refs = Array.isArray(b.references) ? b.references.filter(r => r && /^(https?|ipfs):\/\//.test(cip(r.uri) || '')) : [];
  const authors = Array.isArray(doc.authors) ? doc.authors.map(a => cip(a && a.name)).filter(Boolean) : [];
  body.innerHTML = `
    <p class="fine">${T.docNote(esc(hash.slice(0, 16)) + '…')}</p>
    ${cip(b.title) ? `<h2 class="doc-title" lang="en">${esc(String(cip(b.title)))}</h2>` : ''}
    ${section(T.secAbstract, b.abstract)}
    ${section(T.secMotivation, b.motivation)}
    ${section(T.secRationale, b.rationale)}
    ${refs.length ? `<h3>${T.secReferences}</h3><ul>${refs.map(r => `<li><a href="${esc(cip(r.uri))}" target="_blank" rel="noopener noreferrer">${esc(String(cip(r.label) || cip(r.uri)))}</a></li>`).join('')}</ul>` : ''}
    ${authors.length ? `<h3>${T.secAuthors}</h3><p>${authors.map(n => esc(String(n))).join(', ')}</p>` : ''}`;
}

// The connected wallet: { key, name, stake } in this browser, where stake is
// the stake key hash. Connecting reads only the reward address; the wallet is
// asked again, and checked to be on the same account, when signing.
const WALLET_KEY = 'tvoah.wallet';
function wallet() {
  try { const w = JSON.parse(localStorage.getItem(WALLET_KEY)); return w && /^[0-9a-f]{56}$/.test(w.stake) ? w : null; } catch (e) { return null; }
}
function disconnectWallet() {
  try { localStorage.removeItem(WALLET_KEY); } catch (e) { /* storage blocked */ }
  location.reload();
}

// What the chain says about the connected wallet: its answers (answers.json)
// and the transaction of its current registration (elig/<first 3 hex>.json).
let MINE = { answers: {}, reg: undefined };
async function loadMine(data) {
  const w = wallet();
  if (!w || !data) { MINE = { answers: {}, reg: undefined }; return; }
  const get = async url => { try { const r = await fetch(url, { cache: 'no-cache' }); return r.ok ? await r.json() : null; } catch (e) { return null; } };
  const e = data.eligibility || { dir: 'elig', prefix: 3 };
  const [answers, shard] = await Promise.all([get('answers.json'), get(`${e.dir}/${w.stake.slice(0, e.prefix)}.json`)]);
  MINE = {
    answers: (answers && answers.credentials && answers.credentials[w.stake]) || {},
    // null: known not registered; undefined: could not be read. Then answering
    // waits: a fee paid for an answer the tally refuses is worse than a retry.
    reg: shard ? (shard[w.stake.slice(e.prefix)] ?? null) : undefined,
  };
}
const eligibleFor = a => MINE.reg !== undefined && MINE.reg !== null && MINE.reg < a.pos;
const eligUnknown = () => !!wallet() && MINE.reg === undefined;
const canAnswer = a => !!wallet() && eligibleFor(a);

// Answers sent from this browser that the tally has not picked up yet. The
// ledger takes a transaction only in a slot before its time-to-live; once the
// tally has reached that slot without it, it never landed ({ lost: true }).
// Records from before the ttl was kept had one of at most two hours.
const UNIX_MINUS_SLOT = 1591566291;                   // mainnet: slot = unix time - this
function pendingFor(a) {
  const w = wallet();
  if (!w) return null;
  let sent = [];
  try { sent = JSON.parse(localStorage.getItem('tvoah.sent')) || []; } catch (e) { /* none */ }
  const onChainTx = (MINE.answers[a.id] || {}).tx;
  for (let i = sent.length - 1; i >= 0; i--) {
    const s = sent[i];
    if (!(s.stake === w.stake && s.answers && s.answers[a.id])) continue;
    if (s.tx === onChainTx) return null;
    const ttl = s.ttl ?? Math.floor(Date.parse(s.at) / 1000) - UNIX_MINUS_SLOT + 2 * 3600;
    return DATA && DATA.tally && DATA.tally.slot >= ttl ? { ...s, lost: true } : s;
  }
  return null;
}

const txLink = tx => `<a href="https://cardanoscan.io/transaction/${esc(tx)}" target="_blank" rel="noopener noreferrer">tx ${esc(tx.slice(0, 10))}…</a>`;
function mineTag(a) {
  if (!wallet()) return '';
  if (eligUnknown()) return `<p class="answered-tag muted">${T.eligUnknownShort}</p>`;
  if (!eligibleFor(a)) return `<p class="answered-tag muted">${T.notEligibleShort}</p>`;
  const p = pendingFor(a), c = MINE.answers[a.id];
  if (p && !p.lost) return `<p class="answered-tag">${T.pending(T[p.answers[a.id]], txLink(p.tx))}</p>`;
  const lost = p ? `<p class="answered-tag muted">${T.notLanded(T[p.answers[a.id]], txLink(p.tx))}</p>` : '';
  if (c) return lost + `<p class="answered-tag">${T.onChain(T[c.choice], txLink(c.tx))} · ${c.counted ? T.onChainCounted : T.onChainNot(T.reasons[c.reason] || esc(c.reason))}</p>`;
  return lost;
}
function mineBlock(a) {
  if (!wallet()) return `<div class="connect-first"><p><strong>${T.connectFirst}</strong></p><p class="fine">${T.connectNote}</p></div>`;
  if (eligUnknown()) return `<div class="notice">${T.eligUnknown}</div>`;
  if (!eligibleFor(a)) return `<div class="notice">${T.notEligible}</div>`;
  const c = MINE.answers[a.id], p = pendingFor(a);
  return mineTag(a) + (c && c.counted && (!p || p.lost) ? `<p class="fine">${T.changeMind}</p>` : '');
}

// Bech32 (BIP-173) for showing the stake address, e.g. stake1u9…
function bech32(hrp, bytes) {
  const CH = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l', G = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
  const words = []; let acc = 0, bits = 0;
  for (const b of bytes) { acc = (acc << 8) | b; bits += 8; while (bits >= 5) { bits -= 5; words.push((acc >> bits) & 31); } }
  if (bits) words.push((acc << (5 - bits)) & 31);
  const polymod = v => { let c = 1; for (const x of v) { const t = c >> 25; c = ((c & 0x1ffffff) << 5) ^ x; for (let i = 0; i < 5; i++) if ((t >> i) & 1) c ^= G[i]; } return c; };
  const exp = [...hrp].map(c => c.charCodeAt(0) >> 5).concat([0], [...hrp].map(c => c.charCodeAt(0) & 31));
  const pm = polymod(exp.concat(words, [0, 0, 0, 0, 0, 0])) ^ 1;
  const sum = [0, 1, 2, 3, 4, 5].map(i => (pm >> (5 * (5 - i))) & 31);
  return hrp + '1' + words.concat(sum).map(w => CH[w]).join('');
}
function shortStake(hash) {
  const a = bech32('stake', [0xe1, ...hash.match(/../g).map(h => parseInt(h, 16))]);
  return a.slice(0, 11) + '…' + a.slice(-5);
}

async function connectWallet() {
  const list = typeof wallets === 'function' ? wallets() : [];
  const box = document.createElement('div');
  box.className = 'modal-overlay';
  box.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-label="${T.connectHeading}">
      <div class="modal-head"><h2>${T.connectHeading}</h2><button class="btn ghost" data-close>${T.close}</button></div>
      <div class="modal-body"></div></div>`;
  const close = () => { box.remove(); document.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  const onKey = e => { if (e.key === 'Escape') close(); };
  box.addEventListener('click', e => { if (e.target === box || e.target.hasAttribute('data-close')) close(); });
  document.addEventListener('keydown', onKey);
  document.body.style.overflow = 'hidden';
  document.body.appendChild(box);
  const body = box.querySelector('.modal-body');
  if (!list.length) { body.innerHTML = `<p>${T.noWallet}</p>`; return; }
  body.innerHTML = `<p class="fine">${T.connectNote}</p>
    <div class="wallets">${list.map(w => `<button class="btn ghost wallet" data-wallet="${esc(w.key)}">
      ${/^data:image\//.test(w.icon) ? `<img src="${esc(w.icon)}" alt="">` : ''}${esc(w.name)}</button>`).join('')}</div>`;
  body.querySelectorAll('[data-wallet]').forEach(btn => btn.addEventListener('click', async () => {
    const w = list.find(x => x.key === btn.dataset.wallet);
    body.innerHTML = `<p>${T.signStep.connect}</p>`;
    try {
      const stake = await stakeKeyOf(w.key);
      try { localStorage.setItem(WALLET_KEY, JSON.stringify({ key: w.key, name: w.name, stake })); } catch (e) { /* storage blocked */ }
      location.reload();
    } catch (e) {
      console.error(e);
      const msg = T.signErr[e.key] ? T.signErr[e.key](esc(w.name)) : T.signErr.failed(esc(w.name));
      body.innerHTML = `<p>${msg}</p>`;
    }
  }));
}

// Answers being gathered before one signature: { actionId: 'yes'|'no'|'none' }.
// Kept in this browser only (localStorage), never sent anywhere until signed.
// One basket per connected wallet; without a wallet there is nothing to answer with.
const basketKey = () => wallet() ? 'tvoah.answers.' + wallet().stake : null;
let DATA = null;

function basket() {
  if (!basketKey()) return {};
  try { return JSON.parse(localStorage.getItem(basketKey())) || {}; } catch (e) { return {}; }
}
function saveBasket(b) {
  if (!basketKey()) return;
  try { localStorage.setItem(basketKey(), JSON.stringify(b)); } catch (e) { /* storage blocked */ }
  drawBasket();
}
function choose(id, value) {
  const b = basket(), had = id in b; b[id] = value; saveBasket(b);
  toast(`${had ? T.changed : T.added} <button class="link" data-act="basket">${T.viewAnswers}</button>`);
  const also = document.getElementById('also');
  if (also) also.disabled = false;
}
function removeAnswer(id) {
  const b = basket(); delete b[id]; saveBasket(b);
  drawBasketList();
  if (DATA && onIndex()) { renderIndex(DATA); footer(); }
  document.querySelectorAll(`.choice input`).forEach(i => { if (new URLSearchParams(location.search).get('id') === id) i.checked = false; });
}
function clearAnswers() {
  saveBasket({});
  drawBasketList();
  document.querySelectorAll('.choice input').forEach(i => { i.checked = false; });
  if (DATA && onIndex()) { renderIndex(DATA); footer(); }
}

// Back to the overview, where the actions still without an answer can be chosen.
function answerAnother() { location.href = '/'; }

// An answer to an action that is no longer open cannot count: take it out and say so.
function pruneBasket(data) {
  const b = basket(), open = new Set(data.actions.filter(isOpen).map(a => a.id));
  const gone = Object.keys(b).filter(id => !open.has(id));
  if (!gone.length) return [];
  gone.forEach(id => delete b[id]);
  try { localStorage.setItem(basketKey(), JSON.stringify(b)); } catch (e) { /* storage blocked */ }
  return gone.map(id => { const a = data.actions.find(x => x.id === id); return a ? titleOf(a) : id; });
}

// The answers live behind one button in the top bar, like a shopping basket:
// a choice adds to it with a short notice, and the basket opens as a list to
// remove answers, go on answering, or sign them all at once.
function drawBasket(pruned = []) {
  const n = Object.keys(basket()).length, btn = document.getElementById('cart');
  if (btn) {
    btn.hidden = n === 0;
    btn.innerHTML = `${T.cart} <span class="cart-count num">${n}</span>`;
  }
  if (pruned.length) toast(pruned.map(t => T.basketPruned(esc(t))).join('<br>'), 9000);
}

function toast(html, ms = 4000) {
  document.querySelector('.toast')?.remove();
  const el = document.createElement('div');
  el.className = 'toast';
  el.setAttribute('role', 'status');
  el.innerHTML = html;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), ms);
}

function openBasket() {
  document.querySelector('.toast')?.remove();
  const box = document.createElement('div');
  box.className = 'modal-overlay basket-modal';
  box.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-label="${T.cart}">
      <div class="modal-head"><h2>${T.cart}</h2><button class="btn ghost" data-close>${T.close}</button></div>
      <div class="modal-body"></div></div>`;
  const close = () => { box.remove(); document.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  const onKey = e => { if (e.key === 'Escape') close(); };
  box.addEventListener('click', e => { if (e.target === box || e.target.hasAttribute('data-close')) close(); });
  document.addEventListener('keydown', onKey);
  document.body.style.overflow = 'hidden';
  document.body.appendChild(box);
  box.closeBasket = close;
  drawBasketList();
}

function drawBasketList() {
  const box = document.querySelector('.basket-modal');
  if (!box) return;
  // Signing lives in sign.js and is off until switched on in this browser.
  const SIGN_ON = typeof signingOn === 'function' && signingOn();
  const b = basket(), ids = Object.keys(b);
  const title = id => { const a = DATA && DATA.actions.find(x => x.id === id); return a ? titleOf(a) : id; };
  const openIds = DATA ? DATA.actions.filter(isOpen).map(a => a.id) : [];
  const all = openIds.length && openIds.every(id => b[id]);
  box.querySelector('.modal-body').innerHTML = !ids.length ? `<p>${T.basketEmpty}</p>
      <div class="answer-actions"><button class="btn ghost" data-act="another">${T.alsoAnswer}</button></div>` : `
    <p class="fine">${T.basketReady(ids.length)}</p>
    <ul class="basket-list">${ids.map(id => `<li>
      <a href="/action?id=${encodeURIComponent(id)}">${esc(title(id))}</a>
      <span class="basket-choice">${T[b[id]] || esc(b[id])}</span>
      <button class="link" data-act="remove" data-arg="${esc(id)}">${T.remove}</button></li>`).join('')}</ul>
    ${all ? `<p class="fine">${T.allAnswered}</p>` : ''}
    <div class="answer-actions">
      ${all ? '' : `<button class="btn ghost" data-act="another">${T.alsoAnswer}</button>`}
      <button class="btn ghost" data-act="clear">${T.clearAll}</button>
      <span class="spacer"></span>
      ${SIGN_ON ? `<button class="btn" data-act="sign">${T.sign}</button>`
        : `<button class="btn" disabled title="${T.basketNotYet}">${T.sign}</button>`}
    </div>
    ${SIGN_ON && DATA && DATA.answers_open ? '' : `<p class="fine">${SIGN_ON ? T.signTestOn : T.basketNotYet}</p>`}`;
}

// The tally is refreshed every quarter hour on the server. An open page asks
// for it every five minutes (and at once when its tab becomes visible again)
// and redraws only when the tally has moved on. A choice survives a redraw:
// it is in the basket the moment it is made, and drawn from there.
// 'no-cache': the browser asks with the file's Last-Modified date and gets a
// 304 while the tally has not moved, instead of the whole file every time.
const REFRESH_MS = 5 * 60 * 1000;

async function loadData() {
  try {
    const d = await (await fetch('data.json', { cache: 'no-cache' })).json();
    d._loadedAt = performance.now();                  // sign.js: time since, for a clock that is behind
    return d;
  } catch (e) { return null; }
}

function renderPage(page, data) {
  // A fault in drawing must not leave a white page: say so, and keep the rest.
  try {
    if (['index', 'action'].includes(page) && !data) document.querySelector('main').innerHTML = `<div class="notice">${T.noData}</div>`;
    if (page === 'index' && data) renderIndex(data);
    if (page === 'action' && data) renderAction(data);
    if (page === 'how') renderHow();
    if (page === 'recount') renderRecount();
    if (page === 'contact') renderContact();
    if (page === 'disclaimer') renderDisclaimer();
  } catch (e) {
    console.error(e);
    document.querySelector('main').innerHTML = `<div class="notice">${T.renderError}</div>`;
  }
}

// The ticker along the bottom, as on a news channel: what happened on chain
// lately (data.news, written by the generator). Nobody chooses the items. It
// pauses under the pointer or keyboard focus, and stands still for readers
// who ask their device for less motion. The run is drawn twice so that it
// loops without a gap; the copy is hidden from screen readers and the tab key.
function tickerItems(data) {
  const byId = Object.fromEntries(data.actions.map(a => [a.id, a]));
  return (data.news || []).map(n => {
    const a = n.action ? byId[n.action] : null;
    const say = T.news[n.kind];
    if (!say || (n.action && !a)) return '';
    const when = n.closes_at ? new Date(n.closes_at).toLocaleDateString(T.locale, { day: 'numeric', month: 'short' })
      : n.ends_at ? new Date(n.ends_at).toLocaleString(T.locale, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
    const alert = n.kind === 'closing';
    const text = (alert ? '⚠ ' : '') + say({ title: a ? esc(titleOf(a)) : '', count: n.count, epoch: n.epoch, when });
    const cls = alert ? ' class="ticker-alert"' : '';
    return a ? `<a${cls} href="/action?id=${encodeURIComponent(a.id)}">${text}</a>` : `<span${cls}>${text}</span>`;
  }).filter(Boolean);
}
function drawTicker(data) {
  document.querySelector('.ticker')?.remove();
  const items = data ? tickerItems(data) : [];
  document.body.classList[items.length ? 'add' : 'remove']('has-ticker');
  if (!items.length) return;
  const run = items.join('<span class="ticker-sep" aria-hidden="true">•</span>') + '<span class="ticker-sep" aria-hidden="true">•</span>';
  const copy = run.replace(/<a /g, '<a tabindex="-1" ');
  document.body.insertAdjacentHTML('beforeend', `
    <div class="ticker" role="region" aria-label="${T.newsLabel}">
      <span class="ticker-label">${T.newsLabel}</span>
      <div class="ticker-window"><div class="ticker-track">
        <div class="ticker-run">${run}</div><div class="ticker-run" aria-hidden="true">${copy}</div>
      </div></div>
    </div>`);
  // About 60 pixels a second, whatever the length.
  const first = document.querySelector('.ticker-run'), track = document.querySelector('.ticker-track');
  if (first && track) track.style.animationDuration = Math.max(20, Math.round(first.scrollWidth / 60)) + 's';
}

function footer() {
  document.querySelector('main').insertAdjacentHTML('beforeend', `<footer>${T.footer}</footer>`);
}

async function refresh(page, current) {
  if (document.hidden || !['index', 'action'].includes(page)) return current;
  const data = await loadData();
  if (!data || (current && data.tally.time === current.tally.time)) return current;
  const y = window.scrollY;
  DATA = data;
  await loadMine(data);
  const pruned = pruneBasket(data);
  renderPage(page, data);
  drawTicker(data);
  drawBasket(pruned);
  footer();
  const stamp = document.querySelector('.tally-stamp');
  if (stamp) stamp.textContent = T.tally(fmt(data.tally.block), data.tally.epoch);
  window.scrollTo(0, y);
  return data;
}

async function boot(page) {
  let data = await loadData();
  DATA = data;
  await loadMine(data);
  const pruned = data ? pruneBasket(data) : [];
  renderPage(page, data);
  chrome(data);
  drawTicker(data);
  drawBasket(pruned);
  const tick = async () => { data = await refresh(page, data); };
  setInterval(tick, REFRESH_MS);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) tick(); });
}

// Every button and choice is wired here rather than in the markup, and the
// page starts from here rather than from a script in the page, so that the
// Content-Security-Policy can refuse inline script altogether.
// On a phone the navigation folds away behind the menu button (styles.css);
// it sits inside the top bar, so it opens where the reader is.
function toggleMenu(open) {
  const on = document.body.classList.toggle('menu-open', open);
  document.querySelector('.menu-btn')?.setAttribute('aria-expanded', String(on));
}
const ACTS = {
  menu: () => toggleMenu(),
  lang: el => setLang(el.dataset.arg),
  basket: () => openBasket(),
  connect: () => connectWallet(),
  disconnect: () => disconnectWallet(),
  doc: el => openDoc(el.dataset.arg),
  another: () => answerAnother(),
  remove: el => removeAnswer(el.dataset.arg),
  clear: () => clearAnswers(),
  sign: () => { document.querySelector('.basket-modal').closeBasket(); openSigner(); },
};
document.addEventListener('click', e => {
  const el = e.target.closest && e.target.closest('[data-act]');
  if (el && ACTS[el.dataset.act]) ACTS[el.dataset.act](el);
});
document.addEventListener('change', e => {
  if (e.target.dataset && e.target.dataset.act === 'choose') choose(e.target.dataset.arg, e.target.value);
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') toggleMenu(false); });
document.addEventListener('DOMContentLoaded', () => boot(document.body.dataset.page));
