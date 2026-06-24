class AdvancedCookieStorageAPI {
  constructor(options = {}) {
    this.storageKey = options.storageKey || 'cookies_storage';
    this.autoBackup = options.autoBackup !== false;
    this.encryptionKey = options.encryptionKey || null;
    
    if (this.autoBackup) {
      this.backupCookies();
      this.startAutoBackup(options.backupInterval || 60000); // Default: every minute
    }
  }

  // Simple encryption (for basic security)
  encrypt(data) {
    if (!this.encryptionKey) return data;
    // Note: For production, use a proper encryption library
    return btoa(JSON.stringify(data));
  }

  decrypt(data) {
    if (!this.encryptionKey) return data;
    try {
      return JSON.parse(atob(data));
    } catch {
      return data;
    }
  }

  getAllCookies() {
    const cookies = {};
    document.cookie.split(';').forEach(cookie => {
      if (cookie.trim()) {
        const [name, ...rest] = cookie.split('=');
        const value = rest.join('=');
        cookies[name.trim()] = decodeURIComponent(value);
      }
    });
    return cookies;
  }

  backupCookies() {
    const cookies = this.getAllCookies();
    const dataToStore = this.encryptionKey ? this.encrypt(cookies) : JSON.stringify(cookies);
    localStorage.setItem(this.storageKey, dataToStore);
    return cookies;
  }

  getStoredCookies() {
    const stored = localStorage.getItem(this.storageKey);
    if (!stored) return null;
    
    try {
      if (this.encryptionKey) {
        return this.decrypt(stored);
      }
      return JSON.parse(stored);
    } catch {
      return null;
    }
  }

  restoreCookies(restoreOptions = {}) {
    const storedCookies = this.getStoredCookies();
    if (!storedCookies) return false;

    const { path = '/', domain = '', secure = false, httpOnly = false } = restoreOptions;
    
    Object.entries(storedCookies).forEach(([name, value]) => {
      let cookieString = `${name}=${encodeURIComponent(value)}; path=${path}`;
      if (domain) cookieString += `; domain=${domain}`;
      if (secure) cookieString += `; secure`;
      if (httpOnly) cookieString += `; httponly`;
      document.cookie = cookieString;
    });
    return true;
  }

  setCookie(name, value, options = {}) {
    const { days = 7, path = '/', domain = '', secure = false } = options;
    
    let cookieString = `${name}=${encodeURIComponent(value)}; path=${path}`;
    
    if (days) {
      const expires = new Date();
      expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
      cookieString += `; expires=${expires.toUTCString()}`;
    }
    
    if (domain) cookieString += `; domain=${domain}`;
    if (secure) cookieString += `; secure`;
    
    document.cookie = cookieString;
    
    if (this.autoBackup) {
      this.backupCookies();
    }
  }

  deleteCookie(name, path = '/') {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}`;
    
    if (this.autoBackup) {
      this.backupCookies();
    }
  }

  clearAllCookies() {
    const cookies = this.getAllCookies();
    Object.keys(cookies).forEach(name => {
      this.deleteCookie(name);
    });
    localStorage.removeItem(this.storageKey);
  }

  startAutoBackup(intervalMs) {
    if (this.backupInterval) clearInterval(this.backupInterval);
    this.backupInterval = setInterval(() => this.backupCookies(), intervalMs);
  }

  stopAutoBackup() {
    if (this.backupInterval) {
      clearInterval(this.backupInterval);
      this.backupInterval = null;
    }
  }

  exportCookies() {
    return JSON.stringify(this.getStoredCookies(), null, 2);
  }

  importCookies(cookiesJson, overwrite = false) {
    try {
      const cookies = JSON.parse(cookiesJson);
      if (overwrite) {
        this.clearAllCookies();
      }
      Object.entries(cookies).forEach(([name, value]) => {
        this.setCookie(name, value);
      });
      return true;
    } catch {
      return false;
    }
  }
}

// Usage:
const advancedAPI = new AdvancedCookieStorageAPI({
  storageKey: 'my_cookies_backup',
  autoBackup: true,
  backupInterval: 30000, // Backup every 30 seconds
  encryptionKey: 'my-secret-key' // Optional
});

// Export/import functionality
const exported = advancedAPI.exportCookies();
console.log('Exported cookies:', exported);

// Import cookies from backup
advancedAPI.importCookies(exported, false);