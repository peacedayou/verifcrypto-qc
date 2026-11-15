// Les mêmes vecteurs que les tests Python : les deux versions doivent répondre pareil.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { analyser, chercher, evoqueRecuperation, ratio } from "../web/verif.js";

const V = JSON.parse(readFileSync(new URL("./vecteurs.json", import.meta.url)));
const D = JSON.parse(readFileSync(new URL("../data/amf_mises_en_garde.json", import.meta.url)));

test("analyser", () => {
  for (const [e, genre, valeur] of V.analyser) assert.deepEqual([analyser(e).genre, analyser(e).valeur], [genre, valeur], e);
});

test("chercher", () => {
  for (const [e, slugs] of V.chercher) {
    const r = analyser(e);
    const found = r.genre.startsWith("adresse") ? [] : chercher(r, D).map((c) => c.url.split("/").pop());
    assert.deepEqual(found, slugs, e);
  }
});

test("récupération", () => {
  for (const [e, att] of V.recuperation) assert.equal(evoqueRecuperation(e), att, e);
});

test("ratio identique à difflib", () => {
  assert.equal(ratio("abcd", "bcde"), 0.75);
  assert.equal(ratio("novapeakbloom", "novapeakblooms"), 26 / 27);
});
