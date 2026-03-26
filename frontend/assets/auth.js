// frontend/assets/auth.js
// Shared Supabase auth bootstrap for static pages.

(function bootstrapFinSightAuth() {
  const URL_KEY = "finsight.supabase.url";
  const ANON_KEY = "finsight.supabase.anon";
  const NEXT_KEY = "finsight.auth.next";
  const host = window.location.hostname;
  const IS_LOCALHOST = host === "localhost" || host === "127.0.0.1" || host === "[::1]";
  const API_BASE = window.FINSIGHT_API_BASE || (IS_LOCALHOST ? "http://localhost:8000" : "");
  let publicConfigRequested = false;

  function normalizePath(path) {
    if (!path) return "./dashboard.html";
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    if (path.startsWith("/")) return path;
    return `./${path.replace(/^\.\//, "")}`;
  }

  async function fetchPublicConfig() {
    if (publicConfigRequested) return;
    publicConfigRequested = true;

    try {
      const response = await fetch(`${API_BASE}/api/auth/public-config`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      if (!response.ok) return;

      const data = await response.json();
      if (!data?.configured) return;

      persistConfig(data.supabase_url, data.supabase_anon_key);
    } catch {
      // Ignore config bootstrap failures and allow other fallback paths.
    }
  }

  function getConfig() {
    const url = String(window.FINSIGHT_SUPABASE_URL || localStorage.getItem(URL_KEY) || "").trim();
    const anonKey = String(window.FINSIGHT_SUPABASE_ANON_KEY || localStorage.getItem(ANON_KEY) || "").trim();
    return { url, anonKey, configured: Boolean(url && anonKey) };
  }

  function persistConfig(url, anonKey) {
    const cleanUrl = String(url || "").trim();
    const cleanAnon = String(anonKey || "").trim();

    if (cleanUrl) localStorage.setItem(URL_KEY, cleanUrl);
    if (cleanAnon) localStorage.setItem(ANON_KEY, cleanAnon);
  }

  function clearConfig() {
    localStorage.removeItem(URL_KEY);
    localStorage.removeItem(ANON_KEY);
  }

  function getAuthClient() {
    return window.finsightSupabaseClient || (window.supabase?.auth ? window.supabase : null);
  }

  function getCreateClientFn() {
    if (window.supabaseJs && typeof window.supabaseJs.createClient === "function") {
      return window.supabaseJs.createClient;
    }
    if (window.supabase && typeof window.supabase.createClient === "function") {
      return window.supabase.createClient;
    }
    return null;
  }

  async function initializeClient() {
    if (getAuthClient()) return { ok: true };

    await fetchPublicConfig();

    const config = getConfig();
    if (!config.configured) {
      return { ok: false, message: "Auth is not configured yet. Please contact support." };
    }

    const createClient = getCreateClientFn();
    if (!createClient) {
      return { ok: false, message: "Supabase SDK is not loaded." };
    }

    try {
      const client = createClient(config.url, config.anonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true
        }
      });
      window.finsightSupabaseClient = client;
      // Backward compatibility with existing checks in app.js.
      window.supabase = client;
      return { ok: true };
    } catch (err) {
      return { ok: false, message: String(err?.message || "Failed to initialize Supabase client.") };
    }
  }

  async function getSession() {
    const init = await initializeClient();
    const client = getAuthClient();
    if (!init.ok || !client?.auth) return null;

    const { data, error } = await client.auth.getSession();
    if (error) return null;
    return data?.session || null;
  }

  async function signInWithGoogle(redirectTo, nextPath) {
    const init = await initializeClient();
    const client = getAuthClient();
    if (!init.ok || !client?.auth) {
      return { error: new Error(init.message || "Supabase auth unavailable.") };
    }

    const safeNext = normalizePath(nextPath || "./dashboard.html");
    localStorage.setItem(NEXT_KEY, safeNext);

    return client.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: redirectTo || window.location.href,
        queryParams: {
          prompt: "select_account"
        }
      }
    });
  }

  async function signOut() {
    const client = getAuthClient();
    if (!client?.auth) return { error: null };
    return client.auth.signOut();
  }

  function consumeNextPath(fallbackPath) {
    const fallback = normalizePath(fallbackPath || "./dashboard.html");
    const stored = localStorage.getItem(NEXT_KEY);
    localStorage.removeItem(NEXT_KEY);
    return normalizePath(stored || fallback);
  }

  window.finsightAuth = {
    getConfig,
    persistConfig,
    clearConfig,
    fetchPublicConfig,
    initializeClient,
    getSession,
    signInWithGoogle,
    signOut,
    consumeNextPath
  };

  fetchPublicConfig().then(() => {
    initializeClient();
  });
})();
