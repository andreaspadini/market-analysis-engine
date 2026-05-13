export type HttpErrorCode = "HTTP_ERROR" | "NETWORK_ERROR";

export type HttpError = {
  code: HttpErrorCode;
  status: number | null;
  message: string;
};

export type HttpResponseType = "json" | "text" | "arraybuffer";

export type HttpClient = {
  post<TResponse>(path: string, body: unknown): Promise<TResponse>;
  get<TResponse>(
    path: string,
    options?: { responseType?: HttpResponseType }
  ): Promise<TResponse>;
};

function normalizeBaseUrl(baseUrl: string): string {
  const trimmed = baseUrl.trim();
  if (!trimmed) return "";
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

function joinUrl(baseUrl: string, path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${p}`;
}

function messageFromStatus(status: number): string {
  if (status === 400) return "Bad request.";
  if (status === 401) return "Unauthorized.";
  if (status === 403) return "Forbidden.";
  if (status === 404) return "Not found.";
  if (status === 409) return "Conflict.";
  if (status === 422) return "Validation error.";
  if (status === 429) return "Too many requests.";
  if (status >= 500) return "Server error.";
  return "Request failed.";
}

async function parseJsonSafe(res: Response): Promise<any | null> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function buildHttpError(res: Response, body: any | null): HttpError {
  const message =
    body && body.message ? String(body.message) : messageFromStatus(res.status);

  const err = {
    code: "HTTP_ERROR" as const,
    status: res.status,
    message,
    error_code: body?.error_code,
    details: body?.details,
  } as HttpError & {
    error_code?: string;
    details?: unknown;
  };

  console.error("FULL BACKEND ERROR:", {
    status: res.status,
    body,
  });

  return err;
}

export function createHttpClient(baseUrl: string): HttpClient {
  const base = normalizeBaseUrl(baseUrl);

  async function request<TResponse>(
    method: "GET" | "POST",
    path: string,
    body?: unknown,
    options?: { responseType?: HttpResponseType }
  ): Promise<TResponse> {
    const url = joinUrl(base, path);

    let res: Response;
    try {
      res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: method === "POST" ? JSON.stringify(body ?? {}) : undefined,
      });
    } catch (error: unknown) {
      const err: HttpError = {
        code: "NETWORK_ERROR",
        status: null,
        message:
          error instanceof Error && error.message
            ? `Network error: ${error.message}`
            : "Network error.",
      };
      throw err;
    }

    if (!res.ok) {
      const parsed = await parseJsonSafe(res);
      throw buildHttpError(res, parsed);
    }

    const responseType = options?.responseType;

    if (responseType === "arraybuffer") {
      return (await res.arrayBuffer()) as TResponse;
    }

    if (responseType === "text") {
      return (await res.text()) as unknown as TResponse;
    }

    const contentType = res.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      return (await res.json()) as TResponse;
    }

    // fallback: text (csv, plain, ecc.)
    return (await res.text()) as unknown as TResponse;
  }

  return {
    post: <TResponse>(path: string, body: unknown) =>
      request<TResponse>("POST", path, body),

    get: <TResponse>(
      path: string,
      options?: { responseType?: HttpResponseType }
    ) => request<TResponse>("GET", path, undefined, options),
  };
}