export type QueryIntentCatalogEntry = {
  intentId: string;
  label: string;
  description: string;
  exampleDescription: string;
  exampleParams: Record<string, unknown>;
  deprecated: boolean;
  replacementIntentId: string | null;
  semanticNote: string | null;
  paramsSchema: Record<string, unknown>;
};

export type RawQueryIntentCatalogEntry = {
  intent_id?: unknown;
  params_schema?: unknown;
  deprecated?: unknown;
  replacement_intent_id?: unknown;
  semantic_note?: unknown;
  example_description?: unknown;
  example_params?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toTitleLabel(intentId: string): string {
  return intentId
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function normalizeQueryIntentCatalog(
  items: RawQueryIntentCatalogEntry[]
): QueryIntentCatalogEntry[] {
  return items
    .filter((item) => typeof item.intent_id === "string" && item.intent_id.trim())
    .map((item) => {
      const intentId = String(item.intent_id).trim();
      const deprecated = item.deprecated === true;
      const replacementIntentId =
        typeof item.replacement_intent_id === "string"
          ? item.replacement_intent_id
          : null;
      const semanticNote =
        typeof item.semantic_note === "string" ? item.semantic_note : null;
      const paramsSchema = isRecord(item.params_schema) ? item.params_schema : {};

      return {
        intentId,
        label: deprecated ? `${toTitleLabel(intentId)} (deprecated)` : toTitleLabel(intentId),
        description: semanticNote ?? `Public query intent: ${intentId}`,
        exampleDescription:
          typeof item.example_description === "string"
            ? item.example_description
            : replacementIntentId
              ? `Recommended replacement: ${replacementIntentId}`
              : `Backend public intent: ${intentId}`,
        exampleParams: isRecord(item.example_params) ? item.example_params : {},
        deprecated,
        replacementIntentId,
        semanticNote,
        paramsSchema,
      };
    });
}

export function getQueryIntentCatalogEntry(
  catalog: QueryIntentCatalogEntry[],
  intentId: string
): QueryIntentCatalogEntry | null {
  const normalized = intentId.trim();

  if (!normalized) {
    return null;
  }

  return catalog.find((entry) => entry.intentId === normalized) ?? null;
}