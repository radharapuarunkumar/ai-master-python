/**
 * Auth state management.
 * Firebase is the source of truth; localStorage is a fast-load cache.
 * Cookies (httpOnly JWTs) are managed by the backend automatically.
 */

const Auth = {
  USER_KEY: "amp_user",

  /** Store user profile after login */
  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  /** Retrieve cached user object (may be stale) */
  getUser() {
    try {
      return JSON.parse(localStorage.getItem(this.USER_KEY) || "null");
    } catch { return null; }
  },

  /** Clear all local auth state */
  clear() {
    localStorage.removeItem(this.USER_KEY);
  },

  /** True if we have a locally cached user */
  isLoggedIn() {
    return !!this.getUser();
  },

  /** Fetch fresh user from API and update cache */
  async refreshUser() {
    try {
      const user = await API.AuthApi.me();
      this.setUser(user);
      return user;
    } catch {
      this.clear();
      return null;
    }
  },

  /**
   * Guard: ensures the user is authenticated before allowing page access.
   * Checks localStorage first (instant), then API (authoritative).
   * Redirects to login if unauthenticated.
   */
  async requireAuth() {
    const cached = this.getUser();
    if (!cached) {
      const user = await this.refreshUser();
      if (!user) {
        window.location.href = "/frontend/pages/login.html";
        return null;
      }
      return user;
    }
    return cached;
  },

  /** Guard: redirect to dashboard if already authenticated */
  async requireGuest() {
    const user = await this.refreshUser();
    if (user) {
      window.location.href = "/frontend/pages/dashboard.html";
    }
  },

  /**
   * Logout: signs out of Firebase, clears local state, calls backend logout,
   * then redirects to login.
   */
  async logout() {
    // 1. Sign out of Firebase (clears Firebase session)
    try {
      if (typeof FirebaseAuth !== "undefined") {
        await FirebaseAuth.signOutUser();
      }
    } catch (e) {
      console.warn("[Auth] Firebase sign-out error:", e);
    }
    // 2. Clear local cache
    this.clear();
    // 3. Tell backend to clear httpOnly cookies
    try { await API.AuthApi.logout(); } catch {}
    // 4. Redirect
    window.location.href = "/frontend/pages/login.html";
  },
};

window.Auth = Auth;

/* ── Toast utility ───────────────────────────────────────── */
const Toast = {
  show(message, type = 'info', duration = 3000) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration + 300);
  },
  success: (msg) => Toast.show(msg, 'success'),
  error:   (msg) => Toast.show(msg, 'error'),
  info:    (msg) => Toast.show(msg, 'info'),
};
window.Toast = Toast;

/* ── Sidebar builder ─────────────────────────────────────── */
const Sidebar = {
  NAV: [
    { icon: '⊞', label: 'Dashboard',    href: '/frontend/pages/dashboard.html',    section: null },
    { section: 'Learn' },
    { icon: '📚', label: 'Courses',      href: '/frontend/pages/courses.html' },
    { icon: '▶',  label: 'My Progress',  href: '/frontend/pages/progress.html' },
    { icon: '🗂', label: 'Projects',     href: '/frontend/pages/projects.html' },
    { section: 'AI Tools' },
    { icon: '💬', label: 'AI Chat',      href: '/frontend/pages/chat.html' },
    { icon: '🎙', label: 'AI Tutor',     href: '/frontend/pages/tutor.html' },
    { icon: '🎯', label: 'Interview',    href: '/frontend/pages/interview.html' },
    { section: 'Career' },
    { icon: '📄', label: 'Resume',       href: '/frontend/pages/resume.html' },
    { icon: '🏆', label: 'Certificates', href: '/frontend/pages/certificates.html' },
  ],

  render(activePage = '') {
    const user = Auth.getUser();
    const initials = user ? user.full_name?.split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2) : '??';

    const navHtml = this.NAV.map(item => {
      if (item.section) {
        return `<div class="nav-section-label">${item.section}</div>`;
      }
      const active = activePage && item.href?.includes(activePage) ? 'active' : '';
      const badge = item.badge ? `<span class="nav-badge">${item.badge}</span>` : '';
      return `
        <a class="nav-item ${active}" href="${item.href}">
          <span class="nav-item-icon">${item.icon}</span>
          <span>${item.label}</span>
          ${badge}
        </a>`;
    }).join('');

    const roleBadge = { admin: '👑 Admin', premium: '⭐ Premium', free: 'Free' };

    return `
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-logo">
          <div class="sidebar-logo-icon">🐍</div>
          <div>
            <div class="sidebar-logo-text">AI Master Python</div>
            <div class="sidebar-logo-sub">Learning Platform</div>
          </div>
        </div>
        <nav class="sidebar-nav">${navHtml}</nav>
        <div class="sidebar-footer">
          <div class="sidebar-user" onclick="Auth.logout()">
            <div class="avatar-placeholder">${initials}</div>
            <div class="sidebar-user-info">
              <div class="sidebar-user-name">${user?.full_name || 'Guest'}</div>
              <div class="sidebar-user-role">${roleBadge[user?.role] || 'Free'}</div>
            </div>
            <span style="color:var(--text-muted);font-size:0.8rem">↪</span>
          </div>
        </div>
      </aside>
      <div class="sidebar-overlay" id="sidebar-overlay" onclick="Sidebar.close()"></div>`;
  },

  init(activePage) {
    const placeholder = document.getElementById('sidebar-placeholder');
    if (placeholder) placeholder.outerHTML = this.render(activePage);
    // Hamburger
    document.getElementById('hamburger-btn')?.addEventListener('click', () => this.toggle());
  },

  toggle() {
    document.getElementById('sidebar')?.classList.toggle('open');
    document.getElementById('sidebar-overlay')?.classList.toggle('open');
  },
  close() {
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('sidebar-overlay')?.classList.remove('open');
  },
};
window.Sidebar = Sidebar;

/* ── Helpers ─────────────────────────────────────────────── */
const Utils = {
  /** Format a number with K/M abbreviation */
  formatNum: (n) => n >= 1000000 ? `${(n/1000000).toFixed(1)}M` : n >= 1000 ? `${(n/1000).toFixed(1)}K` : String(n),

  /** Convert minutes to human-readable */
  formatMinutes: (m) => m >= 60 ? `${Math.floor(m/60)}h ${m%60}m` : `${m}m`,

  /** Relative time */
  timeAgo: (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)   return 'just now';
    if (mins < 60)  return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins/60)}h ago`;
    return `${Math.floor(mins/1440)}d ago`;
  },

  /** Difficulty colour */
  difficultyBadge: (level) => {
    const map = { beginner:'success', intermediate:'warning', advanced:'danger' };
    return `<span class="badge badge-${map[level]||'brand'}">${level}</span>`;
  },

  /** Lesson type icon */
  lessonTypeIcon: (type) => ({
    reading:'📖', video:'▶', exercise:'💻', quiz:'❓', project:'🛠'
  }[type] || '📄'),

  /** Build skeleton rows */
  skeletons: (count, height = '80px') =>
    Array(count).fill(0).map(() =>
      `<div class="skeleton" style="height:${height};border-radius:var(--r-md)"></div>`
    ).join(''),
};
window.Utils = Utils;
