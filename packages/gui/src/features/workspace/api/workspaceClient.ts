import type {
  O6QueryPublicIntentCatalogResponse,
  O6ArtifactManifestResponse,
  O6Client,
} from "../../../api/bindings/o6";
import type {
  PatternRunRequest,
  PatternRunSubmitResponse,
  QueryRunRequest,
  QueryRunSubmitResponse,
  RootRunRequest,
  RootRunSubmitResponse,
  StatisticalRunRequest,
  StatisticalRunSubmitResponse,
} from "../model/workspaceTypes";


export type WorkspaceClient = {
  postRootRun(payload: RootRunRequest): Promise<RootRunSubmitResponse>;
  postStatisticalRun(
    payload: StatisticalRunRequest
  ): Promise<StatisticalRunSubmitResponse>;
  postQueryRun(payload: QueryRunRequest): Promise<QueryRunSubmitResponse>;
  postPatternRun(
    payload: PatternRunRequest
  ): Promise<PatternRunSubmitResponse>;
  getArtifactManifest(
    toolId: string,
    fingerprint: string
  ): Promise<O6ArtifactManifestResponse>;
  getArtifactJson<T = unknown>(
    toolId: string,
    fingerprint: string,
    relpath: string
  ): Promise<T>;
  getQueryPublicIntentCatalog(): Promise<O6QueryPublicIntentCatalogResponse>;
};

export function createWorkspaceClient(o6Client: O6Client): WorkspaceClient {
  return {
    async postRootRun(payload) {
      const response = await o6Client.postRootRun({
        api_version: "1.0",
        dataset: payload.dataset,
        config: payload.config,
      });

      return {
        run_id: response.run_id,
        artifact: response.artifact ?? null,
      };
    },


    async postStatisticalRun(payload) {
      const response = await o6Client.postStatisticalRun({
        api_version: "1.0",
        root_artifact_ref: payload.root_artifact_ref,
        config: payload.config,
      });
    
    

      return {
        run_id: response.run_id,
        artifact: response.artifact ?? null,
      };
    },

    async postQueryRun(payload) {
      const response = await o6Client.postQueryRun({
        api_version: "1.0",
        statistical_artifact_ref: payload.statistical_artifact_ref,
        intent_id: payload.query.intent_id,
        params: payload.query.params,
      });

      return {
        run_id: response.run_id,
        artifact: response.artifact ?? null,
      };
    },

    async postPatternRun(payload) {
      const response = await o6Client.postPatternRun({
        api_version: "1.0",
        dataset: payload.dataset,
        config: payload.config,
      });

      return {
        run_id: response.run_id,
        artifact: response.artifact ?? null,
      };
    },

    
    getArtifactManifest(toolId, fingerprint) {
      return o6Client.getArtifactManifest(toolId, fingerprint);
    },

    getArtifactJson(toolId, fingerprint, relpath) {
      return o6Client.getArtifactJson(toolId, fingerprint, relpath);
    },

    getQueryPublicIntentCatalog() {
      return o6Client.getQueryPublicIntentCatalog();
    },
  };
}