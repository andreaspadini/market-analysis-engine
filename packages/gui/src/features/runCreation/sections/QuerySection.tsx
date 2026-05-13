// packages/gui/src/features/runCreation/sections/QuerySection.tsx
import React, { useCallback, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Stack } from "../../../components/layout/Stack";
import { Grid } from "../../../components/layout/Grid";
import type { RunCreationState } from "../state/useRunCreationState";

/**
 * G2.3 — Query Section
 * - intent_id dropdown (guard-rails from embedded registry list)
 * - Explicit param mapping per intent (no schema-driven rendering)
 * - Strict-safe: params wiped on intent change
 */

type IntentMeta = { id: string; title: string };

const INTENTS: IntentMeta[] = [
  { id: "weekday_volatility_and_breakout_success", title: "Weekday: volatilità + successo breakout" },
  { id: "retest_probability_by_session_minutes", title: "Retest: probabilità entro X minuti (per sessione)" },
  { id: "volatility_by_weekday_raw", title: "Volatilità per weekday (raw)" },
  { id: "success_by_weekday_raw", title: "Successo breakout per weekday (raw)" },
  { id: "prev_day_vwap_acceptance_rates_h60", title: "Acceptance su VWAP (prev day) — rates h60" },
  { id: "p_success_given_prev_day_poc_accept5m_h60", title: "P(success | POC acceptance 5m prev day) — h60" },
  { id: "success_by_weekday_session_raw", title: "Successo breakout per weekday + session (raw)" },
  { id: "p_success_given_retest_raw", title: "P(success | retest) (raw)" },
  { id: "p_success_given_retest_by_horizon_session_direction_raw", title: "P(success | retest) by horizon + session + direction (raw)" },
  { id: "retest_first_bucket_counts_raw", title: "Bucket temporali del primo retest (raw)" },
  { id: "success_by_weekday_session", title: "Successo breakout per weekday + session (report)" },
  { id: "prev_day_level_acceptance_h60", title: "Acceptance su level (prev day, h60) — report" },
  { id: "prev_day_conditional_success_given_level_accept5m_h60", title: "P(success | acceptance 5m su level prev day, h60) — report" },
  { id: "vah_first_close_above_bucket_counts_raw", title: "VAH: bucket del primo close sopra (counts, raw)" },
  { id: "time_above_vah_bucket_h60", title: "Tempo sopra VAH (bucket primo close sopra) — report" },
  { id: "level_time_confirm_h60", title: "LV04: timing conferma livello (first close bucket) h60" },
  { id: "win01_success_by_w0900_1300_vol_bucket_report", title: "WIN01: success by 09:00-13:00 vol bucket" },
  { id: "mp06_success_accept5m_high_vol_report", title: "MP06: success given accept5m in high vol by session" },
  { id: "mp07_success_accept5m_by_delta_sign_report", title: "MP07: success accept5m by delta sign (with avg init delta/volume) per session" },
  { id: "win03_success_by_bucket_and_init_vol_delta_report", title: "WIN03: success by window bucket + init vol bucket + init delta bucket" },
  { id: "success_by_weekday_report", title: "Successo breakout per weekday (report)" },
  { id: "success_by_weekday", title: "success_by_weekday" },
  { id: "volatility_by_weekday", title: "volatility_by_weekday" },
  { id: "success_by_month", title: "success_by_month" },
  { id: "success_by_day_of_month", title: "success_by_day_of_month" },
  { id: "success_by_week_of_month", title: "success_by_week_of_month" },
  { id: "success_by_hour", title: "success_by_hour" },
  { id: "success_by_day_of_month_and_hour", title: "success_by_day_of_month_and_hour" },
  { id: "volatility_by_day_of_month", title: "volatility_by_day_of_month" },
  { id: "volatility_by_hour", title: "volatility_by_hour" },
  { id: "volatility_by_month", title: "volatility_by_month" },
  { id: "success_by_month_best", title: "Ranking: mese con più successo" },
  { id: "success_by_month_worst", title: "Ranking: mese con meno successo" },
  { id: "volatility_by_hour_best", title: "Ranking: ora più volatile" },
  { id: "volatility_by_hour_worst", title: "Ranking: ora meno volatile" },
  { id: "volatility_by_day_of_month_best", title: "Ranking: giorno del mese più volatile" },
  { id: "volatility_by_day_of_month_worst", title: "Ranking: giorno del mese meno volatile" },
  { id: "compare_volatility_by_weekday", title: "Confronto volatilità per giorno della settimana" },
  { id: "compare_success_by_weekday", title: "Confronto successo per giorno della settimana" },
  { id: "compare_volatility_by_day_of_month", title: "Confronto volatilità per giorno del mese" },
  { id: "compare_volatility_by_hour", title: "Confronto volatilità per ora" },
  { id: "compare_success_by_month", title: "Confronto successo per mese" },
  { id: "compare_volatility_by_weekday", title: "Confronto volatilità per giorno della settimana" },
  { id: "compare_success_by_weekday", title: "Confronto successo per giorno della settimana" },
  { id: "compare_volatility_by_day_of_month", title: "Confronto volatilità per giorno del mese" },
  { id: "compare_volatility_by_hour", title: "Confronto volatilità per ora" },
  { id: "compare_success_by_month", title: "Confronto successo per mese" },
  { id: "compare_success_by_day_of_month", title: "Confronto successo per giorno del mese" },
  { id: "compare_success_by_week_of_month", title: "Confronto successo per settimana del mese" }
];

