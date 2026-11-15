// Même logique que verifcrypto/normalize.py et verifier.py, pour la page Web.
// Les deux versions sont testées avec les mêmes vecteurs (tests/vecteurs.json).

const EVM_RE = /^0x[0-9a-fA-F]{40}$/;
const BTC_RE = /^(bc1[02-9ac-hj-np-z]{11,71}|[13][1-9A-HJ-NP-Za-km-z]{25,34})$/;
const DOMAIN_RE = /^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;
const LEGAL = new Set(["inc", "incorporated", "ltd", "ltee", "limited", "llc", "llp", "lp", "plc", "corp",
  "corporation", "co", "company", "sa", "sas", "sarl", "srl", "gmbh", "ag", "pte", "bv", "ou",
  "holding", "holdings", "group", "groupe"]);
const RECUP = ["recuperation", "recovery", "recover", "recuperer", "remboursement"];

export function stripAccents(t) {
  return t.normalize("NFKD").replace(/[̀-ͯ]/g, "");
}

export function normaliserDomaine(texte) {
  let t = texte.trim().replace(/^[,;]+|[,;]+$/g, "").toLowerCase();
  t = t.replace(/^[a-z][a-z0-9+.-]*:\/\//, "");
  t = t.split("/")[0].split("?")[0].split("#")[0];
  t = t.split("@").pop().split(":")[0].replace(/^\.+|\.+$/g, "");
  if (t.startsWith("www.")) t = t.slice(4);
  if (/[^\x00-\x7f]/.test(t)) {
    try { t = new URL("http://" + t).hostname; } catch { return null; }
  }
  return DOMAIN_RE.test(t) ? t : null;
}

export function normaliserNom(texte) {
  let t = stripAccents(texte).toLowerCase().replace(/\(.*?\)/g, " ");
  const mots = t.match(/[a-z0-9]+/g) || [];
  while (mots.length && LEGAL.has(mots[mots.length - 1])) mots.pop();
  return mots.join(" ");
}

const compacter = (n) => n.replaceAll(" ", "");

export function analyser(texte) {
  const brut = texte.trim();
  if (!brut) throw new Error("Entrée vide : indiquez un site, une adresse de portefeuille ou un nom.");
  if (EVM_RE.test(brut)) return { brut, genre: "adresse_evm", valeur: brut.toLowerCase() };
  if (BTC_RE.test(brut)) return { brut, genre: "adresse_btc", valeur: brut };
  if (!brut.includes(" ") || brut.includes("://")) {
    const d = normaliserDomaine(brut);
    if (d) return { brut, genre: "site", valeur: d };
  }
  const nom = normaliserNom(brut);
  if (!nom) throw new Error("Je ne reconnais ni un site, ni une adresse, ni un nom dans cette entrée.");
  return { brut, genre: "nom", valeur: nom };
}

// Ratio de similarité de difflib (SequenceMatcher.ratio) pour de courtes chaînes
export function ratio(a, b) {
  const matches = (a1, a2, b1, b2) => {
    let best = [a1, b1, 0];
    for (let i = a1; i < a2; i++) for (let j = b1; j < b2; j++) {
      let k = 0;
      while (i + k < a2 && j + k < b2 && a[i + k] === b[j + k]) k++;
      if (k > best[2]) best = [i, j, k];
    }
    if (!best[2]) return 0;
    const [i, j, k] = best;
    return k + matches(a1, i, b1, j) + matches(i + k, a2, j + k, b2);
  };
  const total = a.length + b.length;
  return total ? (2 * matches(0, a.length, 0, b.length)) / total : 1;
}

const memeDomaine = (r, l) => r === l || r.endsWith("." + l) || l.endsWith("." + r);

export function chercher(req, donnees) {
  const out = [];
  for (const e of donnees.mises_en_garde) {
    let raison = null;
    if (req.genre === "site") {
      for (const s of e.sites || []) {
        const d = normaliserDomaine(s);
        if (d && memeDomaine(req.valeur, d)) { raison = `site « ${d} » inscrit dans la mise en garde`; break; }
      }
    } else if (req.genre === "nom") {
      const noms = [e.nom, ...(e.autres_noms || [])];
      for (const n of noms) {
        const nn = normaliserNom(n);
        if (nn && (nn === req.valeur || compacter(nn) === compacter(req.valeur))) { raison = `nom « ${n} » (correspondance exacte)`; break; }
      }
      if (!raison && req.valeur.length >= 5) {
        for (const n of noms) {
          const nn = normaliserNom(n);
          if (nn && ratio(compacter(nn), compacter(req.valeur)) >= 0.88) { raison = `nom « ${n} » (correspondance approximative : vérifiez sur la fiche)`; break; }
        }
      }
    }
    if (raison) out.push({ titre: `Mise en garde à l'encontre de : ${e.nom}`, url: e.url, date: e.date_publication, correspondance: raison, categories: e.categories || [] });
  }
  return out;
}

export function evoqueRecuperation(texte) {
  const t = stripAccents(texte.toLowerCase());
  return RECUP.some((m) => t.includes(m));
}
