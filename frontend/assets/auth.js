// frontend/assets/auth.js
// Shared Supabase auth bootstrap for static pages.

(function bootstrapFinSightAuth() {
  const URL_KEY = "finsight.supabase.url";
  const ANON_KEY = "finsight.supabase.anon";
  const NEXT_KEY = "finsight.auth.next";

  function normalizePath(path) {
    if (!path) return "./dashboard.html";
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    if (path.startsWith("/")) return path;
    return `./${path.replace(/^\.\//, "")}`;
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

  function initializeClient() {
    if (window.supabase?.auth) return { ok: true };

    const config = getConfig();
    if (!config.configured) {
      return { ok: false, message: "Supabase URL and anon key are not configured." };
    }

    if (!window.supabaseJs?.createClient) {
      return { ok: false, message: "Supabase SDK is not loaded." };
    }

    try {
      window.supabase = window.supabaseJs.createClient(config.url, config.anonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true
        }
      });
      return { ok: true };
    } catch (err) {
      return { ok: false, message: String(err?.message || "Failed to initialize Supabase client.") };
    }
  }

  async function getSession() {
    const init = initializeClient();
    if (!init.ok || !window.supabase?.auth) return null;

    const { data, error } = await window.supabase.auth.getSession();
    if (error) return null;
    return data?.session || null;
  }

  async function signInWithGoogle(redirectTo, nextPath) {
    const init = initializeClient();
    if (!init.ok || !window.supabase?.auth) {
      return { error: new Error(init.message || "Supabase auth unavailable.") };
    }

    const safeNext = normalizePath(nextPath || "./dashboard.html");
    localStorage.setItem(NEXT_KEY, safeNext);

    return window.supabase.auth.signInWithOAuth({
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
    if (!window.supabase?.auth) return { error: null };
    return window.supabase.auth.signOut();
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
    initializeClient,
    getSession,
    signInWithGoogle,
    signOut,
    consumeNextPath
  };

  initializeClient();
})();