const SUPPORTED_INTENTS_V1 = new Set<string>([
  "weekday_volatility_and_breakout_success",
  "retest_probability_by_session_minutes",
  "volatility_by_weekday_raw",
  "success_by_weekday_raw",
  "prev_day_vwap_acceptance_rates_h60",
  "p_success_given_prev_day_poc_accept5m_h60",
  "success_by_weekday_session_raw",
  "p_success_given_retest_raw",
  "p_success_given_retest_by_horizon_session_direction_raw",
  "retest_first_bucket_counts_raw",
  "success_by_weekday_session",
  "prev_day_level_acceptance_h60",
  "prev_day_conditional_success_given_level_accept5m_h60",
  "vah_first_close_above_bucket_counts_raw",
  "time_above_vah_bucket_h60",
  "level_time_confirm_h60",
  "win01_success_by_w0900_1300_vol_bucket_report",
  "mp06_success_accept5m_high_vol_report",
  "mp07_success_accept5m_by_delta_sign_report",
  "win03_success_by_bucket_and_init_vol_delta_report",
  "success_by_weekday_report",
  "success_by_weekday",
  "volatility_by_weekday",
  "success_by_month",
  "success_by_day_of_month",
  "success_by_week_of_month",
  "success_by_hour",
  "success_by_day_of_month_and_hour",
  "volatility_by_day_of_month",
  "volatility_by_hour",
  "volatility_by_month",
  "success_by_month_best",
  "success_by_month_worst",
  "volatility_by_hour_best",
  "volatility_by_hour_worst",
  "volatility_by_day_of_month_best",
  "volatility_by_day_of_month_worst",
  "compare_volatility_by_weekday",
  "compare_success_by_weekday",
  "compare_volatility_by_day_of_month",
  "compare_volatility_by_hour",
  "compare_success_by_month",
  "compare_volatility_by_weekday",
  "compare_success_by_weekday",
  "compare_volatility_by_day_of_month",
  "compare_volatility_by_hour",
  "compare_success_by_month",
  "compare_success_by_day_of_month",
  "compare_success_by_week_of_month"
]);

