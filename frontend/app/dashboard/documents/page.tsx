"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";

import { Navbar } from "@/components/auth/navbar";
import { api, ApiError } from "@/lib/api";
import type { DocumentRecord, Indicator, Site } from "@/lib/types";

const documentTypeLabels: Record<string, string> = {
  facture_energie: "Facture énergie",
  bordereau_dechets: "Bordereau déchets",
  contrat: "Contrat",
  attestation: "Attestation",
  autre: "Autre",
};

const fieldLabels: Record<string, string> = {
  provider: "Fournisseur",
  document_date: "Date document",
  period_start: "Début période",
  period_end: "Fin période",
  amount: "Montant total",
  amount_due: "Montant à payer",
  quantity: "Quantité",
  unit: "Unité",
  gas_quantity: "Quantité gaz",
  gas_unit: "Unité gaz",
};

const editableFields = ["provider", "document_date", "period_start", "period_end", "amount", "amount_due", "quantity", "unit", "gas_quantity", "gas_unit"];
const requiredFields = ["document_date", "quantity", "unit"];

function normalizeUnit(value: string) {
  return value.trim().toLowerCase().replace("³", "3");
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [filename, setFilename] = useState("facture-energie.txt");
  const [siteId, setSiteId] = useState("");
  const [indicatorId, setIndicatorId] = useState("");
  const [rawText, setRawText] = useState("Facture énergie\nFournisseur: STEG\nDate: 2026-02-15\nTotal: 450.25\nConsommation: 1240 kWh");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentRecord | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [ocrBusy, setOcrBusy] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const [showRawText, setShowRawText] = useState(false);

  const selectDocument = useCallback((document: DocumentRecord) => {
    setSelected(document);
    setFilename(document.filename);
    setRawText(document.raw_text);
    const current = document.extracted_data?.fields ?? {};
    setFields(Object.fromEntries(editableFields.map((key) => [key, String(current[key] ?? "")])));
  }, []);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [documentData, siteData, indicatorData] = await Promise.all([
        api.get<DocumentRecord[]>("/documents"),
        api.get<Site[]>("/sites"),
        api.get<Indicator[]>("/reference/indicators"),
      ]);
      setDocuments(documentData);
      setSites(siteData);
      setIndicators(indicatorData);
      if (!selected && documentData[0]) selectDocument(documentData[0]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les documents.");
    }
  }, [selected, selectDocument]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (indicatorId || !fields.unit || indicators.length === 0) return;
    const unit = normalizeUnit(fields.unit);
    const match = indicators.find((indicator) => normalizeUnit(indicator.unit) === unit);
    if (match) setIndicatorId(String(match.id));
  }, [fields.unit, indicatorId, indicators]);

  const extractedCount = editableFields.filter((key) => fields[key]).length;
  const missingRequired = requiredFields.filter((key) => !fields[key]);
  const validationReady = missingRequired.length === 0;

  async function readFile(file: File) {
    setFilename(file.name);
    setError(null);
    setMessage(null);
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);

    if (file.type.startsWith("image/")) {
      setImageFile(file);
      setImagePreviewUrl(URL.createObjectURL(file));
      setRawText("");
      setOcrProgress(0);
      setMessage("Photo importée. Lancez l'extraction automatique, puis vérifiez les champs.");
      return;
    }

    setImageFile(null);
    setOcrProgress(0);
    setImagePreviewUrl(null);
    if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
      setRawText("");
      setError("Le PDF nécessite une étape OCR. Copiez le texte extrait ou saisissez les valeurs visibles.");
      return;
    }

    setRawText(await file.text());
  }

  async function extractTextFromImage() {
    if (!imageFile) return;
    setOcrBusy(true);
    setOcrProgress(0);
    setError(null);
    setMessage("Extraction OCR en cours...");
    let worker: Awaited<ReturnType<(typeof import("tesseract.js"))["createWorker"]>> | null = null;
    try {
      const { createWorker } = await import("tesseract.js");
      const activeWorker = await createWorker("fra+eng", 1, {
        logger: (event: { status?: string; progress?: number }) => {
          if (event.status === "recognizing text" && typeof event.progress === "number") {
            setOcrProgress(Math.round(event.progress * 100));
          }
        },
      });
      worker = activeWorker;
      const result = await activeWorker.recognize(imageFile);
      const extractedText = (result.data.text ?? "").trim();
      if (!extractedText) {
        setError("OCR terminé, mais aucun texte exploitable n'a été détecté. Essayez une photo plus nette ou complétez les champs visibles.");
        return;
      }
      setRawText(extractedText);
      setMessage("Texte extrait automatiquement. Vous pouvez maintenant analyser le document.");
    } catch {
      setError("Impossible d'extraire automatiquement le texte. Vérifiez la connexion ou complétez les valeurs visibles manuellement.");
    } finally {
      if (worker) await worker.terminate();
      setOcrBusy(false);
    }
  }

  async function uploadDocument(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const document = await api.post<DocumentRecord>("/documents", {
        filename,
        raw_text: rawText,
        site_id: siteId ? Number(siteId) : null,
      });
      selectDocument(document);
      setMessage("Document analysé.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'analyser le document.");
    } finally {
      setBusy(false);
    }
  }

  async function validateDocument() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const cleanedFields = Object.fromEntries(Object.entries(fields).filter(([, value]) => value !== ""));
      const document = await api.post<DocumentRecord>(`/documents/${selected.id}/validate`, {
        fields: cleanedFields,
        indicator_id: indicatorId ? Number(indicatorId) : null,
        site_id: siteId ? Number(siteId) : selected.site_id,
        create_environmental_entry: true,
      });
      selectDocument(document);
      setMessage("Extraction validée et intégrée si les champs sont complets.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de valider le document.");
    } finally {
      setBusy(false);
    }
  }

  async function reanalyzeDocument() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const document = await api.post<DocumentRecord>(`/documents/${selected.id}/reanalyze`);
      selectDocument(document);
      setMessage("Document réanalysé avec les règles d'extraction les plus récentes.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de réanalyser le document.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-end justify-between gap-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Traitement documentaire intelligent</p>
              <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Extraction automatique OCR</h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
                Importez une facture, extrayez le texte automatiquement, contrôlez les champs clés et intégrez la donnée au référentiel ESG.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              {[
                ["Documents", documents.length],
                ["Champs", `${extractedCount}/10`],
                ["Confiance", selected?.extracted_data?.confidence ? `${selected.extracted_data.confidence}%` : "--"],
              ].map(([label, value]) => (
                <div key={label} className="min-w-24 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <p className="text-lg font-bold text-slate-950">{value}</p>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-5 grid gap-2 md:grid-cols-3">
            {[
              ["1", "Importer", imagePreviewUrl || rawText ? "En cours" : "À faire"],
              ["2", "Extraire", rawText ? "Texte prêt" : "OCR requis"],
              ["3", "Valider", validationReady ? "Prêt" : `${missingRequired.length} champ(s) manquant(s)`],
            ].map(([step, title, state]) => (
              <div key={step} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-xs font-bold text-white">{step}</span>
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{title}</p>
                    <p className="text-xs font-medium text-slate-500">{state}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {error ? <p className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        {message ? <p className="mt-6 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

        <section className="mt-6 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <form onSubmit={uploadDocument} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold text-slate-950">Dépôt et analyse</h2>
                <p className="mt-1 text-sm text-slate-500">Photo, image ou fichier texte. L&apos;OCR se lance depuis la prévisualisation.</p>
              </div>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">OCR local</span>
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                Fichier
                <input type="file" accept=".txt,.csv,.pdf,.jpg,.jpeg,.png,.webp" onChange={(e) => e.target.files?.[0] && readFile(e.target.files[0])} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Nom
                <input value={filename} onChange={(e) => setFilename(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700 sm:col-span-2">
                Site
                <select value={siteId} onChange={(e) => setSiteId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="">Aucun site</option>
                  {sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
                </select>
              </label>
            </div>
            {imagePreviewUrl ? (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="relative h-72 w-full">
                  <Image src={imagePreviewUrl} alt={filename} fill unoptimized className="rounded-md object-contain" />
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <button type="button" onClick={extractTextFromImage} disabled={ocrBusy || busy} className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60">
                    {ocrBusy ? "Extraction..." : "Extraire automatiquement"}
                  </button>
                  {ocrBusy ? (
                    <div className="min-w-40 flex-1">
                      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                        <div className="h-full bg-emerald-600 transition-all" style={{ width: `${ocrProgress}%` }} />
                      </div>
                      <p className="mt-1 text-xs font-medium text-slate-500">{ocrProgress}%</p>
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">Texte OCR</p>
                  <p className="text-xs text-slate-500">{rawText ? `${rawText.length} caractères détectés` : "Aucun texte extrait pour le moment"}</p>
                </div>
                <button type="button" onClick={() => setShowRawText((value) => !value)} className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                  {showRawText ? "Masquer" : "Afficher"}
                </button>
              </div>
              {showRawText ? (
                <label className="mt-3 block text-sm font-medium text-slate-700">
                  Contenu extrait
                  <textarea value={rawText} onChange={(e) => setRawText(e.target.value)} rows={9} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
                </label>
              ) : null}
            </div>
            <button disabled={busy || ocrBusy || !rawText} className="mt-4 w-full rounded-lg bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:opacity-60">
              {busy ? "Analyse en cours..." : "Analyser le document"}
            </button>
          </form>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-slate-950">Contrôle et validation</h2>
                <p className="mt-1 text-sm text-slate-500">Vérifiez les valeurs avant de créer la donnée environnementale.</p>
              </div>
              {selected ? <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">{documentTypeLabels[selected.document_type]}</span> : null}
            </div>
            {selected ? (
              <>
                <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{selected.filename}</p>
                      <p className="mt-1 text-xs text-slate-500">Confiance {selected.extracted_data?.confidence ?? 0}% · statut {selected.status}</p>
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${validationReady ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                      {validationReady ? "Prêt à valider" : "À compléter"}
                    </span>
                  </div>
                  {!validationReady ? (
                    <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
                      Champs requis manquants : {missingRequired.map((key) => fieldLabels[key]).join(", ")}.
                    </p>
                  ) : null}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {editableFields.map((key) => (
                    <label key={key} className="text-sm font-medium text-slate-700">
                      {fieldLabels[key] ?? key}
                      <input value={fields[key] ?? ""} onChange={(e) => setFields({ ...fields, [key]: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                    </label>
                  ))}
                  <label className="text-sm font-medium text-slate-700 sm:col-span-2">
                    Indicateur à alimenter
                    <select value={indicatorId} onChange={(e) => setIndicatorId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                      <option value="">Non renseigné</option>
                      {indicators.map((indicator) => <option key={indicator.id} value={indicator.id}>{indicator.name}</option>)}
                    </select>
                  </label>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button type="button" onClick={validateDocument} disabled={busy || !validationReady} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">
                    Valider l&apos;extraction
                  </button>
                  <button type="button" onClick={reanalyzeDocument} disabled={busy} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60">
                    Réanalyser
                  </button>
                </div>
              </>
            ) : (
              <p className="mt-8 text-sm text-slate-500">Sélectionnez ou analysez un document pour corriger ses champs.</p>
            )}
          </div>
        </section>

        <section className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
            <div>
              <h2 className="font-semibold text-slate-950">Documents traités</h2>
              <p className="mt-1 text-xs text-slate-500">Historique des analyses et validations.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">{documents.length} document(s)</span>
          </div>
          <div className="divide-y divide-slate-100">
            {documents.map((document) => (
              <button key={document.id} type="button" onClick={() => selectDocument(document)} className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-slate-50">
                <div>
                  <p className="font-medium text-slate-900">{document.filename}</p>
                  <p className="text-xs text-slate-500">{documentTypeLabels[document.document_type]} · {document.status}</p>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{document.extracted_data?.confidence ?? 0}%</span>
              </button>
            ))}
            {documents.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-400">Aucun document.</p> : null}
          </div>
        </section>
      </main>
    </>
  );
}