export function QuerySection({
  runCreation,
}: {
  runCreation: RunCreationState;
}) {
  const {
    pipelineParametersV1,
    setQueryIntentId,
    setQueryParam,
    removeQueryParam,
    setEngineField,
  } = runCreation;

  const selectedIntentId = pipelineParametersV1.engines.query.intent_id;
  const params = pipelineParametersV1.engines.query.params;

  const intentOptions = useMemo(
    () => [...INTENTS].sort((a, b) => a.id.localeCompare(b.id)),
    []
  );

  const onChangeIntent = useCallback(
    (nextIntentId: string) => {
      if (!SUPPORTED_INTENTS_V1.has(nextIntentId)) return;

      setQueryIntentId(nextIntentId);
      setEngineField("query", "params", {});
    },
    [setQueryIntentId, setEngineField]
  );

  const isSupported = selectedIntentId ? SUPPORTED_INTENTS_V1.has(selectedIntentId) : true;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Query</CardTitle>
      </CardHeader>

      <CardContent>
        <Stack gap={16}>
          <div className="subtle">
            Select an intent only if you want a query report in the run results.
          </div>

          <Grid columns="1fr 1fr" gap={16}>
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: 12,
                  opacity: 0.8,
                  marginBottom: 6,
                }}
              >
                Query intent
              </label>
              <select
                value={selectedIntentId}
                onChange={(e) => onChangeIntent(e.target.value)}
                style={{ width: "100%", padding: 8, borderRadius: 8 }}
              >
                <option value="">— no query —</option>
                {intentOptions.map((opt) => (
                  <option key={opt.id} value={opt.id}>
                    {opt.title || opt.id}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  fontSize: 12,
                  opacity: 0.8,
                  marginBottom: 6,
                }}
              >
                Status
              </label>
              <div className="pill">
                {selectedIntentId ? "Intent selected" : "Optional section"}
              </div>
            </div>
          </Grid>

          {!selectedIntentId && (
            <div className="subtle">
              Leave this empty to run the pipeline without a query step configuration from the UI.
            </div>
          )}

          {selectedIntentId && !isSupported && (
            <div
              style={{
                padding: 12,
                borderRadius: 10,
                background: "rgba(255, 165, 0, 0.12)",
                border: "1px solid rgba(255, 165, 0, 0.25)",
              }}
            >
              <div style={{ fontWeight: 700 }}>Intent not supported in V1</div>
              <div style={{ fontSize: 13, opacity: 0.9, marginTop: 4 }}>
                This intent exists but is not enabled for the current explicit UI mapping.
              </div>
            </div>
          )}

          {selectedIntentId && isSupported && (
            <div style={{ maxHeight: 260, overflowY: "auto" }}>
              {renderParamsForm(selectedIntentId, params, setQueryParam, removeQueryParam)}
            </div>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

type ParamsObject = Record<string, unknown>;

function renderParamsForm(
  intentId: string,
  params: ParamsObject,
  setQueryParam: (key: string, value: unknown) => void,
  removeQueryParam: (key: string) => void
) {
  switch (intentId) {
    case "weekday_volatility_and_breakout_success":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>weekday</label>
                <select
                  value={(params["weekday"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("weekday");
                    else setQueryParam("weekday", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"Monday"} value={"Monday"}>{"Monday"}</option>
                  <option key={"Tuesday"} value={"Tuesday"}>{"Tuesday"}</option>
                  <option key={"Wednesday"} value={"Wednesday"}>{"Wednesday"}</option>
                  <option key={"Thursday"} value={"Thursday"}>{"Thursday"}</option>
                  <option key={"Friday"} value={"Friday"}>{"Friday"}</option>
                  <option key={"Saturday"} value={"Saturday"}>{"Saturday"}</option>
                  <option key={"Sunday"} value={"Sunday"}>{"Sunday"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "retest_probability_by_session_minutes":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>session</label>
                <select
                  value={(params["session"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("session");
                    else setQueryParam("session", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"asia"} value={"asia"}>{"asia"}</option>
                  <option key={"europe"} value={"europe"}>{"europe"}</option>
                  <option key={"usa"} value={"usa"}>{"usa"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>minutes</label>
                <input
                  type="number"
                  value={typeof params["minutes"] === "number" ? String(params["minutes"] as number) : ""}
                  min={1}
                  max={240}
                  onChange={(e) => {
                    const raw = e.target.value;
                    if (raw === "") removeQueryParam("minutes");
                    else setQueryParam("minutes", Number(raw));
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_weekday_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "success_by_weekday_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>weekday</label>
                <input
                  type="text"
                  value={(params["weekday"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("weekday");
                    else setQueryParam("weekday", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "prev_day_vwap_acceptance_rates_h60":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "p_success_given_prev_day_poc_accept5m_h60":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "success_by_weekday_session_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "p_success_given_retest_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "p_success_given_retest_by_horizon_session_direction_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "retest_first_bucket_counts_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "success_by_weekday_session":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>weekday</label>
                <select
                  value={(params["weekday"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("weekday");
                    else setQueryParam("weekday", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"Monday"} value={"Monday"}>{"Monday"}</option>
                  <option key={"Tuesday"} value={"Tuesday"}>{"Tuesday"}</option>
                  <option key={"Wednesday"} value={"Wednesday"}>{"Wednesday"}</option>
                  <option key={"Thursday"} value={"Thursday"}>{"Thursday"}</option>
                  <option key={"Friday"} value={"Friday"}>{"Friday"}</option>
                  <option key={"Saturday"} value={"Saturday"}>{"Saturday"}</option>
                  <option key={"Sunday"} value={"Sunday"}>{"Sunday"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>session</label>
                <select
                  value={(params["session"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("session");
                    else setQueryParam("session", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"asia"} value={"asia"}>{"asia"}</option>
                  <option key={"europe"} value={"europe"}>{"europe"}</option>
                  <option key={"usa"} value={"usa"}>{"usa"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "prev_day_level_acceptance_h60":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>level</label>
                <select
                  value={(params["level"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("level");
                    else setQueryParam("level", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"vah"} value={"vah"}>{"vah"}</option>
                  <option key={"val"} value={"val"}>{"val"}</option>
                  <option key={"poc"} value={"poc"}>{"poc"}</option>
                  <option key={"vwap"} value={"vwap"}>{"vwap"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>minutes</label>
                <select
                  value={(params["minutes"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("minutes");
                    else setQueryParam("minutes", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={5} value={5}>{5}</option>
                  <option key={10} value={10}>{10}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>side</label>
                <select
                  value={(params["side"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("side");
                    else setQueryParam("side", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"above"} value={"above"}>{"above"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "prev_day_conditional_success_given_level_accept5m_h60":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>level</label>
                <select
                  value={(params["level"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("level");
                    else setQueryParam("level", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"vah"} value={"vah"}>{"vah"}</option>
                  <option key={"val"} value={"val"}>{"val"}</option>
                  <option key={"poc"} value={"poc"}>{"poc"}</option>
                  <option key={"vwap"} value={"vwap"}>{"vwap"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "vah_first_close_above_bucket_counts_raw":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "time_above_vah_bucket_h60":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>minutes</label>
                <input
                  type="number"
                  value={typeof params["minutes"] === "number" ? String(params["minutes"] as number) : ""}
                  min={0}
                  max={240}
                  onChange={(e) => {
                    const raw = e.target.value;
                    if (raw === "") removeQueryParam("minutes");
                    else setQueryParam("minutes", Number(raw));
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>mode</label>
                <select
                  value={(params["mode"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("mode");
                    else setQueryParam("mode", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"nearest"} value={"nearest"}>{"nearest"}</option>
                  <option key={"at_least"} value={"at_least"}>{"at_least"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "level_time_confirm_h60":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>level</label>
                <select
                  value={(params["level"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("level");
                    else setQueryParam("level", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"vah"} value={"vah"}>{"vah"}</option>
                  <option key={"val"} value={"val"}>{"val"}</option>
                  <option key={"poc"} value={"poc"}>{"poc"}</option>
                  <option key={"vwap"} value={"vwap"}>{"vwap"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>side</label>
                <select
                  value={(params["side"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("side");
                    else setQueryParam("side", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"above"} value={"above"}>{"above"}</option>
                  <option key={"below"} value={"below"}>{"below"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>minutes</label>
                <input
                  type="number"
                  value={typeof params["minutes"] === "number" ? String(params["minutes"] as number) : ""}
                  min={1}
                  max={240}
                  onChange={(e) => {
                    const raw = e.target.value;
                    if (raw === "") removeQueryParam("minutes");
                    else setQueryParam("minutes", Number(raw));
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>mode</label>
                <select
                  value={(params["mode"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("mode");
                    else setQueryParam("mode", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"nearest"} value={"nearest"}>{"nearest"}</option>
                  <option key={"at_least"} value={"at_least"}>{"at_least"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "win01_success_by_w0900_1300_vol_bucket_report":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>bucket</label>
                <input
                  type="text"
                  value={(params["bucket"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("bucket");
                    else setQueryParam("bucket", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "mp06_success_accept5m_high_vol_report":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>session</label>
                <select
                  value={(params["session"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("session");
                    else setQueryParam("session", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"asia"} value={"asia"}>{"asia"}</option>
                  <option key={"europe"} value={"europe"}>{"europe"}</option>
                  <option key={"usa"} value={"usa"}>{"usa"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "mp07_success_accept5m_by_delta_sign_report":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>session</label>
                <select
                  value={(params["session"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("session");
                    else setQueryParam("session", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"asia"} value={"asia"}>{"asia"}</option>
                  <option key={"europe"} value={"europe"}>{"europe"}</option>
                  <option key={"usa"} value={"usa"}>{"usa"}</option>
                </select>
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "win03_success_by_bucket_and_init_vol_delta_report":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>wbucket</label>
                <input
                  type="text"
                  value={(params["wbucket"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("wbucket");
                    else setQueryParam("wbucket", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>volbucket</label>
                <input
                  type="text"
                  value={(params["volbucket"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("volbucket");
                    else setQueryParam("volbucket", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>deltabucket</label>
                <input
                  type="text"
                  value={(params["deltabucket"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("deltabucket");
                    else setQueryParam("deltabucket", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_weekday_report":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "success_by_weekday":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>weekday</label>
                <input
                  type="text"
                  value={(params["weekday"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("weekday");
                    else setQueryParam("weekday", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_weekday":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>weekday</label>
                <input
                  type="text"
                  value={(params["weekday"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("weekday");
                    else setQueryParam("weekday", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>month</label>
                <input
                  type="text"
                  value={(params["month"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("month");
                    else setQueryParam("month", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_day_of_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>day_of_month</label>
                <input
                  type="text"
                  value={(params["day_of_month"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("day_of_month");
                    else setQueryParam("day_of_month", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_week_of_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>week_of_month</label>
                <input
                  type="text"
                  value={(params["week_of_month"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("week_of_month");
                    else setQueryParam("week_of_month", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_hour":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>hour</label>
                <input
                  type="text"
                  value={(params["hour"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("hour");
                    else setQueryParam("hour", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_day_of_month_and_hour":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>day_of_month</label>
                <input
                  type="text"
                  value={(params["day_of_month"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("day_of_month");
                    else setQueryParam("day_of_month", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>hour</label>
                <input
                  type="text"
                  value={(params["hour"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("hour");
                    else setQueryParam("hour", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_day_of_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>day_of_month</label>
                <input
                  type="text"
                  value={(params["day_of_month"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("day_of_month");
                    else setQueryParam("day_of_month", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_hour":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>hour</label>
                <input
                  type="text"
                  value={(params["hour"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("hour");
                    else setQueryParam("hour", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.8, fontSize: 13 }}>No params for this intent.</div>
          </CardContent>
        </Card>
      );

    case "success_by_month_best":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>rank</label>
                <select
                  value={(params["rank"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("rank");
                    else setQueryParam("rank", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"best"} value={"best"}>{"best"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "success_by_month_worst":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>rank</label>
                <select
                  value={(params["rank"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("rank");
                    else setQueryParam("rank", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"worst"} value={"worst"}>{"worst"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_hour_best":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>rank</label>
                <select
                  value={(params["rank"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("rank");
                    else setQueryParam("rank", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"best"} value={"best"}>{"best"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_hour_worst":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>rank</label>
                <select
                  value={(params["rank"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("rank");
                    else setQueryParam("rank", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"worst"} value={"worst"}>{"worst"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_day_of_month_best":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>rank</label>
                <select
                  value={(params["rank"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("rank");
                    else setQueryParam("rank", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"best"} value={"best"}>{"best"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "volatility_by_day_of_month_worst":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>rank</label>
                <select
                  value={(params["rank"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("rank");
                    else setQueryParam("rank", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">—</option>
                  <option key={"worst"} value={"worst"}>{"worst"}</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_volatility_by_weekday":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_success_by_weekday":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_volatility_by_day_of_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_volatility_by_hour":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_success_by_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_success_by_day_of_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    case "compare_success_by_week_of_month":
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <Stack gap={12}>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>a</label>
                <input
                  type="text"
                  value={(params["a"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("a");
                    else setQueryParam("a", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>b</label>
                <input
                  type="text"
                  value={(params["b"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("b");
                    else setQueryParam("b", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, opacity: 0.8, marginBottom: 6 }}>title</label>
                <input
                  type="text"
                  value={(params["title"] as string) ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") removeQueryParam("title");
                    else setQueryParam("title", v);
                  }}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                />
              </div>
            </Stack>
          </CardContent>
        </Card>
      );

    default:
      return (
        <Card>
          <CardHeader>
            <CardTitle>Query parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ opacity: 0.85, fontSize: 13 }}>
              No UI mapping for this intent.
            </div>
          </CardContent>
        </Card>
      );
  }
}